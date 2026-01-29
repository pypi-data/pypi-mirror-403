from typing import Iterable, Union

from pydantic.fields import FieldInfo

from pydantic_variants.core import DecomposedModel, ModelTransformer, VariantContext


class Tag:
    """Tag class for marking fields with metadata keys.

    Can be used with Annotated or Field(metadata=[...]):
        - Annotated[int, Tag('internal')]  -> stored in field.metadata
        - Field(metadata=[Tag('internal')]) -> stored in json_schema_extra['metadata']

    Convenience constructors for semantic clarity:
        - Tag.exclude('internal') - create tag for exclusion filtering
        - Tag.include('public') - create tag for inclusion filtering
    """

    def __init__(self, key: str):
        self.key = key

    def __eq__(self, other):
        return isinstance(other, Tag) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return f"Tag('{self.key}')"

    @classmethod
    def exclude(cls, key: str) -> "Tag":
        """Create a tag intended for exclusion filtering.

        This is semantically equivalent to Tag(key), but makes the intent clear.

        Example:
            exclude_input = Tag.exclude('exclude_from_input')
            class User(BaseModel):
                password: Annotated[str, exclude_input]  # Will be filtered out
        """
        return cls(key)

    @classmethod
    def include(cls, key: str) -> "Tag":
        """Create a tag intended for inclusion filtering.

        This is semantically equivalent to Tag(key), but makes the intent clear.

        Example:
            public_field = Tag.include('public')
            class User(BaseModel):
                name: Annotated[str, public_field]  # Will be included
        """
        return cls(key)

    def in_field(self, field: FieldInfo) -> bool:
        """Check if this tag is present in the field's metadata.

        Handles both Annotated metadata and Field(metadata=[...]) which
        Pydantic stores in json_schema_extra['metadata'].
        """
        # Check regular metadata (from Annotated)
        if field.metadata:
            if any(isinstance(item, Tag) and item == self for item in field.metadata):
                return True

        # Check json_schema_extra['metadata'] (from Field(metadata=[...]))
        if field.json_schema_extra and isinstance(field.json_schema_extra, dict):
            extra_metadata = field.json_schema_extra.get("metadata", [])
            if any(isinstance(item, Tag) and item == self for item in extra_metadata):  # type: ignore[attr-defined]
                return True

        return False


class FilterTag(ModelTransformer):
    """
    Filters out fields that have Tag instances in their metadata matching the specified keys.

    Searches through field metadata for Tag instances and removes fields where any
    Tag.key matches the provided filter keys.

    Args:
        keys: Single key string, Tag instance, or iterable of key strings/Tags to filter out

    Raises:
        ValueError: If not operating on a DecomposedModel

    Example:
        # Filter fields tagged with 'internal' (string)
        FilterTag('internal')

        # Filter using Tag instance directly
        exclude_input = Tag('exclude_from_input')
        FilterTag(exclude_input)

        # Filter fields tagged with multiple keys
        FilterTag(['internal', 'deprecated', 'admin_only'])

        # Mix Tag instances and strings
        FilterTag([exclude_input, 'deprecated'])

        # Usage with Field metadata
        class User(BaseModel):
            id: int = Field(metadata=[Tag('internal')])
            name: str
            email: str = Field(metadata=[Tag('admin_only')])
    """

    def __init__(self, keys: Union[str, "Tag", Iterable[Union[str, "Tag"]]]):
        if isinstance(keys, str):
            self.filter_keys = {keys}
        elif isinstance(keys, Tag):
            self.filter_keys = {keys.key}
        else:
            # Iterable of strings or Tags
            self.filter_keys = {k.key if isinstance(k, Tag) else k for k in keys}

    def __call__(self, context: VariantContext) -> VariantContext:
        if not isinstance(context.current_variant, DecomposedModel):
            raise ValueError("FilterByTags transformer requires DecomposedModel, got built model")

        new_fields = {}
        for name, field in context.current_variant.model_fields.items():
            if not self._has_matching_tag(field):
                new_fields[name] = field

        context.current_variant.model_fields = new_fields
        return context

    def _has_matching_tag(self, field: FieldInfo) -> bool:
        """Check if field has any Tag in metadata that matches our filter keys.

        Handles both:
        - Annotated[int, Tag('x')] -> stored in field.metadata
        - Field(metadata=[Tag('x')]) -> stored in json_schema_extra['metadata']
        """
        # Check regular metadata (from Annotated)
        if field.metadata:
            for metadata_item in field.metadata:
                if isinstance(metadata_item, Tag) and metadata_item.key in self.filter_keys:
                    return True

        # Check json_schema_extra['metadata'] (from Field(metadata=[...]))
        if field.json_schema_extra and isinstance(field.json_schema_extra, dict):
            extra_metadata = field.json_schema_extra.get("metadata", [])
            for metadata_item in extra_metadata:  # type: ignore[attr-defined]
                if isinstance(metadata_item, Tag) and metadata_item.key in self.filter_keys:
                    return True

        return False
