from copy import copy
import logging
from typing import Any, Callable, Protocol

from pydantic import BaseModel, computed_field, field_validator, model_validator, field_serializer, model_serializer
from pydantic.fields import FieldInfo
from pydantic._internal._model_construction import ModelMetaclass

# Default null logger that does nothing
_null_logger = logging.getLogger("pydantic_variants.null")
_null_logger.addHandler(logging.NullHandler())


class VariantPipe:
    """
    Used to compose variant creation flows by chaining operations.
    remember to supply a VariantContext in the beginning of the pipeline.
    and ExtractVariant at the end to get the final model.

    This is an immutable pipeline that holds an ordered tuple of operations (functions).
    Supports list-like operations but returns new instances for immutability.

    Args:
        *operations: Callable operations to chain in the pipeline
        logger: Optional logger for debug output
        debug: If True, enables debug logging (requires logger)
    """

    def __init__(self, *operations: Callable, logger: logging.Logger | None = None, debug: bool = False):
        self._operations: tuple[Callable, ...] = tuple(operations)
        self._logger = logger or _null_logger
        self._debug = debug

    def __call__(self, obj: Any) -> Any:
        """Execute all operations sequentially on the input object"""
        if self._debug:
            model_name = obj.__name__ if hasattr(obj, "__name__") else str(obj)
            self._logger.debug(f"Starting pipeline on {model_name} with {len(self._operations)} operations")

        for i, operation in enumerate(self._operations):
            op_name = operation.__class__.__name__ if hasattr(operation, "__class__") else str(operation)
            if self._debug:
                self._logger.debug(f"  [{i + 1}/{len(self._operations)}] Executing {op_name}")

            obj = operation(obj)

            if self._debug and hasattr(obj, "current_variant"):
                # Log current state after transformer
                if hasattr(obj.current_variant, "model_fields"):
                    fields = list(obj.current_variant.model_fields.keys())
                    self._logger.debug(f"    -> Fields after {op_name}: {fields}")
                elif hasattr(obj.current_variant, "__name__"):
                    self._logger.debug(f"    -> Built model: {obj.current_variant.__name__}")

        if self._debug:
            self._logger.debug("Pipeline completed")

        return obj

    def append(self, operation: Callable) -> "VariantPipe":
        """Return a new pipeline with the operation appended"""
        return VariantPipe(*self._operations, operation, logger=self._logger, debug=self._debug)

    def insert(self, index: int, operation: Callable) -> "VariantPipe":
        """Return a new pipeline with the operation inserted at the given index"""
        ops = list(self._operations)
        ops.insert(index, operation)
        return VariantPipe(*ops, logger=self._logger, debug=self._debug)

    def replace(self, index: int, operation: Callable) -> "VariantPipe":
        """Return a new pipeline with the operation at index replaced"""
        ops = list(self._operations)
        ops[index] = operation
        return VariantPipe(*ops, logger=self._logger, debug=self._debug)

    def with_debug(self, logger: logging.Logger, debug: bool = True) -> "VariantPipe":
        """Return a new pipeline with debug logging enabled"""
        return VariantPipe(*self._operations, logger=logger, debug=debug)

    def __getitem__(self, key: int | slice) -> Callable | "VariantPipe":
        """Support indexing and slicing"""
        if isinstance(key, slice):
            return VariantPipe(*self._operations[key])
        return self._operations[key]

    def __len__(self) -> int:
        """Return the number of operations in the pipeline"""
        return len(self._operations)

    def __iter__(self):
        """Allow iteration over operations"""
        return iter(self._operations)

    def __repr__(self) -> str:
        return f"VariantPipe({', '.join(op.__name__ if hasattr(op, '__name__') else str(op) for op in self._operations)})"


