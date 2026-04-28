"""
生成计算机专业相关的模拟资源，导入推荐系统使用。
所有资源只有数据库记录，无实际文件。
"""
import mysql.connector
import random
import uuid
import logging
import hashlib
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost', 'port': 3306, 'database': 'resource_db',
    'user': 'root', 'password': '123456'
}

UPLOAD_DIR = 'E:/resource-sharing-platform/uploads/simulated/'

# ── 计算机专业资源标题 ──────────────────────────────────
CS_RESOURCES = [
    # === 编程语言 ===
    ("C语言程序设计 教学大纲", "pdf", 520_000),
    ("C语言程序设计 期末试题(A卷)含答案", "pdf", 890_000),
    ("C++面向对象程序设计 课件 第2章-类与对象", "pptx", 2_200_000),
    ("C++面向对象程序设计 实验指导书", "pdf", 780_000),
    ("Java程序设计 第5章 异常处理 课件", "pptx", 1_500_000),
    ("Java程序设计基础 课后习题答案", "pdf", 640_000),
    ("Java Web应用开发 实验报告模板", "docx", 120_000),
    ("Python程序设计 教学案例集", "zip", 5_200_000),
    ("Python数据分析 实验指导书", "pdf", 920_000),
    ("Python网络爬虫技术 课件全册", "pptx", 4_800_000),
    ("Go语言并发编程 入门教程", "pdf", 1_100_000),
    ("Rust程序设计 第3章 所有权系统 课件", "pptx", 1_800_000),
    ("JavaScript基础与DOM操作 教学案例", "zip", 3_200_000),
    ("TypeScript入门与实践 课程讲义", "pdf", 860_000),

    # === 数据结构与算法 ===
    ("数据结构 第6章 二叉树 课件", "pptx", 2_600_000),
    ("数据结构与算法 期末试卷及答案", "pdf", 1_200_000),
    ("算法设计与分析 第4章 贪心算法 课件", "pptx", 1_900_000),
    ("算法设计与分析 实验指导手册", "pdf", 720_000),
    ("数据结构 课程设计——校园导航系统", "zip", 4_500_000),
    ("LeetCode高频算法题解 分类汇编", "pdf", 2_800_000),
    ("排序算法可视化演示程序 源代码", "zip", 350_000),
    ("ACM程序设计竞赛 培训讲义", "pdf", 1_600_000),
    ("剑指Offer 名企面试题精解 第2版", "pdf", 3_100_000),

    # === 计算机组成与体系结构 ===
    ("计算机组成原理 第4章 存储器层次结构 课件", "pptx", 3_200_000),
    ("计算机组成原理 实验——MIPS模拟器", "zip", 890_000),
    ("计算机组成原理 期末复习提纲", "pdf", 450_000),
    ("计算机体系结构 第3章 指令级并行 课件", "pptx", 2_700_000),
    ("数字逻辑 实验报告——加法器设计", "docx", 180_000),

    # === 操作系统 ===
    ("操作系统 第5章 进程管理 课件", "pptx", 2_400_000),
    ("操作系统 第8章 文件系统 课件", "pptx", 1_800_000),
    ("操作系统 课程设计——简单文件系统", "zip", 3_600_000),
    ("Linux系统管理 实验指导书", "pdf", 980_000),
    ("Linux Shell编程 从入门到实践", "pdf", 1_400_000),
    ("操作系统 考研真题精选 200题", "pdf", 2_100_000),
    ("Windows系统编程 第6章 进程与线程 课件", "pptx", 1_700_000),

    # === 计算机网络 ===
    ("计算机网络 第5章 传输层 课件", "pptx", 2_900_000),
    ("计算机网络 第7版 课后习题答案", "pdf", 1_300_000),
    ("TCP/IP协议分析 实验指导书", "pdf", 850_000),
    ("计算机网络 课程设计——简单Web服务器", "zip", 420_000),
    ("Wireshark抓包分析 实验报告", "docx", 2_100_000),
    ("计算机网络 考研真题解析", "pdf", 1_800_000),
    ("HTTP协议详解 技术文档", "pdf", 560_000),

    # === 数据库 ===
    ("数据库系统概论 第7章 关系数据库设计 课件", "pptx", 2_300_000),
    ("数据库系统概论 实验指导书——SQL练习", "pdf", 680_000),
    ("MySQL数据库管理 实验手册", "pdf", 1_000_000),
    ("Redis入门与实战 课件", "pptx", 1_600_000),
    ("数据库课程设计——图书管理系统", "zip", 5_800_000),
    ("SQL性能优化 实战案例集", "pdf", 1_200_000),
    ("MongoDB非关系型数据库 教学大纲", "docx", 95_000),

    # === 软件工程 ===
    ("软件工程 第4章 需求分析 课件", "pptx", 2_000_000),
    ("软件工程 课程设计——网上商城系统文档", "zip", 6_500_000),
    ("UML建模 实验指导书", "pdf", 750_000),
    ("软件测试 第5章 白盒测试方法 课件", "pptx", 1_400_000),
    ("敏捷开发方法 Scrum实践指南", "pdf", 880_000),
    ("Git版本控制 入门到精通 教程", "pdf", 1_100_000),

    # === 人工智能 ===
    ("机器学习 第7章 支持向量机 课件", "pptx", 3_400_000),
    ("机器学习 课后习题与实验指导", "pdf", 1_500_000),
    ("深度学习 第8章 卷积神经网络 课件", "pptx", 4_200_000),
    ("深度学习框架PyTorch 入门教程", "pdf", 2_300_000),
    ("自然语言处理 第5章 序列标注 课件", "pptx", 2_800_000),
    ("计算机视觉 实验——图像分类实战", "zip", 12_000_000),
    ("人工智能导论 期末试卷", "pdf", 620_000),
    ("神经网络与深度学习 课程设计指南", "docx", 210_000),

    # === 信息安全 ===
    ("网络安全 第6章 防火墙技术 课件", "pptx", 2_100_000),
    ("密码学 第4章 公钥密码体制 课件", "pptx", 1_900_000),
    ("CTF竞赛入门 实验指导手册", "pdf", 3_600_000),
    ("Web安全渗透测试 实验指南", "pdf", 2_000_000),
    ("信息安全 课程设计——加密通信系统", "zip", 780_000),

    # === 其他CS相关 ===
    ("计算机导论 第3章 计算思维 课件", "pptx", 1_300_000),
    ("离散数学 第6章 图论 课件", "pptx", 2_500_000),
    ("离散数学 课后习题详解", "pdf", 1_700_000),
    ("编译原理 第4章 语法分析 课件", "pptx", 2_800_000),
    ("编译原理 实验——词法分析器实现", "zip", 320_000),
    ("计算机图形学 第7章 光照模型 课件", "pptx", 3_000_000),
    ("计算机图形学 实验——OpenGL基础", "zip", 1_200_000),
    ("大数据技术 Hadoop与Spark入门", "pdf", 2_400_000),
    ("云计算技术 第5章 虚拟化技术 课件", "pptx", 2_200_000),
    ("物联网技术概论 教学大纲", "docx", 88_000),
    ("人机交互 第6章 可用性评估 课件", "pptx", 1_600_000),
    ("区块链技术 原理与应用 课件", "pptx", 2_500_000),
    ("嵌入式系统 实验——LED驱动开发", "zip", 560_000),
    ("软件工程 专业英语 词汇手册", "pdf", 340_000),
    ("计算机专业 考研复试 面试题汇总", "pdf", 1_800_000),
    ("IT项目管理 第8章 风险管理 课件", "pptx", 1_500_000),
    ("微服务架构设计 实践指南", "pdf", 1_900_000),
    ("Docker容器技术 从入门到实战", "pdf", 1_600_000),
    ("Kubernetes集群管理 入门教程", "pdf", 2_100_000),
]

