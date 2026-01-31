"""
Помощники для частых задач разработки
"""

import re
import hashlib
import random
import string
from typing import List, Dict, Any, Optional


class QuickConfig:
    """Простой класс для работы с конфигурацией"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Вернуть конфигурацию как словарь"""
        return self._config.copy()


def generate_password(length: int = 12, include_symbols: bool = True) -> str:
    """Генерирует случайный пароль"""
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    
    return ''.join(random.choice(chars) for _ in range(length))


def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Хеширует строку указанным алгоритмом"""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def validate_email(email: str) -> bool:
    """Проверяет корректность email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def clean_string(text: str) -> str:
    """Очищает строку от лишних пробелов и символов"""
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    # Убираем специальные символы (оставляем только буквы, цифры, пробелы и основную пунктуацию)
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Разбивает список на части заданного размера"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Объединяет несколько словарей в один"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


class SimpleLogger:
    """Простой логгер для быстрой отладки"""
    
    def __init__(self, name: str = "MyDevTools"):
        self.name = name
    
    def info(self, message: str) -> None:
        """Информационное сообщение"""
        print(f"[{self.name}] INFO: {message}")
    
    def warning(self, message: str) -> None:
        """Предупреждение"""
        print(f"[{self.name}] WARNING: {message}")
    
    def error(self, message: str) -> None:
        """Ошибка"""
        print(f"[{self.name}] ERROR: {message}")
    
    def debug(self, message: str) -> None:
        """Отладочное сообщение"""
        print(f"[{self.name}] DEBUG: {message}")


# Создаем глобальный экземпляр логгера
logger = SimpleLogger()