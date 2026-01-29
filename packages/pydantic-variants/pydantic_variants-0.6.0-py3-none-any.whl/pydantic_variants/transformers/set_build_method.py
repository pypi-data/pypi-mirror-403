from typing import Any, Callable

from pydantic_variants.core import DecomposedModel, ModelTransformer, VariantContext


class SetBuildMethod(ModelTransformer):
    """
    Attaches a build method to the root model for creating variant instances.

    This is a convenience wrapper around SetAttribute specifically for the common
    pattern of adding build_output(), build_private_output(), etc. methods.

    The method will be attached to the root model (original model), allowing
    instances of the root model to create variant instances via self.VariantName.

    Args:
        method_name: Name of the method to attach (e.g., 'build_output')
        method: The method/function to attach. Should accept 'self' as first arg.

    Raises:
        ValueError: If current_variant is not yet built (use after BuildVariant)

    Example:
        # Simple usage
        def build_output(self):
            return self.Output.model_validate(self.model_dump())

        SetBuildMethod('build_output', build_output)

        # With lambda (for simple cases)
        SetBuildMethod('build_output', lambda self: self.Output(**self.model_dump()))

        # In a pipeline
        VariantPipe(
            VariantContext("Output"),
            FilterFields(exclude=['password']),
            BuildVariant(),
            ConnectVariant(),
            SetBuildMethod('build_output', build_output),
            ExtractVariant(),
        )
    """

    def __init__(self, method_name: str, method: Callable[[Any], Any]):
        self.method_name = method_name
        self.method = method

    def __call__(self, context: VariantContext) -> VariantContext:
        if isinstance(context.current_variant, DecomposedModel):
            raise ValueError("SetBuildMethod requires built model. Use BuildVariant before SetBuildMethod.")

        # Attach the method to the root model
        setattr(context.original_model, self.method_name, self.method)

        return context
