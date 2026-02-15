# Web Server Setup Guide for Serving Voucher Images

This guide explains how to configure your web server (nginx or Apache) to serve voucher images from the `images` directory, making them accessible at `http://209.38.84.84/images/voucher_XXXXXXX.jpg`.

## Overview

Your Flask application saves voucher images to the `images` directory. To make these images publicly accessible, you need to configure your web server to serve static files from this directory.

---

## Option 1: Nginx Configuration (Recommended)

### Step 1: Locate Your Nginx Configuration

On most Linux systems, nginx configuration files are located at:
- `/etc/nginx/sites-available/` (for site-specific configs)
- `/etc/nginx/nginx.conf` (main config file)

### Step 2: Add Location Block for Images

Add the following location block to your nginx server configuration. This should be added inside your `server` block:

```nginx
server {
    listen 80;
    server_name 209.38.84.84;  # Your server IP or domain name

    # ... your existing Flask app configuration ...

    # Serve static images from the images directory
    location /images/ {
        alias /path/to/your/project/images/;  # Replace with your actual project path
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # Allow CORS if needed (for cross-origin requests)
        add_header Access-Control-Allow-Origin *;
        
        # Security headers
        add_header X-Content-Type-Options "nosniff";
    }
}
```

### Step 3: Update the Path

Replace `/path/to/your/project/images/` with the actual absolute path to your project's `images` directory. For example:
- `/home/username/Birthday_Voucher/images/`
- `/var/www/birthday_voucher/images/`

**Important:** The path must end with a trailing slash, and the `alias` directive should point to the directory containing the images.

### Step 4: Test and Reload Nginx

```bash
# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

### Step 5: Set Proper Permissions

Ensure the `images` directory has proper permissions:

```bash
# Make sure nginx can read the directory
sudo chmod 755 /path/to/your/project/images/
sudo chmod 644 /path/to/your/project/images/*.jpg

# If needed, change ownership
sudo chown -R www-data:www-data /path/to/your/project/images/
```

---

## Option 2: Apache Configuration

### Step 1: Locate Your Apache Configuration

Apache configuration files are typically located at:
- `/etc/apache2/sites-available/` (for site-specific configs)
- `/etc/apache2/apache2.conf` (main config file)

### Step 2: Add Directory or Alias Directive

Add one of the following to your Apache virtual host configuration:

**Option A: Using Alias (Recommended)**

```apache
<VirtualHost *:80>
    ServerName 209.38.84.84  # Your server IP or domain name
    
    # ... your existing Flask app configuration ...

    # Serve static images from the images directory
    Alias /images /path/to/your/project/images
    
    <Directory "/path/to/your/project/images">
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
        
        # Set proper MIME types
        <FilesMatch "\.(jpg|jpeg|png|gif)$">
            Header set Content-Type "image/jpeg"
        </FilesMatch>
    </Directory>
</VirtualHost>
```

**Option B: Using Directory Directive**

```apache
<VirtualHost *:80>
    ServerName 209.38.84.84
    
    # ... your existing Flask app configuration ...

    <Directory "/path/to/your/project/images">
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

### Step 3: Update the Path

Replace `/path/to/your/project/images` with the actual absolute path to your project's `images` directory.

### Step 4: Enable Required Modules (if needed)

```bash
# Enable mod_headers if you want to add custom headers
sudo a2enmod headers

# Enable mod_alias if using Alias directive
sudo a2enmod alias
```

### Step 5: Test and Reload Apache

```bash
# Test Apache configuration
sudo apache2ctl configtest

# If test passes, reload Apache
sudo systemctl reload apache2
```

### Step 6: Set Proper Permissions

```bash
# Make sure Apache can read the directory
sudo chmod 755 /path/to/your/project/images/
sudo chmod 644 /path/to/your/project/images/*.jpg

# If needed, change ownership
sudo chown -R www-data:www-data /path/to/your/project/images/
```

---

## Option 3: Using Flask's Built-in Static File Serving (Not Recommended for Production)

If you don't have nginx or Apache, you can serve static files directly from Flask, but this is **not recommended for production** as it's less efficient:

```python
from flask import send_from_directory

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory('images', filename)
```

**Note:** This approach is less efficient and should only be used for development or if you can't configure a proper web server.

---

## Testing the Configuration

After configuring your web server, test that images are accessible:

1. **Generate a test voucher** (this will create an image in the `images` directory)
2. **Access the image directly** in your browser:
   ```
   http://209.38.84.84/images/voucher_1234567.jpg
   ```
3. **Check the response headers** using curl:
   ```bash
   curl -I http://209.38.84.84/images/voucher_1234567.jpg
   ```

You should see:
- HTTP 200 status code
- Proper Content-Type header (image/jpeg)
- The image should display in your browser

---

## Troubleshooting

### Images Return 404 Not Found

1. **Check the file path**: Ensure the path in your web server config matches the actual directory location
2. **Check file permissions**: Make sure the web server user (usually `www-data` or `nginx`) can read the files
3. **Check file exists**: Verify the image file actually exists in the `images` directory
4. **Check nginx/Apache error logs**:
   ```bash
   # Nginx
   sudo tail -f /var/log/nginx/error.log
   
   # Apache
   sudo tail -f /var/log/apache2/error.log
   ```

### Images Return 403 Forbidden

1. **Check directory permissions**: The directory must be readable by the web server user
2. **Check SELinux** (if enabled): You may need to set the proper SELinux context
3. **Check directory listing**: Ensure `Options Indexes` is not required if you don't want directory listing

### CORS Issues (if accessing from different domain)

If you need to serve images to external domains, make sure CORS headers are properly configured in your web server.

---

## Security Considerations

1. **Limit access**: Consider restricting access to specific IPs or domains if needed
2. **Rate limiting**: Implement rate limiting to prevent abuse
3. **File validation**: Ensure only image files are served from this directory
4. **HTTPS**: Use HTTPS in production to encrypt image transfers

---

## Example: Complete Nginx Configuration

Here's a complete example nginx configuration that serves both your Flask app and static images:

```nginx
server {
    listen 80;
    server_name 209.38.84.84;

    # Serve static images
    location /images/ {
        alias /home/username/Birthday_Voucher/images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin *;
    }

    # Proxy Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Need Help?

If you're still having issues:
1. Check your web server error logs
2. Verify file paths and permissions
3. Test with a simple HTML file first to ensure the directory is accessible
4. Make sure your firewall allows HTTP/HTTPS traffic on port 80/443

