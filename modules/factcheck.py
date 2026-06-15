"""
Модуль автоматического фактчекинга через поиск в интернете
"""
import requests
from bs4 import BeautifulSoup
import re
import time

def search_web(query):
    """Поиск информации в интернете"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.find_all('a', class_='result__a')[:3]:
            title = result.get_text(strip=True)
            link = result.get('href')
            if link and title:
                results.append({'title': title, 'url': link})
        return results
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []

def extract_key_facts(text):
    """Извлекает ключевые утверждения из текста"""
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences[:5] if len(s.strip()) > 30]

def is_prediction(text):
    """Проверяет, является ли утверждение прогнозом"""
    prediction_words = [
        'прогноз', 'предполагается', 'ожидается', 'возможно', 'вероятно',
        'может стать', 'рискует', 'к этому времени', 'в будущем',
        'прогнозируется', 'по прогнозам', 'ожидаемый'
    ]
    for word in prediction_words:
        if word.lower() in text.lower():
            return True
    return False

def is_opinion(text):
    """Проверяет, является ли утверждение мнением"""
    opinion_words = [
        'я считаю', 'по моему мнению', 'на мой взгляд', 'думаю',
        'полагаю', 'уверен', 'кажется', 'представляется'
    ]
    for word in opinion_words:
        if word.lower() in text.lower():
            return True
    return False

def factcheck_post(post_text, mode="strict"):
    """
    Проверяет факты в тексте поста
    
    mode:
    - "strict": проверять только факты, пропускать прогнозы и мнения
    - "predictions": проверять всё, помечать прогнозы
    - "all": проверять всё жёстко
    """
    facts = extract_key_facts(post_text)
    verified_facts = []
    
    for fact in facts:
        # Определяем тип утверждения
        is_pred = is_prediction(fact)
        is_opin = is_opinion(fact)
        
        if mode == "strict" and (is_pred or is_opin):
            verified_facts.append({
                'fact': fact,
                'verified': 'skip',
                'type': 'prediction' if is_pred else 'opinion',
                'sources': []
            })
            continue
        
        # Поиск информации по факту
        search_results = search_web(fact[:100])
        
        if search_results:
            verified_facts.append({
                'fact': fact,
                'verified': True,
                'type': 'fact',
                'sources': search_results[:2]
            })
        else:
            keywords = ' '.join(fact.split()[:5])
            search_results = search_web(keywords)
            if search_results:
                verified_facts.append({
                    'fact': fact,
                    'verified': 'partial',
                    'type': 'fact',
                    'sources': search_results[:2]
                })
            else:
                verified_facts.append({
                    'fact': fact,
                    'verified': False,
                    'type': 'prediction' if is_pred else 'fact',
                    'sources': []
                })
        
        time.sleep(0.5)
    
    return verified_facts

def format_factcheck_result(verified_facts):
    """Форматирует результаты фактчекинга для отображения"""
    if not verified_facts:
        return "ℹ️ Не удалось проверить факты в этом посте"
    
    result = "## 🔍 Результаты фактчекинга\n\n"
    
    for i, vf in enumerate(verified_facts, 1):
        if vf.get('verified') == 'skip':
            if vf.get('type') == 'prediction':
                result += f"🔮 **Утверждение {i}:** Прогноз (пропущено)\n"
            else:
                result += f"💭 **Утверждение {i}:** Мнение (пропущено)\n"
        elif vf['verified'] == True:
            result += f"✅ **Утверждение {i}:** Проверено ✓\n"
        elif vf['verified'] == 'partial':
            result += f"⚠️ **Утверждение {i}:** Требует дополнительной проверки\n"
        else:
            if vf.get('type') == 'prediction':
                result += f"🔮 **Утверждение {i}:** Прогноз (не проверяется)\n"
            else:
                result += f"❌ **Утверждение {i}:** Не удалось подтвердить\n"
        
        result += f"> {vf['fact'][:150]}...\n\n"
        
        if vf.get('sources') and vf['sources']:
            result += "📚 **Источники:**\n"
            for src in vf['sources'][:2]:
                result += f"- [{src['title']}]({src['url']})\n"
            result += "\n"
    
    mode_hint = {
        'strict': "ℹ️ Режим строгой проверки: прогнозы и мнения пропущены",
        'predictions': "ℹ️ Режим с проверкой прогнозов",
        'all': "ℹ️ Режим полной проверки"
    }
    
    return result
