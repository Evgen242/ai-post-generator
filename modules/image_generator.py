"""
Модуль генерации изображений с поддержкой нескольких бесплатных API
"""
import requests
import base64
import time

def generate_image(prompt):
    """
    Генерирует изображение по текстовому запросу, перебирая несколько API
    """
    if not prompt:
        print("Ошибка: пустой промпт")
        return None
    
    # Ограничиваем длину промпта
    clean_prompt = prompt[:200].replace(' ', '%20')
    
    # Список бесплатных API для генерации изображений
    apis = [
        {
            "name": "Pollinations",
            "url": f"https://image.pollinations.ai/prompt/{clean_prompt}",
            "timeout": 30
        },
        {
            "name": "Pollinations (alt)",
            "url": f"https://pollinations.ai/p/{clean_prompt}",
            "timeout": 30
        },
        {
            "name": "SDXL (HuggingFace)",
            "url": f"https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            "headers": {"Authorization": "Bearer hf_placeholder"},
            "timeout": 60
        }
    ]
    
    for api in apis:
        try:
            print(f"Пробуем API: {api['name']}")
            
            headers = {}
            if 'headers' in api:
                headers = api['headers']
            
            if api['name'] == "SDXL (HuggingFace)":
                # Для HuggingFace нужен POST запрос с JSON
                payload = {"inputs": prompt[:200]}
                response = requests.post(api['url'], headers=headers, json=payload, timeout=api['timeout'])
            else:
                response = requests.get(api['url'], timeout=api['timeout'])
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    img_base64 = base64.b64encode(response.content).decode()
                    print(f"✅ Изображение сгенерировано через {api['name']}")
                    return f"data:image/png;base64,{img_base64}"
                else:
                    print(f"Ответ не изображение: {content_type[:50]}")
            else:
                print(f"HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"Таймаут {api['name']}")
        except Exception as e:
            print(f"Ошибка {api['name']}: {e}")
        
        time.sleep(0.5)
    
    # Fallback: пробуем старый добрый Pollinations с ретраем
    for i in range(2):
        try:
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}?nologo=true"
            response = requests.get(url, timeout=45)
            if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                img_base64 = base64.b64encode(response.content).decode()
                print(f"✅ Изображение сгенерировано через Pollinations (попытка {i+2})")
                return f"data:image/png;base64,{img_base64}"
        except:
            pass
        time.sleep(1)
    
    print("❌ Все API не сработали")
    return None
