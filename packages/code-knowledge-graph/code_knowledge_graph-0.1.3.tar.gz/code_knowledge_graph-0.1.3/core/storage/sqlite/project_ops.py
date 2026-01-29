"""Project operations mixin for SQLite storage.

This module contains project-related database operations.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import ProjectRecord

logger = logging.getLogger(__name__)


class ProjectOpsMixin:
    """Mixin class for project-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def save_project(
        self,
        path: Path,
        files: list,
        graph: dict
    ) -> int:
        """Save project data to storage."""
        cursor = self._get_cursor()
        path_str = str(path.resolve())
        project_name = path.name

        # Check if project exists
        existing = self.get_project(path_str)
        if existing:
            project_id = existing.id
            # Delete existing files (cascade deletes imports, functions, etc.)
            cursor.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
            # Update project record
            cursor.execute(
                """
                UPDATE projects
                SET last_scanned = CURRENT_TIMESTAMP, file_count = ?
                WHERE id = ?
                """,
                (len(files), project_id)
            )
        else:
            # Insert new project
            cursor.execute(
                """
                INSERT INTO projects (path, name, file_count)
                VALUES (?, ?, ?)
                """,
                (path_str, project_name, len(files))
            )
            project_id = cursor.lastrowid

        # Build path to file_id mapping for import resolution
        path_to_file_id: dict[str, int] = {}

        # Insert files
        for file_info in files:
            rel_path = file_info.relative_path
            depth = len(Path(rel_path).parts) - 1  # Depth from root

            try:
                modified_time = datetime.fromtimestamp(
                    Path(path / rel_path).stat().st_mtime
                )
            except (OSError, FileNotFoundError):
                modified_time = datetime.now()

            cursor.execute(
                """
                INSERT INTO files (project_id, relative_path, file_type, size, depth, modified_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    rel_path,
                    file_info.file_type,
                    file_info.size,
                    depth,
                    modified_time.isoformat()
                )
            )
            file_id = cursor.lastrowid
            path_to_file_id[rel_path] = file_id

        # Build edge list per source file for import resolution
        source_edges: dict[str, list[str]] = {}
        if "edges" in graph:
            for edge in graph["edges"]:
                source = edge.get("from", "")
                target = edge.get("to", "")
                if source not in source_edges:
                    source_edges[source] = []
                source_edges[source].append(target)

        # Insert imports
        for file_info in files:
            file_id = path_to_file_id.get(file_info.relative_path)
            if not file_id:
                continue

            source_path = file_info.relative_path
            edges = source_edges.get(source_path, [])

            for idx, imp in enumerate(file_info.imports):
                # Resolve import to file_id if it's internal
                resolved_file_id = None

                # Match by index - edges are in same order as imports
                if idx < len(edges):
                    target = edges[idx]
                    # Skip external dependencies
                    if not target.startswith("external:") and target in path_to_file_id:
                        resolved_file_id = path_to_file_id[target]

                cursor.execute(
                    """
                    INSERT INTO imports (file_id, module, import_type, line, resolved_file_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        file_id,
                        imp.module,
                        imp.import_type,
                        imp.line,
                        resolved_file_id
                    )
                )

        self.conn.commit()
        logger.info(f"Saved project {project_name} with {len(files)} files")
        return project_id

    def save_project_incremental(
        self,
        path: Path,
        files: list,
        graph: dict
    ) -> tuple[int, dict]:
        """Save project data with incremental updates based on file modification time.

        Only updates files that have been modified since the last scan.
        Returns a tuple of (project_id, update_stats).
        """
        cursor = self._get_cursor()
        path_str = str(path.resolve())
        project_name = path.name

        stats = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}

        # Check if project exists
        existing = self.get_project(path_str)
        if not existing:
            # First scan - use regular save
            project_id = self.save_project(path, files, graph)
            stats["added"] = len(files)
            return project_id, stats

        project_id = existing.id

        # Get existing files and their modification times
        existing_files = {}
        cursor.execute(
            """
            SELECT relative_path, modified_time, id
            FROM files WHERE project_id = ?
            """,
            (project_id,)
        )
        for row in cursor.fetchall():
            existing_files[row["relative_path"]] = {
                "modified_time": row["modified_time"],
                "id": row["id"]
            }

        # Categorize files
        new_files = []
        modified_files = []
        unchanged_files = []
        current_paths = set()

        for file_info in files:
            rel_path = file_info.relative_path
            current_paths.add(rel_path)

            if rel_path not in existing_files:
                new_files.append(file_info)
            else:
                # Check modification time
                try:
                    current_mtime = datetime.fromtimestamp(
                        Path(path / rel_path).stat().st_mtime
                    )
                except (OSError, FileNotFoundError):
                    current_mtime = datetime.now()

                stored_mtime = existing_files[rel_path]["modified_time"]
                if isinstance(stored_mtime, str):
                    stored_mtime = datetime.fromisoformat(stored_mtime)

                # Compare timestamps (with 1 second tolerance)
                if abs((current_mtime - stored_mtime).total_seconds()) > 1:
                    modified_files.append(file_info)
                else:
                    unchanged_files.append(file_info)

        # Find removed files
        removed_paths = set(existing_files.keys()) - current_paths

        # Delete removed files
        for removed_path in removed_paths:
            file_id = existing_files[removed_path]["id"]
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            stats["removed"] += 1

        # Delete modified files (will be re-inserted)
        for file_info in modified_files:
            file_id = existing_files[file_info.relative_path]["id"]
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))

        # Build path to file_id mapping (include unchanged files)
        path_to_file_id: dict[str, int] = {}
        for file_info in unchanged_files:
            path_to_file_id[file_info.relative_path] = (
                existing_files[file_info.relative_path]["id"]
            )

        # Insert new and modified files
        files_to_insert = new_files + modified_files
        for file_info in files_to_insert:
            rel_path = file_info.relative_path
            depth = len(Path(rel_path).parts) - 1

            try:
                modified_time = datetime.fromtimestamp(
                    Path(path / rel_path).stat().st_mtime
                )
            except (OSError, FileNotFoundError):
                modified_time = datetime.now()

            cursor.execute(
                """
                INSERT INTO files (project_id, relative_path, file_type, size, depth, modified_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    rel_path,
                    file_info.file_type,
                    file_info.size,
                    depth,
                    modified_time.isoformat()
                )
            )
            file_id = cursor.lastrowid
            path_to_file_id[rel_path] = file_id

        # Build edge list per source file for import resolution
        source_edges: dict[str, list[str]] = {}
        if "edges" in graph:
            for edge in graph["edges"]:
                source = edge.get("from", "")
                target = edge.get("to", "")
                if source not in source_edges:
                    source_edges[source] = []
                source_edges[source].append(target)

        # Insert imports for new and modified files
        for file_info in files_to_insert:
            file_id = path_to_file_id.get(file_info.relative_path)
            if not file_id:
                continue

            source_path = file_info.relative_path
            edges = source_edges.get(source_path, [])

            for idx, imp in enumerate(file_info.imports):
                resolved_file_id = None

                # Match by index - edges are in same order as imports
                if idx < len(edges):
                    target = edges[idx]
                    # Skip external dependencies
                    if not target.startswith("external:") and target in path_to_file_id:
                        resolved_file_id = path_to_file_id[target]

                cursor.execute(
                    """
                    INSERT INTO imports (file_id, module, import_type, line, resolved_file_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        file_id,
                        imp.module,
                        imp.import_type,
                        imp.line,
                        resolved_file_id
                    )
                )

        # Update project record
        cursor.execute(
            """
            UPDATE projects
            SET last_scanned = CURRENT_TIMESTAMP, file_count = ?
            WHERE id = ?
            """,
            (len(files), project_id)
        )

        self.conn.commit()

        stats["added"] = len(new_files)
        stats["updated"] = len(modified_files)
        stats["unchanged"] = len(unchanged_files)

        logger.info(
            f"Incremental update for {project_name}: "
            f"{stats['added']} added, {stats['updated']} updated, "
            f"{stats['unchanged']} unchanged, {stats['removed']} removed"
        )
        return project_id, stats

    def get_project(self, path: str) -> Optional[ProjectRecord]:
        """Get project record by path."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()
        if row:
            return ProjectRecord(
                id=row["id"],
                path=row["path"],
                name=row["name"],
                last_scanned=row["last_scanned"],
                file_count=row["file_count"]
            )
        return None

    def get_project_by_id(self, project_id: int) -> Optional[ProjectRecord]:
        """Get project record by ID."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        if row:
            return ProjectRecord(
                id=row["id"],
                path=row["path"],
                name=row["name"],
                last_scanned=row["last_scanned"],
                file_count=row["file_count"]
            )
        return None

    def list_projects(self) -> list[ProjectRecord]:
        """List all stored projects."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM projects ORDER BY last_scanned DESC"
        )
        rows = cursor.fetchall()

        return [
            ProjectRecord(
                id=row["id"],
                path=row["path"],
                name=row["name"],
                last_scanned=row["last_scanned"],
                file_count=row["file_count"]
            )
            for row in rows
        ]

    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its data."""
        cursor = self._get_cursor()
        cursor.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )
        deleted = cursor.rowcount > 0
        self.conn.commit()
        return deleted
