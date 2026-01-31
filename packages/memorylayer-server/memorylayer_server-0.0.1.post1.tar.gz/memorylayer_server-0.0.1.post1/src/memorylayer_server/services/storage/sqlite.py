"""SQLite storage backend with sqlite-vec support."""
import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from scitrera_app_framework import Plugin, Variables as Variables

from ...models.memory import Memory, RememberInput, MemoryType, MemorySubtype
from ...models.association import Association, AssociateInput, GraphQueryResult, GraphPath, RelationshipType
from ...models.workspace import Workspace, MemorySpace
from ...models.resource import Resource, ResourceType
from ...models.category import Category
from ...models.session import Session, SessionContext

from .base import StorageBackend, StoragePluginBase
from ...config import MEMORYLAYER_SQLITE_STORAGE_PATH, DEFAULT_MEMORYLAYER_SQLITE_STORAGE_PATH


def _parse_datetime_utc(dt_str: str | None) -> datetime | None:
    """Parse datetime string and ensure it's timezone-aware (UTC).

    SQLite stores datetimes as naive strings. This helper parses them
    and adds UTC timezone if not present.
    """
    if not dt_str:
        return None
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class SQLiteStorageBackend(StorageBackend):
    """SQLite storage backend with optional sqlite-vec support."""

    def __init__(self, db_path: str = "memorylayer.db"):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
        """
        super().__init__()
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._has_vec_extension = False

    async def connect(self) -> None:
        """Initialize storage connection."""
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")

        # Try to load sqlite-vec extension
        try:
            await self._connection.enable_load_extension(True)
            await self._connection.load_extension("vec0")
            self._has_vec_extension = True
            self.logger.info("sqlite-vec extension loaded successfully")
        except Exception as e:
            self.logger.warning("sqlite-vec extension not available, using fallback: %s", e)
            self._has_vec_extension = False

        # Create tables
        await self._create_tables()

        self.logger.info("Connected to SQLite database at %s", self.db_path)

    async def disconnect(self) -> None:
        """Close storage connection."""
        if self._connection:
            await self._connection.close()
            self.logger.info("Disconnected from SQLite database")

    async def health_check(self) -> bool:
        """Check if storage is healthy."""
        try:
            if self._connection:
                await self._connection.execute("SELECT 1")
                return True
            return False
        except Exception as e:
            self.logger.error("Health check failed: %s", e)
            return False

    async def _create_tables(self) -> None:
        """Create database tables."""
        # Workspaces
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS workspaces
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           tenant_id
                                           TEXT
                                           NOT
                                           NULL,
                                           name
                                           TEXT
                                           NOT
                                           NULL,
                                           settings
                                           TEXT
                                           DEFAULT
                                           '{}',
                                           created_at
                                           TEXT
                                           DEFAULT (
                                           datetime
                                       (
                                           'now'
                                       )),
                                           updated_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       ))
                                           )
                                       """)

        # Memory Spaces
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS memory_spaces
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           workspace_id
                                           TEXT
                                           NOT
                                           NULL
                                           REFERENCES
                                           workspaces
                                       (
                                           id
                                       ),
                                           name TEXT NOT NULL,
                                           description TEXT,
                                           settings TEXT DEFAULT '{}',
                                           created_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       )),
                                           UNIQUE
                                       (
                                           workspace_id,
                                           name
                                       )
                                           )
                                       """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_spaces_workspace ON memory_spaces(workspace_id)"
        )

        # Memories
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS memories
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           workspace_id
                                           TEXT
                                           NOT
                                           NULL,
                                           space_id
                                           TEXT
                                           REFERENCES
                                           memory_spaces
                                       (
                                           id
                                       ),
                                           user_id TEXT,
                                           content TEXT NOT NULL,
                                           content_hash TEXT NOT NULL,
                                           type TEXT NOT NULL CHECK
                                       (
                                           type
                                           IN
                                       (
                                           'episodic',
                                           'semantic',
                                           'procedural',
                                           'working'
                                       )),
                                           subtype TEXT,
                                           importance REAL DEFAULT 0.5,
                                           tags TEXT DEFAULT '[]',
                                           metadata TEXT DEFAULT '{}',
                                           embedding BLOB,
                                           access_count INTEGER DEFAULT 0,
                                           last_accessed_at TEXT,
                                           decay_factor REAL DEFAULT 1.0,
                                           deleted_at TEXT,
                                           created_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       )),
                                           updated_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       ))
                                           )
                                       """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_workspace ON memories(workspace_id) WHERE deleted_at IS NULL"
        )
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_workspace_type ON memories(workspace_id, type) WHERE deleted_at IS NULL"
        )

        # Create FTS5 virtual table for full-text search
        await self._connection.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                workspace_id UNINDEXED,
                content,
                tokenize='porter'
            )
        """)

        # Memory Associations
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS memory_associations
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           workspace_id
                                           TEXT
                                           NOT
                                           NULL,
                                           source_id
                                           TEXT
                                           NOT
                                           NULL
                                           REFERENCES
                                           memories
                                       (
                                           id
                                       ),
                                           target_id TEXT NOT NULL REFERENCES memories
                                       (
                                           id
                                       ),
                                           relationship TEXT NOT NULL,
                                           strength REAL DEFAULT 0.5,
                                           metadata TEXT DEFAULT '{}',
                                           created_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       )),
                                           UNIQUE
                                       (
                                           source_id,
                                           target_id,
                                           relationship
                                       )
                                           )
                                       """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_associations_workspace ON memory_associations(workspace_id)"
        )
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_associations_source ON memory_associations(source_id)"
        )
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_associations_target ON memory_associations(target_id)"
        )

        # Resources
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS resources
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           workspace_id
                                           TEXT
                                           NOT
                                           NULL,
                                           type
                                           TEXT
                                           NOT
                                           NULL,
                                           content
                                           TEXT
                                           NOT
                                           NULL,
                                           content_hash
                                           TEXT
                                           NOT
                                           NULL,
                                           metadata
                                           TEXT
                                           DEFAULT
                                           '{}',
                                           processed
                                           INTEGER
                                           DEFAULT
                                           0,
                                           extracted_items
                                           TEXT
                                           DEFAULT
                                           '[]',
                                           created_at
                                           TEXT
                                           DEFAULT (
                                           datetime
                                       (
                                           'now'
                                       ))
                                           )
                                       """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_resources_workspace ON resources(workspace_id)"
        )

        # Categories
        await self._connection.execute("""
                                       CREATE TABLE IF NOT EXISTS categories
                                       (
                                           id
                                           TEXT
                                           PRIMARY
                                           KEY,
                                           workspace_id
                                           TEXT
                                           NOT
                                           NULL,
                                           name
                                           TEXT
                                           NOT
                                           NULL,
                                           summary
                                           TEXT
                                           NOT
                                           NULL,
                                           item_ids
                                           TEXT
                                           DEFAULT
                                           '[]',
                                           last_updated
                                           TEXT
                                           DEFAULT (
                                           datetime
                                       (
                                           'now'
                                       )),
                                           created_at TEXT DEFAULT
                                       (
                                           datetime
                                       (
                                           'now'
                                       ))
                                           )
                                       """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_categories_workspace ON categories(workspace_id)"
        )

        # Sessions table (for persistent session storage)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            )
        """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_workspace ON sessions(workspace_id)"
        )
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)"
        )

        # Session context table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS session_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                ttl_seconds INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(session_id, key),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        await self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_session_contexts_session ON session_contexts(session_id)"
        )

        await self._connection.commit()

    # Memory operations
    async def create_memory(self, workspace_id: str, input: RememberInput) -> Memory:
        """Store a new memory."""
        # Compute content hash
        content_hash = hashlib.sha256(input.content.encode()).hexdigest()

        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        cursor = await self._connection.execute(
            """
            INSERT INTO memories (id, workspace_id, space_id, user_id,
                                  content, content_hash, type, subtype,
                                  importance, tags, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                workspace_id,
                input.space_id,
                input.user_id,
                input.content,
                content_hash,
                input.type.value if input.type else MemoryType.SEMANTIC.value,
                input.subtype.value if input.subtype else None,
                input.importance,
                json.dumps(input.tags),
                json.dumps(input.metadata),
                now,
                now,
            ),
        )

        # Insert into FTS index
        await self._connection.execute(
            "INSERT INTO memories_fts (id, workspace_id, content) VALUES (?, ?, ?)",
            (memory_id, workspace_id, input.content),
        )

        await self._connection.commit()

        return await self.get_memory(workspace_id, memory_id)

    async def get_memory(self, workspace_id: str, memory_id: str) -> Optional[Memory]:
        """Get memory by ID."""
        cursor = await self._connection.execute(
            """
            SELECT *
            FROM memories
            WHERE id = ?
              AND workspace_id = ?
              AND deleted_at IS NULL
            """,
            (memory_id, workspace_id),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        # Update access tracking
        await self._connection.execute(
            """
            UPDATE memories
            SET access_count     = access_count + 1,
                last_accessed_at = datetime('now')
            WHERE id = ?
            """,
            (memory_id,),
        )
        await self._connection.commit()

        return self._row_to_memory(row)

    async def update_memory(self, workspace_id: str, memory_id: str, **updates) -> Optional[Memory]:
        """Update memory fields."""
        # Build SET clause
        set_parts = []
        values = []
        for key, value in updates.items():
            if key in ("tags", "metadata"):
                set_parts.append(f"{key} = ?")
                values.append(json.dumps(value))
            elif key == "embedding":
                # Embedding is stored as binary BLOB
                set_parts.append(f"{key} = ?")
                values.append(self._serialize_embedding(value) if value else None)
            else:
                set_parts.append(f"{key} = ?")
                values.append(value)

        if not set_parts:
            return await self.get_memory(workspace_id, memory_id)

        set_parts.append("updated_at = datetime('now')")
        values.extend([memory_id, workspace_id])

        query = f"""
            UPDATE memories
            SET {', '.join(set_parts)}
            WHERE id = ? AND workspace_id = ? AND deleted_at IS NULL
        """

        cursor = await self._connection.execute(query, values)
        await self._connection.commit()

        if cursor.rowcount == 0:
            return None

        return await self.get_memory(workspace_id, memory_id)

    async def delete_memory(self, workspace_id: str, memory_id: str, hard: bool = False) -> bool:
        """Soft or hard delete memory."""
        if hard:
            cursor = await self._connection.execute(
                "DELETE FROM memories WHERE id = ? AND workspace_id = ?",
                (memory_id, workspace_id),
            )
            # Also delete from FTS index
            await self._connection.execute(
                "DELETE FROM memories_fts WHERE id = ?",
                (memory_id,),
            )
        else:
            cursor = await self._connection.execute(
                """
                UPDATE memories
                SET deleted_at = datetime('now')
                WHERE id = ?
                  AND workspace_id = ?
                """,
                (memory_id, workspace_id),
            )

        await self._connection.commit()
        return cursor.rowcount > 0

    async def search_memories(
            self,
            workspace_id: str,
            query_embedding: list[float],
            limit: int = 10,
            min_relevance: float = 0.5,
            types: Optional[list[str]] = None,
            subtypes: Optional[list[str]] = None,
            tags: Optional[list[str]] = None,
    ) -> list[tuple[Memory, float]]:
        """Vector similarity search using sqlite-vec or fallback."""
        if self._has_vec_extension:
            return await self._search_with_vec(
                workspace_id, query_embedding, limit, min_relevance, types, subtypes, tags
            )
        else:
            return await self._search_with_fallback(
                workspace_id, query_embedding, limit, min_relevance, types, subtypes, tags
            )

    async def _search_with_vec(
            self,
            workspace_id: str,
            query_embedding: list[float],
            limit: int,
            min_relevance: float,
            types: Optional[list[str]],
            subtypes: Optional[list[str]],
            tags: Optional[list[str]],
    ) -> list[tuple[Memory, float]]:
        """Search using sqlite-vec extension."""
        # Build WHERE clause
        where_parts = ["workspace_id = ?", "deleted_at IS NULL", "embedding IS NOT NULL"]
        params = [workspace_id]

        if types:
            placeholders = ",".join("?" * len(types))
            where_parts.append(f"type IN ({placeholders})")
            params.extend(types)

        if subtypes:
            placeholders = ",".join("?" * len(subtypes))
            where_parts.append(f"subtype IN ({placeholders})")
            params.extend(subtypes)

        if tags:
            for tag in tags:
                where_parts.append("tags LIKE ?")
                params.append(f'%"{tag}"%')

        where_clause = " AND ".join(where_parts)

        # Use sqlite-vec for similarity search
        query_vec_blob = self._serialize_embedding(query_embedding)
        params.append(query_vec_blob)
        params.append(limit)

        query = f"""
            SELECT *, vec_distance_cosine(embedding, ?) as distance
            FROM memories
            WHERE {where_clause}
            ORDER BY distance ASC
            LIMIT ?
        """

        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            # Convert distance to relevance (1 - distance for cosine)
            distance = row["distance"]
            relevance = 1.0 - distance

            if relevance >= min_relevance:
                memory = self._row_to_memory(row)
                results.append((memory, relevance))

        return results

    async def _search_with_fallback(
            self,
            workspace_id: str,
            query_embedding: list[float],
            limit: int,
            min_relevance: float,
            types: Optional[list[str]],
            subtypes: Optional[list[str]],
            tags: Optional[list[str]],
    ) -> list[tuple[Memory, float]]:
        """Fallback: compute cosine similarity in Python."""
        # Build WHERE clause
        where_parts = ["workspace_id = ?", "deleted_at IS NULL", "embedding IS NOT NULL"]
        params = [workspace_id]

        if types:
            placeholders = ",".join("?" * len(types))
            where_parts.append(f"type IN ({placeholders})")
            params.extend(types)

        if subtypes:
            placeholders = ",".join("?" * len(subtypes))
            where_parts.append(f"subtype IN ({placeholders})")
            params.extend(subtypes)

        if tags:
            for tag in tags:
                where_parts.append("tags LIKE ?")
                params.append(f'%"{tag}"%')

        where_clause = " AND ".join(where_parts)

        query = f"SELECT * FROM memories WHERE {where_clause}"
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        # Compute cosine similarity in Python
        results = []
        for row in rows:
            if row["embedding"]:
                embedding = self._deserialize_embedding(row["embedding"])
                relevance = self._cosine_similarity(query_embedding, embedding)

                if relevance >= min_relevance:
                    memory = self._row_to_memory(row)
                    results.append((memory, relevance))

        # Sort by relevance descending and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def full_text_search(
            self,
            workspace_id: str,
            query: str,
            limit: int = 10,
    ) -> list[Memory]:
        """Full-text search using SQLite FTS5."""
        cursor = await self._connection.execute(
            """
            SELECT m.*
            FROM memories m
                     INNER JOIN memories_fts fts ON m.id = fts.id
            WHERE fts.workspace_id = ?
              AND fts.content MATCH ?
              AND m.deleted_at IS NULL LIMIT ?
            """,
            (workspace_id, query, limit),
        )
        rows = await cursor.fetchall()

        return [self._row_to_memory(row) for row in rows]

    async def get_memory_by_hash(self, workspace_id: str, content_hash: str) -> Optional[Memory]:
        """Get memory by content hash for deduplication."""
        cursor = await self._connection.execute(
            """
            SELECT *
            FROM memories
            WHERE workspace_id = ?
              AND content_hash = ?
              AND deleted_at IS NULL LIMIT 1
            """,
            (workspace_id, content_hash),
        )
        row = await cursor.fetchone()
        return self._row_to_memory(row) if row else None

    # Association operations
    async def create_association(self, workspace_id: str, input: AssociateInput) -> Association:
        """Create graph edge between memories."""
        association_id = f"assoc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        await self._connection.execute(
            """
            INSERT INTO memory_associations (id, workspace_id, source_id, target_id,
                                             relationship, strength, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                association_id,
                workspace_id,
                input.source_id,
                input.target_id,
                input.relationship.value,
                input.strength,
                json.dumps(input.metadata),
                now,
            ),
        )
        await self._connection.commit()

        cursor = await self._connection.execute(
            "SELECT * FROM memory_associations WHERE id = ?",
            (association_id,),
        )
        row = await cursor.fetchone()

        return self._row_to_association(row)

    async def get_associations(
            self,
            workspace_id: str,
            memory_id: str,
            direction: str = "both",
            relationships: Optional[list[str]] = None,
    ) -> list[Association]:
        """Get associations for a memory."""
        # Build WHERE clause
        where_parts = ["workspace_id = ?"]
        params = [workspace_id]

        if direction == "outgoing":
            where_parts.append("source_id = ?")
            params.append(memory_id)
        elif direction == "incoming":
            where_parts.append("target_id = ?")
            params.append(memory_id)
        else:  # both
            where_parts.append("(source_id = ? OR target_id = ?)")
            params.extend([memory_id, memory_id])

        if relationships:
            placeholders = ",".join("?" * len(relationships))
            where_parts.append(f"relationship IN ({placeholders})")
            params.extend(relationships)

        where_clause = " AND ".join(where_parts)

        cursor = await self._connection.execute(
            f"SELECT * FROM memory_associations WHERE {where_clause}",
            params,
        )
        rows = await cursor.fetchall()

        return [self._row_to_association(row) for row in rows]

    async def traverse_graph(
            self,
            workspace_id: str,
            start_id: str,
            max_depth: int = 3,
            relationships: Optional[list[str]] = None,
            direction: str = "both",
    ) -> GraphQueryResult:
        """Multi-hop graph traversal using recursive CTE."""
        # Build recursive CTE
        # Note: Use separate filters for base case (no table alias) and recursive case (with 'a.' prefix)
        base_rel_filter = ""
        recursive_rel_filter = ""
        if relationships:
            rel_list = ", ".join([f"'{r}'" for r in relationships])
            base_rel_filter = f"AND relationship IN ({rel_list})"
            recursive_rel_filter = f"AND a.relationship IN ({rel_list})"

        # Build direction condition for join and next node selection
        if direction == "outgoing":
            direction_condition = "a.source_id = gt.current_node"
            next_node = "a.target_id"
            # Base case: start from associations where source_id = start_id
            base_start_condition = "source_id = ?"
            base_current_node = "target_id"
        elif direction == "incoming":
            direction_condition = "a.target_id = gt.current_node"
            next_node = "a.source_id"
            # Base case: start from associations where target_id = start_id (finding who points to us)
            base_start_condition = "target_id = ?"
            base_current_node = "source_id"
        else:  # both
            direction_condition = "(a.source_id = gt.current_node OR a.target_id = gt.current_node)"
            next_node = "CASE WHEN a.source_id = gt.current_node THEN a.target_id ELSE a.source_id END"
            # Base case: start from associations where start_id is either source or target
            base_start_condition = "(source_id = ? OR target_id = ?)"
            base_current_node = "CASE WHEN source_id = ? THEN target_id ELSE source_id END"

        # Build params based on direction
        # For "both" direction, the CASE WHEN in SELECT needs start_id first
        # Params order: [SELECT CASE placeholder], WHERE workspace_id, WHERE condition placeholders
        if direction == "both":
            # CASE WHEN source_id = ? (start_id), workspace_id = ?, source_id = ? OR target_id = ?
            base_case_params = (start_id, workspace_id, start_id, start_id)
        else:
            # workspace_id = ?, start_condition = ?
            base_case_params = (workspace_id, start_id)

        query = f"""
        WITH RECURSIVE graph_traverse(
            id, source_id, target_id, relationship, strength, metadata, created_at,
            depth, current_node, path
        ) AS (
            -- Base case
            SELECT
                id, source_id, target_id, relationship, strength, metadata, created_at,
                1 as depth,
                {base_current_node} as current_node,
                json_array(source_id, target_id) as path
            FROM memory_associations
            WHERE workspace_id = ?
              AND {base_start_condition}
              {base_rel_filter}

            UNION

            -- Recursive case
            SELECT
                a.id, a.source_id, a.target_id, a.relationship, a.strength, a.metadata, a.created_at,
                gt.depth + 1,
                {next_node},
                json_insert(gt.path, '$[#]', {next_node})
            FROM memory_associations a
            INNER JOIN graph_traverse gt ON (
                {direction_condition}
                AND a.workspace_id = ?
                {recursive_rel_filter}
                AND gt.depth < ?
            )
            WHERE NOT EXISTS (
                SELECT 1 FROM json_each(gt.path)
                WHERE json_each.value = {next_node}
            )
        )
        SELECT * FROM graph_traverse;
        """

        # Build final parameters: base_case_params + recursive_case_params
        params = base_case_params + (workspace_id, max_depth)
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()

        # Build paths from results
        paths = []
        unique_nodes = set([start_id])

        for row in rows:
            path_nodes = json.loads(row["path"])
            unique_nodes.update(path_nodes)

            # Create association edge
            edge = Association(
                id=row["id"],
                workspace_id=workspace_id,
                source_id=row["source_id"],
                target_id=row["target_id"],
                relationship=RelationshipType(row["relationship"]),
                strength=row["strength"],
                metadata=json.loads(row["metadata"]),
                created_at=_parse_datetime_utc(row["created_at"]),
            )

            path = GraphPath(
                nodes=path_nodes,
                edges=[edge],
                total_strength=row["strength"],
                depth=row["depth"],
            )
            paths.append(path)

        return GraphQueryResult(
            paths=paths,
            total_paths=len(paths),
            unique_nodes=list(unique_nodes),
            query_latency_ms=0,
        )

    # Workspace operations
    async def create_workspace(self, workspace: Workspace) -> Workspace:
        """Create workspace."""
        await self._connection.execute(
            """
            INSERT INTO workspaces (id, tenant_id, name, settings, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                workspace.id,
                workspace.tenant_id,
                workspace.name,
                json.dumps(workspace.settings),
                workspace.created_at.isoformat(),
                workspace.updated_at.isoformat(),
            ),
        )
        await self._connection.commit()

        return workspace

    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM workspaces WHERE id = ?",
            (workspace_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_workspace(row)

    # Memory Space operations
    async def create_memory_space(self, workspace_id: str, space: MemorySpace) -> MemorySpace:
        """Create a memory space within a workspace."""
        await self._connection.execute(
            """
            INSERT INTO memory_spaces (id, workspace_id, name, description, settings, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                space.id,
                workspace_id,
                space.name,
                space.description,
                json.dumps(space.settings),
                space.created_at.isoformat(),
            ),
        )
        await self._connection.commit()

        return space

    async def get_memory_space(self, workspace_id: str, space_id: str) -> Optional[MemorySpace]:
        """Get memory space by ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM memory_spaces WHERE id = ? AND workspace_id = ?",
            (space_id, workspace_id),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_memory_space(row)

    async def list_memory_spaces(self, workspace_id: str) -> list[MemorySpace]:
        """List all memory spaces in a workspace."""
        cursor = await self._connection.execute(
            "SELECT * FROM memory_spaces WHERE workspace_id = ? ORDER BY created_at",
            (workspace_id,),
        )
        rows = await cursor.fetchall()

        return [self._row_to_memory_space(row) for row in rows]

    # Resource operations
    async def create_resource(self, workspace_id: str, resource: Resource) -> Resource:
        """Store raw resource."""
        await self._connection.execute(
            """
            INSERT INTO resources (id, workspace_id, type, content, content_hash,
                                   metadata, processed, extracted_items, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resource.id,
                workspace_id,
                resource.type.value,
                json.dumps(resource.content),
                resource.content_hash,
                json.dumps(resource.metadata),
                1 if resource.processed else 0,
                json.dumps(resource.extracted_items),
                resource.created_at.isoformat(),
            ),
        )
        await self._connection.commit()

        return resource

    async def get_resource(self, workspace_id: str, resource_id: str) -> Optional[Resource]:
        """Get resource by ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM resources WHERE id = ? AND workspace_id = ?",
            (resource_id, workspace_id),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_resource(row)

    # Category operations
    async def get_or_create_category(self, workspace_id: str, name: str) -> Category:
        """Get existing or create new category."""
        # Try to get existing
        cursor = await self._connection.execute(
            "SELECT * FROM categories WHERE workspace_id = ? AND name = ?",
            (workspace_id, name.lower()),
        )
        row = await cursor.fetchone()

        if row:
            return self._row_to_category(row)

        # Create new
        category_id = f"cat_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        await self._connection.execute(
            """
            INSERT INTO categories (id, workspace_id, name, summary, item_ids, last_updated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (category_id, workspace_id, name.lower(), f"Category: {name}", "[]", now, now),
        )
        await self._connection.commit()

        return await self.get_or_create_category(workspace_id, name)

    async def update_category_summary(
            self,
            workspace_id: str,
            category_id: str,
            summary: str,
            item_ids: list[str]
    ) -> Category:
        """Update category summary."""
        cursor = await self._connection.execute(
            """
            UPDATE categories
            SET summary      = ?,
                item_ids     = ?,
                last_updated = datetime('now')
            WHERE id = ?
              AND workspace_id = ?
            """,
            (summary, json.dumps(item_ids), category_id, workspace_id),
        )
        await self._connection.commit()

        if cursor.rowcount == 0:
            raise ValueError(f"Category {category_id} not found")

        cursor = await self._connection.execute(
            "SELECT * FROM categories WHERE id = ?",
            (category_id,),
        )
        row = await cursor.fetchone()

        return self._row_to_category(row)

    # Statistics
    async def get_workspace_stats(self, workspace_id: str) -> dict:
        """Get memory statistics for workspace."""
        # Count memories by type
        cursor = await self._connection.execute(
            """
            SELECT type, COUNT(*) as count
            FROM memories
            WHERE workspace_id = ? AND deleted_at IS NULL
            GROUP BY type
            """,
            (workspace_id,),
        )
        type_counts = {row["type"]: row["count"] for row in await cursor.fetchall()}

        # Count associations
        cursor = await self._connection.execute(
            "SELECT COUNT(*) as count FROM memory_associations WHERE workspace_id = ?",
            (workspace_id,),
        )
        assoc_count = (await cursor.fetchone())["count"]

        # Count categories
        cursor = await self._connection.execute(
            "SELECT COUNT(*) as count FROM categories WHERE workspace_id = ?",
            (workspace_id,),
        )
        category_count = (await cursor.fetchone())["count"]

        return {
            "total_memories": sum(type_counts.values()),
            "memories_by_type": type_counts,
            "total_associations": assoc_count,
            "total_categories": category_count,
        }

    # Session operations
    async def create_session(self, workspace_id: str, session: Session) -> Session:
        """Store a new session."""
        await self._connection.execute(
            """
            INSERT INTO sessions (id, workspace_id, user_id, metadata, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                workspace_id,
                session.user_id,
                json.dumps(session.metadata),
                session.expires_at.isoformat(),
                session.created_at.isoformat(),
            ),
        )
        await self._connection.commit()
        self.logger.info("Created persistent session: %s in workspace: %s", session.id, workspace_id)
        return session

    async def get_session(self, workspace_id: str, session_id: str) -> Optional[Session]:
        """Get session by ID (returns None if not found or expired)."""
        cursor = await self._connection.execute(
            "SELECT * FROM sessions WHERE id = ? AND workspace_id = ?",
            (session_id, workspace_id),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        session = self._row_to_session(row)

        # Check expiration
        if session.is_expired:
            self.logger.info("Session expired: %s, cleaning up", session_id)
            await self.delete_session(workspace_id, session_id)
            return None

        return session

    async def delete_session(self, workspace_id: str, session_id: str) -> bool:
        """Delete session and all its context (CASCADE)."""
        cursor = await self._connection.execute(
            "DELETE FROM sessions WHERE id = ? AND workspace_id = ?",
            (session_id, workspace_id),
        )
        await self._connection.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            self.logger.info("Deleted session: %s", session_id)
        return deleted

    async def set_session_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> SessionContext:
        """Set context key-value within session."""
        now = datetime.now(timezone.utc)

        # Use INSERT OR REPLACE for upsert behavior
        await self._connection.execute(
            """
            INSERT INTO session_contexts (session_id, workspace_id, key, value, ttl_seconds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, key) DO UPDATE SET
                value = excluded.value,
                ttl_seconds = excluded.ttl_seconds,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                workspace_id,
                key,
                json.dumps(value),
                ttl_seconds,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        await self._connection.commit()

        return SessionContext(
            session_id=session_id,
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            created_at=now,
            updated_at=now,
        )

    async def get_session_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str
    ) -> Optional[SessionContext]:
        """Get specific context entry."""
        cursor = await self._connection.execute(
            "SELECT * FROM session_contexts WHERE session_id = ? AND workspace_id = ? AND key = ?",
            (session_id, workspace_id, key),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return self._row_to_session_context(row)

    async def get_all_session_context(
        self,
        workspace_id: str,
        session_id: str
    ) -> list[SessionContext]:
        """Get all context entries for session."""
        cursor = await self._connection.execute(
            "SELECT * FROM session_contexts WHERE session_id = ? AND workspace_id = ?",
            (session_id, workspace_id),
        )
        rows = await cursor.fetchall()

        return [self._row_to_session_context(row) for row in rows]

    async def cleanup_expired_sessions(self, workspace_id: str) -> int:
        """Delete all expired sessions."""
        now = datetime.now(timezone.utc).isoformat()

        cursor = await self._connection.execute(
            "DELETE FROM sessions WHERE workspace_id = ? AND expires_at < ?",
            (workspace_id, now),
        )
        await self._connection.commit()

        return cursor.rowcount

    # Helper methods
    def _row_to_memory(self, row: aiosqlite.Row) -> Memory:
        """Convert database row to Memory domain model."""
        return Memory(
            id=row["id"],
            workspace_id=row["workspace_id"],
            space_id=row["space_id"],
            user_id=row["user_id"],
            content=row["content"],
            content_hash=row["content_hash"],
            type=MemoryType(row["type"]),
            subtype=MemorySubtype(row["subtype"]) if row["subtype"] else None,
            importance=row["importance"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            embedding=self._deserialize_embedding(row["embedding"]) if row["embedding"] else None,
            access_count=row["access_count"],
            last_accessed_at=_parse_datetime_utc(row["last_accessed_at"]),
            decay_factor=row["decay_factor"],
            created_at=_parse_datetime_utc(row["created_at"]),
            updated_at=_parse_datetime_utc(row["updated_at"]),
        )

    def _row_to_association(self, row: aiosqlite.Row) -> Association:
        """Convert database row to Association domain model."""
        return Association(
            id=row["id"],
            workspace_id=row["workspace_id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relationship=RelationshipType(row["relationship"]),
            strength=row["strength"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=_parse_datetime_utc(row["created_at"]),
        )

    def _row_to_workspace(self, row: aiosqlite.Row) -> Workspace:
        """Convert database row to Workspace domain model."""
        return Workspace(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            settings=json.loads(row["settings"]) if row["settings"] else {},
            created_at=_parse_datetime_utc(row["created_at"]),
            updated_at=_parse_datetime_utc(row["updated_at"]),
        )

    def _row_to_memory_space(self, row: aiosqlite.Row) -> MemorySpace:
        """Convert database row to MemorySpace domain model."""
        return MemorySpace(
            id=row["id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            description=row["description"],
            settings=json.loads(row["settings"]) if row["settings"] else {},
            created_at=_parse_datetime_utc(row["created_at"]),
        )

    def _row_to_resource(self, row: aiosqlite.Row) -> Resource:
        """Convert database row to Resource domain model."""
        return Resource(
            id=row["id"],
            workspace_id=row["workspace_id"],
            type=ResourceType(row["type"]),
            content=json.loads(row["content"]),
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            processed=bool(row["processed"]),
            extracted_items=json.loads(row["extracted_items"]) if row["extracted_items"] else [],
            created_at=_parse_datetime_utc(row["created_at"]),
        )

    def _row_to_category(self, row: aiosqlite.Row) -> Category:
        """Convert database row to Category domain model."""
        return Category(
            id=row["id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            summary=row["summary"],
            item_ids=json.loads(row["item_ids"]) if row["item_ids"] else [],
            last_updated=_parse_datetime_utc(row["last_updated"]),
            created_at=_parse_datetime_utc(row["created_at"]),
        )

    def _row_to_session(self, row: aiosqlite.Row) -> Session:
        """Convert database row to Session domain model."""
        return Session(
            id=row["id"],
            workspace_id=row["workspace_id"],
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            expires_at=_parse_datetime_utc(row["expires_at"]),
            created_at=_parse_datetime_utc(row["created_at"]),
        )

    def _row_to_session_context(self, row: aiosqlite.Row) -> SessionContext:
        """Convert database row to SessionContext domain model."""
        return SessionContext(
            session_id=row["session_id"],
            key=row["key"],
            value=json.loads(row["value"]) if row["value"] else None,
            ttl_seconds=row["ttl_seconds"],
            created_at=_parse_datetime_utc(row["created_at"]),
            updated_at=_parse_datetime_utc(row["updated_at"]),
        )

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        """Serialize embedding to binary format for storage."""
        import struct
        return struct.pack(f'{len(embedding)}f', *embedding)

    def _deserialize_embedding(self, blob: bytes) -> list[float]:
        """Deserialize embedding from binary format."""
        import struct
        num_floats = len(blob) // 4
        return list(struct.unpack(f'{num_floats}f', blob))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            raise ValueError("Vectors must have same length")

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


class SqliteStorageBackendPlugin(StoragePluginBase):
    PROVIDER_NAME = 'sqlite'

    def initialize(self, v: Variables, logger: Logger) -> object | None:
        return SQLiteStorageBackend(
            db_path=v.environ(MEMORYLAYER_SQLITE_STORAGE_PATH, default=DEFAULT_MEMORYLAYER_SQLITE_STORAGE_PATH)
        )
