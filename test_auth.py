#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы авторизации
Запуск: python3 test_auth.py
"""
import sys
import os
import hashlib
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, '/var/www/apps/post-generator')

import db
import auth

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Красивый вывод результатов теста"""
    status = f"{GREEN}✅ ПРОЙДЕН{RESET}" if passed else f"{RED}❌ НЕ ПРОЙДЕН{RESET}"
    print(f"{BLUE}📋 Тест:{RESET} {name}")
    print(f"   Статус: {status}")
    if details:
        print(f"   Детали: {details}")
    print()

def test_connection():
    """Тест 1: Подключение к БД"""
    try:
        conn = db.get_connection()
        conn.close()
        print_test("Подключение к PostgreSQL", True, "Соединение установлено")
        return True
    except Exception as e:
        print_test("Подключение к PostgreSQL", False, str(e))
        return False

def test_tables():
    """Тест 2: Существование таблиц"""
    conn = db.get_connection()
    cur = conn.cursor()
    
    tables = ['users', 'posts', 'reg_attempts']
    all_exist = True
    
    for table in tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        exists = cur.fetchone()[0]
        if not exists:
            all_exist = False
            print_test(f"Таблица {table}", False, "Таблица не найдена")
        else:
            print_test(f"Таблица {table}", True, "OK")
    
    cur.close()
    conn.close()
    return all_exist

def test_register():
    """Тест 3: Регистрация нового пользователя"""
    test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"
    test_password = "test123"
    
    user_id, msg = auth.register_user(test_username, test_password, language='ru')
    
    if user_id:
        print_test("Регистрация пользователя", True, f"Создан ID: {user_id}, Логин: {test_username}")
        return user_id, test_username
    else:
        print_test("Регистрация пользователя", False, msg)
        return None, None

def test_duplicate_register():
    """Тест 4: Запрет дубликата"""
    test_username = f"duplicate_{datetime.now().strftime('%H%M%S')}"
    test_password = "test123"
    
    # Первая регистрация
    user_id1, _ = auth.register_user(test_username, test_password, language='ru')
    
    # Вторая регистрация (дубликат)
    user_id2, msg = auth.register_user(test_username, test_password, language='ru')
    
    if user_id1 and not user_id2:
        print_test("Запрет дубликата логина", True, "Дубликат отклонён")
        return True
    else:
        print_test("Запрет дубликата логина", False, "Дубликат был создан")
        return False

def test_login(user_id, username):
    """Тест 5: Вход пользователя"""
    if not user_id:
        print_test("Вход пользователя", False, "Нет тестового пользователя")
        return False
    
    test_password = "test123"
    user = auth.login_user(username, test_password)
    
    if user:
        print_test("Вход пользователя", True, f"Вошёл: {user['username']}, Кредитов: {user['credits']}")
        return True
    else:
        print_test("Вход пользователя", False, "Неверный логин или пароль")
        return False

def test_credits(user_id):
    """Тест 6: Система кредитов"""
    if not user_id:
        print_test("Система кредитов", False, "Нет тестового пользователя")
        return False
    
    credits_before = auth.get_user_credits(user_id)
    auth.use_credit(user_id)
    credits_after = auth.get_user_credits(user_id)
    
    if credits_after == credits_before - 1:
        print_test("Система кредитов", True, f"Было: {credits_before}, Стало: {credits_after}")
        return True
    else:
        print_test("Система кредитов", False, f"Ожидалось {credits_before - 1}, Получено {credits_after}")
        return False

def test_reg_limit():
    """Тест 7: Лимит регистраций"""
    ip = "127.0.0.1"
    fingerprint = f"test_fingerprint_{datetime.now().strftime('%H%M%S')}"
    
    # Проверяем лимит
    is_ok, msg = db.check_reg_limit(ip, fingerprint, max_per_day=3)
    
    print_test("Лимит регистраций", is_ok, msg if not is_ok else "OK")
    return is_ok

def test_avatar(user_id):
    """Тест 8: Сохранение аватара"""
    if not user_id:
        print_test("Сохранение аватара", False, "Нет тестового пользователя")
        return False
    
    test_avatar_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    try:
        db.save_avatar(user_id, test_avatar_url)
        avatar = db.get_avatar(user_id)
        
        if avatar == test_avatar_url:
            print_test("Сохранение аватара", True, "Аватар сохранён и получен")
            return True
        else:
            print_test("Сохранение аватара", False, "Аватар не совпадает")
            return False
    except Exception as e:
        print_test("Сохранение аватара", False, str(e))
        return False

def cleanup_test_user(user_id):
    """Очистка: удаление тестового пользователя"""
    if user_id:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"{YELLOW}🧹 Очистка: тестовый пользователь ID {user_id} удалён{RESET}")

def run_all_tests():
    """Запуск всех тестов"""
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}🧪 ЗАПУСК ТЕСТОВ АВТОРИЗАЦИИ{RESET}")
    print(f"{BLUE}{'='*50}{RESET}\n")
    
    results = []
    
    # Тест 1: Подключение к БД
    results.append(test_connection())
    
    # Тест 2: Существование таблиц
    if results[-1]:
        results.append(test_tables())
    else:
        results.append(False)
    
    # Тест 3: Регистрация
    user_id, username = None, None
    if results[-1]:
        user_id, username = test_register()
        results.append(user_id is not None)
    
    # Тест 4: Запрет дубликата
    if results[-1]:
        results.append(test_duplicate_register())
    
    # Тест 5: Вход
    if user_id:
        results.append(test_login(user_id, username))
    else:
        results.append(False)
    
    # Тест 6: Кредиты
    if user_id:
        results.append(test_credits(user_id))
    else:
        results.append(False)
    
    # Тест 7: Лимит регистраций
    results.append(test_reg_limit())
    
    # Тест 8: Аватар
    if user_id:
        results.append(test_avatar(user_id))
    else:
        results.append(False)
    
    # Очистка
    if user_id:
        cleanup_test_user(user_id)
    
    # Итог
    print(f"\n{BLUE}{'='*50}{RESET}")
    total = len(results)
    passed = sum(results)
    print(f"{BLUE}📊 РЕЗУЛЬТАТЫ:{RESET}")
    print(f"   ✅ Пройдено: {passed}/{total}")
    print(f"   ❌ Не пройдено: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!{RESET}")
    else:
        print(f"\n{YELLOW}⚠️ Часть тестов не пройдена. Проверьте логи.{RESET}")
    
    print(f"{BLUE}{'='*50}{RESET}\n")

if __name__ == "__main__":
    run_all_tests()
