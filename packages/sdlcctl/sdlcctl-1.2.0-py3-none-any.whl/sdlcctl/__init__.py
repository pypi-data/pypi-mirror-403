"""
SDLC 6.0.0 Specification Validator CLI (sdlcctl)

A CLI tool for validating SDLC 6.0.0 folder structure and specification compliance.
Supports 4-Tier Classification: LITE, STANDARD, PROFESSIONAL, ENTERPRISE.
Includes YAML frontmatter validation, BDD requirements checking, and OpenSpec conversion.

Usage:
    sdlcctl validate [--path PATH] [--tier TIER] [--format FORMAT]
    sdlcctl fix [--dry-run] [--interactive]
    sdlcctl init [--tier TIER] [--scaffold]
    sdlcctl report [--format FORMAT] [--output PATH]
    sdlcctl spec validate [--tier TIER] [--strict]
    sdlcctl spec convert --from openspec --path .openspec/

Version: 1.2.0
Framework: SDLC 6.0.0
Sprint: 125 - Multi-Frontend Alignment
"""

__version__ = "1.2.0"
__author__ = "SDLC Orchestrator Team"
__framework__ = "SDLC 6.0.0"

from .validation.engine import SDLCValidator, ValidationResult
from .validation.tier import Tier, TierDetector
from .validation.scanner import FolderScanner
from .validation.p0 import P0ArtifactChecker

__all__ = [
    "SDLCValidator",
    "ValidationResult",
    "Tier",
    "TierDetector",
    "FolderScanner",
    "P0ArtifactChecker",
]
