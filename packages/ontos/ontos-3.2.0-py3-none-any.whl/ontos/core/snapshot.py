"""
Snapshot primitive for document collection.

Creates an immutable snapshot of all documents at a point in time.
Used by export and migration commands.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ontos.core.types import DocumentData, ValidationResult
from ontos.core.graph import DependencyGraph, build_graph
from ontos.core.validation import ValidationOrchestrator


@dataclass
class SnapshotFilters:
    """Filters for document selection."""
    types: Optional[List[str]] = None
    status: Optional[List[str]] = None
    concepts: Optional[List[str]] = None


@dataclass
class DocumentSnapshot:
    """Immutable snapshot of all documents at a point in time."""
    timestamp: datetime
    project_root: Path
    documents: Dict[str, DocumentData]
    graph: DependencyGraph
    validation_result: ValidationResult
    git_commit: Optional[str] = None
    ontos_version: str = ""
    warnings: List[str] = field(default_factory=list)

    @property
    def by_type(self) -> Dict[str, List[DocumentData]]:
        """Group documents by type."""
        result: Dict[str, List[DocumentData]] = {}
        for doc in self.documents.values():
            doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
            if doc_type not in result:
                result[doc_type] = []
            result[doc_type].append(doc)
        return result

    @property
    def by_status(self) -> Dict[str, List[DocumentData]]:
        """Group documents by status."""
        result: Dict[str, List[DocumentData]] = {}
        for doc in self.documents.values():
            doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
            if doc_status not in result:
                result[doc_status] = []
            result[doc_status].append(doc)
        return result


def _matches_filter(doc: DocumentData, filters: Optional[SnapshotFilters]) -> bool:
    """Check if document matches filter criteria."""
    if filters is None:
        return True

    # Type filter
    if filters.types:
        doc_type = doc.type.value if hasattr(doc.type, 'value') else str(doc.type)
        if doc_type not in filters.types:
            return False

    # Status filter
    if filters.status:
        doc_status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
        if doc_status not in filters.status:
            return False

    # Concept filter
    if filters.concepts:
        doc_concepts = set(doc.tags)
        if not doc_concepts.intersection(set(filters.concepts)):
            return False

    return True


def create_snapshot(
    root: Path,
    include_content: bool = True,
    filters: Optional[SnapshotFilters] = None,
    git_commit_provider: Optional[callable] = None,
) -> DocumentSnapshot:
    """
    Create a snapshot of all documents.

    Args:
        root: Project root directory
        include_content: Whether to include document content
        filters: Optional filters (type, status, concept)
        git_commit_provider: Optional callback to get git commit hash

    Returns:
        Immutable DocumentSnapshot
    """
    import ontos
    from ontos.io.config import load_project_config
    from ontos.io.files import scan_documents, load_document_from_content
    from ontos.io.yaml import parse_frontmatter_content

    # Load config
    config = load_project_config(repo_root=root)

    # Determine docs directory
    docs_dir = root / config.paths.docs_dir
    internal_dir = root / ".ontos-internal"

    scan_dirs = []
    if docs_dir.exists():
        scan_dirs.append(docs_dir)
    if internal_dir.exists():
        scan_dirs.append(internal_dir)

    # Scan documents
    skip_patterns = config.scanning.skip_patterns if config.scanning else ["_template.md", "archive/*"]
    doc_paths = scan_documents(scan_dirs, skip_patterns=skip_patterns)

    # Load documents
    documents: Dict[str, DocumentData] = {}
    warnings: List[str] = []
    for path in doc_paths:
        try:
            content = path.read_text(encoding='utf-8')
            doc = load_document_from_content(path, content, parse_frontmatter_content)

            # Apply filters
            if _matches_filter(doc, filters):
                # Optionally strip content
                if not include_content:
                    doc = DocumentData(
                        id=doc.id,
                        type=doc.type,
                        status=doc.status,
                        filepath=doc.filepath,
                        frontmatter=doc.frontmatter,
                        content="",  # Strip content
                        depends_on=doc.depends_on,
                        impacts=doc.impacts,
                        tags=doc.tags,
                        aliases=doc.aliases,
                    )
                documents[doc.id] = doc
        except Exception as e:
            # S2: Log warnings on parse failure instead of silent skip
            warnings.append(f"Skipped {path}: {e}")
            continue

    # Build graph
    graph, _ = build_graph(documents)

    # Run validation
    orchestrator = ValidationOrchestrator(documents, {})
    validation_result = orchestrator.validate_all()

    # Get git commit if provider given
    git_commit = None
    if git_commit_provider:
        try:
            git_commit = git_commit_provider()
        except Exception:
            pass

    return DocumentSnapshot(
        timestamp=datetime.now(),
        project_root=root,
        documents=documents,
        graph=graph,
        validation_result=validation_result,
        git_commit=git_commit,
        ontos_version=ontos.__version__,
        warnings=warnings,
    )
