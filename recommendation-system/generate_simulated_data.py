"""
生成模拟用户行为数据，让推荐系统有足够数据做协同过滤。
模拟教师/学生对考研资源的浏览和下载行为。
"""
import mysql.connector
import random
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'resource_db',
    'user': 'root',
    'password': '123456'
}

# 资源ID列表（30个考研资源）
RESOURCE_IDS = list(range(2050, 2080))

# 按学科分类的资源
RESOURCES_BY_SUBJECT = {
    'english': [2050, 2053, 2058, 2059, 2060, 2063, 2064, 2067, 2068, 2069, 2073, 2078, 2079],
    'math': [2056, 2057, 2065, 2066, 2070, 2071, 2072, 2075, 2076, 2077],
    'politics': [2051, 2052, 2054, 2055, 2061, 2062, 2074],
}

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 获取模拟用户列表（sim_teacher 和 sim_student）
    cursor.execute(
        "SELECT id, role FROM user "
        "WHERE username LIKE 'sim_%%' "
        "ORDER BY id"
    )
    sim_users = cursor.fetchall()
    logger.info(f"找到 {len(sim_users)} 个模拟用户")

    # 获取现有行为数据，避免重复
    cursor.execute("SELECT DISTINCT user_id, resource_id, action_type FROM resource_user_behavior")
    existing = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    logger.info(f"现有 {len(existing)} 条行为记录")

    # 已存在的(user_id, resource_id)组合（看或下载过就算）
    existing_user_resources = set()
    for uid, rid, _ in existing:
        existing_user_resources.add((uid, rid))

    # 为每个资源计算学科标签
    resource_subject = {}
    for subj, rids in RESOURCES_BY_SUBJECT.items():
        for rid in rids:
            resource_subject[rid] = subj

    now = datetime.now()
    records_to_insert = []

    # --- 策略：按角色和学科偏好生成行为 ---
    random.seed(42)

    # 资源热度分布（Zipf-like，前几个资源更热门）
    popularity_weights = [1.0 / (i + 1) for i in range(len(RESOURCE_IDS))]
    total_weight = sum(popularity_weights)
    popularity_weights = [w / total_weight for w in popularity_weights]

    selected_count = 0

    for user_id, role in sim_users:
        # 只取前80个模拟用户（40教师 + 40学生），数据量适中
        if user_id >= 9 + 80:
            break

        # 决定该用户的行为数量（每个用户 5~20 条）
        num_views = random.randint(4, 12)
        num_downloads = random.randint(1, min(6, num_views))

        # 已为此用户生成行为的资源集合
        user_used_resources = set()

        # 根据角色决定学科偏好
        if role == 'TEACHER':
            # 教师：可能专注于某1-2个学科
            preferred_subjects = random.sample(list(RESOURCES_BY_SUBJECT.keys()), random.randint(1, 2))
        else:
            # 学生：可能需要所有学科，但有强偏好
            preferred_subjects = random.sample(list(RESOURCES_BY_SUBJECT.keys()), random.randint(2, 3))

        # 从偏好学科中选资源
        preferred_rids = []
        for subj in preferred_subjects:
            preferred_rids.extend(RESOURCES_BY_SUBJECT[subj])

        # 如果没有偏好资源，用所有资源
        if not preferred_rids:
            preferred_rids = RESOURCE_IDS.copy()

        # 选 num_views 个资源来浏览
        available_for_view = [r for r in preferred_rids if (user_id, r) not in existing_user_resources and r not in user_used_resources]
        if len(available_for_view) < num_views:
            # 补一些非偏好的资源
            other = [r for r in RESOURCE_IDS if r not in preferred_rids and (user_id, r) not in existing_user_resources and r not in user_used_resources]
            available_for_view.extend(other)
            random.shuffle(available_for_view)

        if not available_for_view:
            continue

        view_count = min(num_views, len(available_for_view))
        viewed_rids = random.sample(available_for_view, view_count)
        user_used_resources.update(viewed_rids)

        # 生成浏览记录
        for rid in viewed_rids:
            # 时间在最近30天内随机分布
            days_ago = random.randint(0, 30)
            hours_offset = random.randint(6, 23)
            create_time = now - timedelta(days=days_ago, hours=random.randint(0, 23) - hours_offset,
                                          minutes=random.randint(0, 59))

            records_to_insert.append((user_id, rid, 'VIEW', create_time))

        # 选一些已浏览的资源来下载
        download_rids = random.sample(viewed_rids, min(num_downloads, len(viewed_rids)))
        for rid in download_rids:
            days_ago = random.randint(0, 15)
            create_time = now - timedelta(days=days_ago, hours=random.randint(6, 23),
                                          minutes=random.randint(0, 59))
            records_to_insert.append((user_id, rid, 'DOWNLOAD', create_time))

        selected_count += 1

    logger.info(f"为 {selected_count} 个模拟用户生成了 {len(records_to_insert)} 条行为记录")

    # 批量插入
    if records_to_insert:
        insert_sql = (
            "INSERT INTO resource_user_behavior (user_id, resource_id, action_type, create_time) "
            "VALUES (%s, %s, %s, %s)"
        )
        batch_size = 500
        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()
            logger.info(f"已插入 {i + len(batch)} / {len(records_to_insert)} 条")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM resource_user_behavior")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM resource_user_behavior")
    users_with_data = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT resource_id) FROM resource_user_behavior")
    resources_with_data = cursor.fetchone()[0]

    logger.info(f"完成！总计行为数: {total}, 有行为的用户: {users_with_data}, 有行为的资源: {resources_with_data}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
