import datetime
import inspect
import uuid
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from inspect import isclass
from typing import get_type_hints, get_args, get_origin, Any

from bson import ObjectId
from pydantic import BaseModel

from . import Entity
from . import MappedField
from .utils import enum_from_string

# Pre-computed tuples for faster isinstance checks
_PRIMITIVE_TYPES = (str, int, float, bool)
_PRIMITIVE_TYPES_WITH_UUID = (str, int, float, bool, uuid.UUID, datetime.datetime, ObjectId)
_ALL_PRIMITIVE_TYPES = (str, int, float, bool, uuid.UUID, datetime.datetime, datetime.date, datetime.time, ObjectId, Decimal)


# Cache expensive type operations
@lru_cache(maxsize=128)
def _get_cached_type_hints(cls):
    """Cached version of get_type_hints."""
    return get_type_hints(cls)


@lru_cache(maxsize=256)
def _get_cached_args(cls):
    """Cached version of get_args."""
    return get_args(cls)


@lru_cache(maxsize=256)
def _get_cached_origin(cls):
    """Cached version of get_origin."""
    return get_origin(cls)


class Mapper:
    def __init__(self):
        # Cache for enum string conversions
        self._enum_cache = {}
    
    def _enum_to_string(self, enum_obj):
        """Optimized enum to string conversion with caching."""
        enum_type = type(enum_obj)
        if enum_type not in self._enum_cache:
            # Cache the prefix to remove
            prefix = f"{enum_type.__name__}."
            self._enum_cache[enum_type] = prefix
        else:
            prefix = self._enum_cache[enum_type]
        
        enum_str = str(enum_obj)
        if enum_str.startswith(prefix):
            return enum_str[len(prefix):]
        return enum_str

    def map_to_dict_dto(self, obj, visited=None, max_depth=50):
        """Convert object to dictionary, with cycle detection to prevent infinite recursion."""
        if visited is None:
            visited = set()

        # Safety check: prevent excessive recursion depth
        if max_depth <= 0:
            return None

        # Prevent infinite recursion from circular references
        obj_id = id(obj)
        if obj_id in visited:
            return None  # Return None for circular references
        visited.add(obj_id)

        try:
            if isinstance(obj, list):
                new_list = []
                for item in obj:
                    new_item = self.map_entity_to_dict(item, visited)
                    new_list.append(new_item)
                return new_list

            if obj is None:
                return None

            if isinstance(obj, (str, int, float, bool, uuid.UUID, datetime.datetime, ObjectId)):
                return obj

            if isinstance(obj, datetime.date):
                return datetime.datetime(year=obj.year, month=obj.month, day=obj.day)

            if isinstance(obj, datetime.time):
                return datetime.datetime(year=1, month=1, day=1, hour=obj.hour, minute=obj.minute, second=obj.second,
                                         microsecond=obj.microsecond)

            if isinstance(obj, Enum):
                return str(obj).replace("{}.".format(type(obj).__name__), "")

            # Handle Pydantic models - use their built-in serialization
            if hasattr(obj, 'model_dump'):
                # Pydantic v2
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                # Pydantic v1
                return obj.dict()
            elif hasattr(obj, '__pydantic_model__'):
                # Pydantic model class
                return obj.model_dump() if hasattr(obj, 'model_dump') else obj.dict()

            # Check if this is an entity (has MappedField attributes) - use map_entity_to_dict instead
            if not isinstance(obj, dict):
                # Check if object has MappedField attributes (it's an entity)
                # Use a safer check that doesn't iterate through all members
                try:
                    # Check class attributes only, not instance attributes
                    cls = type(obj)
                    has_mapped_fields = any(
                        hasattr(cls, name) and "MappedField" in type(getattr(cls, name)).__name__
                        for name in dir(cls)
                        if not name.startswith("__")
                    )
                    if has_mapped_fields:
                        return self.map_entity_to_dict(obj, visited)
                except Exception:
                    # If check fails, fall through to regular processing
                    pass

                d = {}
                # this is to handle base class members
                # Use dir() instead of getmembers to avoid triggering property accessors
                try:
                    for attr_name in dir(obj):
                        if attr_name.startswith("_") and attr_name != "_id":
                            continue
                        try:
                            attr_value = getattr(obj, attr_name)
                            if not (inspect.ismethod(attr_value) or
                                    inspect.isfunction(attr_value) or
                                    inspect.isbuiltin(attr_value)):
                                # Check if we've already seen this object to prevent cycles
                                attr_id = id(attr_value) if not isinstance(attr_value, (str, int, float, bool,
                                                                                        type(None))) else None
                                if attr_id is None or attr_id not in visited:
                                    d[attr_name] = attr_value
                        except (AttributeError, RuntimeError):
                            # Skip attributes that can't be accessed
                            continue
                except Exception:
                    # Fallback to original method if dir() fails
                    for m in [
                        m
                        for m in inspect.getmembers(obj)
                        if not (m[0].startswith("_") and m[0] != "_id")
                           and not inspect.ismethod(m[1])
                           and not inspect.isfunction(m[1])
                           and not inspect.isbuiltin(m[1])
                    ]:
                        d[m[0]] = m[1]
            else:
                d = obj

            # Process dictionary values with cycle detection
            result = {}
            for key, value in d.items():
                # Check for cycles before processing
                if isinstance(value, (str, int, float, bool, type(None))):
                    result[key] = value
                else:
                    value_id = id(value)
                    if value_id in visited:
                        result[key] = None  # Circular reference
                    else:
                        result[key] = self.map_to_dict_dto(value, visited, max_depth - 1)
            return result
        finally:
            # Remove from visited set when done processing this object
            visited.discard(obj_id)

    def map_entity_to_dict(self, obj, visited=None):
        """Convert entity to dictionary, with cycle detection to prevent infinite recursion."""
        if visited is None:
            visited = set()

        # Early return for None (common case)
        if obj is None:
            return None

        # Prevent infinite recursion from circular references
        obj_id = id(obj)
        if obj_id in visited:
            return None  # Return None for circular references
        visited.add(obj_id)

        try:
            # Handle lists early (common case) - pre-allocate for better performance
            if isinstance(obj, list):
                new_list = [None] * len(obj)
                for i, item in enumerate(obj):
                    new_list[i] = self.map_entity_to_dict(item, visited)
                return new_list

            # Handle primitive types early (most common case)
            if isinstance(obj, _PRIMITIVE_TYPES_WITH_UUID):
                return obj

            # Handle date/time conversions
            if isinstance(obj, datetime.date):
                return datetime.datetime(year=obj.year, month=obj.month, day=obj.day)

            if isinstance(obj, datetime.time):
                return datetime.datetime(year=1, month=1, day=1, hour=obj.hour, minute=obj.minute,
                                         second=obj.second, microsecond=obj.microsecond)

            if isinstance(obj, Decimal):
                return str(obj)

            if isinstance(obj, Enum):
                return self._enum_to_string(obj)

        finally:
            # Remove from visited set when done processing this object
            visited.discard(obj_id)

        if isinstance(obj, dict):
            return obj

        # Handle entities
        if not isinstance(obj, Entity):
            raise Exception("Not an entity!")

        # Get class-level MappedField definitions (already cached in Entity class)
        class_fields = type(obj).get_mapped_fields()

        # Pre-allocate dictionary
        d = {}
        
        for attr_name, mapped_field in class_fields.items():
            # Early skip for ignored/lookup fields (most common skip case)
            if mapped_field.ignore or mapped_field.is_lookup:
                continue

            attr_value = getattr(obj, attr_name)
            d[attr_name] = self.map_entity_to_dict(attr_value, visited)

        return d

    def map_entity_to_raw_dict(self, obj, visited=None):
        """Convert entity to dictionary, with cycle detection to prevent infinite recursion."""
        if visited is None:
            visited = set()

        # Early return for None
        if obj is None:
            return None

        # Prevent infinite recursion from circular references
        obj_id = id(obj)
        if obj_id in visited:
            return None  # Return None for circular references
        visited.add(obj_id)

        try:
            # Handle lists early - pre-allocate for better performance
            if isinstance(obj, list):
                new_list = [None] * len(obj)
                for i, item in enumerate(obj):
                    new_list[i] = self.map_entity_to_raw_dict(item, visited)
                return new_list

            # Handle all primitive types - convert to string
            if isinstance(obj, _ALL_PRIMITIVE_TYPES):
                return str(obj)

            if isinstance(obj, Enum):
                return self._enum_to_string(obj)

        finally:
            # Remove from visited set when done processing this object
            visited.discard(obj_id)

        # Handle entities
        if not isinstance(obj, Entity):
            raise Exception("Not an entity!")

        # Get class-level MappedField definitions (already cached in Entity class)
        class_fields = type(obj).get_mapped_fields()
        
        d = {}
        
        for attr_name, mapped_field in class_fields.items():
            # Early skip for ignored/lookup fields
            if mapped_field.ignore or mapped_field.is_lookup:
                continue

            attr_value = getattr(obj, attr_name)
            d[attr_name] = self.map_entity_to_raw_dict(attr_value, visited)

        return d

    def map_to_object_dto(self, source_obj, cls):
        if type(source_obj) is list:
            new_list = []
            element_cls = get_args(cls)
            for item in source_obj:
                new_item = self.map_to_object_dto(item, cls=element_cls[0])
                new_list.append(new_item)
            return new_list

        if cls == uuid.UUID:
            if isinstance(source_obj, uuid.UUID):
                return source_obj
            else:
                return uuid.UUID(source_obj)

        if cls == datetime.datetime:
            if isinstance(source_obj, datetime.datetime):
                return source_obj
            else:
                # 2023-10-12 15:49:22.634236
                return datetime.datetime.strptime(source_obj, '%Y-%m-%d %H:%M:%S.%f')

        if cls == datetime.date:
            if isinstance(source_obj, datetime.datetime):
                return datetime.date(source_obj.year, source_obj.month, source_obj.day)
            else:
                # 2023-10-12 15:49:22.634236
                return datetime.date.fromisoformat(source_obj)

        if cls == datetime.time:
            if isinstance(source_obj, datetime.datetime):
                return datetime.time(source_obj.hour, source_obj.minute, source_obj.second, source_obj.microsecond)
            else:
                # 2023-10-12 15:49:22.634236
                return datetime.time.fromisoformat(source_obj)

        if cls == ObjectId:
            if isinstance(source_obj, ObjectId):
                return source_obj
            else:
                return ObjectId(source_obj)

        if isclass(cls) and issubclass(cls, Enum):
            return cls[source_obj]

        if cls in (str, int, float, bool):
            if isinstance(source_obj, ObjectId):
                return str(source_obj)
            else:
                return source_obj

        new_obj = cls()

        if not isinstance(source_obj, dict):
            if isinstance(cls, type(None)):
                return source_obj
            else:
                return cls(source_obj)

        # Type guard: source_obj is now guaranteed to be a dict
        assert isinstance(source_obj, dict), "source_obj must be a dict at this point"
        source_dict: dict = source_obj

        # Use cached type hints (expensive operation)
        type_hint = _get_cached_type_hints(cls)

        for key in type_hint.keys():
            prop_cls = type_hint.get(key)
            if prop_cls is None:
                continue

            value = source_dict.get(key)

            if value is None:
                continue

            new_obj.__dict__[key] = self.map_to_object_dto(value, prop_cls)

        return new_obj   

    def map_dict_to_entity(self, source_obj, cls, context):
        # Optimized list type detection using get_origin instead of string check
        origin = _get_cached_origin(cls)
        if origin is list:
            new_list = []
            element_cls = _get_cached_args(cls)
            if element_cls:
                element_type = element_cls[0]
                for item in source_obj:
                    new_list.append(self.map_dict_to_entity(item, element_type, context))
            else:
                # Fallback if we can't determine element type
                new_list.extend(source_obj)
            return new_list

        if cls == uuid.UUID:
            if isinstance(source_obj, uuid.UUID):
                return source_obj
            elif source_obj:
                return uuid.UUID(source_obj)
            return None

        if cls == datetime.datetime:
            if isinstance(source_obj, datetime.datetime):
                return source_obj
            elif isinstance(source_obj, str) and source_obj:
                try:
                    return datetime.datetime.strptime(source_obj, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    return datetime.datetime.fromisoformat(source_obj.replace('Z', '+00:00'))
            return None

        if cls == datetime.date:
            if isinstance(source_obj, datetime.date):
                return source_obj
            elif isinstance(source_obj, datetime.datetime):
                return datetime.date(source_obj.year, source_obj.month, source_obj.day)
            elif isinstance(source_obj, str) and source_obj:
                return datetime.date.fromisoformat(source_obj)
            return None

        if cls == datetime.time:
            if isinstance(source_obj, datetime.time):
                return source_obj
            elif isinstance(source_obj, datetime.datetime):
                return datetime.time(source_obj.hour, source_obj.minute, source_obj.second, source_obj.microsecond)
            elif isinstance(source_obj, str) and source_obj:
                return datetime.time.fromisoformat(source_obj)
            return None

        if cls == ObjectId:
            if isinstance(source_obj, ObjectId):
                return source_obj
            elif source_obj:
                return ObjectId(source_obj)
            return None

        if isclass(cls) and issubclass(cls, Enum):
            if source_obj:
                return enum_from_string(cls, source_obj)
            return None

        # Handle primitive types early (most common case)
        if cls in _PRIMITIVE_TYPES:
            return source_obj

        new_obj = cls()

        if not isinstance(source_obj, dict):
            if isinstance(cls, type(None)):
                return source_obj
            elif source_obj is None:
                return None
            else:
                return cls(source_obj)

        # Get MappedField definitions from class
        class_fields = cls.get_mapped_fields()

        # Process each MappedField
        for attr_name, mapped_field in class_fields.items():
            # Skip ignored fields
            if mapped_field.ignore:
                continue

            # Skip lookup fields - they reference ObjectId fields that are set separately
            # Lookup fields use field_name to point to the ObjectId field (e.g., user -> user_id)
            # The ObjectId field itself will be processed in a separate iteration
            # Lookup fields are loaded later via lazy loading or RepositoryContext
            if mapped_field.is_lookup:
                # Optimize dictionary lookup
                field_name = mapped_field.field_name
                source_value = source_obj.get(field_name)
                
                if source_value is None:
                    continue
                    
                if isinstance(source_value, list):
                    # List lookup - pre-allocate list
                    mapped_field.value = []
                    element_cls = _get_cached_args(mapped_field.field_type)[0]
                    repo = context.get_repository(element_cls)
                    for obj_id in source_value:
                        obj = repo.get_by_id(obj_id, context)
                        if obj:  # Only append if found
                            mapped_field.value.append(obj)
                else:
                    # Single lookup
                    repo = context.get_repository(mapped_field.field_type)
                    obj = repo.get_by_id(source_value, context)
                    mapped_field.value = obj

            else:
                # Use field_name to get value from source (or fallback to attr_name)
                # Optimize dictionary lookup - try field_name first, then attr_name
                dict_key = mapped_field.field_name or attr_name
                source_value = source_obj.get(dict_key) or source_obj.get(attr_name)
                
                if source_value is None:
                    continue  # Field not in source, skip

                # Map the value using field_type
                mapped_value = self.map_dict_to_entity(source_value, mapped_field.field_type, context)
                setattr(new_obj, attr_name, mapped_value)

        return new_obj

    def map_model_to_entity(self, source_obj, entity_cls, context) -> Any:
        """Convert a Pydantic model to an entity instance."""
        if isinstance(source_obj, list):
            new_list = []
            element_cls = get_args(entity_cls)
            if element_cls:
                for item in source_obj:
                    new_item = self.map_model_to_entity(item, element_cls[0], context)
                    new_list.append(new_item)
            return new_list

        if source_obj is None:
            return None

        # Handle primitive types
        if isinstance(source_obj, (str, int, float, bool, uuid.UUID, datetime.datetime, ObjectId)):
            # Convert string to ObjectId if needed
            if isinstance(source_obj, str) and entity_cls == ObjectId:
                return ObjectId(source_obj) if source_obj else None
            return source_obj

        if isinstance(source_obj, datetime.date):
            # If entity expects datetime, convert date to datetime
            if entity_cls == datetime.datetime:
                return datetime.datetime(year=source_obj.year, month=source_obj.month, day=source_obj.day)
            return source_obj

        if isinstance(source_obj, datetime.time):
            # If entity expects datetime, convert time to datetime
            if entity_cls == datetime.datetime:
                return datetime.datetime(year=1, month=1, day=1, hour=source_obj.hour, minute=source_obj.minute,
                                         second=source_obj.second, microsecond=source_obj.microsecond)
            return source_obj

        if isinstance(source_obj, Enum):
            return source_obj

        # Handle Pydantic models - convert to dict first, then process
        if isinstance(source_obj, BaseModel):
            # Convert Pydantic model to dict
            if hasattr(source_obj, 'model_dump'):
                # Pydantic v2
                source_dict = source_obj.model_dump()
            elif hasattr(source_obj, 'dict'):
                # Pydantic v1
                source_dict = source_obj.dict()
            else:
                source_dict = source_obj.__dict__
        elif isinstance(source_obj, dict):
            source_dict = source_obj
        else:
            # Not a model or dict, try to use as-is
            return source_obj

        # Create new entity instance
        new_entity = entity_cls()

        # Get MappedField definitions from entity class hierarchy
        entity_class_fields = entity_cls.get_mapped_fields()

        # Handle _id specially - map from 'id' in model
        if '_id' in entity_class_fields:
            mapped_field = entity_class_fields['_id']
            if not mapped_field.ignore and not mapped_field.is_lookup:
                # Get 'id' from model (or '_id' as fallback)
                id_value = source_dict.get('id') or source_dict.get('_id')
                if id_value:
                    # Convert string to ObjectId
                    if isinstance(id_value, str) and id_value:
                        try:
                            new_entity._id = ObjectId(id_value)
                        except Exception:
                            new_entity._id = id_value
                    elif isinstance(id_value, ObjectId):
                        new_entity._id = id_value
                    else:
                        new_entity._id = id_value

        # Process each MappedField
        for attr_name, mapped_field in entity_class_fields.items():
            # Skip _id since we handled it above
            if attr_name == '_id':
                continue

            # Skip ignored fields
            if mapped_field.ignore:
                continue

            # Handle lookup fields - extract ID from model and set ObjectId field
            if mapped_field.is_lookup:
                # Lookup fields in model (e.g., user: UserModel) should have their ID extracted
                # and set to the corresponding ObjectId field (e.g., user_id)
                # The field_name points to the ObjectId field name
                object_id_field_name = mapped_field.field_name

                # Check if field_type is a list type (list[EntityType])
                is_list_type = False
                if hasattr(mapped_field.field_type, '__origin__'):
                    origin = get_origin(mapped_field.field_type)
                    is_list_type = (origin is list)
                elif mapped_field.field_type is list:
                    is_list_type = True

                # Check if model has the lookup field (e.g., 'user' or 'locations')
                if attr_name in source_dict:
                    lookup_value = source_dict[attr_name]

                    if is_list_type:
                        # Handle list lookup fields (e.g., locations: list[LocationModel])
                        if lookup_value and isinstance(lookup_value, list):
                            # Extract IDs from all models in the list
                            object_id_list = []
                            for lookup_model in lookup_value:
                                if lookup_model is not None:
                                    # Extract ID from the model
                                    if isinstance(lookup_model, BaseModel):
                                        lookup_id = getattr(lookup_model, 'id', None) or getattr(lookup_model, '_id',
                                                                                                 None)
                                    elif isinstance(lookup_model, dict):
                                        lookup_id = lookup_model.get('id') or lookup_model.get('_id')
                                    else:
                                        lookup_id = lookup_model

                                    if lookup_id:
                                        # Convert to ObjectId if it's a string
                                        if isinstance(lookup_id, str):
                                            try:
                                                object_id_list.append(ObjectId(lookup_id))
                                            except Exception:
                                                object_id_list.append(lookup_id)
                                        elif isinstance(lookup_id, ObjectId):
                                            object_id_list.append(lookup_id)
                                        else:
                                            object_id_list.append(lookup_id)

                            # Set the ObjectId list field (e.g., location_ids)
                            setattr(new_entity, object_id_field_name, object_id_list)
                    else:
                        # Handle single lookup field (e.g., user: UserModel)
                        if lookup_value is not None:
                            # Extract ID from the model
                            if isinstance(lookup_value, BaseModel):
                                lookup_id = getattr(lookup_value, 'id', None) or getattr(lookup_value, '_id', None)
                            elif isinstance(lookup_value, dict):
                                lookup_id = lookup_value.get('id') or lookup_value.get('_id')
                            else:
                                lookup_id = lookup_value

                            # Convert to ObjectId if it's a string
                            if lookup_id:
                                if isinstance(lookup_id, str):
                                    try:
                                        object_id_value = ObjectId(lookup_id)
                                    except Exception:
                                        object_id_value = lookup_id
                                elif isinstance(lookup_id, ObjectId):
                                    object_id_value = lookup_id
                                else:
                                    object_id_value = lookup_id

                                # Set the ObjectId field (e.g., user_id)
                                setattr(new_entity, object_id_field_name, object_id_value)

                continue

            # Handle regular (non-lookup) fields
            # Use field_name to get value from source (or fallback to attr_name)
            dict_key = mapped_field.field_name if mapped_field.field_name else attr_name

            # Get value from source dictionary
            if dict_key in source_dict:
                source_value = source_dict[dict_key]
            elif attr_name in source_dict:
                source_value = source_dict[attr_name]
            else:
                continue  # Field not in source, skip

            # Map the value using field_type
            mapped_value = self.map_model_to_entity(source_value, mapped_field.field_type, context)

            # Set the value - check if class uses .value pattern or direct assignment
            if hasattr(new_entity, attr_name):
                attr_instance = getattr(new_entity, attr_name)
                if isinstance(attr_instance, MappedField):
                    attr_instance.value = mapped_value
                else:
                    # Direct assignment (for classes like User, Location)
                    setattr(new_entity, attr_name, mapped_value)
            else:
                # Attribute doesn't exist yet, set directly
                setattr(new_entity, attr_name, mapped_value)

        return new_entity

    def map_entity_to_model(self, obj, model_cls, context) -> Any:
        if isinstance(obj, list):
            new_list = []
            element_cls = get_args(model_cls)
            if element_cls:
                for item in obj:
                    new_item = self.map_entity_to_model(item, element_cls[0], context)
                    new_list.append(new_item)
            return new_list

        if obj is None:
            return None

        # Handle primitive types
        if isinstance(obj, (str, int, float, bool, uuid.UUID, datetime.datetime, ObjectId)):
            # Convert ObjectId to string for model
            if isinstance(obj, ObjectId):
                return str(obj)
            return obj

        if isinstance(obj, datetime.date):
            return datetime.datetime(year=obj.year, month=obj.month, day=obj.day)

        if isinstance(obj, datetime.time):
            return datetime.datetime(year=1, month=1, day=1, hour=obj.hour, minute=obj.minute,
                                     second=obj.second, microsecond=obj.microsecond)

        if isinstance(obj, Enum):
            return str(obj).replace("{}.".format(type(obj).__name__), "")

        # if isinstance(obj, MappedField):
        #     # Skip ignored fields
        #     if obj.ignore:
        #         return None
        #
        #     if obj.is_lookup:
        #         return None
        #
        #     # Handle special types
        #     if obj.field_type == datetime.date:
        #         if obj.value is None:
        #             return None
        #         return datetime.datetime(year=obj.value.year, month=obj.value.month, day=obj.value.day)
        #     elif obj.field_type == datetime.time:
        #         if obj.value is None:
        #             return None
        #         return datetime.datetime(year=1, month=1, day=1, hour=obj.value.hour, minute=obj.value.minute,
        #                                  second=obj.value.second, microsecond=obj.value.microsecond)
        #     elif hasattr(obj, "value") and isinstance(obj.value, Enum):
        #         return str(obj.value).replace("{}.".format(type(obj.value).__name__), "")
        #     elif hasattr(obj, "value"):
        #         # Recursively process complex values, but check for primitives first
        #         value = obj.value
        #         if isinstance(value, (str, int, float, bool, uuid.UUID, datetime.datetime, ObjectId, datetime.date,
        #                               datetime.time, Enum)):
        #             # Convert ObjectId to string for model
        #             if isinstance(value, ObjectId):
        #                 return str(value)
        #             return value
        #         # For complex objects, recursively process
        #         return self.map_entity_to_model(value, obj.field_type, context)
        #     else:
        #         return None

        # Create new model instance
        new_obj = model_cls()

        # Get MappedField definitions from entity class hierarchy
        entity_class_fields = type(obj).get_mapped_fields()
        # for entity_cls in type(obj).__mro__:
        #     for name, attr in inspect.getmembers(entity_cls):
        #         if "MappedField" in type(attr).__name__ and name not in entity_class_fields:
        #             entity_class_fields[name] = attr

        # Get model field names from type hints
        model_type_hints = get_type_hints(model_cls)

        # Handle _id specially - map to 'id' in model
        if hasattr(obj, '_id') and '_id' in entity_class_fields:
            mapped_field = entity_class_fields['_id']
            if not mapped_field.ignore and not mapped_field.is_lookup:
                attr_value = getattr(obj, '_id', None)
                if attr_value is not None:
                    # Convert ObjectId to string
                    # if isinstance(attr_value, ObjectId):
                    #     id_value = str(attr_value)

                    id_value = str(attr_value) if not isinstance(attr_value, str) else attr_value

                    # Set 'id' field in model (not '_id')
                    if 'id' in model_type_hints:
                        setattr(new_obj, 'id', id_value)

        # Process other instance members
        for n, f in entity_class_fields.items():
            attr_name = n
            try:
                attr_value = getattr(obj, attr_name)

                # Skip _id since we handled it above
                if attr_name == '_id':
                    continue

                # Check if this field has a MappedField definition
                mapped_field = entity_class_fields.get(attr_name)

                if mapped_field:
                    # Skip ignored fields
                    if mapped_field.ignore:
                        continue

                    # Determine the model field name (use attr_name, or check if there's a mapping)
                    # For now, assume model field name matches entity attribute name
                    model_field_name = attr_name

                    # Check if model has this field
                    if model_field_name not in model_type_hints:
                        continue

                    # Handle lookup fields - they reference other entities
                    if mapped_field.is_lookup:
                        # Get the expected model type from the model's type hints
                        expected_model_type = model_type_hints[model_field_name]

                        # Check if the lookup field has been loaded (has a value)
                        if isinstance(attr_value, MappedField):
                            lookup_value = attr_value.value
                        else:
                            # Direct value - might be the loaded entity
                            lookup_value = attr_value

                        if lookup_value is not None:
                            # Map the loaded entity/entities to the model
                            # The expected_model_type might be a generic like list[UserModel]
                            # map_entity_to_model handles this by checking isinstance(obj, list) first
                            mapped_value = self.map_entity_to_model(lookup_value, expected_model_type, context)
                            if mapped_value is not None:
                                setattr(new_obj, model_field_name, mapped_value)
                        # If not loaded, leave as None/empty list (don't auto-load)
                        continue

                    # Handle regular (non-lookup) fields
                    # Handle the value - could be MappedField or direct value
                    if isinstance(attr_value, MappedField):
                        # Value is a MappedField, process its value
                        mapped_value = self.map_entity_to_model(attr_value, mapped_field.field_type, context)
                    else:
                        # Direct value assignment, process it
                        mapped_value = self.map_entity_to_model(attr_value, mapped_field.field_type, context)

                    # Set the value on the model
                    if mapped_value is not None:
                        setattr(new_obj, model_field_name, mapped_value)
            except Exception as e:
                # skip missing attribute
                ...

        return new_obj
