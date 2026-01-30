import sys
from enum import Enum

from pymongo.synchronous.database import Database

# Type cache for frequently used types
_type_cache: dict[str, type | None] = {}


def get_custom_type(type_name):
    """Retrieves a custom class type from its string name by searching all loaded modules.
    
    Uses an internal cache to speed up repeated lookups of the same type.
    
    Args:
        type_name: The string name of the type to retrieve
        
    Returns:
        The type class if found, None otherwise
    """
    # Check cache first
    if type_name in _type_cache:
        return _type_cache[type_name]
    
    # First check the current module's globals
    if type_name in globals() and isinstance(globals()[type_name], type):
        result = globals()[type_name]
        _type_cache[type_name] = result
        return result
    
    # Search through all loaded modules
    for module_name, module in sys.modules.items():
        # Skip None modules and built-in modules (those without dots are typically built-ins)
        if module is None:
            continue
        
        # Skip modules that start with underscore (internal/private modules)
        # but allow modules like '__main__' if they have dots
        if module_name.startswith('_') and '.' not in module_name:
            continue
        
        try:
            # Check if the type exists in this module's globals
            if hasattr(module, type_name):
                attr = getattr(module, type_name)
                if isinstance(attr, type):
                    _type_cache[type_name] = attr
                    return attr
        except (AttributeError, ImportError, TypeError):
            # Skip modules that can't be accessed
            continue
    
    # Cache None result to avoid repeated searches for non-existent types
    _type_cache[type_name] = None
    return None


def clear_type_cache():
    """Clears the type cache. Useful for testing or when modules are reloaded."""
    global _type_cache
    _type_cache.clear()



def collection_exists(db:Database, name:str)->bool:
    if name in db.list_collection_names():
        return True
    return False

def enum_from_string(enum_class: type[Enum], value: str, case_sensitive: bool = False) -> Enum | None:
    """Convert a string to an Enum value, optionally case-insensitive.
    
    Args:
        enum_class: The Enum class to search in
        value: The string value to convert
        case_sensitive: If False, performs case-insensitive matching
        
    Returns:
        The matching Enum member, or None if not found
        
    Example:
        >>> class Status(Enum):
        ...     ACTIVE = "Active"
        ...     INACTIVE = "Inactive"
        >>> enum_from_string(Status, "active")  # Returns Status.ACTIVE
        >>> enum_from_string(Status, "ACTIVE")  # Returns Status.ACTIVE
        >>> enum_from_string(Status, "invalid")  # Returns None
    """
    if not isinstance(value, str):
        return None
    
    if case_sensitive:
        # Direct lookup
        try:
            return enum_class[value]
        except KeyError:
            # Try by value
            for member in enum_class:
                if str(member.value) == value:
                    return member
            return None
    else:
        # Case-insensitive lookup
        value_lower = value.lower()
        for member in enum_class:
            # Match by name (case-insensitive)
            if member.name.lower() == value_lower:
                return member
            # Match by value (case-insensitive)
            if str(member.value).lower() == value_lower:
                return member
        return None