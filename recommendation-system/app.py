#!/usr/bin/env python3
"""
资源推荐系统 - 基于物品的协同过滤
提供个性化资源推荐服务
"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import mysql.connector
import redis
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import TruncatedSVD
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RecommendationSystem:
    """推荐系统核心类"""

    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.redis_client = None
        self.db_conn = None
        self.model = None  # 兼容旧代码：等同 item_cf
        self.model_item_cf = None
        self.model_user_cf = None
        self.svd_model = None
        self.interaction_matrix = None  # csr 用户×资源，供 User-CF / SVD 推理
        self.resource_ids = None
        self.user_ids = None
        self.user_index_map = None
        self.resource_index_map = None
        self.last_train_time = None

        # 配置
        self.config = {
            'mysql': {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'database': os.getenv('MYSQL_DATABASE', 'resource_db'),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', '123456')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'password': os.getenv('REDIS_PASSWORD', None)
            },
            'model': {
                'n_neighbors': 20,  # 邻居数量
                'metric': 'cosine',  # 相似度度量
                'min_interactions': 3  # 最小交互次数
            },
            'cache': {
                'ttl': 3600,  # 缓存时间（秒）
                'prefix': 'rec:'
            }
        }

        # 注册路由
        self.setup_routes()

    def _convert_numpy_types(self, obj):
        """将numpy类型转换为Python原生类型，确保JSON可序列化"""
        import numpy as np

        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    def setup_routes(self):
        """设置API路由"""
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

        @self.app.route('/recommendations/<int:user_id>', methods=['GET'])
        def get_recommendations(user_id):
            """获取用户推荐"""
            try:
                limit = int(request.args.get('limit', 10))
                exclude_viewed = request.args.get('exclude_viewed', 'true').lower() == 'true'

                algorithm = request.args.get('algorithm', 'item_cf').strip().lower()
                recommendations = self.recommend_for_user(
                    user_id, limit, exclude_viewed, algorithm=algorithm
                )
                preview = [x.get('resource_id') for x in recommendations[:8]]
                logger.info(
                    "GET /recommendations/%s algo=%s count=%s preview_ids=%s",
                    user_id, algorithm, len(recommendations), preview
                )
                response_data = {
                    'success': True,
                    'user_id': user_id,
                    'algorithm': algorithm,
                    'recommendations': recommendations,
                    'count': len(recommendations)
                }
                # 转换numpy类型确保JSON可序列化
                response_data = self._convert_numpy_types(response_data)
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"获取推荐失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/train', methods=['POST'])
        def train_model():
            """训练推荐模型"""
            try:
                force = request.args.get('force', 'false').lower() == 'true'
                success = self.train(force=force)
                return jsonify({
                    'success': success,
                    'message': '模型训练完成' if success else '模型未更新',
                    'last_train_time': self.last_train_time.isoformat() if self.last_train_time else None
                })
            except Exception as e:
                logger.error(f"训练模型失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/similar/<int:resource_id>', methods=['GET'])
        def get_similar_resources(resource_id):
            """获取相似资源"""
            try:
                limit = int(request.args.get('limit', 10))
                similar = self.get_similar_resources_by_id(resource_id, limit)
                return jsonify({
                    'success': True,
                    'resource_id': resource_id,
                    'similar_resources': similar,
                    'count': len(similar)
                })
            except Exception as e:
                logger.error(f"获取相似资源失败: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """获取系统统计信息"""
            return jsonify({
                'success': True,
                'stats': {
                    'model_trained': self.model is not None,
                    'last_train_time': self.last_train_time.isoformat() if self.last_train_time else None,
                    'resource_count': len(self.resource_ids) if self.resource_ids else 0,
                    'user_count': len(self.user_ids) if self.user_ids else 0,
                    'redis_connected': self.redis_client is not None,
                    'db_connected': self.db_conn is not None,
                    'algorithms_available': {
                        'item_cf': self.model_item_cf is not None,
                        'user_cf': self.model_user_cf is not None,
                        'svd': self.svd_model is not None
                    }
                }
            })

        @self.app.route('/algorithms', methods=['GET'])
        def list_algorithms():
            """论文用：算法说明与 API 参数"""
            return jsonify({
                'success': True,
                'algorithms': [
                    {
                        'id': 'item_cf',
                        'name': 'Item-CF',
                        'description': '基于物品的协同过滤：资源在“被哪些用户消费”向量上相似，推荐与用户历史资源相似的其他资源。',
                        'api_param': 'algorithm=item_cf'
                    },
                    {
                        'id': 'user_cf',
                        'name': 'User-CF',
                        'description': '基于用户的协同过滤：寻找兴趣向量相似的用户，聚合其交互过的资源作为推荐候选。',
                        'api_param': 'algorithm=user_cf'
                    },
                    {
                        'id': 'svd',
                        'name': 'SVD',
                        'description': '矩阵分解（TruncatedSVD）：将用户-资源交互矩阵分解为潜在因子空间，用潜在因子预测用户对未交互资源的偏好得分。',
                        'api_param': 'algorithm=svd'
                    }
                ],
                'evaluation_endpoint': 'POST /evaluation/compare',
                'evaluation_metrics': ['precision_at_k', 'recall_at_k', 'f1_at_k']
            })

        @self.app.route('/evaluation/compare', methods=['POST'])
        def evaluation_compare():
            """离线对比三种算法：按用户留出部分交互作为测试集，计算 Precision@K / Recall@K / F1@K"""
            try:
                body = request.get_json(silent=True) or {}
                k = int(body.get('k', request.args.get('k', 10)))
                test_ratio = float(body.get('test_ratio', request.args.get('test_ratio', 0.2)))
                max_users = int(body.get('max_users', request.args.get('max_users', 400)))
                random_seed = int(body.get('random_seed', 42))
                if k < 1 or test_ratio <= 0 or test_ratio >= 1:
                    return jsonify({'success': False, 'error': 'invalid k or test_ratio'}), 400
                result = self.compare_algorithms_offline(
                    k=k, test_ratio=test_ratio, max_users=max_users, random_seed=random_seed
                )
                return jsonify(self._convert_numpy_types({'success': True, **result}))
            except Exception as e:
                logger.error(f"离线评估失败: {e}", exc_info=True)
                return jsonify({'success': False, 'error': str(e)}), 500

    def connect_database(self):
        """连接数据库"""
        try:
            if self.db_conn is None or not self.db_conn.is_connected():
                self.db_conn = mysql.connector.connect(**self.config['mysql'])
                logger.info("MySQL数据库连接成功")
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise

    def connect_redis(self):
        """连接Redis"""
        try:
            redis_config = self.config['redis'].copy()
            if redis_config['password'] is None:
                del redis_config['password']
            self.redis_client = redis.Redis(**redis_config)
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None

    def get_user_behavior_data(self):
        """从数据库获取用户行为数据"""
        self.connect_database()

        query = """
        SELECT
            user_id,
            resource_id,
            action_type,
            COUNT(*) as interaction_count,
            MAX(create_time) as last_interaction
        FROM resource_user_behavior
        WHERE action_type IN ('VIEW', 'DOWNLOAD')
        GROUP BY user_id, resource_id, action_type
        ORDER BY user_id, resource_id
        """

        cursor = self.db_conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        logger.info(f"获取到 {len(rows)} 条行为记录")
        return rows

    def prepare_interaction_matrix(self, behavior_data):
        """准备用户-资源交互矩阵"""
        # 转换为DataFrame
        df = pd.DataFrame(behavior_data)

        # 给不同行为类型分配权重
        df['weight'] = df['action_type'].apply(
            lambda x: 2.0 if x == 'DOWNLOAD' else 1.0  # 下载权重更高
        )

        # 考虑时间衰减（最近的行为更重要）
        if 'last_interaction' in df.columns:
            df['last_interaction'] = pd.to_datetime(df['last_interaction'])
            max_time = df['last_interaction'].max()
            df['time_weight'] = 1.0 + (df['last_interaction'] - max_time).dt.total_seconds() / (30 * 24 * 3600)  # 30天衰减
            df['weight'] = df['weight'] * df['time_weight']

        # 聚合权重
        df_agg = df.groupby(['user_id', 'resource_id'])['weight'].sum().reset_index()

        # 创建用户和资源的映射
        self.user_ids = [int(uid) for uid in sorted(df_agg['user_id'].unique())]
        self.resource_ids = [int(rid) for rid in sorted(df_agg['resource_id'].unique())]

        self.user_index_map = {user_id: idx for idx, user_id in enumerate(self.user_ids)}
        self.resource_index_map = {resource_id: idx for idx, resource_id in enumerate(self.resource_ids)}

        # 创建稀疏矩阵
        n_users = len(self.user_ids)
        n_resources = len(self.resource_ids)

        rows = [self.user_index_map[row['user_id']] for _, row in df_agg.iterrows()]
        cols = [self.resource_index_map[row['resource_id']] for _, row in df_agg.iterrows()]
        data = [row['weight'] for _, row in df_agg.iterrows()]

        interaction_matrix = csr_matrix((data, (rows, cols)), shape=(n_users, n_resources))

        logger.info(f"创建交互矩阵: {n_users} 用户 × {n_resources} 资源")
        return interaction_matrix

    def train(self, force=False):
        """训练推荐模型"""
        try:
            # 检查是否需要重新训练（每24小时或强制）
            if not force and self.last_train_time:
                hours_since_last_train = (datetime.now() - self.last_train_time).total_seconds() / 3600
                if hours_since_last_train < 24 and self.model is not None:
                    logger.info(f"模型最近已训练 ({hours_since_last_train:.1f} 小时前)，跳过训练")
                    return False

            logger.info("开始训练推荐模型...")

            # 获取行为数据
            behavior_data = self.get_user_behavior_data()
            if len(behavior_data) < self.config['model']['min_interactions']:
                logger.warning(f"行为数据不足 ({len(behavior_data)} 条)，跳过训练")
                return False

            # 准备交互矩阵（用户 × 资源）
            interaction_matrix = self.prepare_interaction_matrix(behavior_data)
            self.interaction_matrix = interaction_matrix

            n_users = interaction_matrix.shape[0]
            n_items = interaction_matrix.shape[1]
            nn_k = min(self.config['model']['n_neighbors'], max(1, n_items - 1), max(1, n_users - 1))

            # Item-CF：在物品×用户矩阵上做 KNN（与历史实现一致）
            self.model_item_cf = NearestNeighbors(
                n_neighbors=min(nn_k + 1, max(2, n_items)),
                metric=self.config['model']['metric'],
                algorithm='brute'
            )
            item_user_matrix = interaction_matrix.T
            self.model_item_cf.fit(item_user_matrix)
            self.model = self.model_item_cf

            # User-CF：在用户×资源矩阵上做 KNN
            self.model_user_cf = NearestNeighbors(
                n_neighbors=min(nn_k + 1, max(2, n_users)),
                metric=self.config['model']['metric'],
                algorithm='brute'
            )
            self.model_user_cf.fit(interaction_matrix)

            # SVD（TruncatedSVD）：潜在因子模型
            # TruncatedSVD 要求 n_components < min(n_samples, n_features)
            n_comp = min(50, max(1, n_users - 1), max(1, n_items - 1))
            if n_comp < 1:
                n_comp = 1
            self.svd_model = TruncatedSVD(
                n_components=n_comp,
                random_state=42,
                algorithm='randomized',
                n_iter=10
            )
            self.svd_model.fit(interaction_matrix)

            self.last_train_time = datetime.now()
            logger.info(
                f"模型训练完成: Item-CF / User-CF / SVD，资源 {len(self.resource_ids)}，"
                f"用户 {len(self.user_ids)}，SVD 维度 {n_comp}"
            )

            # 保存模型
            self.save_model()
            return True

        except Exception as e:
            logger.error(f"模型训练失败: {e}", exc_info=True)
            raise

    def save_model(self):
        """保存模型到文件"""
        try:
            model_data = {
                'model': self.model,
                'model_item_cf': self.model_item_cf,
                'model_user_cf': self.model_user_cf,
                'svd_model': self.svd_model,
                'interaction_matrix': self.interaction_matrix,
                'resource_ids': self.resource_ids,
                'user_ids': self.user_ids,
                'user_index_map': self.user_index_map,
                'resource_index_map': self.resource_index_map,
                'last_train_time': self.last_train_time
            }
            joblib.dump(model_data, 'recommendation_model.joblib')
            logger.info("模型已保存到文件")
        except Exception as e:
            logger.error(f"保存模型失败: {e}")

    def load_model(self):
        """从文件加载模型"""
        try:
            if os.path.exists('recommendation_model.joblib'):
                model_data = joblib.load('recommendation_model.joblib')
                self.model = model_data.get('model') or model_data.get('model_item_cf')
                self.model_item_cf = model_data.get('model_item_cf') or self.model
                self.model_user_cf = model_data.get('model_user_cf')
                self.svd_model = model_data.get('svd_model')
                self.interaction_matrix = model_data.get('interaction_matrix')
                self.resource_ids = model_data['resource_ids']
                self.user_ids = model_data['user_ids']
                self.user_index_map = model_data['user_index_map']
                self.resource_index_map = model_data['resource_index_map']
                self.last_train_time = model_data['last_train_time']
                if self.model_item_cf is None:
                    self.model_item_cf = self.model
                logger.info("模型已从文件加载")
                return True
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
        return False

    def get_cache_key(self, user_id: int, algorithm: str = 'item_cf') -> str:
        """生成缓存键（按算法区分）"""
        return f"{self.config['cache']['prefix']}v3:{algorithm}:user:{user_id}"

    def get_existing_resource_ids(self, resource_ids: List[int]) -> set:
        """查询当前仍存在的资源ID集合"""
        if not resource_ids:
            return set()

        self.connect_database()
        placeholders = ', '.join(['%s'] * len(resource_ids))
        query = f"SELECT id FROM resource WHERE id IN ({placeholders})"

        cursor = self.db_conn.cursor(dictionary=True)
        cursor.execute(query, tuple(resource_ids))
        rows = cursor.fetchall()
        cursor.close()
        return {int(row['id']) for row in rows}

    def recommend_for_user(
            self,
            user_id: int,
            limit: int = 10,
            exclude_viewed: bool = True,
            algorithm: str = 'item_cf'
    ) -> List[Dict[str, Any]]:
        """为用户生成推荐，algorithm: item_cf | user_cf | svd"""
        valid_algos = {'item_cf', 'user_cf', 'svd'}
        algorithm = (algorithm or 'item_cf').strip().lower()
        if algorithm not in valid_algos:
            algorithm = 'item_cf'

        cache_key = self.get_cache_key(user_id, algorithm)
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    recommendations = json.loads(cached)
                    recommendations = self._convert_numpy_types(recommendations)
                    if not recommendations:
                        logger.info(f"用户 {user_id} 推荐缓存为空，清理后重新计算")
                        self.redis_client.delete(cache_key)
                        raise ValueError("empty recommendation cache")
                    cached_ids = [
                        int(item.get('resource_id'))
                        for item in recommendations
                        if item.get('resource_id') is not None
                    ]
                    existing_ids = self.get_existing_resource_ids(cached_ids)
                    has_stale_items = any(rid not in existing_ids for rid in cached_ids)
                    if not has_stale_items:
                        logger.info(f"从缓存获取用户 {user_id} 的推荐 ({algorithm})")
                        return recommendations[:limit]

                    logger.info(f"用户 {user_id} 推荐缓存存在失效资源，重新生成推荐")
                    self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")

        if user_id not in self.user_index_map:
            logger.warning(
                f"用户 {user_id} 不在训练数据中，返回热门资源（已排除本人上传）；"
                f"建议执行 POST /train?force=true 使模型包含新用户"
            )
            ts = self._recommendation_tie_seed(user_id, algorithm)
            return self.get_popular_resources(limit, exclude_uploader_id=user_id, tie_seed=ts)

        self.connect_database()
        cursor = self.db_conn.cursor(dictionary=True)

        if exclude_viewed:
            cursor.execute("""
                SELECT DISTINCT resource_id
                FROM resource_user_behavior
                WHERE user_id = %s
                  AND EXISTS (
                      SELECT 1 FROM resource r WHERE r.id = resource_user_behavior.resource_id
                  )
            """, (user_id,))
            viewed_resources = {row['resource_id'] for row in cursor.fetchall()}
        else:
            viewed_resources = set()

        cursor.execute("""
            SELECT resource_id, COUNT(*) as interaction_count
            FROM resource_user_behavior
            WHERE user_id = %s
              AND EXISTS (
                  SELECT 1 FROM resource r WHERE r.id = resource_user_behavior.resource_id
              )
            GROUP BY resource_id
            ORDER BY interaction_count DESC
            LIMIT 5
        """, (user_id,))
        user_resources = cursor.fetchall()
        cursor.close()

        if not user_resources:
            logger.info(f"用户 {user_id} 无有效历史行为，返回热门（已排除本人上传）")
            ts = self._recommendation_tie_seed(user_id, algorithm)
            return self.get_popular_resources(limit, exclude_uploader_id=user_id, tie_seed=ts)

        if algorithm == 'user_cf' and self.model_user_cf is not None and self.interaction_matrix is not None:
            candidate_ids = self._candidate_ids_user_cf(user_id, viewed_resources, limit)
        elif algorithm == 'svd' and self.svd_model is not None and self.interaction_matrix is not None:
            candidate_ids = self._candidate_ids_svd(user_id, viewed_resources, limit)
        else:
            candidate_ids = self._candidate_ids_item_cf(user_id, user_resources, viewed_resources, limit)

        if algorithm in ('user_cf', 'svd') and not candidate_ids:
            candidate_ids = self._candidate_ids_item_cf(user_id, user_resources, viewed_resources, limit)

        return self._finalize_recommendation_list(
            user_id, candidate_ids, limit, viewed_resources, cache_key, algorithm=algorithm
        )

    def _candidate_ids_item_cf(
            self,
            user_id: int,
            user_resources: List[Dict[str, Any]],
            viewed_resources: set,
            limit: int
    ) -> List[int]:
        all_similar: Dict[int, float] = {}
        for user_resource in user_resources:
            resource_id = user_resource['resource_id']
            interaction_weight = user_resource['interaction_count']
            if resource_id not in self.resource_index_map:
                continue
            similar = self.get_similar_resources_by_id(resource_id, limit * 2)
            for sim in similar:
                sim_resource_id = sim['resource_id']
                if sim_resource_id in viewed_resources:
                    continue
                all_similar[sim_resource_id] = all_similar.get(sim_resource_id, 0) + (
                        float(sim['similarity']) * interaction_weight
                )
        # 同分时按 (资源id, 用户) 打散，避免不同用户总撞到同一排序
        sorted_similar = sorted(
            all_similar.items(),
            key=lambda x: (-x[1], (x[0] + user_id * 1009) % 1_000_000_007)
        )
        return [item[0] for item in sorted_similar[:limit * 5]]

    def _candidate_ids_user_cf(self, user_id: int, viewed_resources: set, limit: int) -> List[int]:
        u_idx = self.user_index_map[user_id]
        R = self.interaction_matrix
        n_users = R.shape[0]
        nn = min(self.config['model']['n_neighbors'], max(1, n_users - 1))
        if nn < 1:
            return []
        row = R.getrow(u_idx)
        distances, indices = self.model_user_cf.kneighbors(
            row,
            n_neighbors=min(nn + 1, n_users)
        )
        scores: Dict[int, float] = {}
        for j in range(indices.shape[1]):
            v = int(indices[0, j])
            if v == u_idx:
                continue
            sim = 1.0 - float(distances[0, j])
            neighbor_row = R.getrow(v)
            for ci, val in zip(neighbor_row.indices, neighbor_row.data):
                rid = self.resource_ids[int(ci)]
                if rid in viewed_resources:
                    continue
                scores[rid] = scores.get(rid, 0.0) + sim * float(val)
        ranked = sorted(
            scores.items(),
            key=lambda x: (-x[1], (x[0] + user_id * 1009) % 1_000_000_007)
        )
        return [x[0] for x in ranked[:limit * 5]]

    def _candidate_ids_svd(self, user_id: int, viewed_resources: set, limit: int) -> List[int]:
        u_idx = self.user_index_map[user_id]
        row = self.interaction_matrix.getrow(u_idx)
        user_vec = self.svd_model.transform(row)
        scores = (user_vec @ self.svd_model.components_).ravel()
        scores = np.array(scores, dtype=np.float64)
        train_cols = self.interaction_matrix.getrow(u_idx).indices
        scores[train_cols] = -np.inf
        for rid in viewed_resources:
            if rid in self.resource_index_map:
                scores[self.resource_index_map[rid]] = -np.inf
        order = np.lexsort((np.arange(len(scores)), -scores))
        out: List[int] = []
        for col in order:
            if scores[col] == -np.inf or np.isnan(scores[col]):
                continue
            out.append(self.resource_ids[int(col)])
            if len(out) >= limit * 5:
                break
        return out

    @staticmethod
    def _recommendation_tie_seed(user_id: int, algorithm: str) -> int:
        """热门/补充排序用：随用户与算法变化，减轻全员列表雷同"""
        algo_salt = {'item_cf': 1, 'user_cf': 97, 'svd': 389}.get(algorithm, 0)
        return int(user_id) * 100_003 + algo_salt

    def _finalize_recommendation_list(
            self,
            user_id: int,
            candidate_ids: List[int],
            limit: int,
            viewed_resources: set,
            cache_key: str,
            algorithm: str = 'item_cf'
    ) -> List[Dict[str, Any]]:
        tie_seed = self._recommendation_tie_seed(user_id, algorithm)
        recommendations = self.get_resources_details(candidate_ids, exclude_uploader_id=user_id)[:limit]
        if not recommendations:
            logger.info(f"用户 {user_id} 个性化推荐为空，降级返回热门资源")
            recommendations = self.get_popular_resources(
                limit, exclude_uploader_id=user_id, tie_seed=tie_seed
            )
        if len(recommendations) < limit:
            existing_ids = {
                int(item['resource_id'])
                for item in recommendations
                if item.get('resource_id') is not None
            }
            supplement = self.get_recent_resources_for_user(
                user_id=user_id,
                limit=limit - len(recommendations),
                exclude_resource_ids=existing_ids.union(viewed_resources),
                tie_seed=tie_seed
            )
            recommendations.extend(supplement)
        recommendations = self._convert_numpy_types(recommendations)
        if self.redis_client and recommendations:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.config['cache']['ttl'],
                    json.dumps(recommendations)
                )
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        return recommendations

    def get_similar_resources_by_id(self, resource_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取相似资源"""
        m = self.model_item_cf or self.model
        if m is None or resource_id not in self.resource_index_map:
            return []

        resource_idx = self.resource_index_map[resource_id]

        # 获取邻居
        distances, indices = m.kneighbors(
            m._fit_X[resource_idx].reshape(1, -1),
            n_neighbors=min(limit + 1, len(self.resource_ids))
        )

        similar_resources = []
        for i in range(1, len(indices[0])):  # 跳过自己
            similar_idx = indices[0][i]
            similar_resource_id = self.resource_ids[similar_idx]
            similarity = 1 - distances[0][i]  # 转换为相似度

            similar_resources.append({
                'resource_id': similar_resource_id,
                'similarity': float(similarity)
            })

        return self._convert_numpy_types(similar_resources)

    def get_popular_resources(
            self,
            limit: int = 10,
            exclude_uploader_id: Optional[int] = None,
            tie_seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取热门资源；tie_seed 用于同热度下的 per-user/per-algo 打散"""
        self.connect_database()

        order_by = "ORDER BY interaction_count DESC, user_count DESC"
        params: List[Any] = []
        if exclude_uploader_id is not None:
            where_extra = "WHERE 1=1 AND r.uploader_id <> %s"
            params.append(exclude_uploader_id)
        else:
            where_extra = "WHERE 1=1"
        if tie_seed is not None:
            s = abs(int(tie_seed)) % 999_983
            # 使用seed作为第一排序字段，使不同算法/用户的热门资源顺序明显不同
            order_by = f"ORDER BY MOD(r.id * %s, 999983) DESC, interaction_count DESC, user_count DESC"
            params.append(s)
        params.append(limit)

        query = f"""
        SELECT
            r.id as resource_id,
            r.title,
            r.file_type,
            r.file_size,
            r.create_time,
            u.nickname as uploader_name,
            COUNT(DISTINCT b.user_id) as user_count,
            COUNT(*) as interaction_count
        FROM resource r
        LEFT JOIN resource_user_behavior b ON r.id = b.resource_id
        LEFT JOIN user u ON r.uploader_id = u.id
        {where_extra}
        GROUP BY r.id, r.title, r.file_type, r.file_size, r.create_time, u.nickname
        {order_by}
        LIMIT %s
        """

        cursor = self.db_conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        result = [
            {
                'resource_id': row['resource_id'],
                'title': row['title'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'create_time': row['create_time'].isoformat() if row['create_time'] else None,
                'uploader': row['uploader_name'],
                'popularity': {
                    'user_count': row['user_count'],
                    'interaction_count': row['interaction_count']
                }
            }
            for row in rows
        ]
        # 若热门结果为空，降级到最新资源，避免推荐区域无内容
        if not result:
            fb_order = "ORDER BY r.create_time DESC"
            fb_params: List[Any] = []
            if tie_seed is not None:
                s = abs(int(tie_seed)) % 999_983
                # 使用seed作为第一排序字段，使不同算法/用户的降级资源顺序不同
                fb_order = f"ORDER BY MOD(r.id * %s, 999983) DESC, r.create_time DESC"
                fb_params.append(s)
            fb_params.append(limit)
            fallback_query = f"""
            SELECT
                r.id as resource_id,
                r.title,
                r.file_type,
                r.file_size,
                r.create_time
            FROM resource r
            {fb_order}
            LIMIT %s
            """
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute(fallback_query, tuple(fb_params))
            fallback_rows = cursor.fetchall()
            cursor.close()
            result = [
                {
                    'resource_id': row['resource_id'],
                    'title': row['title'],
                    'file_type': row['file_type'],
                    'file_size': row['file_size'],
                    'create_time': row['create_time'].isoformat() if row['create_time'] else None,
                    'uploader': None,
                    'popularity': {
                        'user_count': 0,
                        'interaction_count': 0
                    }
                }
                for row in fallback_rows
            ]

        return self._convert_numpy_types(result)

    def get_resources_details(self, resource_ids: List[int], exclude_uploader_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取资源详细信息"""
        if not resource_ids:
            return []

        self.connect_database()

        placeholders = ', '.join(['%s'] * len(resource_ids))
        query = f"""
        SELECT
            r.id,
            r.title,
            r.file_type,
            r.file_size,
            r.create_time,
            u.nickname as uploader_name
        FROM resource r
        LEFT JOIN user u ON r.uploader_id = u.id
        WHERE r.id IN ({placeholders})
          {"AND r.uploader_id <> %s" if exclude_uploader_id is not None else ""}
        ORDER BY FIELD(r.id, {placeholders})
        """

        # 重复参数用于ORDER BY FIELD
        params = resource_ids.copy()
        if exclude_uploader_id is not None:
            params.append(exclude_uploader_id)
        params.extend(resource_ids)

        cursor = self.db_conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()

        result = [
            {
                'resource_id': row['id'],
                'title': row['title'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'create_time': row['create_time'].isoformat() if row['create_time'] else None,
                'uploader': row['uploader_name']
            }
            for row in rows
        ]
        return self._convert_numpy_types(result)

    def get_recent_resources_for_user(
            self,
            user_id: int,
            limit: int,
            exclude_resource_ids: Optional[set] = None,
            tie_seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """补充最新资源（排除本人上传、已浏览和已在候选中的资源）；tie_seed 控制起始窗口，减轻全员雷同"""
        if limit <= 0:
            return []

        self.connect_database()
        exclude_resource_ids = exclude_resource_ids or set()
        seed = int(tie_seed or 0)
        skip_n = (int(user_id) * 17 + seed * 19) % 40

        order_by = "ORDER BY r.create_time DESC"
        qparams: List[Any] = [user_id, user_id]
        if tie_seed is not None:
            s = abs(seed) % 999_983
            order_by += ", MOD(r.id + %s, 999983)"
            qparams.append(s)
        fetch_cap = min(limit * 12 + skip_n + 20, 800)
        qparams.append(fetch_cap)

        query = f"""
        SELECT
            r.id,
            r.title,
            r.file_type,
            r.file_size,
            r.create_time,
            u.nickname as uploader_name
        FROM resource r
        LEFT JOIN user u ON r.uploader_id = u.id
        WHERE r.uploader_id <> %s
          AND NOT EXISTS (
              SELECT 1
              FROM resource_user_behavior b
              WHERE b.user_id = %s
                AND b.resource_id = r.id
          )
        {order_by}
        LIMIT %s
        """

        cursor = self.db_conn.cursor(dictionary=True)
        cursor.execute(query, tuple(qparams))
        rows = cursor.fetchall()
        cursor.close()

        result = []
        skipped = 0
        for row in rows:
            rid = int(row['id'])
            if rid in exclude_resource_ids:
                continue
            if skipped < skip_n:
                skipped += 1
                continue
            result.append({
                'resource_id': rid,
                'title': row['title'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'create_time': row['create_time'].isoformat() if row['create_time'] else None,
                'uploader': row['uploader_name']
            })
            if len(result) >= limit:
                break

        return self._convert_numpy_types(result)

    def compare_algorithms_offline(
            self,
            k: int = 10,
            test_ratio: float = 0.2,
            max_users: int = 400,
            random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        按用户留出部分 (user, item) 交互作为测试集，仅在训练集上拟合三种算法，
        计算 Precision@K / Recall@K / F1@K（论文对比用）。
        """
        from collections import defaultdict

        rng = random.Random(random_seed)
        np.random.seed(random_seed)

        logger.info(
            "[eval] start compare_algorithms_offline: K=%s test_ratio=%s max_users=%s seed=%s",
            k, test_ratio, max_users, random_seed
        )

        behavior_data = self.get_user_behavior_data()
        if len(behavior_data) < 20:
            logger.warning("[eval] abort: not enough behavior rows")
            return {
                'error': '行为数据过少，无法评估',
                'k': k,
                'test_ratio': test_ratio
            }

        logger.info("[eval] loaded %d raw behavior rows (before user-item aggregate)", len(behavior_data))

        df = pd.DataFrame(behavior_data)
        df['weight'] = df['action_type'].apply(lambda x: 2.0 if x == 'DOWNLOAD' else 1.0)
        if 'last_interaction' in df.columns:
            df['last_interaction'] = pd.to_datetime(df['last_interaction'])
            max_time = df['last_interaction'].max()
            df['time_weight'] = 1.0 + (df['last_interaction'] - max_time).dt.total_seconds() / (30 * 24 * 3600)
            df['weight'] = df['weight'] * df['time_weight']

        df_agg = df.groupby(['user_id', 'resource_id'])['weight'].sum().reset_index()
        user_to_pairs: Dict[int, List[tuple]] = defaultdict(list)
        for _, row in df_agg.iterrows():
            user_to_pairs[int(row['user_id'])].append((int(row['resource_id']), float(row['weight'])))

        train_pairs_by_user: Dict[int, List[tuple]] = {}
        test_true: Dict[int, set] = {}

        for uid, pairs in user_to_pairs.items():
            if len(pairs) < 3:
                continue
            pairs = pairs.copy()
            rng.shuffle(pairs)
            n_test = max(1, int(len(pairs) * test_ratio))
            test_part = pairs[:n_test]
            train_part = pairs[n_test:]
            if len(train_part) < 1:
                continue
            train_pairs_by_user[uid] = train_part
            test_true[uid] = {int(t[0]) for t in test_part}

        logger.info(
            "[eval] train/test split done: eligible_train_users=%d",
            len(train_pairs_by_user)
        )

        train_user_ids = sorted(train_pairs_by_user.keys())
        resource_ids_set = set()
        for plist in train_pairs_by_user.values():
            for rid, _ in plist:
                resource_ids_set.add(rid)
        resource_ids = sorted(resource_ids_set)
        user_index_map = {u: i for i, u in enumerate(train_user_ids)}
        resource_index_map = {r: j for j, r in enumerate(resource_ids)}

        rows_ix = []
        cols_ix = []
        data_v = []
        for uid in train_user_ids:
            ui = user_index_map[uid]
            for rid, w in train_pairs_by_user[uid]:
                rows_ix.append(ui)
                cols_ix.append(resource_index_map[rid])
                data_v.append(w)

        n_u = len(train_user_ids)
        n_i = len(resource_ids)
        if n_u < 2 or n_i < 2:
            logger.warning("[eval] matrix too small: users=%d items=%d", n_u, n_i)
            return {'error': '训练矩阵过小', 'k': k}

        R_train = csr_matrix((data_v, (rows_ix, cols_ix)), shape=(n_u, n_i))
        nnz = R_train.nnz
        logger.info(
            "[eval] R_train shape: %d users x %d items, nnz=%d",
            n_u, n_i, nnz
        )

        nn_k = min(self.config['model']['n_neighbors'], max(1, n_u - 1), max(1, n_i - 1))
        logger.info("[eval] fitting Item-CF (item KNN, cosine)…")
        item_nn = NearestNeighbors(
            n_neighbors=min(nn_k + 1, max(2, n_i)),
            metric=self.config['model']['metric'],
            algorithm='brute'
        )
        item_nn.fit(R_train.T)
        logger.info("[eval] Item-CF fit done")

        logger.info("[eval] fitting User-CF (user KNN, cosine)…")
        user_nn = NearestNeighbors(
            n_neighbors=min(nn_k + 1, max(2, n_u)),
            metric=self.config['model']['metric'],
            algorithm='brute'
        )
        user_nn.fit(R_train)
        logger.info("[eval] User-CF fit done")

        n_comp = min(50, max(1, n_u - 1), max(1, n_i - 1))
        logger.info("[eval] fitting SVD (TruncatedSVD, n_components=%d)…", n_comp)
        svd_eval = TruncatedSVD(
            n_components=n_comp,
            random_state=random_seed,
            algorithm='randomized',
            n_iter=10
        )
        svd_eval.fit(R_train)
        logger.info("[eval] SVD fit done")

        eval_users = [u for u in test_true if u in user_index_map]
        rng.shuffle(eval_users)
        eval_users = eval_users[:max_users]
        total_eval = len(eval_users)
        log_every = max(1, total_eval // 10)
        logger.info(
            "[eval] scoring %d users (Top-%d, log every ~%d users)",
            total_eval, k, log_every
        )

        def topk_item_cf(uidx: int) -> List[int]:
            row = R_train.getrow(uidx)
            nz = list(zip(row.indices, row.data))
            if not nz:
                return []
            nz.sort(key=lambda x: -x[1])
            top_items = nz[:5]
            scores: Dict[int, float] = {}
            train_cols = set(row.indices.tolist())
            for col, w in top_items:
                dist, ind = item_nn.kneighbors(
                    item_nn._fit_X[col].reshape(1, -1),
                    n_neighbors=min(k * 3 + 1, n_i)
                )
                for pos in range(1, ind.shape[1]):
                    j = int(ind[0, pos])
                    if j in train_cols:
                        continue
                    sim = 1.0 - float(dist[0, pos])
                    rid = resource_ids[j]
                    scores[rid] = scores.get(rid, 0.0) + sim * float(w)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [x[0] for x in ranked[:k]]

        def topk_user_cf(uidx: int) -> List[int]:
            dist, ind = user_nn.kneighbors(
                R_train.getrow(uidx),
                n_neighbors=min(nn_k + 1, n_u)
            )
            row = R_train.getrow(uidx)
            train_cols = set(row.indices.tolist())
            scores: Dict[int, float] = {}
            for pos in range(ind.shape[1]):
                v = int(ind[0, pos])
                if v == uidx:
                    continue
                sim = 1.0 - float(dist[0, pos])
                vr = R_train.getrow(v)
                for ci, val in zip(vr.indices, vr.data):
                    if ci in train_cols:
                        continue
                    rid = resource_ids[int(ci)]
                    scores[rid] = scores.get(rid, 0.0) + sim * float(val)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [x[0] for x in ranked[:k]]

        def topk_svd(uidx: int) -> List[int]:
            row = R_train.getrow(uidx)
            uv = svd_eval.transform(row)
            sc = (uv @ svd_eval.components_).ravel()
            sc = np.array(sc, dtype=np.float64)
            for c in row.indices:
                sc[c] = -np.inf
            order = np.argsort(-sc)
            out: List[int] = []
            for c in order:
                if sc[c] == -np.inf or np.isnan(sc[c]):
                    continue
                out.append(resource_ids[int(c)])
                if len(out) >= k:
                    break
            return out

        metrics = {
            'item_cf': {'precision': [], 'recall': [], 'f1': []},
            'user_cf': {'precision': [], 'recall': [], 'f1': []},
            'svd': {'precision': [], 'recall': [], 'f1': []}
        }

        for step, uid in enumerate(eval_users, start=1):
            uidx = user_index_map[uid]
            true_set = test_true[uid]
            if not true_set:
                continue

            for algo, fn in (
                    ('item_cf', topk_item_cf),
                    ('user_cf', topk_user_cf),
                    ('svd', topk_svd)
            ):
                pred = fn(uidx)
                hits = len(set(pred) & true_set)
                prec = hits / float(k) if k else 0.0
                rec = hits / float(max(len(true_set), 1))
                if prec + rec > 0:
                    f1 = 2.0 * prec * rec / (prec + rec)
                else:
                    f1 = 0.0
                metrics[algo]['precision'].append(prec)
                metrics[algo]['recall'].append(rec)
                metrics[algo]['f1'].append(f1)

            if step == 1 or step == total_eval or step % log_every == 0:
                logger.info(
                    "[eval] progress: %d / %d users",
                    step, total_eval
                )

        def avg(vals: List[float]) -> float:
            return float(sum(vals) / len(vals)) if vals else 0.0

        summary = {}
        chart_series = {'labels': ['Item-CF', 'User-CF', 'SVD'], 'precision': [], 'recall': [], 'f1': []}
        for key, label in (('item_cf', 'Item-CF'), ('user_cf', 'User-CF'), ('svd', 'SVD')):
            p = avg(metrics[key]['precision'])
            r = avg(metrics[key]['recall'])
            f = avg(metrics[key]['f1'])
            summary[key] = {
                'precision_at_k': round(p, 6),
                'recall_at_k': round(r, 6),
                'f1_at_k': round(f, 6),
                'evaluated_users': len(metrics[key]['precision'])
            }
            chart_series['precision'].append(round(p, 6))
            chart_series['recall'].append(round(r, 6))
            chart_series['f1'].append(round(f, 6))

        logger.info(
            "[eval] DONE — Item-CF P@K=%.6f R@K=%.6f F1=%.6f | "
            "User-CF P@K=%.6f R@K=%.6f F1=%.6f | SVD P@K=%.6f R@K=%.6f F1=%.6f",
            summary['item_cf']['precision_at_k'], summary['item_cf']['recall_at_k'], summary['item_cf']['f1_at_k'],
            summary['user_cf']['precision_at_k'], summary['user_cf']['recall_at_k'], summary['user_cf']['f1_at_k'],
            summary['svd']['precision_at_k'], summary['svd']['recall_at_k'], summary['svd']['f1_at_k'],
        )

        return {
            'methodology': (
                '按用户随机留出 test_ratio 比例的 (用户,资源) 交互作为测试集；'
                '仅用训练集交互拟合三种模型；对每个测试用户预测 Top-K，'
                '与测试集中该用户真实资源集合计算 P@K、R@K、F1@K 后对用户取平均。'
            ),
            'k': k,
            'test_ratio': test_ratio,
            'random_seed': random_seed,
            'users_in_train_matrix': n_u,
            'items_in_train_matrix': n_i,
            'evaluation_user_count_requested': len(eval_users),
            'metrics_by_algorithm': summary,
            'chart_data': chart_series
        }

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """运行推荐服务"""
        # 连接服务
        self.connect_database()
        self.connect_redis()

        # 尝试加载现有模型
        if not self.load_model():
            logger.info("未找到现有模型，开始训练新模型...")
            self.train()

        logger.info(f"推荐服务启动在 http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='资源推荐系统')
    parser.add_argument('--host', default='0.0.0.0', help='服务主机')
    parser.add_argument('--port', type=int, default=5000, help='服务端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--train', action='store_true', help='训练模型后退出')
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='运行三种算法离线对比评估（终端打印过程与最终 JSON）后退出'
    )
    parser.add_argument('--eval-k', type=int, default=10, dest='eval_k', help='评估 Top-K')
    parser.add_argument(
        '--eval-test-ratio',
        type=float,
        default=0.2,
        dest='eval_test_ratio',
        help='每用户测试集占比'
    )
    parser.add_argument(
        '--eval-max-users',
        type=int,
        default=400,
        dest='eval_max_users',
        help='最多参与评估的用户数'
    )
    parser.add_argument('--eval-seed', type=int, default=42, dest='eval_seed', help='随机种子')

    args = parser.parse_args()

    # 创建推荐系统实例
    rec_sys = RecommendationSystem()

    if args.train:
        # 仅训练模型
        rec_sys.connect_database()
        rec_sys.train(force=True)
        print("模型训练完成")
    elif args.evaluate:
        rec_sys.connect_database()
        out = rec_sys.compare_algorithms_offline(
            k=args.eval_k,
            test_ratio=args.eval_test_ratio,
            max_users=args.eval_max_users,
            random_seed=args.eval_seed
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        # 启动服务
        rec_sys.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()