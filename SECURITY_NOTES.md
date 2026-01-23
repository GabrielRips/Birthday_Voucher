# Security Considerations

## Current Security Status

### ✅ Protected Endpoints (Require Authentication)
- `/daily-check` - Requires Authorization header
- `/manychat-vouchers` - **NOW PROTECTED** - Requires Authorization header
- `/manychat-campaigns` - **NOW PROTECTED** - Requires Authorization header
- `/campaigns-config` (GET, POST, DELETE) - **NOW PROTECTED** - Requires Authorization header

### ⚠️ Public Endpoints (No Authentication Required)
- `/signup` - Public (intended for user signups)
- `/manychat-webhook` - Public (intended for ManyChat webhooks)

## Security Concerns & Recommendations

### 1. Voucher Code Predictability ✅ FIXED

**Previous Issue:** Voucher codes were sequential (TWC-1000, TWC-1001, TWC-1002...)

**Solution Implemented:** Voucher codes are now randomly generated using cryptographically secure random generation.
- Format: `6 alphanumeric characters` (e.g., `A7B9C2`, `X3K9M8`)
- Uses Python's `secrets` module for secure randomness
- Checks database to ensure uniqueness
- Impossible to guess or predict

### 2. Image URL Predictability ⚠️

**Issue:** Image URLs follow predictable pattern: `{base_url}voucher_{code}.jpg`

**Risk:** If someone guesses a voucher code, they can directly access the image.

**Recommendation:**
- Use random/unpredictable voucher codes (see above)
- Consider adding authentication to image access
- Or use signed URLs with expiration times

### 3. Image Directory Access ⚠️

**Issue:** Images are saved to `/var/www/voucher_images/` which may be publicly accessible via web server.

**Risk:** If web server is configured to serve this directory, anyone could browse/access images.

**Recommendation:**
- Ensure web server configuration restricts access to this directory
- Or move images outside web-accessible directory
- Or implement authentication/authorization for image access

### 4. Webhook Endpoints 🔒

**Issue:** `/manychat-webhook` and `/signup` are public endpoints.

**Risk:** Anyone could spam these endpoints to create fake vouchers.

**Recommendation:**
- Add rate limiting
- Add IP whitelisting for ManyChat webhook
- Add CAPTCHA or other bot protection for signup
- Or add API key authentication

### 5. Database Access 🔒

**Issue:** Database credentials stored in `.env` file.

**Risk:** If `.env` file is exposed, database could be compromised.

**Recommendation:**
- Never commit `.env` file to version control
- Use strong database passwords
- Restrict database user permissions (only grant necessary permissions)
- Use SSL/TLS for database connections (already implemented)

## Best Practices

1. **Always use HTTPS** for production
2. **Keep `.env` file secure** - never commit to git
3. **Use strong passwords** for database and API keys
4. **Monitor API usage** for suspicious activity
5. **Implement rate limiting** to prevent abuse
6. **Regular security audits** of endpoints
7. **Keep dependencies updated** to patch vulnerabilities

## Testing Security

To test if endpoints are properly protected:

```bash
# Should return 401 Unauthorized
curl http://your-server/manychat-vouchers?campaign=test

# Should return 200 with Authorization header
curl -H "Authorization: your_webhook_secret_token" \
     http://your-server/manychat-vouchers?campaign=test
```

