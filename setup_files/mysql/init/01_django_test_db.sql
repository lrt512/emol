-- Grant Django test database permissions
GRANT ALL PRIVILEGES ON `test_%`.* TO 'emol_db_user'@'%';
FLUSH PRIVILEGES;
