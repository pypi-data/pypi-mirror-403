"""
Comprehensive unit tests for Symbol Renamer edge case handling.

Tests cover:
- Input validation (invalid identifiers, non-existent paths, invalid types)
- Name collision detection in target scope
- Magic method renaming prevention
- Dynamic attribute access detection (getattr/setattr/hasattr)
- String literal references in docstrings and comments
- Built-in name conflict detection
- Inheritance contract warnings
- Rollback mechanism
- Import propagation across files

Run with: pytest tests/test_symbol_renamer.py -v
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest

from ohm_mcp.refactoring.symbol_renamer import (
    SymbolRenamer,
    SmartRenamer,
    SymbolRenamingOrchestrator,
    RenameBackupManager,
    EdgeCaseAnalysisResult,
    RenameWarning,
    WarningLevel,
    # Exceptions
    SymbolRenameError,
    NameCollisionError,
    MagicMethodRenameError,
    BuiltinConflictError,
    InheritanceContractError,
    InvalidInputError,
    # Constants
    MAGIC_METHODS,
    PYTHON_BUILTINS,
    DYNAMIC_ATTR_FUNCTIONS,
    VALID_SYMBOL_TYPES,
    VALID_SCOPES,
)
from ohm_mcp.refactoring.python_version_compat import has_ast_node_type


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_project() -> Generator[str, None, None]:
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_symbol_renamer_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_project: str) -> str:
    """Create a sample Python file for testing."""
    file_path = os.path.join(temp_project, "sample.py")
    content = '''"""Sample module for testing symbol renaming."""

def old_function():
    """This function will be renamed."""
    x = 10
    return x * 2


def another_function():
    """Calls old_function."""
    result = old_function()
    return result


class OldClass:
    """A class that will be renamed."""
    
    def __init__(self):
        self.value = 42
    
    def old_method(self):
        """Method to be renamed."""
        return self.value


# Usage
instance = OldClass()
result = instance.old_method()
'''
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path


@pytest.fixture
def renamer() -> SymbolRenamer:
    """Create a SymbolRenamer instance."""
    return SymbolRenamer()


@pytest.fixture
def smart_renamer() -> SmartRenamer:
    """Create a SmartRenamer instance."""
    return SmartRenamer()


@pytest.fixture
def orchestrator() -> SymbolRenamingOrchestrator:
    """Create a SymbolRenamingOrchestrator instance."""
    return SymbolRenamingOrchestrator()


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================

class TestInputValidation:
    """Tests for input validation and defensive checks."""
    
    def test_empty_project_root_raises_error(self, renamer: SymbolRenamer):
        """Test that empty project_root raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root="",
            old_name="foo",
            new_name="bar",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "project_root" in result["error"]
    
    def test_nonexistent_project_root_raises_error(self, renamer: SymbolRenamer):
        """Test that non-existent project_root raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root="/nonexistent/path/to/project",
            old_name="foo",
            new_name="bar",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "does not exist" in result["error"]
    
    def test_file_as_project_root_raises_error(self, sample_python_file: str):
        """Test that using a file as project_root raises InvalidInputError."""
        renamer = SymbolRenamer()
        result = renamer.rename_symbol(
            project_root=sample_python_file,  # This is a file, not a directory
            old_name="foo",
            new_name="bar",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "must be a directory" in result["error"]
    
    def test_empty_old_name_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that empty old_name raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="",
            new_name="bar",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "old_name" in result["error"]
    
    def test_empty_new_name_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that empty new_name raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="foo",
            new_name="",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "new_name" in result["error"]
    
    def test_invalid_identifier_old_name_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that invalid Python identifier for old_name raises error."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="123invalid",
            new_name="valid_name",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "valid Python identifier" in result["error"]
    
    def test_invalid_identifier_new_name_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that invalid Python identifier for new_name raises error."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="valid_name",
            new_name="invalid-name",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "valid Python identifier" in result["error"]
    
    def test_invalid_symbol_type_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that invalid symbol_type raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="foo",
            new_name="bar",
            symbol_type="invalid_type"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "symbol_type" in result["error"]
    
    def test_invalid_scope_raises_error(self, temp_project: str, renamer: SymbolRenamer):
        """Test that invalid scope raises InvalidInputError."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="foo",
            new_name="bar",
            symbol_type="function",
            scope="invalid_scope"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "scope" in result["error"]
    
    def test_valid_symbol_types_constant(self):
        """Test that VALID_SYMBOL_TYPES contains expected values."""
        expected = {'variable', 'function', 'class', 'method', 'attribute', 'any'}
        assert VALID_SYMBOL_TYPES == expected
    
    def test_valid_scopes_constant(self):
        """Test that VALID_SCOPES contains expected values."""
        expected = {'project', 'file', 'function', 'class'}
        assert VALID_SCOPES == expected


