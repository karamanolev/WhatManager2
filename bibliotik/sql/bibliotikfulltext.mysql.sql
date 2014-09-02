ALTER TABLE `bibliotik_bibliotikfulltext` ENGINE = MYISAM;
ALTER TABLE `bibliotik_bibliotikfulltext` ADD FULLTEXT `info_fts` (
  `info`
);
ALTER TABLE `bibliotik_bibliotikfulltext` ADD FULLTEXT `info_more_info_fts` (
  `info`,
  `more_info`
);