"""
Safe collection operations for beginners.

This module provides safe versions of common collection operations
that prevent typical mistakes and provide helpful error messages.
"""

from typing import Any, Optional, Union, List, Dict, Tuple


def safe_get(collection: Union[List, Tuple, Dict, str], index: Union[int, str], default: Any = None) -> Any:
    """
    Safely get an element from a collection by index or key.
    
    Предотвращает ошибки IndexError и KeyError, возвращая значение по умолчанию
    вместо исключения. Подходит для списков, кортежей, словарей и строк.
    
    Args:
        collection: Коллекция (список, кортеж, словарь или строка)
        index: Индекс (для списков/кортежей/строк) или ключ (для словарей)
        default: Значение по умолчанию, если элемент не найден
        
    Returns:
        Элемент коллекции или значение по умолчанию
        
    Raises:
        SafeUtilityError: If collection is None or unsupported type
        
    Examples:
        >>> safe_get([1, 2, 3], 1)
        2
        >>> safe_get([1, 2, 3], 10, "не найдено")
        'не найдено'
        >>> safe_get({"name": "Иван"}, "name")
        'Иван'
        >>> safe_get({"name": "Иван"}, "age", 0)
        0
    """
    from ..errors.exceptions import SafeUtilityError
    
    if collection is None:
        raise SafeUtilityError("Коллекция не может быть None. Передайте список, кортеж, словарь или строку.", 
                             utility_name="safe_get")
    
    # Для словарей используем get()
    if isinstance(collection, dict):
        return collection.get(index, default)
    
    # Для списков, кортежей и строк проверяем индекс
    if isinstance(collection, (list, tuple, str)):
        if not isinstance(index, int):
            raise SafeUtilityError(f"Для {type(collection).__name__} индекс должен быть числом, получен {type(index).__name__}", 
                                 utility_name="safe_get")
        
        if 0 <= index < len(collection):
            return collection[index]
        else:
            return default
    
    # Неподдерживаемый тип коллекции
    raise SafeUtilityError(f"Неподдерживаемый тип коллекции: {type(collection).__name__}. "
                         f"Поддерживаются: list, tuple, dict, str", 
                         utility_name="safe_get")


def safe_divide(a: Union[int, float], b: Union[int, float], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely divide two numbers with zero division handling.
    
    Предотвращает ошибку ZeroDivisionError, возвращая значение по умолчанию
    при делении на ноль.
    
    Args:
        a: Делимое (число)
        b: Делитель (число)
        default: Значение по умолчанию при делении на ноль
        
    Returns:
        Результат деления или значение по умолчанию
        
    Raises:
        SafeUtilityError: If arguments are not numbers
        
    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0
        >>> safe_divide(10, 0, -1)
        -1
    """
    from ..errors.exceptions import SafeUtilityError
    import math
    
    # Проверяем типы входных данных
    if not isinstance(a, (int, float)):
        raise SafeUtilityError(f"Делимое должно быть числом, получен {type(a).__name__}", 
                             utility_name="safe_divide")
    
    if not isinstance(b, (int, float)):
        raise SafeUtilityError(f"Делитель должен быть числом, получен {type(b).__name__}", 
                             utility_name="safe_divide")
    
    if not isinstance(default, (int, float)):
        raise SafeUtilityError(f"Значение по умолчанию должно быть числом, получен {type(default).__name__}", 
                             utility_name="safe_divide")
    
    # Проверяем деление на ноль
    if b == 0:
        return default
    
    # Выполняем деление
    result = a / b
    
    # Проверяем на бесконечность или NaN
    if math.isinf(result) or math.isnan(result):
        return default
    
    return result


def safe_max(collection: Union[List, Tuple], default: Any = None) -> Any:
    """
    Safely find maximum value in a collection.
    
    Предотвращает ошибку ValueError при пустой коллекции.
    
    Args:
        collection: Коллекция чисел
        default: Значение по умолчанию для пустой коллекции
        
    Returns:
        Максимальное значение или значение по умолчанию
        
    Raises:
        SafeUtilityError: If collection is not a list or tuple, or elements are not comparable
        
    Examples:
        >>> safe_max([1, 5, 3])
        5
        >>> safe_max([])
        None
        >>> safe_max([], 0)
        0
    """
    from ..errors.exceptions import SafeUtilityError
    
    if not isinstance(collection, (list, tuple)):
        raise SafeUtilityError(f"Коллекция должна быть списком или кортежем, получен {type(collection).__name__}", 
                             utility_name="safe_max")
    
    if len(collection) == 0:
        return default
    
    try:
        return max(collection)
    except TypeError as e:
        raise SafeUtilityError(f"Не удалось найти максимум: {str(e)}. "
                             f"Убедитесь, что все элементы коллекции сравнимы.", 
                             utility_name="safe_max", original_error=e)


def safe_min(collection: Union[List, Tuple], default: Any = None) -> Any:
    """
    Safely find minimum value in a collection.
    
    Предотвращает ошибку ValueError при пустой коллекции.
    
    Args:
        collection: Коллекция чисел
        default: Значение по умолчанию для пустой коллекции
        
    Returns:
        Минимальное значение или значение по умолчанию
        
    Raises:
        SafeUtilityError: If collection is not a list or tuple, or elements are not comparable
        
    Examples:
        >>> safe_min([1, 5, 3])
        1
        >>> safe_min([])
        None
        >>> safe_min([], 0)
        0
    """
    from ..errors.exceptions import SafeUtilityError
    
    if not isinstance(collection, (list, tuple)):
        raise SafeUtilityError(f"Коллекция должна быть списком или кортежем, получен {type(collection).__name__}", 
                             utility_name="safe_min")
    
    if len(collection) == 0:
        return default
    
    try:
        return min(collection)
    except TypeError as e:
        raise SafeUtilityError(f"Не удалось найти минимум: {str(e)}. "
                             f"Убедитесь, что все элементы коллекции сравнимы.", 
                             utility_name="safe_min", original_error=e)


def safe_sum(collection: Union[List, Tuple], default: Union[int, float] = 0) -> Union[int, float]:
    """
    Safely calculate sum of a collection.
    
    Предотвращает ошибки при пустой коллекции или несовместимых типах.
    
    Args:
        collection: Коллекция чисел
        default: Значение по умолчанию для пустой коллекции
        
    Returns:
        Сумма элементов или значение по умолчанию
        
    Raises:
        SafeUtilityError: If collection is not a list or tuple, or elements are not numbers
        
    Examples:
        >>> safe_sum([1, 2, 3])
        6
        >>> safe_sum([])
        0
        >>> safe_sum([], 10)
        10
    """
    from ..errors.exceptions import SafeUtilityError
    
    if not isinstance(collection, (list, tuple)):
        raise SafeUtilityError(f"Коллекция должна быть списком или кортежем, получен {type(collection).__name__}", 
                             utility_name="safe_sum")
    
    if len(collection) == 0:
        return default
    
    try:
        return sum(collection)
    except TypeError as e:
        raise SafeUtilityError(f"Не удалось вычислить сумму: {str(e)}. "
                             f"Убедитесь, что все элементы коллекции являются числами.", 
                             utility_name="safe_sum", original_error=e)