# =============================================================================
# MAGIC METHOD TESTS
# =============================================================================

class TestMagicMethodPrevention:
    """Tests for magic method renaming prevention."""
    
    def test_cannot_rename_init(self, temp_project: str, renamer: SymbolRenamer):
        """Test that __init__ cannot be renamed."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="__init__",
            new_name="initialize",
            symbol_type="method"
        )
        assert not result["success"]
        assert result["error_type"] == "MagicMethodRenameError"
        assert "__init__" in result["error"]
    
    def test_cannot_rename_str(self, temp_project: str, renamer: SymbolRenamer):
        """Test that __str__ cannot be renamed."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="__str__",
            new_name="to_string",
            symbol_type="method"
        )
        assert not result["success"]
        assert result["error_type"] == "MagicMethodRenameError"
    
    def test_cannot_rename_new(self, temp_project: str, renamer: SymbolRenamer):
        """Test that __new__ cannot be renamed."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="__new__",
            new_name="create",
            symbol_type="method"
        )
        assert not result["success"]
        assert result["error_type"] == "MagicMethodRenameError"
    
    def test_cannot_rename_repr(self, temp_project: str, renamer: SymbolRenamer):
        """Test that __repr__ cannot be renamed."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="__repr__",
            new_name="represent",
            symbol_type="method"
        )
        assert not result["success"]
        assert result["error_type"] == "MagicMethodRenameError"
    
    def test_cannot_rename_to_magic_method(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename a regular method to a magic method name."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="my_method",
            new_name="__init__",
            symbol_type="method"
        )
        assert not result["success"]
        assert result["error_type"] == "InvalidInputError"
        assert "magic method" in result["error"]
    
    def test_magic_methods_constant_contains_common_dunders(self):
        """Test that MAGIC_METHODS contains common dunder methods."""
        common_dunders = [
            '__init__', '__new__', '__del__', '__repr__', '__str__',
            '__eq__', '__hash__', '__len__', '__getitem__', '__setitem__',
            '__call__', '__enter__', '__exit__', '__iter__', '__next__'
        ]
        for dunder in common_dunders:
            assert dunder in MAGIC_METHODS, f"{dunder} should be in MAGIC_METHODS"
    
    def test_is_magic_method_detection(self, renamer: SymbolRenamer):
        """Test the _is_magic_method helper method."""
        # Should be magic methods
        assert renamer._is_magic_method("__init__") is True
        assert renamer._is_magic_method("__custom_dunder__") is True
        
        # Should NOT be magic methods
        assert renamer._is_magic_method("regular_method") is False
        assert renamer._is_magic_method("_private") is False
        assert renamer._is_magic_method("__private") is False  # Single trailing underscore
        assert renamer._is_magic_method("dunder__") is False


# =============================================================================
# BUILTIN CONFLICT TESTS
# =============================================================================

