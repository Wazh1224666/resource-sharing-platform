-- 将已入库的旧版模拟资源标题改为「主题·形式」：去掉前缀【毕设模拟数据】与尾部（编号N）
-- 仅处理种子生成的文件（file_name 以 sim_res_ 开头），避免误改其它数据
-- 在 Navicat / mysql 客户端中针对 resource_db 执行一次即可

UPDATE resource
SET title = SUBSTRING_INDEX(
    SUBSTRING(title FROM CHAR_LENGTH('【毕设模拟数据】') + 1),
    '（编号',
    1
)
WHERE title LIKE '【毕设模拟数据】%'
  AND LOCATE('sim_res_', file_name) = 1;
