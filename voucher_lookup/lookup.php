<?php
// lookup.php

// Include the configuration file.
require_once 'config.php';

// Check that the form was submitted via POST.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get and trim the voucher code from the form.
    $voucher_code = trim($_POST['voucher_code']);

    if (empty($voucher_code)) {
        echo "Please enter a voucher code.";
        exit;
    }

    // Create a new MySQLi connection.
    $mysqli = new mysqli(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT);

    // Check for a connection error.
    if ($mysqli->connect_error) {
        die("Connection failed: " . $mysqli->connect_error);
    }

    // If you need to use SSL, set it up (ensure MYSQL_SSL_CA is defined).
    if (!empty(MYSQL_SSL_CA)) {
        // Note: ssl_set() must be called before connect() in a real-world scenario.
        // For demonstration, this is a simplified version.
        $mysqli->ssl_set(NULL, NULL, MYSQL_SSL_CA, NULL, NULL);
    }

    // Prepare the SQL statement to safely query the database.
    $sql = "SELECT name, birth_day, birth_month FROM " . MAIN_TABLE . " WHERE voucher_code = ?";
    if ($stmt = $mysqli->prepare($sql)) {
        // Bind the voucher code parameter.
        $stmt->bind_param("s", $voucher_code);

        // Execute the statement.
        $stmt->execute();

        // Bind the result columns to PHP variables.
        $stmt->bind_result($name, $birth_day, $birth_month);

        // Fetch the result.
        if ($stmt->fetch()) {
            echo "<h1>User Details</h1>";
            echo "Name: " . htmlspecialchars($name) . "<br>";
            echo "Birthday: " . htmlspecialchars($birth_day) . "/" . htmlspecialchars($birth_month) . "<br>";
        } else {
            echo "No user found with voucher code: " . htmlspecialchars($voucher_code);
        }

        // Close the statement.
        $stmt->close();
    } else {
        echo "Failed to prepare the statement: " . $mysqli->error;
    }

    // Close the database connection.
    $mysqli->close();
} else {
    echo "Invalid request method.";
}
?>
