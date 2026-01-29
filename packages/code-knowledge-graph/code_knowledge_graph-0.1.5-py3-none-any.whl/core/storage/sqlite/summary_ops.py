"""Code summary operations mixin for SQLite storage.

This module contains code summary and embedding search operations.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import CodeSummaryRecord

logger = logging.getLogger(__name__)


class SummaryOpsMixin:
    """Mixin class for code summary-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def save_summaries(
        self,
        summaries: list[dict]
    ) -> list[int]:
        """Save code summaries with bilingual support and embeddings."""
        cursor = self._get_cursor()
        summary_ids = []

        for summary in summaries:
            try:
                # Serialize embedding to bytes if present
                embedding_blob = None
                if summary.get("embedding"):
                    import json
                    embedding_blob = json.dumps(summary["embedding"]).encode("utf-8")

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO code_summaries
                    (file_id, entity_type, entity_name, signature, summary,
                     summary_en, summary_zh, embedding, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        summary["file_id"],
                        summary["entity_type"],
                        summary["entity_name"],
                        summary["signature"],
                        summary["summary"],
                        summary.get("summary_en", ""),
                        summary.get("summary_zh", ""),
                        embedding_blob,
                        summary.get("line_number", 0)
                    )
                )
                summary_ids.append(cursor.lastrowid)
            except Exception as e:
                logger.error(f"Failed to save summary: {e}")
                continue

        self.conn.commit()
        return summary_ids

    def get_summary(
        self,
        file_id: int,
        entity_name: str
    ) -> Optional[CodeSummaryRecord]:
        """Get code summary for an entity."""
        cursor = self._get_cursor()
        cursor.execute(
            """
            SELECT * FROM code_summaries
            WHERE file_id = ? AND entity_name = ?
            """,
            (file_id, entity_name)
        )
        row = cursor.fetchone()
        if row:
            # Deserialize embedding if present
            embedding = None
            if row["embedding"]:
                import json
                try:
                    embedding = json.loads(row["embedding"].decode("utf-8"))
                except (json.JSONDecodeError, AttributeError):
                    pass

            return CodeSummaryRecord(
                id=row["id"],
                file_id=row["file_id"],
                entity_type=row["entity_type"],
                entity_name=row["entity_name"],
                signature=row["signature"],
                summary=row["summary"],
                line_number=row["line_number"],
                summary_en=row["summary_en"] or "",
                summary_zh=row["summary_zh"] or "",
                embedding=embedding,
                created_at=row["created_at"]
            )
        return None

    def get_summaries_by_file(
        self,
        file_id: int
    ) -> list[CodeSummaryRecord]:
        """Get all summaries for a file."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM code_summaries WHERE file_id = ?",
            (file_id,)
        )
        rows = cursor.fetchall()

        results = []
        for row in rows:
            # Deserialize embedding if present
            embedding = None
            if row["embedding"]:
                import json
                try:
                    embedding = json.loads(row["embedding"].decode("utf-8"))
                except (json.JSONDecodeError, AttributeError):
                    pass

            results.append(CodeSummaryRecord(
                id=row["id"],
                file_id=row["file_id"],
                entity_type=row["entity_type"],
                entity_name=row["entity_name"],
                signature=row["signature"],
                summary=row["summary"],
                line_number=row["line_number"],
                summary_en=row["summary_en"] or "",
                summary_zh=row["summary_zh"] or "",
                embedding=embedding,
                created_at=row["created_at"]
            ))
        return results

    def search_by_embedding(
        self,
        project_id: int,
        query_embedding: list[float],
        limit: int = 10
    ) -> list[CodeSummaryRecord]:
        """Search for similar code summaries by embedding (cosine similarity).

        Note: This is a simple implementation. For production use with large
        datasets, consider using a dedicated vector database.

        Args:
            project_id: Project ID
            query_embedding: Query vector
            limit: Maximum results to return

        Returns:
            List of similar code summaries sorted by similarity
        """
        import json
        import math

        cursor = self._get_cursor()

        # Get all summaries with embeddings for this project
        cursor.execute(
            """
            SELECT cs.*, f.relative_path
            FROM code_summaries cs
            JOIN files f ON cs.file_id = f.id
            WHERE f.project_id = ? AND cs.embedding IS NOT NULL
            """,
            (project_id,)
        )
        rows = cursor.fetchall()

        def cosine_similarity(a: list[float], b: list[float]) -> float:
            """Calculate cosine similarity between two vectors."""
            if not a or not b or len(a) != len(b):
                return 0.0
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot_product / (norm_a * norm_b)

        # Calculate similarity scores
        scored_results = []
        for row in rows:
            try:
                embedding = json.loads(row["embedding"].decode("utf-8"))
                similarity = cosine_similarity(query_embedding, embedding)

                record = CodeSummaryRecord(
                    id=row["id"],
                    file_id=row["file_id"],
                    entity_type=row["entity_type"],
                    entity_name=row["entity_name"],
                    signature=row["signature"],
                    summary=row["summary"],
                    line_number=row["line_number"],
                    summary_en=row["summary_en"] or "",
                    summary_zh=row["summary_zh"] or "",
                    embedding=embedding,
                    created_at=row["created_at"]
                )
                scored_results.append((similarity, record))
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

        # Sort by similarity (descending) and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [record for _, record in scored_results[:limit]]
