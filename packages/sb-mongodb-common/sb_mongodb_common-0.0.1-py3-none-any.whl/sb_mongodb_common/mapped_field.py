class MappedField:
    name: str
    field_name: str
    field_type: type
    size: int
    precision: int
    ignore: bool
    is_lookup: bool
    is_indexed:bool
    is_unique:bool

    def __str__(self):
        return str(self.name)

    @classmethod
    def mapped_column(cls, name: str = None, field_name: str = None, field_type: type = int,
                      size: int = 50, precision: int = 2, ignore: bool = False,
                      is_lookup: bool = False, is_indexed:bool=False, is_unique:bool=False) -> 'MappedField':
        """Create a MappedField instance with the specified configuration.
        
        Note: The generic type parameter is not used at runtime (Python erases generics),
        so we create a plain MappedField instance.
        """
        # Create instance without type parameter (generics are erased at runtime anyway)
        mapped = MappedField()
        mapped.name = name
        mapped.field_name = field_name or name  # Use field_name if provided, otherwise use name
        mapped.field_type = field_type
        mapped.size = size
        mapped.precision = precision
        mapped.ignore = ignore
        mapped.is_lookup = is_lookup
        mapped.is_indexed = is_indexed
        mapped.is_unique = is_unique

        return mapped
