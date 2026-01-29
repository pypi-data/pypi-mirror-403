import pytest
from constspace import constspace, ConstSpace, ConstSpaceType

# --- Mock Constant Spaces for Testing ---

@constspace
class AppConfig:
    '''Mock configuration for application settings.'''
    VERSION = '1.0.0'
    DEBUG = False
    # Testing internal reference during definition
    DESC = f'App version {VERSION}'

@constspace
class DatabaseConfig:
    '''Mock configuration for database settings.'''
    VERSION = '5.7'
    PORT = 3306

# --- Unit Tests ---

def test_direct_value_access():
    '''
    Ensure that constants can be accessed directly without .value 
    and that internal string interpolation works correctly.
    '''
    assert AppConfig.VERSION == '1.0.0'
    assert AppConfig.DEBUG is False
    assert AppConfig.DESC == 'App version 1.0.0'

def test_readonly_class_attribute_protection():
    '''
    Ensure that modifying a class attribute raises AttributeError.
    This verifies the Metaclass-level protection.
    '''
    with pytest.raises(AttributeError) as excinfo:
        AppConfig.VERSION = '2.0.0'
    assert 'is read-only' in str(excinfo.value).lower()

def test_attribute_deletion_protection():
    '''
    Ensure that deleting a class attribute is prohibited.
    '''
    with pytest.raises(AttributeError) as excinfo:
        del AppConfig.VERSION
    assert 'is read-only' in str(excinfo.value).lower()

def test_instantiation_restriction():
    '''
    Ensure that the class cannot be instantiated.
    This verifies the __init__ override logic.
    '''
    with pytest.raises(TypeError) as excinfo:
        AppConfig()
    assert 'cannot be instantiated' in str(excinfo.value).lower()

def test_type_hinting_and_runtime_check():
    '''
    Ensure that decorated classes are recognized as ConstSpaceType 
    and maintain their identity as class objects.
    '''
    def get_config_version(cfg: ConstSpaceType) -> str:
        return cfg.VERSION

    assert get_config_version(AppConfig) == '1.0.0'
    assert get_config_version(DatabaseConfig) == '5.7'

def test_inheritance_and_mro():
    """
    Verify that the decorator successfully injects the ConstSpace base class
    into the Method Resolution Order (MRO).
    """
    assert issubclass(AppConfig, ConstSpace)
    
    from constspace.core import _ConstSpaceMeta
    assert isinstance(AppConfig, _ConstSpaceMeta)

def test_complex_expressions():
    '''
    Verify that complex logic within the class body is preserved.
    '''
    @constspace
    class MathConstants:
        PI = 3.14159
        TAU = PI * 2
    
    assert MathConstants.TAU == 6.28318

def test_external_modifications_prevention():
    '''
    Verify that even adding new attributes dynamically is prevented.
    '''
    with pytest.raises(AttributeError):
        AppConfig.NEW_VAR = 'not_allowed'