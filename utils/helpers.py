from datetime import datetime, timedelta

def format_time(seconds: int) -> str:
    """Форматирование времени в читаемый вид"""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        return f"{seconds // 60} мин"
    else:
        return f"{seconds // 3600} ч"

def parse_auth_data(auth_str: str) -> dict:
    """Парсинг данных авторизации из строки"""
    # Реальная логика парсинга должна соответствовать формату ваших данных
    return {
        'user_id': auth_str.split('user=')[1].split('&')[0],
        'auth_date': auth_str.split('auth_date=')[1].split('&')[0],
        'signature': auth_str.split('signature=')[1].split('&')[0]
    }
