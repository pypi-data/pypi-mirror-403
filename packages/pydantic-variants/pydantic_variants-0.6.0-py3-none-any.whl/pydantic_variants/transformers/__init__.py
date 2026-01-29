"""
Pydantic Variants Transformers

This package provides transformers for modifying Pydantic models through pipelines.
All transformers can be imported directly from this package.
"""

from pydantic_variants.transformers.attach_builders import AttachBuilders
from pydantic_variants.transformers.build_variant import BuildVariant
from pydantic_variants.transformers.connect_variant import ConnectVariant
from pydantic_variants.transformers.extract_variant import ExtractVariant
from pydantic_variants.transformers.filter_fields import FilterFields
from pydantic_variants.transformers.filter_tag import FilterTag, Tag, computed_with_tags
from pydantic_variants.transformers.make_optional import DefaultFactoryTag, MakeOptional
from pydantic_variants.transformers.model_dict import ModelDict
from pydantic_variants.transformers.modify_fields import ModifyFields
from pydantic_variants.transformers.rename_fields import RenameFields
from pydantic_variants.transformers.set_attributes import SetAttribute
from pydantic_variants.transformers.set_build_method import SetBuildMethod
from pydantic_variants.transformers.set_fields import SetFields
from pydantic_variants.transformers.switch_variant import SwitchVariant

__all__ = [
    "AttachBuilders",
    "BuildVariant",
    "ConnectVariant",
    "DefaultFactoryTag",
    "ExtractVariant",
    "FilterFields",
    "FilterTag",
    "MakeOptional",
    "ModelDict",
    "ModifyFields",
    "RenameFields",
    "SetAttribute",
    "SetBuildMethod",
    "SetFields",
    "SwitchVariant",
    "Tag",
    "computed_with_tags",
]
