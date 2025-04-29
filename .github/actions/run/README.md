# Telert GitHub Action

This GitHub Action runs a command and sends a notification when it completes. It's perfect for long-running tasks in your CI/CD pipelines.

## Usage

```yaml
- name: Run with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm run build  # The command to run
    label: Build completed  # Optional label for the notification
    provider: telegram      # Optional notification provider
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}  # Required for Telegram
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}  # Required for Telegram
```

## Inputs

| Input | Description | Required |
|-------|-------------|----------|
| `command` | The command to run | Yes |
| `label` | Label to identify the command in notification | No |
| `provider` | Notification provider to use (telegram, teams, slack, discord, pushover, desktop, audio) | No |
| `all-providers` | Send to all configured providers (true/false) | No |
| `only-fail` | Only send notification on failure (true/false) | No |
| `message` | Custom notification message | No |
| `token` | Telegram/Pushover token | No |
| `chat-id` | Telegram chat ID | No |
| `webhook-url` | Webhook URL for Teams/Slack/Discord | No |
| `user-key` | Pushover user key | No |

## Examples

### Simple Example

```yaml
- name: Build with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm run build
    label: Build Project
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Using Microsoft Teams

```yaml
- name: Test with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm test
    label: Run Tests
    provider: teams
    webhook-url: ${{ secrets.TEAMS_WEBHOOK_URL }}
```

### Using Slack

```yaml
- name: Deploy with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: ./deploy.sh
    label: Deploy to Production
    provider: slack
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Using Discord

```yaml
- name: Run e2e tests with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm run e2e
    label: E2E Tests
    provider: discord
    webhook-url: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

### Using Pushover

```yaml
- name: Release with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm run release
    label: Create Release
    provider: pushover
    token: ${{ secrets.PUSHOVER_TOKEN }}
    user-key: ${{ secrets.PUSHOVER_USER_KEY }}
```

### Only Notify on Failure

```yaml
- name: Run critical task
  uses: navig-me/telert/actions/run@v1
  with:
    command: ./critical-task.sh
    label: Critical Task
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
    only-fail: true
```

### Using Environment Variables

Instead of providing credentials in the action inputs, you can use environment variables:

```yaml
- name: Build with notification
  uses: navig-me/telert/actions/run@v1
  env:
    TELERT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELERT_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
    TELERT_DEFAULT_PROVIDER: telegram
  with:
    command: npm run build
    label: Build Project
```

## GitLab CI Integration

Telert also provides a GitLab CI template. Include it in your `.gitlab-ci.yml` file:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/navig-me/telert/main/.github/actions/run/gitlab-ci-template.yml'

build:
  extends: .telert-notify
  variables:
    TELERT_COMMAND: "npm run build"
    TELERT_LABEL: "Build completed"
    TELERT_PROVIDER: "telegram"
    TELERT_TOKEN: ${TELEGRAM_BOT_TOKEN}
    TELERT_CHAT_ID: ${TELEGRAM_CHAT_ID}
  script:
    - npm run build
```

## CircleCI Orb Integration

Telert is also available as a CircleCI Orb:

```yaml
version: 2.1
orbs:
  telert: telert/notify@1.0.0

jobs:
  build:
    docker:
      - image: cimg/node:16.13
    steps:
      - checkout
      - telert/run-notify:
          command: "npm run build"
          label: "Build Project"
          provider: "telegram"

workflows:
  build-workflow:
    jobs:
      - build:
          context: telert-credentials
```

For more information on using Telert with CircleCI, see the [CircleCI Orb Registry](https://circleci.com/developer/orbs/orb/telert/notify).