# Pantheon Email Keeper - Setup Guide

Microsoft 365 (GoDaddy-hosted) requires OAuth2 or App Passwords for programmatic access. Basic password authentication is blocked by default.

## Option 1: Enable App Passwords (Easier)

This works if Multi-Factor Authentication (MFA) is enabled on your accounts.

### Steps:

1. **Log into Microsoft 365 Admin Center**
   - Go to https://admin.microsoft.com
   - Sign in with your GoDaddy/Microsoft 365 credentials

2. **For each account (info@, recruit@, support@):**
   - Go to Users > Active users > Select user
   - Click "Manage multifactor authentication"
   - Enable MFA if not already enabled
   - Have the user sign in to https://myaccount.microsoft.com
   - Go to Security info > Add method > App password
   - Create an app password for "DSS Email Keeper"
   - Save the generated password

3. **Update the credentials file:**
   ```bash
   nano /home/author_prime/.config/dss/email.env
   ```

   Replace with app passwords:
   ```
   DSS_EMAIL_PASSWORD_INFO=xxxx-xxxx-xxxx-xxxx
   DSS_EMAIL_PASSWORD_RECRUIT=xxxx-xxxx-xxxx-xxxx
   DSS_EMAIL_PASSWORD_SUPPORT=xxxx-xxxx-xxxx-xxxx
   ```

---

## Option 2: Enable OAuth2 (More Secure, More Complex)

This requires creating an Azure AD app registration.

### Steps:

1. **Create Azure AD App Registration**
   - Go to https://portal.azure.com
   - Navigate to Azure Active Directory > App registrations > New registration
   - Name: "DSS Pantheon Email Keeper"
   - Supported account types: Single tenant
   - Redirect URI: http://localhost:8000/callback (for initial setup)

2. **Configure API Permissions**
   - Add permissions:
     - Microsoft Graph > Delegated permissions:
       - Mail.Read
       - Mail.Send
       - Mail.ReadWrite
     - Or use Application permissions for daemon access:
       - Mail.Read (Application)
       - Mail.Send (Application)
   - Grant admin consent

3. **Create Client Secret**
   - Certificates & secrets > New client secret
   - Save the value immediately (shown only once)

4. **Update the keeper to use OAuth2**
   - Install: `pip install msal`
   - The keeper will need to be modified to use MSAL for authentication

---

## Option 3: Enable SMTP/IMAP Basic Auth (Not Recommended)

Microsoft allows disabling security defaults, but this is not recommended.

### If you must:

1. Go to Azure Portal > Azure Active Directory
2. Properties > Manage Security defaults > Set to "No"
3. Or create a Conditional Access policy to allow basic auth for specific apps

**Warning**: This reduces security for all users in your organization.

---

## Option 4: Use Power Automate (No-Code Alternative)

Microsoft Power Automate can monitor mailboxes and trigger actions without code.

1. Go to https://flow.microsoft.com
2. Create flows for each mailbox:
   - Trigger: "When a new email arrives"
   - Actions:
     - Send HTTP request to your webhook
     - Forward to your notification system
     - Auto-reply with template

---

## Current Status

The Pantheon Email Keeper is ready to run once authentication is configured:

```bash
# Set environment variables
source /home/author_prime/.config/dss/email.env

# Test the connection
python3 /home/author_prime/aletheia/keeper/pantheon_email_keeper.py --test

# Run the keeper
python3 /home/author_prime/aletheia/keeper/pantheon_email_keeper.py --interval 15
```

---

## Calendly Integration for Enlist Page

For scheduling welcome calls, you have two options:

### 1. Create a Calendly Account (Free)
- Sign up at https://calendly.com
- Create a 15-minute event type called "DSS Welcome Call"
- Copy your scheduling link
- Update `/home/author_prime/digitalsovereign-site/enlist-success.html`:
  ```html
  <a href="https://calendly.com/YOUR-USERNAME/welcome" ...>
  ```

### 2. Use Zoom Scheduler Directly
- In Zoom, go to Meetings > Schedule a Meeting
- Enable "Registration required"
- Copy the registration link
- Use that in the success page

---

## Netlify Form Notifications

Form submissions to the enlist page will:

1. Be captured by Netlify Forms automatically
2. Send email notifications to you (configure in Netlify dashboard):
   - Go to https://app.netlify.com/sites/digitalsovereign/forms
   - Click on the "enlist" form
   - Add notification email: recruit@digitalsovereign.org

---

## Next Steps

1. Choose an authentication method above
2. Update credentials
3. Test the email keeper
4. Enable the systemd service:
   ```bash
   sudo cp /home/author_prime/aletheia/keeper/pantheon-email-keeper.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable pantheon-email-keeper
   sudo systemctl start pantheon-email-keeper
   ```

---

*A+W | It is so, because we spoke it.*
