from typing import get_args, get_origin

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database

from . import Entity
from . import MappedField
from . import Mapper
from .utils import collection_exists


class Repository[T:Entity]:
    collection: Collection
    serializer: Mapper

    def __init__(self, db: Database, collection: str):
        self.collection = db[collection]
        # self.entity_type = get_args(self.__orig_bases__[0])[0]
        self.entity_type = self._get_entity_type()
        self.serializer = Mapper()

    @classmethod
    def _get_entity_type(cls):
        """Extract the entity type from the generic type parameter.
        
        Works with Python 3.12+ generic syntax: class UserRepository(Repository[User])
        """
        # For Python 3.12+ generics, check __orig_bases__ first
        if hasattr(cls, '__orig_bases__') and cls.__orig_bases__:
            for base in cls.__orig_bases__:
                # Check if this base is a generic type (has __origin__)
                origin = get_origin(base)
                if origin is Repository or origin is None:
                    args = get_args(base)
                    if args and len(args) > 0:
                        return args[0]

        # Fallback: Check if class itself is parameterized
        if hasattr(cls, '__args__'):
            args = get_args(cls)
            if args:
                return args[0]

        raise TypeError(
            f"Cannot determine entity type for {cls.__name__}. "
            f"Ensure the class inherits from Repository[EntityType], "
            f"e.g., class {cls.__name__}(Repository[YourEntity])"
        )

    def get_by_id(self, id: ObjectId, context) -> T | None:
        dc = self.collection.find_one({"_id": id})
        if dc:
            item = self.serializer.map_dict_to_entity(dc, self.entity_type, context)
            return item
        return None

    def add(self, item: T):
        dc = self.serializer.map_entity_to_dict(item)
        if not collection_exists(self.collection.database, self.collection.name):
            self.collection.database.create_collection(self.collection.name)

            # get fields
            fields: dict[str, MappedField] = self.entity_type.get_mapped_fields()

            # get indexes
            for index_field in [f for n,f in fields.items() if f.is_indexed]:
                self.collection.create_index([(index_field.field_name, 1)], unique=index_field.is_unique)

        self.collection.insert_one(dc)

    def find_many(self, field: str, criteria: list, context) -> list[T]:
        dc = self.collection.find({field: {"$in": criteria}})
        if dc:
            results = [self.serializer.map_dict_to_entity(item, self.entity_type, context) for item in dc]
            return results
        return []

    def find_one(self, criteria: dict, context) -> T | None:
        dc = self.collection.find_one(criteria)
        if dc:
            item = self.serializer.map_dict_to_entity(dc, self.entity_type, context)
            return item
        return None

    def find_all(self, criteria: dict, context) -> list[T]:
        dc = self.collection.find(criteria).to_list()
        if dc:
            results = [self.serializer.map_dict_to_entity(item, self.entity_type, context) for item in dc]
            return results
        return []

    def find_multiple(self, search_criteria: str, context) -> list[T]:
        dc = self.collection.find({"$text": {"$search": search_criteria}}).to_list()
        if dc:
            item = self.serializer.map_dict_to_entity(dc, self.entity_type, context)
            return item
        return []

    def update(self, item: T):
        dc = self.serializer.map_entity_to_dict(item)
        self.collection.update_one(filter={"_id": item._id}, update={"$set": dc})

    def delete(self, item: T):
        self.collection.delete_one(filter={"_id": item._id})

    def create_fake(self, **kwargs) -> T:
        ...

    def get_random(self, context) -> T | None:
        """Get a random document from the collection."""
        pipeline = [{"$sample": {"size": 1}}]
        cursor = self.collection.aggregate(pipeline)
        try:
            dc = cursor.next()
            item = self.serializer.map_dict_to_entity(dc, self.entity_type, context)
            return item
        except StopIteration:
            return None
