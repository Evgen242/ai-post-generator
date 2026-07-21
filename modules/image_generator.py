"""
Модуль генерации изображений через Pollinations AI (бесплатно)
"""
import requests
import os
import random
from datetime import datetime

def generate_image(prompt, style="Реалистичный", detail="Средняя", extra_details=""):
    """Генерация изображения через Pollinations AI"""
    try:
        style_map = {
            "Реалистичный": "photorealistic",
            "Мультяшный": "cartoon",
            "Аниме": "anime",
            "Акварель": "watercolor",
            "3D": "3d",
            "Киберпанк": "cyberpunk"
        }
        
        detail_map = {
            "Быстрая": "low",
            "Средняя": "medium", 
            "Высокая": "high",
            "Максимальная": "ultra"
        }
        
        style_en = style_map.get(style, "photorealistic")
        detail_en = detail_map.get(detail, "medium")
        
        image_prompt = f"{prompt}, {style_en} style, {detail_en} detail"
        if extra_details:
            image_prompt += f", {extra_details}"
        
        seed = random.randint(1, 100000)
        url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=1024&seed={seed}"
        
        print(f"Генерация изображения: {image_prompt[:50]}...")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            filename = f"/tmp/image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filename)
            if file_size > 10000:
                print(f"Изображение сохранено: {filename} ({file_size} байт)")
                return filename
            else:
                print(f"Изображение слишком маленькое: {file_size} байт")
                os.remove(filename)
                return None
        else:
            print(f"Ошибка загрузки: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Ошибка генерации изображения: {e}")
        return None
