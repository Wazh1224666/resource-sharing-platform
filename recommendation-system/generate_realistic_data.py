#!/usr/bin/env python3
"""
生成逼真模拟数据脚本
基于真实世界用户行为模式：
- 帕累托分布 (80/20法则)
- 时间衰减
- 兴趣聚类
- 热点资源
"""

import random
import pandas as pd
from datetime import datetime, timedelta
import mysql.connector
from faker import Faker
import numpy as np
from collections import defaultdict

class RealisticDataGenerator:
    def __init__(self, db_config):
        self.db_config = db_config
        self.fake = Faker('zh_CN')
        self.resource_types = ['pdf', 'docx', 'ppt', 'xlsx', 'jpg', 'png', 'zip', 'mp4']
        self.categories = ['数学', '物理', '化学', '计算机', '英语', '历史', '经济', '艺术']

    def connect_db(self):
        """连接数据库"""
        return mysql.connector.connect(**self.db_config)

    def get_existing_data(self):
        """获取现有的真实数据（如果有的话）"""
        conn = self.connect_db()
        cursor = conn.cursor(dictionary=True)

        # 获取现有用户
        cursor.execute("SELECT id, role FROM user LIMIT 100")
        users = cursor.fetchall()

        # 获取现有资源
        cursor.execute("""
            SELECT id, title, file_type, uploader_id
            FROM resource
            WHERE LOCATE('sim_res_', file_name) <> 1
            LIMIT 1000
        """)
        resources = cursor.fetchall()

        cursor.close()
        conn.close()

        return users, resources

    def generate_user_interest_profiles(self, user_count):
        """生成用户兴趣档案（基于真实模式）"""
        # 按照帕累托分布分配用户活跃度
        user_profiles = []
        for i in range(user_count):
            # 20%的用户高度活跃，50%中等活跃，30%低活跃
            if i < user_count * 0.2:
                activity_level = 'high'  # 高度活跃
                avg_interactions = random.randint(15, 30)
            elif i < user_count * 0.7:
                activity_level = 'medium'  # 中等活跃
                avg_interactions = random.randint(5, 15)
            else:
                activity_level = 'low'  # 低活跃
                avg_interactions = random.randint(1, 5)

            # 每个用户有1-3个主要兴趣类别
            main_interests = random.sample(self.categories, random.randint(1, 3))

            # 每个用户有偏好的资源类型
            preferred_types = random.sample(self.resource_types, random.randint(1, 3))

            user_profiles.append({
                'user_id': i + 1,
                'activity_level': activity_level,
                'avg_interactions': avg_interactions,
                'main_interests': main_interests,
                'preferred_types': preferred_types
            })

        return user_profiles

    def generate_resource_popularity(self, resource_count):
        """生成资源流行度分布（遵循幂律分布）"""
        # 使用幂律分布模拟资源流行度
        resource_popularity = {}

        # 少数资源非常热门
        hot_resources = int(resource_count * 0.1)  # 10%的热门资源
        for i in range(hot_resources):
            # 热门资源的流行度较高
            popularity = random.randint(50, 200)
            resource_popularity[i] = popularity

        # 大多数资源普通流行度
        for i in range(hot_resources, resource_count):
            # 普通资源的流行度较低
            popularity = random.randint(1, 20)
            resource_popularity[i] = popularity

        return resource_popularity

    def generate_time_series_behavior(self, start_date, end_date):
        """生成时间序列行为模式"""
        # 模拟学期周期：学期初和学期末更活跃
        behaviors = []
        current_date = start_date

        while current_date <= end_date:
            # 学期模式：3月-6月，9月-1月更活跃
            month = current_date.month
            if month in [3, 4, 5, 9, 10, 11, 12]:
                base_activity = 1.5
            else:
                base_activity = 0.8

            # 周模式：工作日更活跃
            weekday = current_date.weekday()
            if weekday < 5:  # 周一到周五
                daily_factor = 1.2
            else:
                daily_factor = 0.7

            # 每日模式：白天更活跃
            for hour in range(24):
                if 9 <= hour <= 17:  # 工作时间
                    hourly_factor = 1.5
                elif 19 <= hour <= 22:  # 晚上
                    hourly_factor = 1.2
                else:
                    hourly_factor = 0.5

                # 综合因子
                activity_factor = base_activity * daily_factor * hourly_factor

                behaviors.append({
                    'date': current_date,
                    'hour': hour,
                    'activity_factor': activity_factor
                })

            current_date += timedelta(days=1)

        return behaviors

    def generate_behavior_data(self, users, resources, days=90):
        """生成逼真的用户行为数据"""
        print("开始生成逼真模拟数据...")

        # 1. 获取或生成用户和资源
        if not users or not resources:
            print("警告：真实数据不足，将生成模拟数据")
            users = [{'id': i+1, 'role': random.choice(['STUDENT', 'TEACHER'])}
                    for i in range(100)]
            resources = [{'id': i+1, 'title': f'资源{i+1}', 'file_type': random.choice(self.resource_types)}
                        for i in range(500)]

        user_count = len(users)
        resource_count = len(resources)

        print(f"用户数量: {user_count}, 资源数量: {resource_count}")

        # 2. 生成用户兴趣档案
        user_profiles = self.generate_user_interest_profiles(user_count)

        # 3. 生成资源流行度
        resource_popularity = self.generate_resource_popularity(resource_count)

        # 4. 生成时间序列模式
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        time_patterns = self.generate_time_series_behavior(start_date, end_date)

        # 5. 生成行为数据
        behavior_records = []

        # 按时间模式生成行为
        for time_pattern in time_patterns:
            date = time_pattern['date']
            hour = time_pattern['hour']
            activity_factor = time_pattern['activity_factor']

            # 计算当前时间段应该有多少行为
            base_behaviors = int(activity_factor * 5)  # 基数

            for _ in range(base_behaviors):
                # 根据帕累托分布选择用户
                if random.random() < 0.8:  # 80%的行为由20%的用户产生
                    user_idx = random.randint(0, int(user_count * 0.2) - 1)
                else:
                    user_idx = random.randint(int(user_count * 0.2), user_count - 1)

                user_id = users[user_idx]['id']
                user_profile = user_profiles[user_idx]

                # 根据用户兴趣和资源流行度选择资源
                # 用户更可能与他们兴趣相关的资源交互
                if random.random() < 0.7:  # 70%的概率选择相关资源
                    # 这里简化处理，实际应根据用户兴趣匹配
                    resource_idx = random.randint(0, resource_count - 1)
                else:  # 30%的概率探索新资源
                    resource_idx = random.randint(0, resource_count - 1)

                resource_id = resources[resource_idx]['id']

                # 根据资源流行度增加交互概率
                popularity_boost = resource_popularity.get(resource_idx, 1) / 100
                if random.random() < popularity_boost:
                    # 选择行为类型：80%浏览，20%下载
                    action_type = 'DOWNLOAD' if random.random() < 0.2 else 'VIEW'

                    # 生成时间（当前日期的小时范围内）
                    create_time = datetime(date.year, date.month, date.day, hour,
                                          random.randint(0, 59), random.randint(0, 59))

                    behavior_records.append({
                        'user_id': user_id,
                        'resource_id': resource_id,
                        'action_type': action_type,
                        'create_time': create_time
                    })

        print(f"生成 {len(behavior_records)} 条行为记录")
        return behavior_records

    def insert_behavior_data(self, behavior_records):
        """插入行为数据到数据库"""
        conn = self.connect_db()
        cursor = conn.cursor()

        # 清空现有模拟数据（可选）
        cursor.execute("DELETE FROM resource_user_behavior")

        # 批量插入
        batch_size = 1000
        for i in range(0, len(behavior_records), batch_size):
            batch = behavior_records[i:i+batch_size]

            sql = """
            INSERT INTO resource_user_behavior
            (user_id, resource_id, action_type, create_time)
            VALUES (%s, %s, %s, %s)
            """

            values = [
                (record['user_id'], record['resource_id'],
                 record['action_type'], record['create_time'])
                for record in batch
            ]

            cursor.executemany(sql, values)
            conn.commit()
            print(f"已插入 {i+len(batch)}/{len(behavior_records)} 条记录")

        cursor.close()
        conn.close()
        print("数据插入完成！")

    def analyze_data_patterns(self, behavior_records):
        """分析生成的数据模式"""
        df = pd.DataFrame(behavior_records)

        print("\n=== 数据模式分析 ===")
        print(f"总行为数: {len(df)}")
        print(f"浏览行为: {len(df[df['action_type'] == 'VIEW'])}")
        print(f"下载行为: {len(df[df['action_type'] == 'DOWNLOAD'])}")

        # 用户活跃度分布
        user_counts = df['user_id'].value_counts()
        print(f"\n用户活跃度分布:")
        print(f"最活跃的5个用户: {user_counts.head(5).to_dict()}")
        print(f"平均每个用户行为数: {user_counts.mean():.2f}")

        # 资源流行度分布
        resource_counts = df['resource_id'].value_counts()
        print(f"\n资源流行度分布:")
        print(f"最受欢迎的5个资源: {resource_counts.head(5).to_dict()}")

        # 时间分布
        df['hour'] = pd.to_datetime(df['create_time']).dt.hour
        hour_dist = df['hour'].value_counts().sort_index()
        print(f"\n小时分布: {hour_dist.to_dict()}")

def main():
    """主函数"""
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'resource_db',
        'user': 'root',
        'password': '123456'
    }

    # 创建生成器
    generator = RealisticDataGenerator(db_config)

    try:
        # 1. 获取现有真实数据
        users, resources = generator.get_existing_data()

        # 2. 生成行为数据（90天）
        behavior_records = generator.generate_behavior_data(users, resources, days=90)

        # 3. 分析数据模式
        generator.analyze_data_patterns(behavior_records)

        # 4. 自动插入数据库（用于自动化执行）
        print("\n自动插入数据到数据库...")
        generator.insert_behavior_data(behavior_records)
        print("✅ 数据生成完成！现在可以训练推荐模型了。")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 安装依赖：pip install mysql-connector-python faker pandas numpy
    main()