
import time
from google import genai
from config import VEO3_API_KEY
from celery import Celery
import os

celery_app = Celery(
    'veo3_tasks',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

client = genai.Client(api_key=VEO3_API_KEY)

@celery_app.task
def generate_with_veo3_task(prompt: str) -> str:
    operation = client.models.generate_videos(
        model="veo-3.0-generate-preview",
        prompt=prompt,
    )
    # Poll the operation status until the video is ready
    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)
    # Сохраняем видео во временный файл
    video_bytes = operation.response.video
    filename = f"output_{int(time.time())}.mp4"
    with open(filename, "wb") as f:
        f.write(video_bytes)
    return filename  # Возвращаем путь к видеофайлу
