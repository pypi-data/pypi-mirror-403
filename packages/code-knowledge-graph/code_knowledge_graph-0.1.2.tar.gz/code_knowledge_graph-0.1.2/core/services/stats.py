"""Statistics analysis service.

This module provides high-level statistics and analysis
operations for code knowledge graph data.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..storage import (
    StorageBackend,
    FileTypeStats,
    DepthStats,
    ReferenceRankingItem,
)


@dataclass
class ProjectStats:
    """Comprehensive project statistics."""

    project_path: str
    project_name: str
    total_files: int
    total_size: int
    file_types: list[FileTypeStats]
    depth_stats: DepthStats
    top_referenced: list[ReferenceRankingItem]


@dataclass
class FileStatsResponse:
    """File type statistics response."""

    project_path: str
    total_files: int
    stats: list[FileTypeStats]


@dataclass
class ReferenceRankingResponse:
    """Reference ranking response."""

    project_path: str
    results: list[ReferenceRankingItem]
    total_results: int


@dataclass
class DepthAnalysisResponse:
    """Depth analysis response."""

    project_path: str
    directory_depth: dict
    file_depth: dict


class StatsService:
    """Statistics analysis service.

    Provides high-level methods for querying project statistics
    including file type distribution, reference rankings, and
    depth analysis.
    """

    def __init__(self, storage: StorageBackend):
        """Initialize stats service.

        Args:
            storage: Storage backend instance
        """
        self.storage = storage

    def get_project_stats(
        self,
        project_path: str,
        top_referenced_limit: int = 10
    ) -> Optional[ProjectStats]:
        """Get comprehensive statistics for a project.

        Args:
            project_path: Path to the project
            top_referenced_limit: Number of top referenced files to include

        Returns:
            ProjectStats object or None if project not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        file_stats = self.storage.get_file_stats(project.id)
        depth_stats = self.storage.get_depth_stats(project.id)
        top_referenced = self.storage.get_reference_ranking(
            project.id,
            limit=top_referenced_limit
        )

        total_size = sum(s.total_size for s in file_stats)

        return ProjectStats(
            project_path=project.path,
            project_name=project.name,
            total_files=project.file_count,
            total_size=total_size,
            file_types=file_stats,
            depth_stats=depth_stats,
            top_referenced=top_referenced
        )

    def get_file_type_stats(
        self,
        project_path: str,
        subdirectory: Optional[str] = None
    ) -> Optional[FileStatsResponse]:
        """Get file type distribution statistics.

        Args:
            project_path: Path to the project
            subdirectory: Optional subdirectory to filter by

        Returns:
            FileStatsResponse or None if project not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        stats = self.storage.get_file_stats(project.id, subdirectory)
        total_files = sum(s.count for s in stats)

        return FileStatsResponse(
            project_path=project_path,
            total_files=total_files,
            stats=stats
        )

    def get_reference_ranking(
        self,
        project_path: str,
        limit: int = 20,
        file_type: Optional[str] = None,
        include_external: bool = False
    ) -> Optional[ReferenceRankingResponse]:
        """Get files ranked by incoming reference count.

        Args:
            project_path: Path to the project
            limit: Maximum number of results
            file_type: Optional filter by file type
            include_external: Whether to include external packages

        Returns:
            ReferenceRankingResponse or None if project not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        results = self.storage.get_reference_ranking(
            project.id,
            limit=limit,
            file_type=file_type
        )

        return ReferenceRankingResponse(
            project_path=project_path,
            results=results,
            total_results=len(results)
        )

    def get_depth_analysis(
        self,
        project_path: str,
        subdirectory: Optional[str] = None
    ) -> Optional[DepthAnalysisResponse]:
        """Get directory and file depth analysis.

        Args:
            project_path: Path to the project
            subdirectory: Optional subdirectory to analyze

        Returns:
            DepthAnalysisResponse or None if project not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        stats = self.storage.get_depth_stats(project.id, subdirectory)

        return DepthAnalysisResponse(
            project_path=project_path,
            directory_depth={
                "max": stats.max_directory_depth,
                "distribution": {
                    k: v for k, v in stats.depth_distribution.items()
                    if k <= stats.max_directory_depth
                }
            },
            file_depth={
                "min": stats.min_file_depth,
                "max": stats.max_file_depth,
                "avg": stats.avg_file_depth,
                "distribution": stats.depth_distribution
            }
        )

    def get_files_by_type(
        self,
        project_path: str,
        file_type: str
    ) -> list[str]:
        """Get all files of a specific type in a project.

        Args:
            project_path: Path to the project
            file_type: File type to filter by (e.g., 'python', 'typescript')

        Returns:
            List of relative file paths
        """
        project = self.storage.get_project(project_path)
        if not project:
            return []

        files = self.storage.get_files_by_project(
            project.id,
            file_type=file_type
        )
        return [f.relative_path for f in files]

    def get_files_in_directory(
        self,
        project_path: str,
        subdirectory: str
    ) -> list[str]:
        """Get all files in a specific subdirectory.

        Args:
            project_path: Path to the project
            subdirectory: Subdirectory path relative to project root

        Returns:
            List of relative file paths
        """
        project = self.storage.get_project(project_path)
        if not project:
            return []

        files = self.storage.get_files_by_project(
            project.id,
            subdirectory=subdirectory
        )
        return [f.relative_path for f in files]

    def get_dependency_summary(
        self,
        project_path: str,
        file_path: str
    ) -> Optional[dict]:
        """Get dependency summary for a specific file.

        Args:
            project_path: Path to the project
            file_path: Relative path to the file

        Returns:
            Dictionary with imports and importers, or None if not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        imports = self.storage.get_file_imports(project.id, file_path)
        importers = self.storage.get_file_importers(project.id, file_path)

        return {
            "file_path": file_path,
            "imports": imports,
            "imported_by": importers,
            "imports_count": len(imports),
            "imported_by_count": len(importers)
        }

    def compare_projects(
        self,
        project_path1: str,
        project_path2: str
    ) -> Optional[dict]:
        """Compare statistics between two projects.

        Args:
            project_path1: Path to first project
            project_path2: Path to second project

        Returns:
            Comparison dictionary or None if either project not found
        """
        stats1 = self.get_project_stats(project_path1)
        stats2 = self.get_project_stats(project_path2)

        if not stats1 or not stats2:
            return None

        # Build file type comparison
        types1 = {s.file_type: s for s in stats1.file_types}
        types2 = {s.file_type: s for s in stats2.file_types}
        all_types = set(types1.keys()) | set(types2.keys())

        type_comparison = []
        for ft in sorted(all_types):
            s1 = types1.get(ft)
            s2 = types2.get(ft)
            type_comparison.append({
                "file_type": ft,
                "project1_count": s1.count if s1 else 0,
                "project2_count": s2.count if s2 else 0,
                "project1_percentage": s1.percentage if s1 else 0,
                "project2_percentage": s2.percentage if s2 else 0
            })

        return {
            "project1": {
                "path": stats1.project_path,
                "name": stats1.project_name,
                "total_files": stats1.total_files,
                "total_size": stats1.total_size,
                "max_depth": stats1.depth_stats.max_file_depth
            },
            "project2": {
                "path": stats2.project_path,
                "name": stats2.project_name,
                "total_files": stats2.total_files,
                "total_size": stats2.total_size,
                "max_depth": stats2.depth_stats.max_file_depth
            },
            "file_type_comparison": type_comparison
        }