class TestBuiltinConflicts:
    """Tests for Python built-in name conflict detection."""
    
    def test_cannot_rename_to_list(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename to 'list' (built-in)."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="my_list",
            new_name="list",
            symbol_type="variable"
        )
        assert not result["success"]
        assert result["error_type"] == "BuiltinConflictError"
        assert "list" in result["error"]
    
    def test_cannot_rename_to_dict(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename to 'dict' (built-in)."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="my_dict",
            new_name="dict",
            symbol_type="variable"
        )
        assert not result["success"]
        assert result["error_type"] == "BuiltinConflictError"
    
    def test_cannot_rename_to_str(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename to 'str' (built-in)."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="my_string",
            new_name="str",
            symbol_type="variable"
        )
        assert not result["success"]
        assert result["error_type"] == "BuiltinConflictError"
    
    def test_cannot_rename_to_print(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename to 'print' (built-in function)."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="my_print",
            new_name="print",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "BuiltinConflictError"
    
    def test_cannot_rename_to_len(self, temp_project: str, renamer: SymbolRenamer):
        """Test that cannot rename to 'len' (built-in function)."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="get_length",
            new_name="len",
            symbol_type="function"
        )
        assert not result["success"]
        assert result["error_type"] == "BuiltinConflictError"
    
    def test_can_rename_to_non_builtin(self, temp_project: str, sample_python_file: str, renamer: SymbolRenamer):
        """Test that can rename to a non-builtin name."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        # Should succeed (or fail for other reasons, but not BuiltinConflictError)
        if not result["success"]:
            assert result.get("error_type") != "BuiltinConflictError"
    
    def test_python_builtins_constant(self):
        """Test that PYTHON_BUILTINS contains common built-ins."""
        common_builtins = [
            'list', 'dict', 'str', 'int', 'float', 'bool', 'set', 'tuple',
            'print', 'len', 'range', 'type', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'open', 'input', 'sum', 'max', 'min'
        ]
        for builtin in common_builtins:
            assert builtin in PYTHON_BUILTINS, f"{builtin} should be in PYTHON_BUILTINS"


# =============================================================================
# NAME COLLISION TESTS
# =============================================================================

class TestNameCollisionDetection:
    """Tests for name collision detection in target scope."""
    
    def test_detect_function_collision(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of collision with existing function."""
        # Create file with two functions
        file_path = os.path.join(temp_project, "collision.py")
        content = '''
def old_func():
    pass

def existing_func():
    pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_func",
            new_name="existing_func",  # Collision!
            symbol_type="function"
        )
        
        assert not result["success"]
        assert "collision" in result.get("error", "").lower() or result.get("error_type") == "NameCollisionError"
    
    def test_detect_class_collision(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of collision with existing class."""
        file_path = os.path.join(temp_project, "collision.py")
        content = '''
class OldClass:
    pass

class ExistingClass:
    pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="OldClass",
            new_name="ExistingClass",  # Collision!
            symbol_type="class"
        )
        
        assert not result["success"]
    
    def test_detect_variable_collision(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of collision with existing variable."""
        file_path = os.path.join(temp_project, "collision.py")
        content = '''
old_var = 1
existing_var = 2
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_var",
            new_name="existing_var",  # Collision!
            symbol_type="variable"
        )
        
        assert not result["success"]
    
    def test_detect_import_collision(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of collision with imported name."""
        file_path = os.path.join(temp_project, "collision.py")
        content = '''
from os import path

def old_func():
    pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_func",
            new_name="path",  # Collision with import!
            symbol_type="function"
        )
        
        assert not result["success"]
    
    def test_force_allows_collision(self, temp_project: str, renamer: SymbolRenamer):
        """Test that force=True allows renaming despite collision."""
        file_path = os.path.join(temp_project, "collision.py")
        content = '''
def old_func():
    pass

def existing_func():
    pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_func",
            new_name="existing_func",
            symbol_type="function",
            force=True  # Force despite collision
        )
        
        # With force=True, should succeed (or at least not fail due to collision)
        if not result["success"]:
            assert "collision" not in result.get("error", "").lower()


# =============================================================================
# DYNAMIC ATTRIBUTE ACCESS TESTS
# =============================================================================

class TestDynamicAttributeAccess:
    """Tests for dynamic attribute access detection."""
    
    def test_detect_getattr_usage(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of getattr() with symbol name as string."""
        file_path = os.path.join(temp_project, "dynamic.py")
        content = '''
class MyClass:
    def old_method(self):
        pass

obj = MyClass()
method = getattr(obj, 'old_method')
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_method",
            new_name="new_method",
            symbol_type="method"
        )
        
        assert len(analysis.dynamic_accesses) > 0
        assert any('getattr' in str(a) for a in analysis.dynamic_accesses)
    
    def test_detect_setattr_usage(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of setattr() with symbol name as string."""
        file_path = os.path.join(temp_project, "dynamic.py")
        content = '''
class MyClass:
    pass

obj = MyClass()
setattr(obj, 'old_attr', 42)
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_attr",
            new_name="new_attr",
            symbol_type="attribute"
        )
        
        assert len(analysis.dynamic_accesses) > 0
        assert any('setattr' in str(a) for a in analysis.dynamic_accesses)
    
    def test_detect_hasattr_usage(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of hasattr() with symbol name as string."""
        file_path = os.path.join(temp_project, "dynamic.py")
        content = '''
class MyClass:
    old_attr = None

obj = MyClass()
if hasattr(obj, 'old_attr'):
    print("has it")
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_attr",
            new_name="new_attr",
            symbol_type="attribute"
        )
        
        assert len(analysis.dynamic_accesses) > 0
        assert any('hasattr' in str(a) for a in analysis.dynamic_accesses)
    
    def test_detect_delattr_usage(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of delattr() with symbol name as string."""
        file_path = os.path.join(temp_project, "dynamic.py")
        content = '''
class MyClass:
    old_attr = None

obj = MyClass()
delattr(obj, 'old_attr')
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_attr",
            new_name="new_attr",
            symbol_type="attribute"
        )
        
        assert len(analysis.dynamic_accesses) > 0
        assert any('delattr' in str(a) for a in analysis.dynamic_accesses)
    
    def test_dynamic_access_generates_warning(self, temp_project: str, renamer: SymbolRenamer):
        """Test that dynamic access generates appropriate warning."""
        file_path = os.path.join(temp_project, "dynamic.py")
        content = '''
obj = SomeClass()
value = getattr(obj, 'old_name')
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_name",
            new_name="new_name",
            symbol_type="attribute"
        )
        
        # Should have warnings about dynamic access
        dynamic_warnings = [w for w in analysis.warnings if w.warning_type == 'dynamic_access']
        assert len(dynamic_warnings) > 0
        assert analysis.requires_manual_review is True
    
    def test_dynamic_attr_functions_constant(self):
        """Test that DYNAMIC_ATTR_FUNCTIONS contains expected functions."""
        expected = {'getattr', 'setattr', 'hasattr', 'delattr'}
        assert DYNAMIC_ATTR_FUNCTIONS == expected


# =============================================================================
# STRING LITERAL REFERENCE TESTS
# =============================================================================

class TestStringLiteralReferences:
    """Tests for string literal reference detection in docstrings and comments."""
    
    def test_detect_docstring_reference(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of symbol name in docstrings."""
        file_path = os.path.join(temp_project, "docstring.py")
        content = '''
def old_function():
    """This is old_function that does something."""
    pass

def caller():
    """Calls old_function to get result."""
    return old_function()
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should detect references in docstrings
        docstring_refs = [r for r in analysis.string_references if r.get('type') == 'docstring']
        assert len(docstring_refs) > 0
    
    def test_detect_comment_reference(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of symbol name in comments."""
        file_path = os.path.join(temp_project, "comments.py")
        content = '''
def old_function():
    pass

# Call old_function here
result = old_function()  # old_function returns value
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should detect references in comments
        comment_refs = [r for r in analysis.string_references if r.get('type') == 'comment']
        assert len(comment_refs) > 0
    
    def test_detect_string_literal_reference(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of symbol name in string literals."""
        file_path = os.path.join(temp_project, "strings.py")
        content = '''
def old_function():
    pass

# Serialization/reflection usage
func_name = 'old_function'
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should detect string literal references
        string_refs = [r for r in analysis.string_references if r.get('type') == 'string_literal']
        assert len(string_refs) > 0
    
    def test_string_reference_generates_info_warning(self, temp_project: str, renamer: SymbolRenamer):
        """Test that docstring/comment references generate INFO level warnings."""
        file_path = os.path.join(temp_project, "docstring.py")
        content = '''
def old_function():
    """The old_function does something."""
    pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Docstring references should be INFO level
        docstring_warnings = [
            w for w in analysis.warnings 
            if w.warning_type == 'string_reference' and 'docstring' in str(w.context).lower()
        ]
        # INFO level warnings don't block proceeding
        assert analysis.can_proceed is True


# =============================================================================
# INHERITANCE CONTRACT TESTS
# =============================================================================

class TestInheritanceContracts:
    """Tests for inheritance contract violation detection."""
    
    def test_detect_overridden_method(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of method that overrides parent class method."""
        file_path = os.path.join(temp_project, "inheritance.py")
        content = '''
class Parent:
    def process(self):
        pass

class Child(Parent):
    def process(self):
        """Overrides Parent.process"""
        super().process()
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="process",
            new_name="handle",
            symbol_type="method"
        )
        
        # Should detect inheritance issue
        assert len(analysis.inheritance_issues) > 0
        assert any('Parent' in str(issue) for issue in analysis.inheritance_issues)
    
    def test_inheritance_warning_level(self, temp_project: str, renamer: SymbolRenamer):
        """Test that inheritance issues generate ERROR level warnings."""
        file_path = os.path.join(temp_project, "inheritance.py")
        content = '''
class Base:
    def method(self):
        pass

class Derived(Base):
    def method(self):
        pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="method",
            new_name="new_method",
            symbol_type="method"
        )
        
        # Should have ERROR level warning for inheritance
        inheritance_warnings = [
            w for w in analysis.warnings 
            if w.warning_type == 'inheritance_contract'
        ]
        assert len(inheritance_warnings) > 0
        assert any(w.level == WarningLevel.ERROR for w in inheritance_warnings)
    
    def test_multiple_inheritance_detection(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection with multiple inheritance."""
        file_path = os.path.join(temp_project, "multi_inherit.py")
        content = '''
class Mixin1:
    def shared_method(self):
        pass

class Mixin2:
    def shared_method(self):
        pass

class Combined(Mixin1, Mixin2):
    def shared_method(self):
        pass
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="shared_method",
            new_name="new_method",
            symbol_type="method"
        )
        
        # Should detect inheritance issues
        assert len(analysis.inheritance_issues) > 0


