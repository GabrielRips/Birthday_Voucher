<?php
// config.php

require_once __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

define('MYSQL_HOST', $_ENV['MYSQL_HOST']);
define('MYSQL_PORT', $_ENV['MYSQL_PORT']);
define('MYSQL_USER', $_ENV['MYSQL_USER']);
define('MYSQL_PASSWORD', $_ENV['MYSQL_PASSWORD']);
define('MYSQL_DATABASE', $_ENV['MYSQL_DATABASE']);
define('MYSQL_SSL_CA', $_ENV['MYSQL_SSL_CA']);
define('MAIN_TABLE', $_ENV['MYSQL_USERS_TABLE']);
define('VOUCHER_LOG_TABLE', $_ENV['MYSQL_VOUCHER_LOG_TABLE']);
define('SITE_PASSWORD', $_ENV['SITE_PASSWORD']);
?>
