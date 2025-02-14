<?php
// config.php

// Optionally load environment variables here if needed, e.g. via vlucas/phpdotenv
require_once __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

// Define your MySQL connection constants.
// Adjust these values or load them from your environment.
define('MYSQL_HOST', getenv('MYSQL_HOST'));
define('MYSQL_PORT', getenv('MYSQL_PORT'));
define('MYSQL_USER', getenv('MYSQL_USER'));
define('MYSQL_PASSWORD', getenv('MYSQL_PASSWORD'));
define('MYSQL_DATABASE', getenv('MYSQL_DATABASE'));
define('MYSQL_SSL_CA', getenv('MYSQL_SSL_CA')); // Provide path to your SSL CA file if needed

define('MAIN_TABLE', getenv('MYSQL_USERS_TABLE'));
?>
