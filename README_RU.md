# Veo3 Telegram Bot — Гайд по установке и деплою

## Описание
Veo3 Bot — Telegram-бот для генерации видео по тексту с помощью искусственного интеллекта Veo3. Поддерживает очередь генерации, оплату, админ-панель, аналитику и многое другое.

---

## Быстрый старт (VPS Ubuntu)

### 1. Установите зависимости

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose
```

### 2. Клонируйте репозиторий

```bash
git clone https://github.com/yourusername/veo3_bot.git
cd veo3_bot
```

### 3. Создайте файл .env

Скопируйте пример ниже и заполните своими данными:

```env
BOT_TOKEN=ваш_токен_бота
VEO3_API_KEY=ваш_ключ_veo3
YOOKASSA_SHOP_ID=shop_id
YOOKASSA_API_KEY=api_key
DOMAIN=https://your.domain
YOOMONEY_WALLET=номер_кошелька
CHANNEL_USERNAME=@yourchannel
ADMIN_USER=admin
ADMIN_PASS=yourpassword
DATABASE_URL=postgresql+psycopg2://veo3user:veo3pass@db:5432/veo3
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 4. Запустите контейнеры

```bash
docker-compose up -d --build
```

Бот и админка будут работать в отдельных контейнерах.

---

## Автоматическая установка (скрипт)

Создайте файл `install.sh` и вставьте в него:

```bash
#!/bin/bash
set -e

# 1. Установка зависимостей
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose

# 2. Клонирование репозитория
git clone https://github.com/yourusername/veo3_bot.git || true
cd veo3_bot

# 3. Проверка .env
if [ ! -f .env ]; then
  echo "\nПожалуйста, создайте файл .env на основе README и заполните переменные!"
  exit 1
fi

# 4. Запуск контейнеров
docker-compose up -d --build

echo "\nУстановка завершена! Проверьте логи: docker-compose logs -f"
```

Сделайте скрипт исполняемым и запустите:

```bash
chmod +x install.sh
./install.sh
```

---

## Обновление

```bash
git pull
docker-compose up -d --build
```

---

## Тесты

```bash
docker-compose exec bot pytest
```

---

## Поддержка
По вопросам и предложениям пишите: https://t.me/RoXyGeNOFF