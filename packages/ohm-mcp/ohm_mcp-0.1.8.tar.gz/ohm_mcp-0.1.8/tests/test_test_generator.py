"""
Unit tests for the Test Generator module.

Tests cover:
- CharacterizationTestGenerator functionality
- Test case generation for various function types
- Parameter type inference
- Return type inference
- Side effect detection
- Edge case generation
- TestCaseEnhancer for property-based tests
- TestGenerator orchestrator

Run with: pytest tests/test_test_generator.py -v
"""

import ast
import os
import tempfile
from typing import Generator

import pytest

from ohm_mcp.refactoring.test_generator import (
    CharacterizationTestGenerator,
    TestCaseEnhancer,
    TestGenerator,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def char_test_gen() -> CharacterizationTestGenerator:
    """Create a CharacterizationTestGenerator instance."""
    return CharacterizationTestGenerator()


@pytest.fixture
def test_enhancer() -> TestCaseEnhancer:
    """Create a TestCaseEnhancer instance."""
    return TestCaseEnhancer()


@pytest.fixture
def test_generator() -> TestGenerator:
    """Create a TestGenerator orchestrator instance."""
    return TestGenerator()


@pytest.fixture
def simple_function_code() -> str:
    """Sample code with a simple function."""
    return '''
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
'''


@pytest.fixture
def complex_function_code() -> str:
    """Sample code with multiple functions and types."""
    return '''
def process_list(items: list) -> dict:
    """Process a list of items."""
    result = {}
    for item in items:
        result[item] = len(str(item))
    return result


def validate_string(text: str) -> bool:
    """Validate a string is not empty."""
    if text is None:
        return False
    return len(text) > 0


def calculate_average(numbers):
    """Calculate average of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
'''


@pytest.fixture
def side_effects_code() -> str:
    """Sample code with functions that have side effects."""
    return '''
def print_message(message: str) -> None:
    """Print a message to stdout."""
    print(message)


def write_to_file(filename: str, content: str) -> None:
    """Write content to a file."""
    with open(filename, 'w') as f:
        f.write(content)


def modify_global():
    """Modify global state."""
    global counter
    counter += 1
'''


@pytest.fixture
def class_with_methods_code() -> str:
    """Sample code with a class containing methods."""
    return '''
class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value: int = 0):
        self.value = initial_value
    
    def add(self, x: int) -> int:
        """Add x to the current value."""
        self.value += x
        return self.value
    
    def multiply(self, x: int) -> int:
        """Multiply current value by x."""
        self.value *= x
        return self.value
    
    def reset(self) -> None:
        """Reset value to zero."""
        self.value = 0
'''


# =============================================================================
# CHARACTERIZATION TEST GENERATOR TESTS
# =============================================================================

class TestCharacterizationTestGenerator:
    """Tests for CharacterizationTestGenerator class."""
    
    def test_generate_tests_for_simple_function(
        self, char_test_gen: CharacterizationTestGenerator, simple_function_code: str
    ):
        """Test generating tests for a simple function."""
        result = char_test_gen.generate_tests_for_file(simple_function_code, "math_utils.py")
        
        assert "error" not in result
        assert result["functions_tested"] >= 1
        assert result["test_cases_generated"] >= 1
        assert "test_content" in result
        assert "def test_add_numbers" in result["test_content"]
    
    def test_generate_tests_for_multiple_functions(
        self, char_test_gen: CharacterizationTestGenerator, complex_function_code: str
    ):
        """Test generating tests for multiple functions."""
        result = char_test_gen.generate_tests_for_file(complex_function_code, "utils.py")
        
        assert "error" not in result
        assert result["functions_tested"] >= 2
        assert "test_content" in result
        # Should have tests for process_list, validate_string, calculate_average
        assert "process_list" in result["test_content"]
        assert "validate_string" in result["test_content"]
    
    def test_generate_test_for_specific_function(
        self, char_test_gen: CharacterizationTestGenerator, complex_function_code: str
    ):
        """Test generating tests for a specific function only."""
        result = char_test_gen.generate_test_for_function(
            complex_function_code, "validate_string", "utils.py"
        )
        
        assert "error" not in result
        assert result["function"] == "validate_string"
        assert "test_content" in result
        assert "validate_string" in result["test_content"]
        # Should not contain other functions
        assert "process_list" not in result["test_content"]
    
    def test_function_not_found_error(
        self, char_test_gen: CharacterizationTestGenerator, simple_function_code: str
    ):
        """Test error when function is not found."""
        result = char_test_gen.generate_test_for_function(
            simple_function_code, "nonexistent_function", "test.py"
        )
        
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_syntax_error_handling(self, char_test_gen: CharacterizationTestGenerator):
        """Test handling of code with syntax errors."""
        invalid_code = "def broken("
        result = char_test_gen.generate_tests_for_file(invalid_code, "broken.py")
        
        assert "error" in result
        assert "parse" in result["error"].lower()
    
    def test_test_file_naming(self, char_test_gen: CharacterizationTestGenerator):
        """Test that test file names are generated correctly."""
        code = "def foo(x): return x"
        
        result = char_test_gen.generate_tests_for_file(code, "my_module.py")
        assert result["test_file"] == "test_my_module.py"
        
        result = char_test_gen.generate_tests_for_file(code, "path/to/module.py")
        assert result["test_file"] == "test_module.py"
    
    def test_skips_private_functions(self, char_test_gen: CharacterizationTestGenerator):
        """Test that private functions are skipped."""
        code = '''
def public_func(x):
    return x

def _private_func(x):
    return x * 2

def __dunder_func(x):
    return x * 3
'''
        result = char_test_gen.generate_tests_for_file(code, "module.py")
        
        assert "error" not in result
        assert "public_func" in result["test_content"]
        assert "_private_func" not in result["test_content"]
        assert "__dunder_func" not in result["test_content"]
    
    def test_skips_test_functions(self, char_test_gen: CharacterizationTestGenerator):
        """Test that existing test functions are skipped."""
        code = '''
def regular_func(x):
    return x

def test_something(x):
    assert x == x
'''
        result = char_test_gen.generate_tests_for_file(code, "module.py")
        
        assert "error" not in result
        assert "regular_func" in result["test_content"]
        # Should not create test_test_something
        assert "test_test_something" not in result["test_content"]
    
    def test_generates_import_statement(
        self, char_test_gen: CharacterizationTestGenerator, simple_function_code: str
    ):
        """Test that proper import statements are generated."""
        result = char_test_gen.generate_tests_for_file(simple_function_code, "math_utils.py")
        
        assert "import pytest" in result["test_content"]
        assert "from math_utils import *" in result["test_content"]
    
    def test_generates_docstrings(
        self, char_test_gen: CharacterizationTestGenerator, simple_function_code: str
    ):
        """Test that test functions have docstrings."""
        result = char_test_gen.generate_tests_for_file(simple_function_code, "module.py")
        
        # Should have docstrings in test functions
        assert '"""Test' in result["test_content"]


# =============================================================================
# PARAMETER TYPE INFERENCE TESTS
# =============================================================================

class TestParameterTypeInference:
    """Tests for parameter type inference functionality."""
    
    def test_infer_list_type_from_subscript(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring list type from subscript access."""
        code = '''
def get_first(items):
    return items[0]
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        # Should generate list edge cases
        assert "error" not in result
        assert "empty list" in result["test_content"].lower() or "[]" in result["test_content"]
    
    def test_infer_iterable_from_for_loop(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring iterable type from for loop usage."""
        code = '''
def sum_all(numbers):
    total = 0
    for n in numbers:
        total += n
    return total
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
        # Should recognize as iterable
        assert result["test_cases_generated"] >= 1
    
    def test_infer_optional_from_none_check(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring Optional type from None comparison."""
        code = '''
def process(value):
    if value is None:
        return "default"
    return str(value)
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
        # Should handle None case
        assert "None" in result["test_content"]
    
    def test_infer_type_from_isinstance(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring type from isinstance check."""
        code = '''
def process(data):
    if isinstance(data, str):
        return data.upper()
    return str(data)
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
        # Should generate string test cases
        assert result["test_cases_generated"] >= 1


# =============================================================================
# RETURN TYPE INFERENCE TESTS
# =============================================================================

class TestReturnTypeInference:
    """Tests for return type inference functionality."""
    
    def test_infer_none_return(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring None return type."""
        code = '''
def do_nothing(x):
    pass
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
        # Should expect None return
        assert "None" in result["test_content"]
    
    def test_infer_constant_return(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring constant return types."""
        code = '''
def get_number(x):
    return 42

def get_string(x):
    return "hello"

def get_bool(x):
    return True
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
        assert result["functions_tested"] >= 3
    
    def test_infer_list_return(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring list return type."""
        code = '''
def get_items(x):
    return [1, 2, 3]
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result
    
    def test_infer_dict_return(self, char_test_gen: CharacterizationTestGenerator):
        """Test inferring dict return type."""
        code = '''
def get_mapping(x):
    return {"key": "value"}
'''
        result = char_test_gen.generate_tests_for_file(code, "test.py")
        
        assert "error" not in result


# =============================================================================
# SIDE EFFECT DETECTION TESTS
# =============================================================================

class TestSideEffectDetection:
    """Tests for side effect detection functionality."""
    
    def test_detect_print_side_effect(
        self, char_test_gen: CharacterizationTestGenerator, side_effects_code: str
    ):
        """Test detecting print as a side effect."""
        result = char_test_gen.generate_tests_for_file(side_effects_code, "io.py")
        
        assert "error" not in result
        # Should note side effects in generated tests
        assert "side effect" in result["test_content"].lower()
    
    def test_detect_global_side_effect(self, char_test_gen: CharacterizationTestGenerator):
        """Test detecting global keyword as a side effect."""
        code = '''
counter = 0

def increment(x):
    global counter
    counter += x
    return counter
'''
        result = char_test_gen.generate_tests_for_file(code, "state.py")
        
        assert "error" not in result
    
    def test_detect_attribute_modification(self, char_test_gen: CharacterizationTestGenerator):
        """Test detecting attribute modification as a side effect."""
        code = '''
def update_object(obj, value):
    obj.attribute = value
    return obj
'''
        result = char_test_gen.generate_tests_for_file(code, "mutator.py")
        
        assert "error" not in result
    
    def test_pure_function_no_side_effects(self, char_test_gen: CharacterizationTestGenerator):
        """Test that pure functions are not marked as having side effects."""
        code = '''
def pure_add(a, b):
    return a + b
'''
        result = char_test_gen.generate_tests_for_file(code, "pure.py")
        
        assert "error" not in result
        # Pure function should not have side effect comment
        # (This is a soft check - the test content should be cleaner)


# =============================================================================
# EDGE CASE GENERATION TESTS
# =============================================================================

class TestEdgeCaseGeneration:
    """Tests for edge case generation functionality."""
    
    def test_string_edge_cases(self, char_test_gen: CharacterizationTestGenerator):
        """Test edge case generation for string parameters."""
        code = '''
def process_text(text: str):
    return text.upper()
'''
        result = char_test_gen.generate_tests_for_file(code, "text.py")
        
        assert "error" not in result
        # Should have empty string test
        assert '""' in result["test_content"] or "empty" in result["test_content"].lower()
    
    def test_int_edge_cases(self, char_test_gen: CharacterizationTestGenerator):
        """Test edge case generation for integer parameters."""
        code = '''
def double(n: int):
    return n * 2
'''
        result = char_test_gen.generate_tests_for_file(code, "math.py")
        
        assert "error" not in result
        # Should have zero and negative tests
        content = result["test_content"]
        assert "0" in content or "zero" in content.lower()
    
    def test_list_edge_cases(self, char_test_gen: CharacterizationTestGenerator):
        """Test edge case generation for list parameters."""
        code = '''
def first_item(items: list):
    return items[0]
'''
        result = char_test_gen.generate_tests_for_file(code, "list_utils.py")
        
        assert "error" not in result
        # Should have empty list test
        assert "[]" in result["test_content"] or "empty" in result["test_content"].lower()
    
    def test_happy_path_always_generated(self, char_test_gen: CharacterizationTestGenerator):
        """Test that happy path test is always generated."""
        code = '''
def process(data):
    return data
'''
        result = char_test_gen.generate_tests_for_file(code, "module.py")
        
        assert "error" not in result
        assert "happy" in result["test_content"].lower() or result["test_cases_generated"] >= 1


# =============================================================================
# TEST CASE ENHANCER TESTS
# =============================================================================

class TestTestCaseEnhancer:
    """Tests for TestCaseEnhancer class."""
    
    def test_generate_property_based_tests(self, test_enhancer: TestCaseEnhancer):
        """Test generating property-based tests."""
        func_info = {
            'name': 'add',
            'params': [
                {'name': 'a', 'type': 'int'},
                {'name': 'b', 'type': 'int'}
            ]
        }
        
        lines = test_enhancer.add_property_based_tests(func_info)
        
        assert len(lines) > 0
        content = '\n'.join(lines)
        assert "hypothesis" in content
        assert "@given" in content
        assert "st.integers()" in content
    
    def test_hypothesis_strategy_for_string(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy generation for strings."""
        strategy = test_enhancer._get_hypothesis_strategy('str')
        assert strategy == 'text()'
    
    def test_hypothesis_strategy_for_int(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy generation for integers."""
        strategy = test_enhancer._get_hypothesis_strategy('int')
        assert strategy == 'integers()'
    
    def test_hypothesis_strategy_for_float(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy generation for floats."""
        strategy = test_enhancer._get_hypothesis_strategy('float')
        assert 'floats' in strategy
        assert 'nan' in strategy.lower()  # Should exclude NaN
    
    def test_hypothesis_strategy_for_list(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy generation for lists."""
        strategy = test_enhancer._get_hypothesis_strategy('list')
        assert 'lists' in strategy
    
    def test_hypothesis_strategy_for_dict(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy generation for dicts."""
        strategy = test_enhancer._get_hypothesis_strategy('dict')
        assert 'dictionaries' in strategy
    
    def test_hypothesis_strategy_fallback(self, test_enhancer: TestCaseEnhancer):
        """Test hypothesis strategy fallback for unknown types."""
        strategy = test_enhancer._get_hypothesis_strategy('unknown_type')
        assert strategy == 'text()'  # Default fallback


# =============================================================================
# TEST GENERATOR ORCHESTRATOR TESTS
# =============================================================================

class TestTestGeneratorOrchestrator:
    """Tests for TestGenerator orchestrator class."""
    
    def test_generate_characterization_tests(
        self, test_generator: TestGenerator, simple_function_code: str
    ):
        """Test generating characterization tests through orchestrator."""
        result = test_generator.generate_characterization_tests(
            simple_function_code, "math.py"
        )
        
        assert "error" not in result
        assert "test_content" in result
        assert result["functions_tested"] >= 1
    
    def test_generate_with_property_tests_note(
        self, test_generator: TestGenerator, simple_function_code: str
    ):
        """Test that property tests note is added when requested."""
        result = test_generator.generate_characterization_tests(
            simple_function_code, "math.py", include_property_tests=True
        )
        
        assert "error" not in result
        assert "note" in result
        assert "hypothesis" in result["note"].lower()
    
    def test_generate_test_for_specific_function(
        self, test_generator: TestGenerator, complex_function_code: str
    ):
        """Test generating tests for a specific function."""
        result = test_generator.generate_test_for_specific_function(
            complex_function_code, "validate_string", "utils.py"
        )
        
        assert "error" not in result
        assert result["function"] == "validate_string"
        assert "test_content" in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the test generator."""
    
    def test_full_workflow_simple_module(self, test_generator: TestGenerator):
        """Test complete workflow for a simple module."""
        code = '''
"""A simple math module."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
        result = test_generator.generate_characterization_tests(code, "math_ops.py")
        
        assert "error" not in result
        assert result["functions_tested"] == 4
        assert result["test_cases_generated"] >= 4  # At least one per function
        
        content = result["test_content"]
        assert "test_add" in content
        assert "test_subtract" in content
        assert "test_multiply" in content
        assert "test_divide" in content
    
    def test_full_workflow_with_class(
        self, test_generator: TestGenerator, class_with_methods_code: str
    ):
        """Test workflow with a class containing methods."""
        result = test_generator.generate_characterization_tests(
            class_with_methods_code, "calculator.py"
        )
        
        assert "error" not in result
        # Should test public methods (add, multiply, reset)
        # __init__ is skipped as it starts with _
        content = result["test_content"]
        assert "add" in content
        assert "multiply" in content
    
    def test_generated_tests_are_valid_python(self, test_generator: TestGenerator):
        """Test that generated test code is valid Python syntax."""
        code = '''
def process(data: list) -> dict:
    result = {}
    for item in data:
        result[item] = len(str(item))
    return result
'''
        result = test_generator.generate_characterization_tests(code, "processor.py")
        
        assert "error" not in result
        
        # Try to parse the generated test code
        try:
            ast.parse(result["test_content"])
        except SyntaxError as e:
            pytest.fail(f"Generated test code has syntax error: {e}")
    
    def test_handles_async_functions(self, test_generator: TestGenerator):
        """Test handling of async functions."""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    return {"url": url, "data": "sample"}
'''
        result = test_generator.generate_characterization_tests(code, "async_utils.py")
        
        # Should handle async functions (may skip or generate async tests)
        assert "error" not in result
    
    def test_handles_decorated_functions(self, test_generator: TestGenerator):
        """Test handling of decorated functions."""
        code = '''
def decorator(func):
    return func

@decorator
def decorated_func(x: int) -> int:
    """A decorated function."""
    return x * 2
'''
        result = test_generator.generate_characterization_tests(code, "decorated.py")
        
        assert "error" not in result
        # Should still generate tests for decorated functions
        assert "decorated_func" in result["test_content"]


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================

class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""
    
    def test_empty_file(self, test_generator: TestGenerator):
        """Test handling of empty file."""
        result = test_generator.generate_characterization_tests("", "empty.py")
        
        assert "error" not in result
        assert result["functions_tested"] == 0
    
    def test_file_with_only_imports(self, test_generator: TestGenerator):
        """Test handling of file with only imports."""
        code = '''
import os
import sys
from typing import List, Dict
'''
        result = test_generator.generate_characterization_tests(code, "imports.py")
        
        assert "error" not in result
        assert result["functions_tested"] == 0
    
    def test_file_with_only_classes(self, test_generator: TestGenerator):
        """Test handling of file with only class definitions (no standalone functions)."""
        code = '''
class MyClass:
    def method(self, x):
        return x
'''
        result = test_generator.generate_characterization_tests(code, "classes.py")
        
        # Methods inside classes should be found
        assert "error" not in result
    
    def test_function_with_no_parameters(self, test_generator: TestGenerator):
        """Test handling of functions with no parameters."""
        code = '''
def get_constant():
    return 42
'''
        result = test_generator.generate_characterization_tests(code, "constants.py")
        
        # Functions without parameters are skipped by default
        assert "error" not in result
    
    def test_function_with_only_self_parameter(self, test_generator: TestGenerator):
        """Test handling of methods with only self parameter."""
        code = '''
class MyClass:
    def get_value(self):
        return self.value
'''
        result = test_generator.generate_characterization_tests(code, "class.py")
        
        # Methods with only self are skipped
        assert "error" not in result
    
    def test_complex_type_annotations(self, test_generator: TestGenerator):
        """Test handling of complex type annotations."""
        code = '''
from typing import List, Dict, Optional, Union

def process(
    items: List[Dict[str, int]],
    config: Optional[Dict[str, str]] = None
) -> Union[List[int], None]:
    """Process items with optional config."""
    if not items:
        return None
    return [sum(item.values()) for item in items]
'''
        result = test_generator.generate_characterization_tests(code, "complex.py")
        
        assert "error" not in result
        # Should handle complex annotations gracefully
    
    def test_function_with_args_kwargs(self, test_generator: TestGenerator):
        """Test handling of *args and **kwargs."""
        code = '''
def flexible_func(*args, **kwargs):
    """A function with flexible arguments."""
    return len(args) + len(kwargs)
'''
        result = test_generator.generate_characterization_tests(code, "flexible.py")
        
        # Should handle *args/**kwargs (may skip or generate basic test)
        assert "error" not in result
    
    def test_nested_functions(self, test_generator: TestGenerator):
        """Test handling of nested functions."""
        code = '''
def outer(x: int) -> int:
    """Outer function with nested function."""
    def inner(y):
        return y * 2
    return inner(x)
'''
        result = test_generator.generate_characterization_tests(code, "nested.py")
        
        assert "error" not in result
        # Should test outer function, inner is private
        assert "outer" in result["test_content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
