"""
Validation orchestration for context map generation.

Extracts validation logic from ontos_generate_context_map.py and provides
a unified interface that collects all errors before returning (no hard exits).

Phase 2 Decomposition - Created from Phase2-Implementation-Spec.md Section 4.5
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional, Any

from ontos.core.types import (
    DocumentData,
    ValidationError,
    ValidationResult,
    ValidationErrorType,
)
from ontos.core.graph import (
    build_graph,
    detect_cycles,
    detect_orphans,
    calculate_depths,
)


def validate_describes_field(
    doc: DocumentData,
    valid_targets: Set[str]
) -> Optional[ValidationError]:
    """Validate describes field references valid targets.

    Args:
        doc: Document with optional describes field
        valid_targets: Set of valid target doc_ids

    Returns:
        ValidationError if invalid, None if valid
    """
    describes = doc.frontmatter.get("describes")
    if describes and describes not in valid_targets:
        return ValidationError(
            error_type=ValidationErrorType.SCHEMA,
            doc_id=doc.id,
            filepath=str(doc.filepath),
            message=f"describes '{describes}' not found",
            fix_suggestion=f"Update describes to valid target or remove",
            severity="warning"
        )
    return None


class ValidationOrchestrator:
    """Orchestrates all validation checks and collects errors."""

    def __init__(
        self,
        docs: Dict[str, DocumentData],
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize with documents and optional config.

        Args:
            docs: Dictionary mapping doc_id to DocumentData
            config: Optional configuration dict
        """
        self.docs = docs
        self.config = config or {}
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_all(self) -> ValidationResult:
        """Run all validations and return collected results.

        Returns:
            ValidationResult with all errors and warnings
        """
        self.validate_graph()
        self.validate_log_schema()
        self.validate_impacts()
        self.validate_describes()

        return ValidationResult(
            errors=self.errors,
            warnings=self.warnings
        )

    def validate_graph(self) -> None:
        """Validate dependency graph: broken links, cycles, orphans, depth."""
        graph, broken_link_errors = build_graph(self.docs)
        self.errors.extend(broken_link_errors)

        # Detect cycles
        cycles = detect_cycles(graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            self.errors.append(ValidationError(
                error_type=ValidationErrorType.CYCLE,
                doc_id=cycle[0],
                filepath=str(self.docs[cycle[0]].filepath) if cycle[0] in self.docs else "",
                message=f"Circular dependency: {cycle_str}",
                fix_suggestion="Break the cycle by removing one dependency",
                severity="error"
            ))

        # Detect orphans
        allowed_orphans = set(self.config.get("allowed_orphan_types", ["atom", "log"]))
        orphans = detect_orphans(graph, allowed_orphans)
        for orphan_id in orphans:
            if orphan_id in self.docs:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.ORPHAN,
                    doc_id=orphan_id,
                    filepath=str(self.docs[orphan_id].filepath),
                    message=f"Document has no incoming dependencies",
                    fix_suggestion="Add this document to another document's depends_on",
                    severity="warning"
                ))

        # Check depth
        max_depth = self.config.get("max_dependency_depth", 5)
        depths = calculate_depths(graph)
        for doc_id, depth in depths.items():
            if depth > max_depth:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.DEPTH,
                    doc_id=doc_id,
                    filepath=str(self.docs[doc_id].filepath) if doc_id in self.docs else "",
                    message=f"Dependency depth {depth} exceeds max {max_depth}",
                    fix_suggestion="Consider flattening the dependency chain",
                    severity="warning"
                ))

    def validate_log_schema(self) -> None:
        """Validate log documents have required v2.0 fields."""
        required_fields = {"branch", "event_type", "source"}

        for doc_id, doc in self.docs.items():
            # Handle both enum and string types
            doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
            if doc_type != "log":
                continue

            missing = required_fields - set(doc.frontmatter.keys())
            if missing:
                self.warnings.append(ValidationError(
                    error_type=ValidationErrorType.SCHEMA,
                    doc_id=doc_id,
                    filepath=str(doc.filepath),
                    message=f"Log missing fields: {', '.join(sorted(missing))}",
                    fix_suggestion="Add missing fields to frontmatter",
                    severity="warning"
                ))

    def validate_impacts(self) -> None:
        """Validate impacts[] references exist."""
        valid_ids = set(self.docs.keys())

        for doc_id, doc in self.docs.items():
            for impact in doc.impacts:
                if impact not in valid_ids:
                    self.warnings.append(ValidationError(
                        error_type=ValidationErrorType.IMPACTS,
                        doc_id=doc_id,
                        filepath=str(doc.filepath),
                        message=f"Impact reference '{impact}' not found",
                        fix_suggestion=f"Remove '{impact}' or create the document",
                        severity="warning"
                    ))

    def validate_describes(self) -> None:
        """Validate describes field references."""
        valid_ids = set(self.docs.keys())

        for doc_id, doc in self.docs.items():
            error = validate_describes_field(doc, valid_ids)
            if error:
                self.warnings.append(error)
