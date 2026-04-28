-- 为种子资源标题补回「（编号N）」，N 取自 file_name：sim_res_N.txt
-- 仅处理 file_name 以 sim_res_ 开头且标题尚未含「（编号」的记录

UPDATE resource
SET title = CONCAT(
    title,
    '（编号',
    SUBSTRING_INDEX(SUBSTRING_INDEX(file_name, '.', 1), '_', -1),
    '）'
)
WHERE LOCATE('sim_res_', file_name) = 1
  AND title NOT LIKE '%（编号%';
