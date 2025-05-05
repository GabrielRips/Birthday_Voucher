<?php
session_start();
if (empty($_SESSION['logged_in'])) {
    header("Location: login.php");
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Voucher Lookup</title>
</head>
<body>
    <h1>Enter Voucher Code</h1>
    <form method="POST" action="lookup.php">
        <label for="voucher_code">Voucher Code:</label>
        <input type="text" id="voucher_code" name="voucher_code" required>
        <input type="submit" value="Lookup">
    </form>
</body>
</html>