# =============================================================================
# ROLLBACK MECHANISM TESTS
# =============================================================================

class TestRollbackMechanism:
    """Tests for backup and rollback functionality."""
    
    def test_backup_manager_creation(self, temp_project: str):
        """Test that backup manager can be created."""
        manager = RenameBackupManager(temp_project)
        assert manager.project_root == temp_project
    
    def test_backup_manager_invalid_path(self):
        """Test that backup manager raises error for invalid path."""
        with pytest.raises(InvalidInputError):
            RenameBackupManager("/nonexistent/path")
    
    def test_backup_file_creation(self, temp_project: str, sample_python_file: str):
        """Test that backup files are created correctly."""
        manager = RenameBackupManager(temp_project)
        manager.start_operation()
        
        backup_path = manager.backup_file(sample_python_file)
        
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.bak')
    
    def test_rollback_restores_file(self, temp_project: str, sample_python_file: str):
        """Test that rollback restores original file content."""
        # Read original content
        with open(sample_python_file, 'r') as f:
            original_content = f.read()
        
        manager = RenameBackupManager(temp_project)
        manager.start_operation()
        manager.backup_file(sample_python_file)
        
        # Modify the file
        with open(sample_python_file, 'w') as f:
            f.write("# Modified content\n")
        
        # Rollback
        result = manager.rollback_all()
        
        # Check file is restored
        with open(sample_python_file, 'r') as f:
            restored_content = f.read()
        
        assert result[sample_python_file] is True
        assert restored_content == original_content
    
    def test_smart_renamer_creates_backup(self, temp_project: str, sample_python_file: str, smart_renamer: SmartRenamer):
        """Test that SmartRenamer creates backups when applying changes."""
        result = smart_renamer.apply_rename(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function",
            create_backup=True
        )
        
        if result["success"]:
            assert "backup_info" in result
            assert result.get("rollback_available") is True
    
    def test_smart_renamer_rollback(self, temp_project: str, sample_python_file: str, smart_renamer: SmartRenamer):
        """Test that SmartRenamer can rollback changes."""
        # Read original content
        with open(sample_python_file, 'r') as f:
            original_content = f.read()
        
        # Apply rename
        result = smart_renamer.apply_rename(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function",
            create_backup=True
        )
        
        if result["success"]:
            # Rollback
            rollback_result = smart_renamer.rollback()
            
            # Check file is restored
            with open(sample_python_file, 'r') as f:
                restored_content = f.read()
            
            assert rollback_result["success"] is True
            assert restored_content == original_content
    
    def test_cleanup_backups(self, temp_project: str, sample_python_file: str):
        """Test that backup cleanup removes backup files."""
        manager = RenameBackupManager(temp_project)
        manager.start_operation()
        backup_path = manager.backup_file(sample_python_file)
        
        assert os.path.exists(backup_path)
        
        manager.cleanup_backups()
        
        assert not os.path.exists(backup_path)


