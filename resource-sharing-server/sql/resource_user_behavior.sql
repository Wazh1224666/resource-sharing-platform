-- 用户–资源行为表：用于毕设中协同过滤、推荐等实验（浏览 / 下载）
-- 在 resource_db 中执行一次即可

CREATE TABLE IF NOT EXISTS resource_user_behavior (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户 id',
    resource_id BIGINT NOT NULL COMMENT '资源 id',
    action_type VARCHAR(16) NOT NULL COMMENT 'VIEW 浏览 / DOWNLOAD 下载',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_id (user_id),
    KEY idx_resource_id (resource_id),
    KEY idx_user_resource (user_id, resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