class DecomposedModel:
    """
    Represents a deconstructed Pydantic model that can be modified and rebuilt.

    Preserves:
    - model_fields: Field definitions
    - model_config: Model configuration
    - computed_fields: @computed_field decorated properties
    - field_validators: @field_validator decorated methods
    - model_validators: @model_validator decorated methods
    - field_serializers: @field_serializer decorated methods
    - model_serializers: @model_serializer decorated methods
    - private_attributes: PrivateAttr fields
    - class_methods: Regular methods, classmethods, staticmethods
    """

    model_fields: dict[str, FieldInfo]
    model_config: dict
    original_model_cls: type[BaseModel]
    model_doc: str | None

    def __init__(self, model_cls: type[BaseModel]):
        self.model_fields = copy(model_cls.model_fields)
        self.model_config = copy(model_cls.model_config)  # type: ignore
        self.original_model_cls = model_cls
        self.model_doc = model_cls.__doc__ or None

        # Store decorator info for rebuilding
        # Deep copy to avoid modifying the original model's decorators
        from pydantic._internal._decorators import DecoratorInfos
        original_dec = model_cls.__pydantic_decorators__
        self._pydantic_decorators = DecoratorInfos(
            validators=copy(original_dec.validators),
            field_validators=copy(original_dec.field_validators),
            root_validators=copy(original_dec.root_validators),
            field_serializers=copy(original_dec.field_serializers),
            model_serializers=copy(original_dec.model_serializers),
            model_validators=copy(original_dec.model_validators),
            computed_fields=copy(original_dec.computed_fields),
        )

        # Store private attributes
        self._private_attributes = copy(model_cls.__private_attributes__)

        # Store regular methods (non-field, non-validator, non-decorator)
        self._class_methods: dict[str, Any] = {}
        reserved_names = (
            set(model_cls.model_fields.keys())
            | set(self._pydantic_decorators.computed_fields.keys())
            | set(self._pydantic_decorators.field_validators.keys())
            | set(self._pydantic_decorators.model_validators.keys())
            | set(self._pydantic_decorators.field_serializers.keys())
            | set(self._pydantic_decorators.model_serializers.keys())
            | {"model_config", "variants"}  # Also exclude variants dict
        )
        for name in model_cls.__dict__:
            if name.startswith("_"):
                continue
            if name in reserved_names:
                continue
            value = model_cls.__dict__[name]
            # Skip class types (these are attached variant classes like User.Input)
            if isinstance(value, type):
                continue
            if callable(value) or isinstance(value, (classmethod, staticmethod)):
                self._class_methods[name] = value

    def build(self, name: str, base: Any = None) -> type[BaseModel]:
        """
        Build a new Pydantic model class from the decomposed components.

        Args:
            name: Suffix to append to the original model name
            base: Optional base class (defaults to BaseModel)

        Returns:
            A new Pydantic model class with all preserved features
        """
        base = base or BaseModel

        # Build namespace with annotations
        # Add json_schema_mode_override to ensure computed fields appear in OpenAPI schemas
        config = copy(self.model_config)
        if 'json_schema_mode_override' not in config:
            config['json_schema_mode_override'] = 'serialization'
        
        namespace: dict[str, Any] = {
            "__module__": self.original_model_cls.__module__,
            "__annotations__": {},
            "__doc__": self.model_doc,
            "model_config": config,
        }

        # Add field annotations and FieldInfo objects
        for field_name, field_info in self.model_fields.items():
            namespace["__annotations__"][field_name] = field_info.annotation
            namespace[field_name] = field_info

        # Add private attributes
        for attr_name, private_attr in self._private_attributes.items():
            namespace[attr_name] = private_attr

        # Re-apply computed_field decorators
        for cf_name, dec in self._pydantic_decorators.computed_fields.items():
            prop = dec.info.wrapped_property
            # Recreate the computed_field with all its options
            cf_kwargs = {
                "return_type": dec.info.return_type,
                "alias": dec.info.alias,
                "alias_priority": dec.info.alias_priority,
                "title": dec.info.title,
                "description": dec.info.description,
                "json_schema_extra": dec.info.json_schema_extra,
                "repr": dec.info.repr,
            }
            # Filter out None values
            cf_kwargs = {k: v for k, v in cf_kwargs.items() if v is not None}
            namespace[cf_name] = computed_field(**cf_kwargs)(prop)

        # Re-apply field_validator decorators (only for fields that still exist)
        remaining_fields = set(self.model_fields.keys())
        for fv_name, dec in self._pydantic_decorators.field_validators.items():
            # Only include validators for fields that still exist
            target_fields = tuple(f for f in dec.info.fields if f in remaining_fields or f == "*")
            if not target_fields:
                continue  # Skip validators for removed fields

            original_func = dec.func
            # Unwrap classmethod to get underlying function
            if hasattr(original_func, "__func__"):
                original_func = getattr(original_func, "__func__")

            fv_kwargs: dict[str, Any] = {"mode": dec.info.mode}
            if dec.info.check_fields is not None:
                fv_kwargs["check_fields"] = dec.info.check_fields

            namespace[fv_name] = field_validator(*target_fields, **fv_kwargs)(classmethod(original_func))

        # Re-apply model_validator decorators
        for mv_name, dec in self._pydantic_decorators.model_validators.items():
            original_func = dec.func
            namespace[mv_name] = model_validator(mode=dec.info.mode)(original_func)

        # Re-apply field_serializer decorators (only for fields that still exist)
        for fs_name, dec in self._pydantic_decorators.field_serializers.items():
            target_fields = tuple(f for f in dec.info.fields if f in remaining_fields or f == "*")
            if not target_fields:
                continue  # Skip serializers for removed fields

            original_func = dec.func
            fs_kwargs: dict[str, Any] = {
                "mode": dec.info.mode,
                "when_used": dec.info.when_used,
            }
            namespace[fs_name] = field_serializer(*target_fields, **fs_kwargs)(original_func)

        # Re-apply model_serializer decorators
        for ms_name, dec in self._pydantic_decorators.model_serializers.items():
            original_func = dec.func
            ms_kwargs: dict[str, Any] = {
                "mode": dec.info.mode,
                "when_used": dec.info.when_used,
            }
            if dec.info.return_type is not None:
                ms_kwargs["return_type"] = dec.info.return_type
            namespace[ms_name] = model_serializer(**ms_kwargs)(original_func)

        # Add regular methods
        for method_name, method in self._class_methods.items():
            namespace[method_name] = method

        # Build the new model using ModelMetaclass
        new_model: type[BaseModel] = ModelMetaclass(self.original_model_cls.__name__ + name, (base,), namespace)  # type: ignore[assignment]
        return new_model

    def _prep_fields(self) -> dict[str, tuple[type, FieldInfo]]:
        """Legacy method for backward compatibility."""
        model_fields = {}
        for field_name, field in self.model_fields.items():
            model_fields[field_name] = (
                field.annotation,
                field,
            )
        return model_fields


class VariantContext:
    original_model: type[BaseModel]
    current_variant: DecomposedModel | type[BaseModel]
    metadata: dict[str, Any]

    def __init__(self, name: str):
        self.name = name
        self.metadata = {}

    def __call__(self, model_cls: type[BaseModel]) -> "VariantContext":
        """Initialize with a BaseModel class"""
        self.original_model = model_cls
        self.current_variant = DecomposedModel(model_cls)
        return self


class ModelTransformer(Protocol):
    def __call__(self, context: VariantContext) -> VariantContext: ...