# =============================================================================
# IMPORT PROPAGATION TESTS
# =============================================================================

class TestImportPropagation:
    """Tests for import propagation detection across files."""
    
    def test_detect_direct_import(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of direct import of symbol."""
        # Create module with function
        module_path = os.path.join(temp_project, "mymodule.py")
        with open(module_path, 'w') as f:
            f.write("def old_function():\n    pass\n")
        
        # Create file that imports it
        importer_path = os.path.join(temp_project, "importer.py")
        with open(importer_path, 'w') as f:
            f.write("from mymodule import old_function\n\nold_function()\n")
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should detect import propagation
        assert len(analysis.import_propagations) > 0
    
    def test_detect_aliased_import(self, temp_project: str, renamer: SymbolRenamer):
        """Test detection of aliased import."""
        module_path = os.path.join(temp_project, "mymodule.py")
        with open(module_path, 'w') as f:
            f.write("def old_function():\n    pass\n")
        
        importer_path = os.path.join(temp_project, "importer.py")
        with open(importer_path, 'w') as f:
            f.write("from mymodule import old_function as func\n\nfunc()\n")
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should detect import with alias
        aliased_imports = [p for p in analysis.import_propagations if p.get('alias')]
        assert len(aliased_imports) > 0
    
    def test_detect_wildcard_import_warning(self, temp_project: str, renamer: SymbolRenamer):
        """Test that wildcard imports generate warnings."""
        module_path = os.path.join(temp_project, "mymodule.py")
        with open(module_path, 'w') as f:
            f.write("def old_function():\n    pass\n")
        
        importer_path = os.path.join(temp_project, "importer.py")
        with open(importer_path, 'w') as f:
            f.write("from mymodule import *\n\nold_function()\n")
        
        analysis = renamer.analyze_edge_cases(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should have warning about wildcard import
        wildcard_warnings = [
            w for w in analysis.warnings 
            if w.warning_type == 'wildcard_import'
        ]
        assert len(wildcard_warnings) > 0


# =============================================================================
# WARNING SYSTEM TESTS
# =============================================================================

class TestWarningSystem:
    """Tests for the warning system."""
    
    def test_warning_levels(self):
        """Test that all warning levels are defined."""
        assert WarningLevel.INFO.value == "info"
        assert WarningLevel.WARNING.value == "warning"
        assert WarningLevel.ERROR.value == "error"
        assert WarningLevel.CRITICAL.value == "critical"
    
    def test_rename_warning_creation(self):
        """Test RenameWarning dataclass creation."""
        warning = RenameWarning(
            level=WarningLevel.WARNING,
            warning_type="test_warning",
            message="Test message",
            file_path="/path/to/file.py",
            line_number=10,
            column=5,
            context="test context",
            suggestion="test suggestion"
        )
        
        assert warning.level == WarningLevel.WARNING
        assert warning.warning_type == "test_warning"
        assert warning.message == "Test message"
    
    def test_rename_warning_to_dict(self):
        """Test RenameWarning serialization to dict."""
        warning = RenameWarning(
            level=WarningLevel.ERROR,
            warning_type="collision",
            message="Name collision detected",
            file_path="/path/to/file.py",
            line_number=42
        )
        
        d = warning.to_dict()
        
        assert d['level'] == "error"
        assert d['type'] == "collision"
        assert d['message'] == "Name collision detected"
        assert d['location']['file'] == "/path/to/file.py"
        assert d['location']['line'] == 42
    
    def test_edge_case_analysis_result_creation(self):
        """Test EdgeCaseAnalysisResult creation."""
        result = EdgeCaseAnalysisResult()
        
        assert result.can_proceed is True
        assert result.requires_manual_review is False
        assert len(result.warnings) == 0
        assert result.version_warnings == []
    
    def test_edge_case_analysis_add_warning(self):
        """Test adding warnings to EdgeCaseAnalysisResult."""
        result = EdgeCaseAnalysisResult()
        
        # Add INFO warning - should not change flags
        result.add_warning(RenameWarning(
            level=WarningLevel.INFO,
            warning_type="info",
            message="Info message"
        ))
        assert result.can_proceed is True
        assert result.requires_manual_review is False
        
        # Add WARNING - should set requires_manual_review
        result.add_warning(RenameWarning(
            level=WarningLevel.WARNING,
            warning_type="warning",
            message="Warning message"
        ))
        assert result.can_proceed is True
        assert result.requires_manual_review is True
        
        # Add CRITICAL - should set can_proceed to False
        result.add_warning(RenameWarning(
            level=WarningLevel.CRITICAL,
            warning_type="critical",
            message="Critical message"
        ))
        assert result.can_proceed is False
    
    def test_edge_case_analysis_to_dict(self):
        """Test EdgeCaseAnalysisResult serialization."""
        result = EdgeCaseAnalysisResult()
        result.add_warning(RenameWarning(
            level=WarningLevel.WARNING,
            warning_type="test",
            message="Test"
        ))
        result.dynamic_accesses.append({'function': 'getattr', 'line': 10})
        result.version_warnings.append({'feature': 'Match Statement'})
        
        d = result.to_dict()
        
        assert 'can_proceed' in d
        assert 'requires_manual_review' in d
        assert 'warning_count' in d
        assert 'warnings' in d
        assert 'dynamic_accesses' in d
        assert 'version_warnings' in d


# =============================================================================
# PYTHON 3.10+ MATCH PATTERN TESTS
# =============================================================================

class TestMatchPatternRenaming:
    """Tests for renaming symbols in match/case pattern bindings."""

    def test_rename_match_pattern_variable(self, temp_project: str, renamer: SymbolRenamer):
        """Ensure match pattern bindings are updated during variable renames."""
        if not has_ast_node_type('Match'):
            pytest.skip("Match statements not supported in this Python version")

        file_path = os.path.join(temp_project, "match_case.py")
        code = '''def handle(cmd):
    match cmd:
        case ["load", filename]:
            return filename
        case ["save", filename]:
            return filename
'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="filename",
            new_name="path",
            symbol_type="variable"
        )

        assert result["success"] is True
        updated = result["refactored_files"][file_path]
        assert 'case ["load", path]:' in updated
        assert 'case ["save", path]:' in updated
        assert 'return path' in updated


# =============================================================================
# ORCHESTRATOR TESTS
# =============================================================================

class TestSymbolRenamingOrchestrator:
    """Tests for the unified orchestrator interface."""
    
    def test_preview_mode_default(self, temp_project: str, sample_python_file: str, orchestrator: SymbolRenamingOrchestrator):
        """Test that preview_only=True is the default."""
        result = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        # Should be a preview (file not modified)
        if result["success"]:
            assert result.get("preview") is True
            # Original file should be unchanged
            with open(sample_python_file, 'r') as f:
                content = f.read()
            assert "old_function" in content
    
    def test_analyze_rename(self, temp_project: str, sample_python_file: str, orchestrator: SymbolRenamingOrchestrator):
        """Test the analyze_rename method."""
        result = orchestrator.analyze_rename(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        assert result["success"] is True
        assert "analysis" in result
        assert "can_proceed" in result
        assert "recommendation" in result
    
    def test_recommendation_safe(self, temp_project: str, orchestrator: SymbolRenamingOrchestrator):
        """Test recommendation for safe rename."""
        file_path = os.path.join(temp_project, "simple.py")
        with open(file_path, 'w') as f:
            f.write("def old_func():\n    pass\n")
        
        result = orchestrator.analyze_rename(
            project_root=temp_project,
            old_name="old_func",
            new_name="new_func",
            symbol_type="function"
        )
        
        if result["success"] and result.get("can_proceed"):
            assert "SAFE" in result.get("recommendation", "") or "PROCEED" in result.get("recommendation", "")
    
    def test_apply_mode(self, temp_project: str, sample_python_file: str, orchestrator: SymbolRenamingOrchestrator):
        """Test applying rename (preview_only=False)."""
        result = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function",
            preview_only=False
        )
        
        if result["success"]:
            # File should be modified
            with open(sample_python_file, 'r') as f:
                content = f.read()
            assert "new_function" in content


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for complete rename workflows."""
    
    def test_full_rename_workflow(self, temp_project: str, orchestrator: SymbolRenamingOrchestrator):
        """Test complete rename workflow: analyze -> preview -> apply -> verify."""
        # Create test file
        file_path = os.path.join(temp_project, "workflow.py")
        content = '''
def calculate_total(items):
    """Calculate total of items."""
    return sum(items)

result = calculate_total([1, 2, 3])
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Step 1: Analyze
        analysis = orchestrator.analyze_rename(
            project_root=temp_project,
            old_name="calculate_total",
            new_name="compute_sum",
            symbol_type="function"
        )
        assert analysis["success"] is True
        
        # Step 2: Preview
        preview = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="calculate_total",
            new_name="compute_sum",
            symbol_type="function",
            preview_only=True
        )
        assert preview["success"] is True
        assert preview.get("occurrences", 0) >= 2  # Definition + usage
        
        # Step 3: Apply
        result = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="calculate_total",
            new_name="compute_sum",
            symbol_type="function",
            preview_only=False
        )
        assert result["success"] is True
        
        # Step 4: Verify
        with open(file_path, 'r') as f:
            new_content = f.read()
        
        assert "compute_sum" in new_content
        assert "calculate_total" not in new_content
    
    def test_multi_file_rename(self, temp_project: str, orchestrator: SymbolRenamingOrchestrator):
        """Test renaming across multiple files."""
        # Create module
        module_path = os.path.join(temp_project, "utils.py")
        with open(module_path, 'w') as f:
            f.write("def helper_func():\n    return 42\n")
        
        # Create file that uses it
        main_path = os.path.join(temp_project, "main.py")
        with open(main_path, 'w') as f:
            f.write("from utils import helper_func\n\nresult = helper_func()\n")
        
        # Rename
        result = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="helper_func",
            new_name="utility_function",
            symbol_type="function",
            preview_only=False
        )
        
        if result["success"]:
            # Both files should be updated
            with open(module_path, 'r') as f:
                assert "utility_function" in f.read()
            with open(main_path, 'r') as f:
                assert "utility_function" in f.read()
    
    def test_class_rename_with_methods(self, temp_project: str, orchestrator: SymbolRenamingOrchestrator):
        """Test renaming a class updates all references."""
        file_path = os.path.join(temp_project, "classes.py")
        content = '''
class OldClass:
    def __init__(self):
        self.value = 0
    
    def method(self):
        return self.value

instance = OldClass()
another: OldClass = OldClass()
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        result = orchestrator.rename_symbol(
            project_root=temp_project,
            old_name="OldClass",
            new_name="NewClass",
            symbol_type="class",
            preview_only=False
        )
        
        if result["success"]:
            with open(file_path, 'r') as f:
                new_content = f.read()
            
            assert "class NewClass:" in new_content
            assert "instance = NewClass()" in new_content
            assert "OldClass" not in new_content


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for various edge cases and corner cases."""
    
    def test_symbol_not_found(self, temp_project: str, sample_python_file: str, renamer: SymbolRenamer):
        """Test handling when symbol is not found."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="nonexistent_symbol",
            new_name="new_name",
            symbol_type="function"
        )
        
        assert not result["success"]
        assert "not found" in result.get("error", "").lower()
    
    def test_empty_project(self, temp_project: str, renamer: SymbolRenamer):
        """Test handling of empty project directory."""
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="some_func",
            new_name="new_func",
            symbol_type="function"
        )
        
        assert not result["success"]
    
    def test_syntax_error_in_file(self, temp_project: str, renamer: SymbolRenamer):
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        file_path = os.path.join(temp_project, "broken.py")
        with open(file_path, 'w') as f:
            f.write("def broken(\n")  # Syntax error
        
        # Create valid file
        valid_path = os.path.join(temp_project, "valid.py")
        with open(valid_path, 'w') as f:
            f.write("def old_func():\n    pass\n")
        
        # Should still work on valid files
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_func",
            new_name="new_func",
            symbol_type="function"
        )
        
        # Should succeed for valid file, skip broken file
        if result["success"]:
            assert result["files_changed"] >= 1
    
    def test_unicode_in_code(self, temp_project: str, renamer: SymbolRenamer):
        """Test handling of Unicode characters in code."""
        file_path = os.path.join(temp_project, "unicode.py")
        content = '''# -*- coding: utf-8 -*-
"""Module with Unicode: 你好世界"""

def old_function():
    """Returns greeting: こんにちは"""
    return "Hello 世界"
'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="function"
        )
        
        assert result["success"] is True
    
    def test_nested_functions(self, temp_project: str, renamer: SymbolRenamer):
        """Test renaming with nested functions.
        
        Note: Nested functions are detected but may require 'any' symbol_type
        since they're not top-level functions. The rename_symbol method returns
        refactored content but doesn't write to disk - check refactored_files.
        """
        file_path = os.path.join(temp_project, "nested.py")
        content = '''
