# Pushover Setup for Telert

[Pushover](https://pushover.net/) is a simple service that allows you to send real-time notifications to your Android device, iPhone, iPad, and Desktop.

## Why use Pushover with Telert?

- **Simple**: Pushover has a straightforward API with minimal setup
- **Reliable**: Messages are delivered promptly to your devices
- **Cost-effective**: One-time purchase for each platform (around $5 per platform)
- **Cross-platform**: Works on iOS, Android, and desktops
- **Privacy-focused**: No tracking or ads

## Setup Instructions

### 1. Create a Pushover Account

1. Visit [https://pushover.net/](https://pushover.net/) and sign up for an account
2. After signing up, you will receive your **User Key** on your dashboard

### 2. Install Pushover App

1. Download and install the Pushover app on your devices:
   - [iOS App Store](https://apps.apple.com/us/app/pushover-notifications/id506088175)
   - [Google Play Store](https://play.google.com/store/apps/details?id=net.superblock.pushover)
   - [Desktop clients](https://pushover.net/clients)
2. Sign in with your Pushover account
3. Purchase the app if prompted (one-time fee)

### 3. Create a Pushover Application

1. While logged in to Pushover, go to [https://pushover.net/apps/build](https://pushover.net/apps/build)
2. Fill in the form:
   - **Name**: "Telert" (or any name you prefer)
   - **Type**: Application
   - **Description**: "Terminal command notifications"
   - **URL**: https://github.com/navig-me/telert
   - **Icon**: Optional, you can upload a custom icon
3. Accept the terms and click **Create Application**
4. After creation, you'll receive an **API Token/Key** for your application
5. Save this token - you'll need it for Telert configuration

### 4. Configure Telert to use Pushover

Use one of the following methods to configure Telert with your Pushover credentials:

#### Using CLI

```bash
telert config pushover --token "YOUR_APP_TOKEN" --user "YOUR_USER_KEY" --set-default
telert status  # Test your configuration
```

#### Using Environment Variables

```bash
export TELERT_PUSHOVER_TOKEN="YOUR_APP_TOKEN"
export TELERT_PUSHOVER_USER="YOUR_USER_KEY"
```

#### Using Python API

```python
from telert import configure_pushover

configure_pushover("YOUR_APP_TOKEN", "YOUR_USER_KEY", set_default=True)
```

### 5. Testing Your Configuration

After configuring Pushover, you can test it by running:

```bash
telert send "Test notification from Telert via Pushover"
```

You should receive a notification on all your devices with the Pushover app installed.

## Additional Features

Pushover offers several additional features that you might find useful:

- **Priority Levels**: Support for emergency priorities with retry/expire parameters
- **Notification Sounds**: Different sounds for different types of alerts
- **Quiet Hours**: Set times when notifications aren't delivered
- **Delivery Groups**: Organize users and deliver to groups
- **Message Expiration**: Set when messages should expire

These advanced features are not currently implemented in Telert but may be added in future versions.

## Troubleshooting

If you're having issues with Pushover notifications:

1. **Check Credentials**: Ensure your token and user key are correct
2. **Verify App Installation**: Make sure the Pushover app is installed and logged in on your devices
3. **Check Network**: Ensure your device has internet access
4. **API Limits**: Pushover has a limit of 7,500 messages per month per application

## Privacy and Security Notes

- Telert stores your Pushover credentials locally in `~/.config/telert/config.json`
- Messages are sent securely via HTTPS to Pushover's servers
- Consider what information you're sending in notifications - avoid sending sensitive data