# ── 真实资源（不重复创建，用于记录它们的ID范围）──
REAL_RESOURCE_IDS = list(range(2050, 2080))  # 30 existing resources


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # 获取模拟教师列表
    cursor.execute(
        "SELECT id, username FROM user WHERE username LIKE 'sim_teacher_%' ORDER BY id"
    )
    teachers = cursor.fetchall()
    logger.info(f"找到 {len(teachers)} 个模拟教师账号")

    if not teachers:
        logger.error("没有模拟教师账号，无法分配上传者")
        return

    # 获取现有资源标题，避免重复
    cursor.execute("SELECT title FROM resource")
    existing_titles = {row['title'] for row in cursor.fetchall()}
    logger.info(f"现有 {len(existing_titles)} 个资源标题")

    # 过滤掉已存在的标题
    new_resources = [
        (title, ftype, size)
        for title, ftype, size in CS_RESOURCES
        if title not in existing_titles
    ]
    logger.info(f"待插入新资源: {len(new_resources)} 个 (已过滤掉 {len(CS_RESOURCES) - len(new_resources)} 个重复标题)")

    if not new_resources:
        logger.warning("没有新的资源需要插入")
        return

    # 准备插入数据
    random.seed(20260427)
    records = []
    now = datetime.now()

    for i, (title, file_type, file_size) in enumerate(new_resources):
        # 分配上传者：轮转分配给模拟教师
        teacher = teachers[i % len(teachers)]
        uploader_id = teacher['id']

        # 文件名
        ext = file_type
        file_name = f"{uuid.uuid4().hex[:16]}.{ext}"

        # 文件路径（占位，实际文件不存在）
        file_path = f"{UPLOAD_DIR}{file_name}"

        # 创建时间：过去90天内随机
        days_ago = random.randint(0, 90)
        hours = random.randint(6, 23)
        minutes = random.randint(0, 59)
        create_time = now - timedelta(days=days_ago, hours=24-hours, minutes=minutes)

        records.append((title, file_name, file_path, file_size, file_type, uploader_id, create_time))

    # 批量插入
    insert_sql = (
        "INSERT INTO resource (title, file_name, file_path, file_size, file_type, uploader_id, create_time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )

    batch_size = 50
    inserted_ids = []
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        # 获取最后插入的ID范围
        if cursor.lastrowid:
            for j in range(len(batch)):
                inserted_ids.append(cursor.lastrowid + j)
        logger.info(f"已插入 {i + len(batch)} / {len(records)} 条")

    # 统计验证
    cursor.execute("SELECT COUNT(*) as cnt FROM resource")
    total = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(DISTINCT uploader_id) as cnt FROM resource")
    uploaders = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(DISTINCT file_type) as cnt FROM resource")
    types = cursor.fetchone()['cnt']
    cursor.execute("SELECT uploader_id, COUNT(*) as cnt FROM resource GROUP BY uploader_id ORDER BY cnt DESC LIMIT 5")
    top_uploaders = cursor.fetchall()

    logger.info(f"\n=== 插入完成 ===")
    logger.info(f"资源总数: {total}")
    logger.info(f"上传者数量: {uploaders}")
    logger.info(f"文件类型数量: {types}")
    logger.info(f"各文件类型分布:")
    cursor.execute("SELECT file_type, COUNT(*) as cnt FROM resource GROUP BY file_type ORDER BY cnt DESC")
    for row in cursor.fetchall():
        logger.info(f"  .{row['file_type']}: {row['cnt']} 个")
    logger.info(f"上传者分布(前5):")
    for row in top_uploaders:
        logger.info(f"  用户 {row['uploader_id']}: {row['cnt']} 个资源")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