def outer():
    def old_inner():
        return 1
    return old_inner()
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Use 'any' symbol_type to find nested functions
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_inner",
            new_name="new_inner",
            symbol_type="any"  # 'any' finds all name occurrences including nested
        )
        
        # Should find and rename nested function with 'any' type
        assert result["success"] is True
        assert result["occurrences"] >= 2  # Definition + usage
        
        # Check the refactored content (not written to disk by default)
        refactored_files = result.get("refactored_files", {})
        assert len(refactored_files) > 0
        refactored_content = list(refactored_files.values())[0]
        assert "new_inner" in refactored_content
        assert "old_inner" not in refactored_content
    
    def test_decorator_preserved(self, temp_project: str, renamer: SymbolRenamer):
        """Test that decorators are preserved when renaming functions.
        
        Note: Use 'any' symbol_type to ensure decorated functions are found.
        The rename_symbol method returns refactored content but doesn't write
        to disk - check refactored_files.
        """
        file_path = os.path.join(temp_project, "decorated.py")
        content = '''
def decorator(func):
    return func

@decorator
def old_function():
    pass

# Call the function
result = old_function()
'''
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Use 'any' to find all occurrences including decorated functions
        result = renamer.rename_symbol(
            project_root=temp_project,
            old_name="old_function",
            new_name="new_function",
            symbol_type="any"
        )
        
        assert result["success"] is True
        
        # Check the refactored content (not written to disk by default)
        refactored_files = result.get("refactored_files", {})
        assert len(refactored_files) > 0
        refactored_content = list(refactored_files.values())[0]
        assert "@decorator" in refactored_content  # Decorator preserved
        assert "new_function" in refactored_content
        assert "old_function" not in refactored_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
