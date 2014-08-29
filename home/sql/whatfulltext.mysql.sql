ALTER TABLE `home_whatfulltext` ENGINE = MYISAM;
ALTER TABLE `home_whatfulltext` ADD FULLTEXT `info_fts` (
  `info`
);