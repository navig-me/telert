# CI/CD Integrations for Telert

Telert provides integrations for popular CI/CD platforms to make it easy to get notifications when your builds, tests, or deployments complete.

## GitHub Actions

The Telert GitHub Action allows you to run commands in your workflow and receive notifications when they complete.

### Basic Usage

```yaml
- name: Run tests with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm test
    label: Run Tests
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Available Inputs

| Input | Description | Required |
|-------|-------------|----------|
| `command` | The command to run | Yes |
| `label` | Label to identify the command | No |
| `provider` | Notification provider to use | No |
| `all-providers` | Send to all configured providers | No |
| `only-fail` | Only notify on failure | No |
| `message` | Custom notification message | No |
| `token` | Telegram/Pushover token | No |
| `chat-id` | Telegram chat ID | No |
| `webhook-url` | Webhook URL for Teams/Slack/Discord | No |
| `user-key` | Pushover user key | No |

### Provider-Specific Examples

#### Telegram

```yaml
- name: Run with Telegram notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm run build
    label: Build Project
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

#### Microsoft Teams

```yaml
- name: Run with Teams notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm test
    label: Run Tests
    provider: teams
    webhook-url: ${{ secrets.TEAMS_WEBHOOK_URL }}
```

#### Slack

```yaml
- name: Run with Slack notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: ./deploy.sh
    label: Deploy to Production
    provider: slack
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Using Environment Variables

```yaml
- name: Run with environment variable configuration
  uses: navig-me/telert/actions/run@v1
  env:
    TELERT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELERT_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
    TELERT_DEFAULT_PROVIDER: telegram
  with:
    command: npm run build
    label: Build Project
```

#### Complete Workflow Example

```yaml
name: Build and Notify

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      
      - name: Install dependencies
        uses: navig-me/telert/actions/run@v1
        with:
          command: npm install
          label: Install Dependencies
          provider: telegram
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
      
      - name: Run tests
        uses: navig-me/telert/actions/run@v1
        with:
          command: npm test
          label: Run Tests
          provider: telegram
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
          only-fail: true
      
      - name: Build
        uses: navig-me/telert/actions/run@v1
        with:
          command: npm run build
          label: Build Project
          provider: telegram
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## GitLab CI Integration

Telert provides a GitLab CI template that makes it easy to add notifications to your GitLab pipelines.

### Basic Usage

Include the template in your `.gitlab-ci.yml` file:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/navig-me/telert/main/.github/actions/run/gitlab-ci-template.yml'

build:
  extends: .telert-notify
  variables:
    TELERT_COMMAND: "npm run build"
    TELERT_LABEL: "Build Project"
    TELERT_PROVIDER: "telegram"
    TELERT_TOKEN: ${TELEGRAM_BOT_TOKEN}
    TELERT_CHAT_ID: ${TELEGRAM_CHAT_ID}
  script:
    - npm run build
```

### Available Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELERT_COMMAND` | Command that was run (for notification message) | Yes |
| `TELERT_LABEL` | Label to identify the job | No |
| `TELERT_PROVIDER` | Notification provider to use | No |
| `TELERT_ALL_PROVIDERS` | Set to "true" to send to all providers | No |
| `TELERT_TOKEN` | Telegram/Pushover token | No |
| `TELERT_CHAT_ID` | Telegram chat ID | No |
| `TELERT_TEAMS_WEBHOOK` | Teams webhook URL | No |
| `TELERT_SLACK_WEBHOOK` | Slack webhook URL | No |
| `TELERT_DISCORD_WEBHOOK` | Discord webhook URL | No |
| `TELERT_PUSHOVER_TOKEN` | Pushover token | No |
| `TELERT_PUSHOVER_USER` | Pushover user key | No |

### Complete GitLab CI Example

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/navig-me/telert/main/.github/actions/run/gitlab-ci-template.yml'

stages:
  - setup
  - test
  - build
  - deploy

install:
  extends: .telert-notify
  stage: setup
  variables:
    TELERT_COMMAND: "npm install"
    TELERT_LABEL: "Install Dependencies"
    TELERT_PROVIDER: "telegram"
  script:
    - npm install

test:
  extends: .telert-notify
  stage: test
  variables:
    TELERT_COMMAND: "npm test"
    TELERT_LABEL: "Run Tests"
    TELERT_PROVIDER: "slack"
  script:
    - npm test

build:
  extends: .telert-notify
  stage: build
  variables:
    TELERT_COMMAND: "npm run build"
    TELERT_LABEL: "Build Project"
    TELERT_PROVIDER: "telegram"
  script:
    - npm run build

deploy:
  extends: .telert-notify
  stage: deploy
  variables:
    TELERT_COMMAND: "./deploy.sh"
    TELERT_LABEL: "Deploy to Production"
    TELERT_PROVIDER: "teams"
    TELERT_ALL_PROVIDERS: "true"
  script:
    - ./deploy.sh
  only:
    - main
```

## CircleCI Orb

Telert is available as a CircleCI Orb for easy integration with CircleCI pipelines.

### Basic Usage

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

### Commands

The Telert orb provides two main commands:

#### `run-notify`

Runs a command and sends a notification when it completes.

```yaml
- telert/run-notify:
    command: "npm run build"
    label: "Build Project"
    provider: "telegram"
    all_providers: false
    only_fail: false
    message: "Build completed!"
```

#### `notify`

Sends a notification without running a command. Useful for sending custom notifications at specific points in your workflow.

```yaml
- telert/notify:
    message: "Deployment completed successfully!"
    provider: "slack"
    all_providers: false
```

### Complete CircleCI Example

```yaml
version: 2.1
orbs:
  telert: telert/notify@1.0.0
  node: circleci/node@5.0.2

jobs:
  build-and-test:
    docker:
      - image: cimg/node:16.13
    steps:
      - checkout
      
      - node/install-packages:
          pkg-manager: npm
      
      - telert/run-notify:
          command: "npm run lint"
          label: "Lint Code"
          provider: "telegram"
      
      - telert/run-notify:
          command: "npm test"
          label: "Run Tests"
          provider: "telegram"
          only_fail: true
      
      - telert/run-notify:
          command: "npm run build"
          label: "Build"
          provider: "telegram"
      
      - telert/notify:
          message: "Build and test workflow completed!"
          provider: "slack"

workflows:
  version: 2
  build-test:
    jobs:
      - build-and-test:
          context: telert-credentials
```

### Context Setup

For CircleCI, it's recommended to set up a context with your notification credentials:

1. Go to Organization Settings > Contexts
2. Create a new context named "telert-credentials"
3. Add the relevant environment variables:
   - `TELERT_TOKEN` and `TELERT_CHAT_ID` for Telegram
   - `TELERT_TEAMS_WEBHOOK` for Microsoft Teams
   - `TELERT_SLACK_WEBHOOK` for Slack
   - `TELERT_DISCORD_WEBHOOK` for Discord
   - `TELERT_PUSHOVER_TOKEN` and `TELERT_PUSHOVER_USER` for Pushover

Then reference this context in your workflow configuration.