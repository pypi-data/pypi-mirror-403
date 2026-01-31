# Fishertools

**Tools that make Python easier and safer for beginners**

Fishertools is a Python library designed specifically for beginner developers. It provides clear error explanations, safe utilities, learning tools, and powerful debugging features to help you master Python.

## 🚀 What's New in v0.4.1?

Three powerful new modules for data visualization, type validation, and step-by-step debugging:

- **📊 Visualization Module** - See your data structures clearly
- **✅ Validation Module** - Catch errors before they happen
- **🔍 Debug Module** - Understand your code execution

[See what's new →](docs/modules-v0.4.1.md)

## Quick Start

```bash
pip install fishertools
```

## Quick Reference

| Task | Function | Module |
|------|----------|--------|
| Explain an error | `explain_error(e)` | errors |
| Get element safely | `safe_get(list, index, default)` | safe |
| Divide safely | `safe_divide(a, b, default)` | safe |
| Read file safely | `safe_read_file(path)` | safe |
| Learn Python concepts | `explain(topic)` | learn |
| **Visualize data** | **`visualize(data)`** | **visualization** |
| **Validate types** | **`@validate_types`** | **validation** |
| **Debug step-by-step** | **`@debug_step_by_step`** | **debug** |

## Core Features

### 🔴 Error Explanation
Get clear explanations of Python errors with suggestions for fixing them.

```python
from fishertools import explain_error

try:
    result = 10 / 0
except Exception as e:
    explain_error(e)
```

### 🛡️ Safe Utilities
Functions like `safe_get()`, `safe_divide()`, `safe_read_file()` that prevent typical beginner errors.

```python
from fishertools import safe_get, safe_divide

# Safe dictionary access
value = safe_get(my_dict, "key", default="not found")

# Safe division
result = safe_divide(10, 0, default=0)  # Returns 0 instead of error
```

### 📚 Learning Tools
Structured explanations of Python concepts with examples and best practices.

```python
from fishertools.learn import generate_example, show_best_practice

example = generate_example("list comprehension")
best_practice = show_best_practice("error handling")
```

### 🎯 Ready-made Patterns
Templates for common tasks like menus, file storage, logging, and CLI applications.

### 📊 Data Visualization (v0.4.1+)
Visualize data structures in a human-readable format with proper formatting and indentation.

```python
from fishertools.visualization import visualize

# Visualize lists
numbers = [10, 20, 30, 40, 50]
visualize(numbers)
# Output:
# 📊 Visualization:
# [0] → 10
# [1] → 20
# [2] → 30
# [3] → 40
# [4] → 50

# Visualize dictionaries
user = {"name": "Alice", "age": 25, "email": "alice@example.com"}
visualize(user, title="User Data")
# Output:
# 📊 User Data:
# {
#   'name' → 'Alice'
#   'age' → 25
#   'email' → 'alice@example.com'
# }

# Visualize nested structures
data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
visualize(data, max_depth=3)
```

**Features:**
- List visualization with indices
- Dictionary visualization with keys
- Nested structure support with depth control
- Item limiting for large datasets
- Clean formatting with arrows and indentation

### ✅ Type Validation (v0.4.1+)
Validate function arguments and data structures with clear error messages.

```python
from fishertools.validation import validate_types, validate_email, ValidationError

# Type checking via decorator
@validate_types
def create_user(name: str, age: int, email: str) -> dict:
    return {"name": name, "age": age, "email": email}

user = create_user("Alice", 25, "alice@example.com")  # ✅ Works
# create_user("Bob", "thirty", "bob@example.com")     # ❌ ValidationError

# Email validation
try:
    validate_email("user@example.com")  # ✅ Valid
except ValidationError as e:
    print(f"Error: {e}")

# Number validation
from fishertools.validation import validate_number
validate_number(42, min_val=0, max_val=100)  # ✅ Valid

# Structure validation
from fishertools.validation import validate_structure
schema = {"name": str, "age": int}
data = {"name": "Alice", "age": 25}
validate_structure(data, schema)  # ✅ Valid
```

**Features:**
- Type checking via `@validate_types` decorator
- Email and URL validation
- Number range validation
- String validation with length and pattern checks
- Data structure validation against schemas
- Clear, actionable error messages

### 🔍 Step-by-Step Debugging (v0.4.1+)
Debug functions with step-by-step execution and function call tracing.

```python
from fishertools.debug import debug_step_by_step, trace, set_breakpoint

# Step-by-step debugging
@debug_step_by_step
def calculate_average(numbers):
    total = sum(numbers)
    average = total / len(numbers)
    return average

result = calculate_average([1, 2, 3, 4, 5])
# Output:
# 🔍 Debugging: calculate_average
# Step 1: numbers = [1, 2, 3, 4, 5]
# Step 2: return 3.0
# ✅ Result: 3.0

# Function call tracing
@trace
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(4)
# Shows all function calls with indentation

# Breakpoints
x = 10
set_breakpoint("Check x value")
y = x * 2
# 🔴 Breakpoint: Check x value
#    at script.py:2
```

**Features:**
- Step-by-step execution with variable values
- Function call tracing with indentation
- Breakpoints for pausing execution
- Exception handling with detailed information
- Recursive function support

## 📖 Documentation

Complete documentation is available in the `docs/` folder:

- **[Getting Started](docs/getting-started.md)** - Quick start guide with installation and first example
- **[Features](docs/features.md)** - Overview of all features and capabilities
- **[Installation](docs/installation.md)** - Detailed installation instructions for different operating systems
- **[API Reference](docs/api-reference.md)** - Complete API documentation with all functions and classes
- **[v0.4.1 Modules](docs/modules-v0.4.1.md)** - Detailed documentation for new Visualization, Validation, and Debug modules
- **[Examples](docs/examples.md)** - Practical examples from basic to advanced usage
- **[Limitations](docs/limitations.md)** - Known limitations and performance considerations
- **[Contributing](docs/contributing.md)** - How to contribute to the project

## 🎯 Who Should Use Fishertools?

- **Beginners** - Just starting to learn Python
- **Students** - Learning Python in a classroom
- **Educators** - Teaching Python to others
- **Professionals** - Want safer, more readable code

## 🔄 Integration Examples

### Visualization + Validation

```python
from fishertools.validation import validate_types
from fishertools.visualization import visualize

@validate_types
def process_users(users: list) -> dict:
    visualize(users, title="Input Users")
    result = {"count": len(users), "users": users}
    visualize(result, title="Output")
    return result

users = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
result = process_users(users)
```

### Validation + Debug

```python
from fishertools.validation import validate_types
from fishertools.debug import debug_step_by_step

@validate_types
@debug_step_by_step
def calculate_total(prices: list) -> float:
    total = sum(prices)
    tax = total * 0.1
    final = total + tax
    return final

result = calculate_total([10.0, 20.0, 30.0])
```

### All Three Modules

```python
from fishertools.validation import validate_types, validate_structure
from fishertools.visualization import visualize
from fishertools.debug import debug_step_by_step

@validate_types
@debug_step_by_step
def analyze_data(data: dict) -> dict:
    schema = {"name": str, "values": list}
    validate_structure(data, schema)
    
    visualize(data, title="Input")
    
    result = {
        "name": data["name"],
        "count": len(data["values"]),
        "sum": sum(data["values"])
    }
    
    visualize(result, title="Output")
    return result

data = {"name": "Test", "values": [1, 2, 3, 4, 5]}
result = analyze_data(data)
```

## 📊 Version History

### v0.4.1 (Current)
- ✨ **NEW:** Visualization module for data structure visualization
- ✨ **NEW:** Validation module for type checking and data validation
- ✨ **NEW:** Debug module for step-by-step execution and tracing
- 📈 65+ new tests with 90%+ code coverage
- 📚 Complete documentation for all new modules

### v0.4.0
- 🎓 Knowledge Engine Interactive REPL
- 📚 Extended documentation system

### v0.3.x
- 🛡️ Safe utilities module
- 📚 Learning tools
- 🔴 Error explanation system

## 🧪 Testing

All modules are thoroughly tested:

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_visualization/ -v
pytest tests/test_validation/ -v
pytest tests/test_debug/ -v

# Run with coverage
pytest tests/ --cov=fishertools --cov-report=html
```

**Test Coverage:** 90%+ across all modules

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install fishertools
```

### From Source

```bash
git clone https://github.com/f1sherFM/My_1st_library_python.git
cd My_1st_library_python
pip install -e .
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- How to report bugs
- How to suggest features
- How to submit pull requests
- Code style guidelines

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Fishertools is built with ❤️ for the Python community, especially for beginners learning to code.

---

**Fishertools** - Making Python easier, safer, and more fun for everyone! 🐍✨

**Current Version:** 0.4.1 | **Last Updated:** January 29, 2026
