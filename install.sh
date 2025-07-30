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