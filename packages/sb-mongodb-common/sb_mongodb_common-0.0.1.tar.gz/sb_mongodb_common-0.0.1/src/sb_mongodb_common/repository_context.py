from __future__ import annotations

from . import Repository

"""
Repository Context Pattern - Provides access to repositories and centralized relationship loading.
Eliminates duplication of lazy-loading code across services.
"""

from pymongo.database import Database

# Use module-level variable instead of class variable - more resilient to Flask's reloader
# Module-level variables are less likely to be reset by the reloader
_repository_map: dict[str, type] = {}


class RepositoryContext:
    """
    Context that provides access to all repositories and centralized relationship loading.
    Created at the application/service layer and passed to repositories/services when needed.
    """

    def __init__(self, db: Database):
        self.db = db
        self._repositories: dict[str, Repository] = {}

    @staticmethod
    def register(entity_type: type, repo_type: type):
        print(f"Registering: {entity_type.__name__} to {repo_type.__name__}")
        type_name = entity_type.__name__
        _repository_map[type_name] = repo_type

    @staticmethod
    def get_repository_map():
        """Get the repository map (for debugging/access)."""
        return _repository_map

    def get_repository(self, entity_type: type) -> Repository:
        """Get a repository by type. Lazy-loads repositories on first access."""
        type_name = entity_type.__name__
        if type_name not in self._repositories:
            # find map
            repo_type = _repository_map.get(type_name)
            if repo_type:
                self._repositories[type_name] = repo_type(self.db)
            else:
                raise Exception(
                    f"Repository {type_name} map not found, check registration. Available: {list(_repository_map.keys())}")

        return self._repositories.get(type_name)
