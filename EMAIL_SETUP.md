# Email Notification Setup

## Overview

The daily mortgage rate collector now sends email notifications to `jhasavi@gmail.com` after each run.

## Setup Required

### 1. Create Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (must be enabled)
3. Scroll down to **App passwords**
4. Generate a new app password:
   - App: Mail
   - Device: Other (custom name) → "Mortgage Rate Tracker"
5. Copy the 16-character password (no spaces)

### 2. Add GitHub Secrets

Go to: https://github.com/jhasavi/mortgage-tracker/settings/secrets/actions

Add these secrets:

1. **GMAIL_USERNAME**
   - Value: `jhasavi@gmail.com`

2. **GMAIL_APP_PASSWORD**
   - Value: The 16-character app password from step 1
   - Example format: `abcd efgh ijkl mnop` (spaces will be removed automatically)

### 3. Test the Notification

Trigger a manual workflow run:
```bash
# Via GitHub UI: Actions → Daily mortgage rates → Run workflow
# Or via GitHub CLI:
gh workflow run daily.yml
```

Check your email (jhasavi@gmail.com) for the notification.

## Email Content

Each morning at 7:30 AM EST, you'll receive an email with:
- Run status (success/failure)
- Link to detailed logs
- Direct link to rates page: https://www.namastebostonhomes.com/rates

Example email:
```
Subject: Mortgage Rates Update - success

Daily mortgage rates collection completed.

Status: success
Run: 42
Time: 2026-01-07T12:30:00Z

View details: https://github.com/jhasavi/mortgage-tracker/actions/runs/...

Latest rates: https://www.namastebostonhomes.com/rates
```

## Schedule

- **Time**: 7:30 AM EST (12:30 UTC) daily
- **What happens**:
  1. Collector runs and fetches latest rates from DCU + Navy Federal
  2. Data is stored in Supabase
  3. Email notification is sent to jhasavi@gmail.com
  4. Website automatically shows updated rates

## Troubleshooting

### No email received

1. **Check spam folder** - First-time emails may be filtered
2. **Verify GitHub secrets** are set correctly
3. **Check workflow logs**: https://github.com/jhasavi/mortgage-tracker/actions
4. **App password expired**: Generate a new one

### Email shows failure

1. Click the "View details" link in the email
2. Review the workflow logs
3. Common issues:
   - Parser error (lender website changed)
   - Network timeout
   - Supabase connection issue

### Want to change email address

Update line 54 in `.github/workflows/daily.yml`:
```yaml
to: your-new-email@example.com
```

## Future: User Alert System

Once we have login functionality, users can:
- Set their own alert preferences
- Choose notification frequency (daily, weekly, only on significant changes)
- Filter by lender or rate type
- Set rate thresholds (e.g., notify when 30Y drops below 5.5%)

For now, this admin notification ensures you're aware of daily updates.
