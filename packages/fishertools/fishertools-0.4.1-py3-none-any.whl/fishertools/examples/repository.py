"""
Repository for managing code examples and learning scenarios.
"""

from typing import List, Optional, Dict
from .models import (
    CodeExample, Scenario, ProjectTemplate, LineByLineExplanation,
    ExampleCategory, ProjectType
)


class ExampleRepository:
    """
    Manages collections of examples and scenarios for Python beginners.
    
    Provides categorized examples with step-by-step explanations
    and simple project templates.
    """
    
    def __init__(self, examples_dir: Optional[str] = None):
        """
        Initialize the example repository.
        
        Args:
            examples_dir: Optional directory containing example files
        """
        self.examples_dir = examples_dir
        self._examples: Dict[str, CodeExample] = {}
        self._scenarios: Dict[str, Scenario] = {}
        self._projects: Dict[str, ProjectTemplate] = {}
        self._initialize_default_examples()
        self._initialize_default_scenarios()
        self._initialize_default_projects()
    
    def get_examples_by_topic(self, topic: str) -> List[CodeExample]:
        """
        Get all examples for a specific topic.
        
        Args:
            topic: Topic name (e.g., "lists", "dictionaries", "functions")
            
        Returns:
            List[CodeExample]: Examples matching the topic
        """
        return [
            example for example in self._examples.values()
            if topic.lower() in [t.lower() for t in example.topics]
        ]
    
    def get_examples_by_category(self, category: ExampleCategory) -> List[CodeExample]:
        """
        Get all examples in a specific category.
        
        Args:
            category: Example category
            
        Returns:
            List[CodeExample]: Examples in the category
        """
        return [
            example for example in self._examples.values()
            if example.category == category
        ]
    
    def get_beginner_scenarios(self) -> List[Scenario]:
        """
        Get all scenarios suitable for beginners.
        
        Returns:
            List[Scenario]: Beginner-friendly scenarios
        """
        return [
            scenario for scenario in self._scenarios.values()
            if scenario.difficulty == "beginner"
        ]
    
    def create_simple_project(self, project_type: ProjectType) -> ProjectTemplate:
        """
        Create a simple project template with step-by-step instructions.
        
        Args:
            project_type: Type of project to create
            
        Returns:
            ProjectTemplate: Project template with instructions
        """
        project_id = f"{project_type.value}_project"
        if project_id in self._projects:
            return self._projects[project_id]
        
        # If project doesn't exist, create a basic template
        from .models import ProjectStep
        
        basic_step = ProjectStep(
            step_number=1,
            title=f"Create {project_type.value}",
            description=f"Basic {project_type.value} implementation",
            code_snippet="# Add your code here",
            explanation="This is a placeholder project template"
        )
        
        return ProjectTemplate(
            id=project_id,
            title=f"Simple {project_type.value.replace('_', ' ').title()}",
            description=f"A beginner-friendly {project_type.value} project",
            project_type=project_type,
            difficulty="beginner",
            estimated_time=30,
            steps=[basic_step],
            final_code="# Complete implementation"
        )
    
    def explain_example_line_by_line(self, example: CodeExample) -> LineByLineExplanation:
        """
        Generate line-by-line explanation for a code example.
        
        Args:
            example: Code example to explain
            
        Returns:
            LineByLineExplanation: Detailed line-by-line explanation
        """
        from .models import LineExplanation
        
        lines = example.code.strip().split('\n')
        line_explanations = []
        key_concepts = set()
        
        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines and comments (but still include them)
            if not stripped_line or stripped_line.startswith('#'):
                if stripped_line.startswith('#'):
                    explanation = "This is a comment that explains the code"
                    concepts = ["comments"]
                else:
                    explanation = "Empty line for readability"
                    concepts = []
            else:
                explanation, concepts = self._analyze_code_line(stripped_line)
            
            line_explanations.append(LineExplanation(
                line_number=i,
                code=line,
                explanation=explanation,
                concepts=concepts
            ))
            
            key_concepts.update(concepts)
        
        # Generate summary based on key concepts
        summary = self._generate_explanation_summary(example, list(key_concepts))
        
        return LineByLineExplanation(
            example_id=example.id,
            title=f"Line-by-line: {example.title}",
            lines=line_explanations,
            summary=summary,
            key_concepts=list(key_concepts)
        )
    
    def _analyze_code_line(self, line: str) -> tuple[str, List[str]]:
        """
        Analyze a single line of code and generate explanation.
        
        Args:
            line: Code line to analyze
            
        Returns:
            tuple: (explanation, concepts)
        """
        concepts = []
        
        # Variable assignment
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            if line.count('=') == 1 and '=' not in line.replace('=', ''):
                concepts.append("variable assignment")
                var_name = line.split('=')[0].strip()
                if '[' in line and ']' in line:
                    concepts.append("lists")
                    if line.count('[') == 1 and line.count(']') == 1 and not line.endswith(']'):
                        # This is indexing, not list creation
                        concepts.extend(["indexing", "list access"])
                        explanation = f"Accesses an element from a list using indexing and assigns it to '{var_name}'"
                    else:
                        explanation = f"Creates a list and assigns it to variable '{var_name}'"
                elif '{' in line and '}' in line:
                    concepts.append("dictionaries")
                    explanation = f"Creates a dictionary and assigns it to variable '{var_name}'"
                elif 'input(' in line:
                    concepts.append("user input")
                    explanation = f"Gets input from user and stores it in variable '{var_name}'"
                elif '(' in line and ')' in line:
                    concepts.append("function calls")
                    explanation = f"Calls a function and assigns the result to '{var_name}'"
                else:
                    explanation = f"Assigns a value to variable '{var_name}'"
        
        # Function definitions
        elif line.startswith('def '):
            concepts.extend(["functions", "function definition"])
            func_name = line.split('(')[0].replace('def ', '').strip()
            explanation = f"Defines a function named '{func_name}'"
        
        # Function calls
        elif '(' in line and ')' in line and not line.startswith('def'):
            concepts.append("function calls")
            if 'print(' in line:
                concepts.append("output")
                explanation = "Prints output to the console"
            elif 'input(' in line:
                concepts.append("user input")
                explanation = "Gets input from the user"
            elif '.append(' in line:
                concepts.extend(["lists", "list methods"])
                explanation = "Adds an item to the end of a list"
            elif '.extend(' in line:
                concepts.extend(["lists", "list methods"])
                explanation = "Adds multiple items to the end of a list"
            elif '.get(' in line:
                concepts.extend(["dictionaries", "dict methods"])
                explanation = "Safely gets a value from a dictionary"
            elif 'int(' in line or 'float(' in line or 'str(' in line:
                concepts.append("type conversion")
                explanation = "Converts a value to a different data type"
            else:
                explanation = "Calls a function to perform an operation"
        
        # Control structures
        elif line.startswith('if '):
            concepts.extend(["conditionals", "if statements"])
            explanation = "Checks a condition and executes code if it's true"
        elif line.startswith('elif '):
            concepts.extend(["conditionals", "elif statements"])
            explanation = "Checks an alternative condition"
        elif line.startswith('else:'):
            concepts.extend(["conditionals", "else statements"])
            explanation = "Executes when no previous conditions were true"
        elif line.startswith('while '):
            concepts.extend(["loops", "while loops"])
            explanation = "Repeats code while a condition is true"
        elif line.startswith('for '):
            concepts.extend(["loops", "for loops"])
            explanation = "Repeats code for each item in a sequence"
        
        # Exception handling
        elif line.startswith('try:'):
            concepts.extend(["error handling", "try-except"])
            explanation = "Starts a block that might cause an error"
        elif line.startswith('except'):
            concepts.extend(["error handling", "try-except"])
            explanation = "Handles errors that occur in the try block"
        
        # Return statements
        elif line.startswith('return '):
            concepts.extend(["functions", "return statements"])
            explanation = "Returns a value from the function"
        
        # Import statements
        elif line.startswith('import ') or line.startswith('from '):
            concepts.append("imports")
            explanation = "Imports code from another module"
        
        # Default case
        else:
            explanation = "Executes a Python statement"
        
        return explanation, concepts
    
    def _generate_explanation_summary(self, example: CodeExample, key_concepts: List[str]) -> str:
        """
        Generate a summary of the code explanation.
        
        Args:
            example: The code example
            key_concepts: List of key concepts found in the code
            
        Returns:
            str: Summary explanation
        """
        concept_descriptions = {
            "variable assignment": "storing values in variables",
            "lists": "working with ordered collections",
            "dictionaries": "using key-value data structures",
            "functions": "defining and calling reusable code blocks",
            "conditionals": "making decisions with if/else statements",
            "loops": "repeating code execution",
            "user input": "getting data from users",
            "error handling": "managing potential errors gracefully",
            "output": "displaying results to users"
        }
        
        if not key_concepts:
            return f"This example demonstrates basic Python syntax: {example.description}"
        
        # Get descriptions for found concepts
        found_descriptions = []
        for concept in key_concepts:
            if concept in concept_descriptions:
                found_descriptions.append(concept_descriptions[concept])
        
        if found_descriptions:
            concepts_text = ", ".join(found_descriptions[:-1])
            if len(found_descriptions) > 1:
                concepts_text += f", and {found_descriptions[-1]}"
            else:
                concepts_text = found_descriptions[0]
            
            return f"This example demonstrates {concepts_text}. {example.description}"
        else:
            return f"This example shows various Python programming concepts. {example.description}"
    
    def break_down_complex_concept(self, concept: str, context: str = "") -> List[str]:
        """
        Break down complex programming concepts into simple steps.
        
        Args:
            concept: The complex concept to break down
            context: Additional context about how the concept is used
            
        Returns:
            List[str]: List of simple explanation steps
        """
        concept_breakdowns = {
            "list comprehension": [
                "List comprehension is a concise way to create lists",
                "It follows the pattern: [expression for item in iterable]",
                "The expression is applied to each item in the iterable",
                "The results are collected into a new list",
                "It's equivalent to using a for loop but more compact"
            ],
            
            "dictionary comprehension": [
                "Dictionary comprehension creates dictionaries in one line",
                "It follows the pattern: {key: value for item in iterable}",
                "Each item in the iterable generates a key-value pair",
                "The result is a new dictionary with all the pairs",
                "It's more efficient than using loops to build dictionaries"
            ],
            
            "exception handling": [
                "Exception handling prevents programs from crashing",
                "Use 'try:' to mark code that might cause an error",
                "Use 'except:' to specify what to do if an error occurs",
                "The program continues running after handling the error",
                "Always handle specific exceptions when possible"
            ],
            
            "function parameters": [
                "Functions can accept input values called parameters",
                "Parameters are defined in parentheses after the function name",
                "When calling the function, you provide arguments for each parameter",
                "The function uses these values to perform its task",
                "Parameters make functions flexible and reusable"
            ],
            
            "loops with conditions": [
                "Loops can include conditions to control execution",
                "Use 'if' statements inside loops to check conditions",
                "Use 'continue' to skip the rest of the current iteration",
                "Use 'break' to exit the loop completely",
                "This allows for more complex loop behavior"
            ],
            
            "nested data structures": [
                "Data structures can contain other data structures",
                "Lists can contain other lists (nested lists)",
                "Dictionaries can contain lists or other dictionaries",
                "Access nested elements using multiple brackets or keys",
                "This allows for organizing complex data hierarchically"
            ]
        }
        
        # Return breakdown if available, otherwise create a generic one
        if concept.lower() in concept_breakdowns:
            return concept_breakdowns[concept.lower()]
        
        # Generic breakdown for unknown concepts
        return [
            f"The concept '{concept}' is an important programming idea",
            f"It helps solve specific problems in your code",
            f"Understanding {concept} will make you a better programmer",
            f"Practice using {concept} in different situations",
            f"Look for examples of {concept} in real code"
        ]
    
    def get_concept_prerequisites(self, concept: str) -> List[str]:
        """
        Get the prerequisites needed to understand a concept.
        
        Args:
            concept: The concept to check prerequisites for
            
        Returns:
            List[str]: List of prerequisite concepts
        """
        prerequisites_map = {
            "list comprehension": ["lists", "for loops", "expressions"],
            "dictionary comprehension": ["dictionaries", "for loops", "key-value pairs"],
            "exception handling": ["functions", "conditionals"],
            "nested loops": ["for loops", "while loops", "indentation"],
            "function parameters": ["functions", "variables"],
            "lambda functions": ["functions", "expressions"],
            "file operations": ["strings", "exception handling"],
            "class methods": ["classes", "functions", "self parameter"]
        }
        
        return prerequisites_map.get(concept.lower(), [])
    
    def add_example(self, example: CodeExample) -> None:
        """
        Add a new example to the repository.
        
        Args:
            example: Code example to add
        """
        self._examples[example.id] = example
    
    def search_examples(self, query: str, category: Optional[ExampleCategory] = None) -> List[CodeExample]:
        """
        Search for examples matching a query.
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List[CodeExample]: Matching examples
        """
        query_lower = query.lower()
        results = []
        
        for example in self._examples.values():
            # Filter by category if specified
            if category and example.category != category:
                continue
                
            # Search in title, description, topics, and code
            if (query_lower in example.title.lower() or
                query_lower in example.description.lower() or
                any(query_lower in topic.lower() for topic in example.topics) or
                query_lower in example.code.lower() or
                # Handle plural/singular variations
                (query_lower.endswith('s') and query_lower[:-1] in example.title.lower()) or
                (query_lower.endswith('s') and any(query_lower[:-1] in topic.lower() for topic in example.topics)) or
                (not query_lower.endswith('s') and (query_lower + 's') in example.title.lower()) or
                (not query_lower.endswith('s') and any((query_lower + 's') in topic.lower() for topic in example.topics))):
                results.append(example)
        
        return results
    
    def _initialize_default_examples(self) -> None:
        """Initialize repository with default examples for beginners."""
        from .models import ProjectStep
        
        # List examples
        list_examples = [
            CodeExample(
                id="list_basics",
                title="Working with Lists - Basics",
                description="Learn how to create, access, and modify lists",
                code="""# Creating lists
fruits = ['apple', 'banana', 'orange']
numbers = [1, 2, 3, 4, 5]

# Accessing elements
first_fruit = fruits[0]  # 'apple'
last_number = numbers[-1]  # 5

# Adding elements
fruits.append('grape')
numbers.extend([6, 7])

# Modifying elements
fruits[1] = 'blueberry'

print(f"Fruits: {fruits}")
print(f"Numbers: {numbers}")""",
                explanation="Lists are ordered collections that can store multiple items. You can access items by index, add new items, and modify existing ones.",
                difficulty="beginner",
                topics=["lists", "indexing", "append", "extend"],
                prerequisites=[],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Fruits: ['apple', 'blueberry', 'orange', 'grape']\nNumbers: [1, 2, 3, 4, 5, 6, 7]",
                common_mistakes=["Using 1-based indexing instead of 0-based", "Forgetting that negative indices count from the end"]
            ),
            
            CodeExample(
                id="list_operations",
                title="List Operations and Methods",
                description="Common list operations like sorting, searching, and removing items",
                code="""# Sample list
numbers = [3, 1, 4, 1, 5, 9, 2, 6]

# Sorting
sorted_numbers = sorted(numbers)  # Creates new list
numbers.sort()  # Modifies original list

# Searching
if 5 in numbers:
    position = numbers.index(5)
    print(f"Found 5 at position {position}")

# Removing items
numbers.remove(1)  # Removes first occurrence
last_item = numbers.pop()  # Removes and returns last item

# List comprehension
squares = [x**2 for x in range(1, 6)]

print(f"Sorted: {sorted_numbers}")
print(f"Modified: {numbers}")
print(f"Squares: {squares}")""",
                explanation="Lists have many built-in methods for common operations. Understanding the difference between methods that modify the list and those that return new lists is important.",
                difficulty="beginner",
                topics=["lists", "sorting", "searching", "list comprehension"],
                prerequisites=["list_basics"],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Found 5 at position 4\nSorted: [1, 1, 2, 3, 4, 5, 6, 9]\nModified: [1, 2, 3, 4, 5, 9]\nSquares: [1, 4, 9, 16, 25]",
                common_mistakes=["Confusing sort() and sorted()", "Using remove() when item might not exist"]
            )
        ]
        
        # Dictionary examples
        dict_examples = [
            CodeExample(
                id="dict_basics",
                title="Working with Dictionaries - Basics",
                description="Learn how to create, access, and modify dictionaries",
                code="""# Creating dictionaries
student = {
    'name': 'Alice',
    'age': 20,
    'grade': 'A',
    'courses': ['Math', 'Physics']
}

# Accessing values
name = student['name']
age = student.get('age', 0)  # Safe access with default

# Adding/modifying values
student['email'] = 'alice@example.com'
student['age'] = 21

# Checking if key exists
if 'grade' in student:
    print(f"{name} has grade: {student['grade']}")

# Getting all keys, values, items
print(f"Keys: {list(student.keys())}")
print(f"Values: {list(student.values())}")""",
                explanation="Dictionaries store key-value pairs and provide fast lookup by key. Use get() for safe access to avoid KeyError.",
                difficulty="beginner",
                topics=["dictionaries", "dictionary", "key-value pairs", "get method"],
                prerequisites=[],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Alice has grade: A\nKeys: ['name', 'age', 'grade', 'courses', 'email']\nValues: ['Alice', 21, 'A', ['Math', 'Physics'], 'alice@example.com']",
                common_mistakes=["Using [] instead of get() for optional keys", "Trying to access non-existent keys"]
            )
        ]
        
        # User input examples
        input_examples = [
            CodeExample(
                id="safe_input_basics",
                title="Safe User Input - Basics",
                description="Learn how to safely get and validate user input",
                code="""# Getting basic input
name = input("Enter your name: ").strip()

# Getting and validating numeric input
while True:
    try:
        age = int(input("Enter your age: "))
        if age < 0:
            print("Age cannot be negative. Please try again.")
            continue
        break
    except ValueError:
        print("Please enter a valid number.")

# Getting yes/no input
while True:
    choice = input("Do you want to continue? (y/n): ").lower().strip()
    if choice in ['y', 'yes']:
        print("Continuing...")
        break
    elif choice in ['n', 'no']:
        print("Stopping...")
        break
    else:
        print("Please enter 'y' or 'n'.")

print(f"Hello {name}, you are {age} years old.")""",
                explanation="Always validate user input to prevent errors. Use try-except for type conversion and loops for validation.",
                difficulty="beginner",
                topics=["input", "validation", "try-except", "loops"],
                prerequisites=[],
                category=ExampleCategory.USER_INPUT,
                expected_output="# Output depends on user input",
                common_mistakes=["Not validating input", "Not handling ValueError", "Not stripping whitespace"]
            )
        ]
        
        # Add all examples to repository
        for example in list_examples + dict_examples + input_examples:
            self._examples[example.id] = example
    
    def _initialize_default_scenarios(self) -> None:
        """Initialize repository with default learning scenarios."""
        # Collections scenario
        collections_scenario = Scenario(
            id="collections_basics",
            title="Python Collections Fundamentals",
            description="Learn the basics of working with lists and dictionaries",
            examples=[self._examples["list_basics"], self._examples["dict_basics"]],
            learning_objectives=[
                "Understand how to create and use lists",
                "Learn dictionary key-value operations",
                "Practice safe data access patterns"
            ],
            difficulty="beginner",
            estimated_time=45
        )
        
        self._scenarios[collections_scenario.id] = collections_scenario
    
    def _initialize_default_projects(self) -> None:
        """Initialize repository with default project templates."""
        from .models import ProjectStep
        
        # Calculator project
        calculator_steps = [
            ProjectStep(
                step_number=1,
                title="Create basic calculator functions",
                description="Define functions for basic arithmetic operations",
                code_snippet="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b""",
                explanation="Start by creating simple functions for each operation. Notice the error handling for division by zero.",
                hints=["Remember to handle division by zero", "Keep functions simple and focused"]
            ),
            
            ProjectStep(
                step_number=2,
                title="Create the main calculator loop",
                description="Build the user interface and input handling",
                code_snippet="""def calculator():
    print("Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            # Get first number
            first = input("Enter first number (or 'quit'): ")
            if first.lower() == 'quit':
                break
            first = float(first)
            
            # Get operation
            operation = input("Enter operation (+, -, *, /): ")
            if operation not in ['+', '-', '*', '/']:
                print("Invalid operation!")
                continue
            
            # Get second number
            second = float(input("Enter second number: "))
            
            # Calculate result
            if operation == '+':
                result = add(first, second)
            elif operation == '-':
                result = subtract(first, second)
            elif operation == '*':
                result = multiply(first, second)
            elif operation == '/':
                result = divide(first, second)
            
            print(f"Result: {result}")
            
        except ValueError:
            print("Please enter valid numbers!")

# Run the calculator
calculator()""",
                explanation="The main loop handles user input, validates operations, and calls the appropriate function.",
                hints=["Use try-except for input validation", "Provide clear error messages", "Allow users to exit gracefully"]
            )
        ]
        
        calculator_project = ProjectTemplate(
            id="calculator_project",
            title="Simple Calculator",
            description="Build a basic calculator that performs arithmetic operations",
            project_type=ProjectType.CALCULATOR,
            difficulty="beginner",
            estimated_time=60,
            steps=calculator_steps,
            final_code="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

def calculator():
    print("Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            first = input("Enter first number (or 'quit'): ")
            if first.lower() == 'quit':
                break
            first = float(first)
            
            operation = input("Enter operation (+, -, *, /): ")
            if operation not in ['+', '-', '*', '/']:
                print("Invalid operation!")
                continue
            
            second = float(input("Enter second number: "))
            
            if operation == '+':
                result = add(first, second)
            elif operation == '-':
                result = subtract(first, second)
            elif operation == '*':
                result = multiply(first, second)
            elif operation == '/':
                result = divide(first, second)
            
            print(f"Result: {result}")
            
        except ValueError:
            print("Please enter valid numbers!")

if __name__ == "__main__":
    calculator()""",
            extensions=[
                "Add more operations (power, square root, etc.)",
                "Add memory functions (store/recall)",
                "Create a GUI version using tkinter",
                "Add calculation history"
            ]
        )
        
        self._projects[calculator_project.id] = calculator_project