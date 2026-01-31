"""
Safe input collection module for fishertools.

This module provides validated input collection functions with automatic type checking
and range validation. It helps beginners collect user input safely without writing
repetitive validation code.

Functions:
    ask_int() - Prompt user for an integer with optional range validation
    ask_float() - Prompt user for a float with optional range validation
    ask_str() - Prompt user for a string with optional length validation
    ask_choice() - Prompt user to choose from a list of options
"""

from typing import List, Optional, Any


def ask_int(prompt: str, min: Optional[int] = None, max: Optional[int] = None) -> int:
    """
    Prompt user for an integer with optional range validation.
    
    Args:
        prompt: The prompt to display to the user
        min: Minimum allowed value (inclusive), optional
        max: Maximum allowed value (inclusive), optional
        
    Returns:
        Validated integer from user input
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        
    Example:
        >>> age = ask_int("How old are you? ", min=0, max=150)
        >>> score = ask_int("Enter your score: ")
    """
    while True:
        try:
            user_input = input(prompt)
            value = int(user_input)
            
            # Check min constraint
            if min is not None and value < min:
                print(f"Error: Value must be at least {min}")
                continue
            
            # Check max constraint
            if max is not None and value > max:
                print(f"Error: Value must be at most {max}")
                continue
            
            return value
        except ValueError:
            print(f"Error: Please enter a valid integer")
        except EOFError:
            raise


def ask_float(prompt: str, min: Optional[float] = None, max: Optional[float] = None) -> float:
    """
    Prompt user for a float with optional range validation.
    
    Args:
        prompt: The prompt to display to the user
        min: Minimum allowed value (inclusive), optional
        max: Maximum allowed value (inclusive), optional
        
    Returns:
        Validated float from user input
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        
    Example:
        >>> temperature = ask_float("Enter temperature (C): ", min=-273.15)
        >>> price = ask_float("Enter price: ", min=0)
    """
    while True:
        try:
            user_input = input(prompt)
            value = float(user_input)
            
            # Check min constraint
            if min is not None and value < min:
                print(f"Error: Value must be at least {min}")
                continue
            
            # Check max constraint
            if max is not None and value > max:
                print(f"Error: Value must be at most {max}")
                continue
            
            return value
        except ValueError:
            print(f"Error: Please enter a valid number")
        except EOFError:
            raise


def ask_str(prompt: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> str:
    """
    Prompt user for a string with optional length validation.
    
    Args:
        prompt: The prompt to display to the user
        min_length: Minimum string length, optional
        max_length: Maximum string length, optional
        
    Returns:
        Validated string from user input (whitespace stripped)
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        
    Example:
        >>> name = ask_str("Enter your name: ", min_length=1, max_length=50)
        >>> password = ask_str("Enter password: ", min_length=8)
    """
    while True:
        try:
            user_input = input(prompt)
            value = user_input.strip()
            
            # Check min_length constraint
            if min_length is not None and len(value) < min_length:
                print(f"Error: String must be at least {min_length} characters long")
                continue
            
            # Check max_length constraint
            if max_length is not None and len(value) > max_length:
                print(f"Error: String must be at most {max_length} characters long")
                continue
            
            return value
        except EOFError:
            raise


def ask_choice(prompt: str, options: List[str]) -> str:
    """
    Prompt user to choose from a list of options.
    
    Args:
        prompt: The prompt to display to the user
        options: List of available choices
        
    Returns:
        The selected option (exact string from options list)
        
    Raises:
        EOFError: If user provides EOF (Ctrl+D)
        ValueError: If options list is empty
        
    Example:
        >>> color = ask_choice("Choose a color: ", ["red", "green", "blue"])
        >>> choice = ask_choice("Select: ", ["Yes", "No", "Maybe"])
    """
    if not options:
        raise ValueError("Options list cannot be empty")
    
    while True:
        try:
            # Display options
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            
            user_input = input(prompt).strip()
            
            # Try numeric selection first
            try:
                choice_index = int(user_input) - 1
                if 0 <= choice_index < len(options):
                    return options[choice_index]
                else:
                    print(f"Error: Please enter a number between 1 and {len(options)}")
                    continue
            except ValueError:
                # Try direct text matching
                if user_input in options:
                    return user_input
                else:
                    print(f"Error: '{user_input}' is not a valid option")
                    continue
        except EOFError:
            raise
