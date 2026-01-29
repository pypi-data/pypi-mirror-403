"""Statistics operations mixin for SQLite storage.

This module contains statistics-related database operations.
"""

import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import FileTypeStats, DepthStats, ReferenceRankingItem

logger = logging.getLogger(__name__)


class StatsOpsMixin:
    """Mixin class for statistics-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def get_file_stats(
        self,
        project_id: int,
        subdirectory: Optional[str] = None
    ) -> list[FileTypeStats]:
        """Get file type statistics for a project."""
        cursor = self._get_cursor()

        if subdirectory:
            cursor.execute(
                """
                SELECT file_type, COUNT(*) as count, SUM(size) as total_size
                FROM files
                WHERE project_id = ? AND relative_path LIKE ?
                GROUP BY file_type
                ORDER BY count DESC
                """,
                (project_id, f"{subdirectory}%")
            )
        else:
            cursor.execute(
                """
                SELECT file_type, COUNT(*) as count, SUM(size) as total_size
                FROM files
                WHERE project_id = ?
                GROUP BY file_type
                ORDER BY count DESC
                """,
                (project_id,)
            )

        rows = cursor.fetchall()

        # Calculate total for percentage
        total_count = sum(row["count"] for row in rows)
        if total_count == 0:
            return []

        return [
            FileTypeStats(
                file_type=row["file_type"],
                count=row["count"],
                percentage=round(row["count"] / total_count * 100, 2),
                total_size=row["total_size"] or 0
            )
            for row in rows
        ]

    def get_reference_ranking(
        self,
        project_id: int,
        limit: int = 20,
        file_type: Optional[str] = None
    ) -> list[ReferenceRankingItem]:
        """Get files ranked by incoming reference count.

        This method counts references using two approaches:
        1. Direct resolved_file_id relationships
        2. Module name matching for unresolved imports
        """
        cursor = self._get_cursor()

        # Query to count references using both resolved IDs and module name matching
        if file_type:
            cursor.execute(
                """
                WITH file_references AS (
                    -- Direct resolved references
                    SELECT
                        f.id as file_id,
                        f.relative_path,
                        sf.relative_path as source_path
                    FROM files f
                    JOIN imports i ON i.resolved_file_id = f.id
                    JOIN files sf ON i.file_id = sf.id
                    WHERE f.project_id = ?
                      AND f.file_type = ?
                      AND i.resolved_file_id IS NOT NULL

                    UNION

                    -- Module name pattern matching for unresolved imports
                    SELECT
                        f.id as file_id,
                        f.relative_path,
                        sf.relative_path as source_path
                    FROM files f
                    JOIN imports i ON i.resolved_file_id IS NULL
                    JOIN files sf ON i.file_id = sf.id
                    WHERE f.project_id = ?
                      AND sf.project_id = ?
                      AND f.file_type = ?
                      AND (
                          -- Match module to file path patterns
                          f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '.py'
                          OR f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '/__init__.py'
                          OR f.relative_path LIKE '%' || REPLACE(i.module, '.', '\\') || '.py'
                          OR f.relative_path LIKE '%/' || i.module || '.py'
                          OR f.relative_path LIKE '%/' || i.module || '.ts'
                          OR f.relative_path LIKE '%/' || i.module || '.js'
                          OR f.relative_path LIKE '%/' || i.module || '.go'
                      )
                      AND sf.id != f.id
                )
                SELECT
                    relative_path,
                    COUNT(*) as ref_count,
                    GROUP_CONCAT(DISTINCT source_path) as referencing_files
                FROM file_references
                GROUP BY file_id, relative_path
                HAVING ref_count > 0
                ORDER BY ref_count DESC
                LIMIT ?
                """,
                (project_id, file_type, project_id, project_id, file_type, limit)
            )
        else:
            cursor.execute(
                """
                WITH file_references AS (
                    -- Direct resolved references
                    SELECT
                        f.id as file_id,
                        f.relative_path,
                        sf.relative_path as source_path
                    FROM files f
                    JOIN imports i ON i.resolved_file_id = f.id
                    JOIN files sf ON i.file_id = sf.id
                    WHERE f.project_id = ?
                      AND i.resolved_file_id IS NOT NULL

                    UNION

                    -- Module name pattern matching for unresolved imports
                    SELECT
                        f.id as file_id,
                        f.relative_path,
                        sf.relative_path as source_path
                    FROM files f
                    JOIN imports i ON i.resolved_file_id IS NULL
                    JOIN files sf ON i.file_id = sf.id
                    WHERE f.project_id = ?
                      AND sf.project_id = ?
                      AND (
                          -- Match module to file path patterns
                          f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '.py'
                          OR f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '/__init__.py'
                          OR f.relative_path LIKE '%' || REPLACE(i.module, '.', '\\') || '.py'
                          OR f.relative_path LIKE '%/' || i.module || '.py'
                          OR f.relative_path LIKE '%/' || i.module || '.ts'
                          OR f.relative_path LIKE '%/' || i.module || '.js'
                          OR f.relative_path LIKE '%/' || i.module || '.go'
                      )
                      AND sf.id != f.id
                )
                SELECT
                    relative_path,
                    COUNT(*) as ref_count,
                    GROUP_CONCAT(DISTINCT source_path) as referencing_files
                FROM file_references
                GROUP BY file_id, relative_path
                HAVING ref_count > 0
                ORDER BY ref_count DESC
                LIMIT ?
                """,
                (project_id, project_id, project_id, limit)
            )

        rows = cursor.fetchall()

        return [
            ReferenceRankingItem(
                file_path=row["relative_path"],
                reference_count=row["ref_count"],
                referencing_files=(
                    row["referencing_files"].split(",")
                    if row["referencing_files"]
                    else []
                )
            )
            for row in rows
        ]

    def get_depth_stats(
        self,
        project_id: int,
        subdirectory: Optional[str] = None
    ) -> DepthStats:
        """Get directory and file depth statistics."""
        cursor = self._get_cursor()

        if subdirectory:
            # Adjust depth relative to subdirectory
            subdir_depth = len(Path(subdirectory).parts)
            cursor.execute(
                """
                SELECT
                    MIN(depth - ?) as min_depth,
                    MAX(depth - ?) as max_depth,
                    AVG(depth - ?) as avg_depth,
                    depth - ? as adj_depth,
                    COUNT(*) as count
                FROM files
                WHERE project_id = ? AND relative_path LIKE ?
                GROUP BY adj_depth
                """,
                (subdir_depth, subdir_depth, subdir_depth, subdir_depth,
                 project_id, f"{subdirectory}%")
            )
        else:
            cursor.execute(
                """
                SELECT depth, COUNT(*) as count
                FROM files
                WHERE project_id = ?
                GROUP BY depth
                """,
                (project_id,)
            )

        rows = cursor.fetchall()

        if not rows:
            return DepthStats(
                max_directory_depth=0,
                max_file_depth=0,
                min_file_depth=0,
                avg_file_depth=0.0,
                depth_distribution={}
            )

        # Build depth distribution
        depth_distribution = {}
        total_depth = 0
        total_count = 0
        min_depth = float("inf")
        max_depth = 0

        for row in rows:
            depth = row["depth"] if "depth" in row.keys() else row["adj_depth"]
            count = row["count"]
            depth_distribution[depth] = count
            total_depth += depth * count
            total_count += count
            min_depth = min(min_depth, depth)
            max_depth = max(max_depth, depth)

        avg_depth = total_depth / total_count if total_count > 0 else 0

        return DepthStats(
            max_directory_depth=max_depth,
            max_file_depth=max_depth,
            min_file_depth=int(min_depth) if min_depth != float("inf") else 0,
            avg_file_depth=round(avg_depth, 2),
            depth_distribution=depth_distribution
        )
