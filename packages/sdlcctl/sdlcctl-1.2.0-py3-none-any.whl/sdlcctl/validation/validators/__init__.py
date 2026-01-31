"""
SDLC Structure Validators.

Built-in validators for SDLC 6.0.0 structure compliance.

Part of Sprint 44 - SDLC Structure Scanner Engine.
Updated Sprint 125 - Multi-Frontend Alignment (SpecFrontmatterValidator).
"""

from .stage_folder import StageFolderValidator
from .sequential_numbering import SequentialNumberingValidator
from .naming_convention import NamingConventionValidator
from .header_metadata import HeaderMetadataValidator
from .cross_reference import CrossReferenceValidator
from .spec_frontmatter import SpecFrontmatterValidator

from ..base_validator import get_registry

# Auto-register validators
_registry = get_registry()
_registry.register(StageFolderValidator)
_registry.register(SequentialNumberingValidator)
_registry.register(NamingConventionValidator)
_registry.register(HeaderMetadataValidator)
_registry.register(CrossReferenceValidator)
_registry.register(SpecFrontmatterValidator)

__all__ = [
    "StageFolderValidator",
    "SequentialNumberingValidator",
    "NamingConventionValidator",
    "HeaderMetadataValidator",
    "CrossReferenceValidator",
    "SpecFrontmatterValidator",
]
