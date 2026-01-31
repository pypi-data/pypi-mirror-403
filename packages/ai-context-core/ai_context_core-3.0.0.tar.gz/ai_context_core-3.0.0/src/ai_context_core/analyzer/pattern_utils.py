"""Pattern detection utilities for ai-context-core."""

import ast
from typing import Dict, List, Any


def get_class_name(node: ast.AST) -> str:
    """Get the name of a class from an AST node."""
    return getattr(node, "name", "N/A")


def add_pattern_evidence(
    evidence: List[str], confidence: int, msg: str, weight: int
) -> tuple:
    """Add evidence and update confidence."""
    evidence.append(msg)
    confidence += weight
    return evidence, confidence


def get_pattern_results(
    confidence: int, evidence: List[str], node: ast.AST
) -> List[Dict[str, Any]]:
    """Returns the results if confidence threshold is met."""
    from .constants import (
        PATTERN_DETECTION_CONFIDENCE_THRESHOLD,
        PATTERN_DETECTION_CONFIDENCE_MAXIMUM,
    )

    if confidence >= PATTERN_DETECTION_CONFIDENCE_THRESHOLD:
        name = get_class_name(node)
        return [
            {
                "class": name,
                "confidence": min(confidence, PATTERN_DETECTION_CONFIDENCE_MAXIMUM),
                "evidence": evidence,
            }
        ]
    return []
