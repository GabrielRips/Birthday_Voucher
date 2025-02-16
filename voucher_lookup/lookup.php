<?php
// lookup.php

require_once 'config.php';

// Check that the form was submitted via POST.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Check if this is a confirmation submission.
    if (isset($_POST['confirm_voucher'])) {
        // Get the voucher code and user ID from the hidden fields.
        $voucher_code = trim($_POST['voucher_code']);
        $user_id = trim($_POST['user_id']);

        if (empty($voucher_code)) {
            echo "Voucher code is missing.";
            exit;
        }

        if (empty($user_id)) {
            echo "User ID is missing.";
            exit;
        }

        // Create a new MySQLi connection.
        $mysqli = new mysqli(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT);

        if ($mysqli->connect_error) {
            die("Connection failed: " . $mysqli->connect_error);
        }

        // Update the user's record to mark the voucher as claimed.
        $sql = "UPDATE " . MAIN_TABLE . " SET voucher_claimed = 1, voucher_claimed_date = CURDATE() WHERE voucher_code = ? AND voucher_claimed = 0";
        if ($stmt = $mysqli->prepare($sql)) {
            $stmt->bind_param("s", $voucher_code);
            $stmt->execute();
            
            if ($stmt->affected_rows > 0) {
                // Insert the voucher confirmation into the voucher_log table.
                $logSql = "INSERT INTO " . VOUCHER_LOG_TABLE . " (user_id, voucher_code, claimed_date) VALUES (?, ?, CURDATE())";
                if ($logStmt = $mysqli->prepare($logSql)) {
                    $logStmt->bind_param("is", $user_id, $voucher_code);
                    $logStmt->execute();
                    $logStmt->close();
                } else {
                    echo "Failed to prepare voucher log query: " . $mysqli->error;
                    $stmt->close();
                    $mysqli->close();
                    exit;
                }
                
                $stmt->close();
                $mysqli->close();
                header("Location: index.html");
                exit;
            } else {
                // Either the voucher code is invalid or it was already claimed.
                echo "This voucher has already been confirmed or is invalid.";
                $stmt->close();
                $mysqli->close();
                exit;
            }
        } else {
            echo "Failed to prepare the update statement: " . $mysqli->error;
            exit;
        }
    }

    // Otherwise, handle the lookup.
    $voucher_code = trim($_POST['voucher_code']);

    if (empty($voucher_code)) {
        echo "Please enter a voucher code.";
        exit;
    }

    // Create a new MySQLi connection.
    $mysqli = new mysqli(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT);

    if ($mysqli->connect_error) {
        die("Connection failed: " . $mysqli->connect_error);
    }

    // Set up SSL if necessary.
    if (!empty(MYSQL_SSL_CA)) {
        $mysqli->ssl_set(NULL, NULL, MYSQL_SSL_CA, NULL, NULL);
    }

    // Prepare the SQL statement to safely query the database.
    // Also retrieve the voucher_claimed status and user id.
    $sql = "SELECT id, name, birth_day, birth_month, voucher_claimed FROM " . MAIN_TABLE . " WHERE voucher_code = ?";
    if ($stmt = $mysqli->prepare($sql)) {
        $stmt->bind_param("s", $voucher_code);
        $stmt->execute();
        $stmt->bind_result($user_id, $name, $birth_day, $birth_month, $voucher_claimed);

        if ($stmt->fetch()) {
            echo "<h1>Customer Details</h1>";
            echo "Name: " . htmlspecialchars($name) . "<br>";
            echo "Birthday: " . htmlspecialchars($birth_day) . "/" . htmlspecialchars($birth_month) . "<br>";

            if ($voucher_claimed == 1) {
                // Voucher has already been used.
                echo "<p><strong>This voucher has already been used.</strong></p>";
            } else {
                // Voucher has not been used. Display the confirmation button without a confirmation popup.
                echo '<form method="post" action="lookup.php">';
                echo '<input type="hidden" name="voucher_code" value="' . htmlspecialchars($voucher_code) . '">';
                // Pass the user_id along with the form.
                echo '<input type="hidden" name="user_id" value="' . htmlspecialchars($user_id) . '">';
                echo '<button type="submit" name="confirm_voucher" value="1">Confirm Voucher Use</button>';
                echo '</form>';
            }
        } else {
            echo "No user found with voucher code: " . htmlspecialchars($voucher_code);
        }

        $stmt->close();
    } else {
        echo "Failed to prepare the statement: " . $mysqli->error;
    }

    $mysqli->close();
} else {
    echo "Invalid request method.";
}
?>
