
import time
from google import genai
from config import VEO3_API_KEY

client = genai.Client(api_key=VEO3_API_KEY)

def generate_with_veo3(prompt: str) -> str:
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
