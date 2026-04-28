"""
为模拟资源生成用户行为记录，建立丰富的交互矩阵。
让真实用户和模拟用户都与新旧资源产生交叉行为。
"""
import mysql.connector
import random
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost', 'port': 3306, 'database': 'resource_db',
    'user': 'root', 'password': '123456'
}


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # 获取所有资源ID（新旧都要）
    cursor.execute("SELECT id, uploader_id, title FROM resource ORDER BY id")
    all_resources = cursor.fetchall()
    logger.info(f"资源总数: {len(all_resources)}")

    real_resources = [r for r in all_resources if r['uploader_id'] == 1]
    sim_resources = [r for r in all_resources if r['uploader_id'] != 1]
    logger.info(f"真实资源(admin上传): {len(real_resources)} 个, 模拟资源(教师上传): {len(sim_resources)} 个")

    # 获取用户
    cursor.execute("SELECT id, username FROM user WHERE id >= 1 AND id <= 88 ORDER BY id")
    users = cursor.fetchall()
    logger.info(f"用户数: {len(users)}")

    # 获取现有行为避免重复
    cursor.execute("SELECT DISTINCT user_id, resource_id, action_type FROM resource_user_behavior")
    existing = {(row['user_id'], row['resource_id'], row['action_type']) for row in cursor.fetchall()}
    logger.info(f"现有行为记录: {len(existing)} 条")

    # 为每个用户生成行为
    random.seed(20260427)
    now = datetime.now()
    new_records = []

    for user in users:
        uid = user['id']
        is_simulated = uid >= 9  # 模拟用户

        # 根据角色决定行为数量
        if uid == 1:  # admin
            num_views = random.randint(15, 25)
            num_downloads = random.randint(5, 10)
        elif uid <= 8:  # 真实普通用户
            num_views = random.randint(10, 20)
            num_downloads = random.randint(3, 8)
        else:  # 模拟用户
            num_views = random.randint(8, 18)
            num_downloads = random.randint(2, 6)

        # 确定可能交互的资源池
        # 真实用户：较多真实资源 + 一些模拟资源
        # 模拟用户：较多模拟资源 + 一些真实资源
        if uid == 1:  # admin 可以浏览所有非自己上传的资源
            avoid_ids = {r['id'] for r in real_resources}  # 不能看自己的
            pool = [r for r in all_resources if r['id'] not in avoid_ids]
        elif uid <= 8:  # 真实用户看两类资源
            real_pool = real_resources
            sim_pool = sim_resources
            # 30-50% 模拟资源
            sim_ratio = random.uniform(0.3, 0.5)
            pool = real_pool + random.sample(sim_pool, max(1, int(len(sim_pool) * sim_ratio)))
        else:  # 模拟用户
            real_pool = real_resources
            sim_pool = [r for r in sim_resources if r['uploader_id'] != uid]
            # 40-60% 真实资源
            real_ratio = random.uniform(0.4, 0.6)
            real_count = min(len(real_pool), max(1, int(len(sim_pool) * real_ratio)))
            pool = sim_pool + random.sample(real_pool, real_count) if real_pool else sim_pool

        # 过滤已存在的交互
        available = [r for r in pool if (uid, r['id'], 'VIEW') not in existing]
        if not available:
            continue

        view_count = min(num_views, len(available))
        selected = random.sample(available, view_count)

        # 生成 VIEW 记录
        for res in selected:
            days_ago = random.randint(0, 60)
            create_time = now - timedelta(days=days_ago, hours=random.randint(0, 23),
                                          minutes=random.randint(0, 59))
            new_records.append((uid, res['id'], 'VIEW', create_time))

            # 部分资源也下载
            dl_key = (uid, res['id'], 'DOWNLOAD')
            if dl_key not in existing and random.random() < 0.35:
                dl_days = max(0, days_ago - random.randint(0, 5))
                dl_time = now - timedelta(days=dl_days, hours=random.randint(0, 23),
                                          minutes=random.randint(0, 59))
                new_records.append((uid, res['id'], 'DOWNLOAD', dl_time))

    logger.info(f"新生成行为记录: {len(new_records)} 条")

    # 批量插入
    if new_records:
        insert_sql = (
            "INSERT INTO resource_user_behavior (user_id, resource_id, action_type, create_time) "
            "VALUES (%s, %s, %s, %s)"
        )
        batch_size = 500
        for i in range(0, len(new_records), batch_size):
            batch = new_records[i:i + batch_size]
            try:
                cursor.executemany(insert_sql, batch)
                conn.commit()
            except Exception as e:
                logger.warning(f"批次插入失败: {e}")
                # 逐条插入
                for rec in batch:
                    try:
                        cursor.execute(insert_sql, rec)
                        conn.commit()
                    except Exception:
                        pass
            logger.info(f"已插入 {min(i + batch_size, len(new_records))} / {len(new_records)} 条")

    # 验证
    cursor.execute("SELECT COUNT(*) as cnt FROM resource_user_behavior")
    total = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(DISTINCT user_id) as cnt FROM resource_user_behavior")
    users_with_data = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(DISTINCT resource_id) as cnt FROM resource_user_behavior")
    resources_with_data = cursor.fetchone()['cnt']

    logger.info(f"\n=== 完成 ===")
    logger.info(f"总行为记录: {total}")
    logger.info(f"有行为的用户: {users_with_data}")
    logger.info(f"有行为的资源: {resources_with_data}")

    # 检查资源覆盖情况
    cursor.execute("""
        SELECT r.id, r.title, r.uploader_id,
               CASE WHEN b.cnt IS NULL THEN '无行为' ELSE '有行为' END as status
        FROM resource r
        LEFT JOIN (SELECT resource_id, COUNT(*) as cnt FROM resource_user_behavior GROUP BY resource_id) b
        ON r.id = b.resource_id
        ORDER BY r.id
    """)
    stats = {"有行为": 0, "无行为": 0}
    for row in cursor.fetchall():
        stats[row['status']] += 1
    logger.info(f"资源覆盖: {stats}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
