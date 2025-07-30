# Veo3 Telegram Bot — Installation & Deployment Guide

## Description
Veo3 Bot is a Telegram bot for generating videos from text using Veo3 AI. It supports generation queue, payments, admin panel, analytics, and more.

---

## Quick Start (VPS Ubuntu)

### 1. Install dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose
```

### 2. Clone the repository

```bash
git clone https://github.com/yourusername/veo3_bot.git
cd veo3_bot
```

### 3. Create the .env file

Copy the example below and fill in your data:

```env
BOT_TOKEN=your_bot_token
VEO3_API_KEY=your_veo3_key
YOOKASSA_SHOP_ID=shop_id
YOOKASSA_API_KEY=api_key
DOMAIN=https://your.domain
YOOMONEY_WALLET=wallet_number
CHANNEL_USERNAME=@yourchannel
ADMIN_USER=admin
ADMIN_PASS=yourpassword
DATABASE_URL=postgresql+psycopg2://veo3user:veo3pass@db:5432/veo3
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 4. Start containers

```bash
docker-compose up -d --build
```

The bot and admin panel will run in separate containers.

---

## Automatic installation (script)

Create a file `install.sh` and paste the following:

```bash
#!/bin/bash
set -e

# 1. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose

# 2. Clone repository
git clone https://github.com/yourusername/veo3_bot.git || true
cd veo3_bot

# 3. Check .env
if [ ! -f .env ]; then
  echo "\nPlease create a .env file based on README and fill in the variables!"
  exit 1
fi

# 4. Start containers
docker-compose up -d --build

echo "\nInstallation complete! Check logs: docker-compose logs -f"
```

Make the script executable and run:

```bash
chmod +x install.sh
./install.sh
```

---

## Update

```bash
git pull
docker-compose up -d --build
```

---

## Tests

```bash
docker-compose exec bot pytest
```

---

## Support
For questions and suggestions, contact: https://t.me/RoXyGeNOFF