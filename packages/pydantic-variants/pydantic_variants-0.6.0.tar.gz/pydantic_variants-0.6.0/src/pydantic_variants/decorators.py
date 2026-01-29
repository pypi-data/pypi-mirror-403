import logging
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from pydantic_variants.core import ModelTransformer, VariantContext, VariantPipe
from pydantic_variants.transformers import BuildVariant, ConnectVariant, FilterFields, FilterTag, MakeOptional
from pydantic_variants.transformers.extract_variant import ExtractVariant
from pydantic_variants.transformers.set_build_method import SetBuildMethod

# Generic type variable to preserve the original model type
T = TypeVar("T", bound=BaseModel)


def basic_variant_pipeline(
    name: str, *transformers: ModelTransformer, logger: logging.Logger | None = None, debug: bool = False
) -> VariantPipe:
    """
    Helper function to create a complete variant pipeline.

    Automatically adds VariantContext creation, BuildVariant, and ConnectVariant
    transformers to create a complete pipeline.

    Args:
        name: Name of the variant
        *transformers: Field and model transformers to apply
        logger: Optional logger for debug output
        debug: If True, enables debug logging

    Returns:
        Complete VariantPipe ready for use with @variants decorator
    """

    return VariantPipe(VariantContext(name), *transformers, BuildVariant(), ConnectVariant(), ExtractVariant(), logger=logger, debug=debug)


def variants(
    *pipelines: VariantPipe, delayed_build: bool = False, logger: logging.Logger | None = None, debug: bool = False
) -> Callable[[type[T]], type[T]]:
    """
    Decorator that generates model variants using VariantPipe pipelines.

    Args:
        *pipelines: VariantPipe instances defining transformation pipelines
        delayed_build: If True, attaches pipeline logic to _build_variants method
                      instead of executing immediately
        logger: Optional logger for debug output (applies to all pipelines)
        debug: If True, enables debug logging

    Returns:
        Decorated BaseModel class with variants attached or _build_variants method
    """

    def immediate_decorator(model_cls: type[T]) -> type[T]:
        for pipeline in pipelines:
            # Apply debug settings if provided at decorator level
            if logger or debug:
                pipeline = pipeline.with_debug(logger or logging.getLogger("pydantic_variants"), debug)
            pipeline(model_cls)
        return model_cls

    def delayed_decorator(model_cls: type[T]) -> type[T]:
        def _build_variants():
            for pipeline in pipelines:
                if logger or debug:
                    pipeline = pipeline.with_debug(logger or logging.getLogger("pydantic_variants"), debug)
                pipeline(model_cls)

        model_cls._build_variants = _build_variants  # type: ignore
        return model_cls

    return delayed_decorator if delayed_build else immediate_decorator


def create_variant_pipeline(
    name: str,
    *,
    exclude_fields: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    make_optional: bool = False,
    optional_exclude: tuple[str, ...] = (),
    build_method: tuple[str, Callable[[Any], Any]] | None = None,
    extra_transformers: list[ModelTransformer] | None = None,
    logger: logging.Logger | None = None,
    debug: bool = False,
) -> VariantPipe:
    """
    Factory function to create common variant pipeline patterns with less boilerplate.

    This function creates a complete variant pipeline with commonly used transformers,
    reducing the need to manually compose BuildVariant, ConnectVariant, ExtractVariant, etc.

    Args:
        name: Name of the variant (e.g., 'Input', 'Output', 'Update')
        exclude_fields: List of field names to exclude from the variant
        exclude_tags: List of tag keys to filter out (fields with matching Tags are removed)
        make_optional: If True, makes all fields optional (useful for Update variants)
        optional_exclude: Tuple of field names to exclude from MakeOptional
        build_method: Tuple of (method_name, method) to attach to root model
        extra_transformers: Additional transformers to insert before BuildVariant
        logger: Optional logger for debug output
        debug: If True, enables debug logging

    Returns:
        Complete VariantPipe ready for use with @variants decorator

    Example:
        # Simple input variant
        input_pipe = create_variant_pipeline(
            'Input',
            exclude_fields=['id', 'created_at'],
            exclude_tags=['exclude_from_input'],
        )

        # Update variant with optional fields
        update_pipe = create_variant_pipeline(
            'Update',
            exclude_fields=['id', 'created_at'],
            make_optional=True,
            optional_exclude=('name',),  # name stays required
        )

        # Output variant with build method
        def build_output(self):
            return self.Output.model_validate(self.model_dump())

        output_pipe = create_variant_pipeline(
            'Output',
            exclude_fields=['password'],
            build_method=('build_output', build_output),
        )
    """
    transformers: list[ModelTransformer] = []

    # Add field filtering
    if exclude_fields:
        transformers.append(FilterFields(exclude=exclude_fields))

    # Add tag filtering
    if exclude_tags:
        transformers.append(FilterTag(exclude_tags))

    # Add optional transformation
    if make_optional:
        transformers.append(MakeOptional(exclude=optional_exclude))

    # Add any extra transformers
    if extra_transformers:
        transformers.extend(extra_transformers)

    # Build the complete pipeline
    pipeline_ops = [
        VariantContext(name),
        *transformers,
        BuildVariant(),
        ConnectVariant(),
    ]

    # Add build method if provided
    if build_method:
        method_name, method = build_method
        pipeline_ops.append(SetBuildMethod(method_name, method))

    pipeline_ops.append(ExtractVariant())

    return VariantPipe(*pipeline_ops, logger=logger, debug=debug)


def rebuild_with_variants(
    model_cls: type[T],
    rebuild_kwargs: dict[str, Any] | None = None,
) -> type[T]:
    """
    Rebuild a model and its variants in one call.

    This combines model_rebuild() and _build_variants() into a single operation,
    which is the common pattern needed when models have forward references.

    Args:
        model_cls: The model class to rebuild
        rebuild_kwargs: Keyword arguments to pass to model_rebuild()
                       (e.g., _types_namespace={'Service': Service})

    Returns:
        The rebuilt model class

    Raises:
        AttributeError: If model doesn't have _build_variants method
                       (use @variants(..., delayed_build=True) decorator)

    Example:
        @variants(input_pipe, output_pipe, delayed_build=True)
        class User(BaseModel):
            service: Link['Service']
            ...

        # Later, after Service is defined:
        rebuild_with_variants(User, {'_types_namespace': {'Service': Service}})

        # This is equivalent to:
        # User.model_rebuild(_types_namespace={'Service': Service})
        # User._build_variants()
    """
    # Rebuild the model with forward references
    if rebuild_kwargs:
        model_cls.model_rebuild(**rebuild_kwargs)
    else:
        model_cls.model_rebuild()

    # Build all variants
    if hasattr(model_cls, "_build_variants"):
        model_cls._build_variants()  # type: ignore
    else:
        raise AttributeError(
            f"{model_cls.__name__} does not have _build_variants method. Use @variants(..., delayed_build=True) decorator."
        )

    return model_cls
