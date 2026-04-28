ALTER TABLE resource
ADD COLUMN visibility VARCHAR(16) NOT NULL DEFAULT 'PUBLIC' COMMENT 'PUBLIC or PRIVATE';

UPDATE resource
SET visibility = 'PUBLIC'
WHERE visibility IS NULL OR visibility = '';
