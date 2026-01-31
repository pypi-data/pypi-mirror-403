"""
PostgreSQL Metadata Store Implementation

Stores metadata in PostgreSQL tables within a dedicated schema.
"""

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import psycopg2  # type: ignore[import-untyped]
from alembic.runtime.migration import MigrationContext
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]
from sqlalchemy import create_engine

from pycharter.metadata_store.client import MetadataStoreClient

if TYPE_CHECKING:
    from psycopg2.extensions import (
        connection as Psycopg2Connection,  # type: ignore[import-untyped]
    )
else:
    Psycopg2Connection = Any

try:
    from pycharter.config import get_database_url
except ImportError:
    def get_database_url() -> Optional[str]:  # type: ignore[misc]
        return None


class PostgresMetadataStore(MetadataStoreClient):
    """
    PostgreSQL metadata store implementation.

    Stores metadata in PostgreSQL tables within the specified schema (default: "pycharter"):
    - schemas: JSON Schema definitions
    - governance_rules: Governance rules
    - ownership: Ownership information
    - metadata: Additional metadata
    - coercion_rules: Coercion rules for data transformation
    - validation_rules: Validation rules for data validation

    Connection string format: postgresql://[user[:password]@][host][:port][/database]

    The schema namespace is automatically created if it doesn't exist when connecting.
    However, tables must be initialized separately using 'pycharter db init' (similar to
    'airflow db init'). All tables are created in the specified schema (not in the public schema).

    Example:
        >>> # First, initialize the database schema
        >>> # Run: pycharter db init postgresql://user:pass@localhost/pycharter
        >>>
        >>> # Then connect
        >>> store = PostgresMetadataStore("postgresql://user:pass@localhost/pycharter")
        >>> store.connect()  # Only connects and validates schema
        >>> schema_id = store.store_schema("user", {"type": "object"}, version="1.0")
        >>> store.store_coercion_rules(schema_id, {"age": "coerce_to_integer"}, version="1.0")
        >>> store.store_validation_rules(schema_id, {"age": {"is_positive": {}}}, version="1.0")

    To use a different schema name:
        >>> store = PostgresMetadataStore(
        ...     "postgresql://user:pass@localhost/pycharter",
        ...     schema_name="my_custom_schema"
        ... )
    """

    def __init__(
        self, connection_string: Optional[str] = None, schema_name: str = "pycharter"
    ):
        """
        Initialize PostgreSQL metadata store.

        Args:
            connection_string: Optional PostgreSQL connection string.
                              If not provided, will use configuration from:
                              - PYCHARTER__DATABASE__SQL_ALCHEMY_CONN env var
                              - PYCHARTER_DATABASE_URL env var
                              - pycharter.cfg config file
                              - alembic.ini config file
            schema_name: PostgreSQL schema name to use (default: "pycharter")
        """
        # Try to get connection string from config if not provided
        if not connection_string:
            connection_string = get_database_url()

        if not connection_string:
            raise ValueError(
                "connection_string is required. Provide it directly, or configure it via:\n"
                "  - Environment variable: PYCHARTER__DATABASE__SQL_ALCHEMY_CONN or PYCHARTER_DATABASE_URL\n"
                "  - Config file: pycharter.cfg [database] sql_alchemy_conn\n"
                "  - Config file: alembic.ini sqlalchemy.url"
            )

        super().__init__(connection_string)
        self.schema_name = schema_name
        self._connection: Optional["Psycopg2Connection"] = None

    def connect(self, validate_schema_on_connect: bool = True) -> None:
        """
        Connect to PostgreSQL and validate schema.

        Args:
            validate_schema_on_connect: If True, validate that tables exist after connection

        Raises:
            ValueError: If connection_string is missing
            RuntimeError: If schema validation fails (tables don't exist)

        Note:
            This method only connects and validates. To initialize the database schema,
            run 'pycharter db init' first (similar to 'airflow db init').
        """
        if not self.connection_string:
            raise ValueError("connection_string is required for PostgreSQL")

        self._connection = psycopg2.connect(self.connection_string)
        self._ensure_schema_exists()
        self._set_search_path()

        if validate_schema_on_connect and not self._is_schema_initialized():
            raise RuntimeError(
                "Database schema is not initialized. "
                "Please run 'pycharter db init' to initialize the schema first.\n"
                f"Example: pycharter db init {self.connection_string}"
            )

    def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ============================================================================
    # Connection Management Helpers
    # ============================================================================

    def _ensure_schema_exists(self) -> None:
        """Create the PostgreSQL schema namespace if it doesn't exist."""
        if self._connection is None:
            return

        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
            conn.commit()

    def _set_search_path(self) -> None:
        """Set search_path to use the schema."""
        if self._connection is None:
            return

        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.schema_name}", public')
            conn.commit()

    def _is_schema_initialized(self) -> bool:
        """Check if the database schema is initialized."""
        if self._connection is None:
            return False

        try:
            with self._connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = 'schemas'
                    )
                """,
                    (self.schema_name,),
                )
                return cur.fetchone()[0]
        except Exception:
            return False

    def _require_connection(self) -> None:
        """Raise error if not connected."""
        if self._connection is None:
            raise RuntimeError("Not connected. Call connect() first.")

    def _get_connection(self) -> "Psycopg2Connection":
        """Get connection, raising error if not connected."""
        if self._connection is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._connection

    def _parse_jsonb(self, value: Any) -> Dict[str, Any]:
        """Parse JSONB value (psycopg2 may return dict or str)."""
        if isinstance(value, str):
            return json.loads(value)
        return value if value is not None else {}

    def _table_name(self, table: str) -> str:
        """Get fully qualified table name."""
        return f'"{self.schema_name}".{table}'

    # ============================================================================
    # Schema Info
    # ============================================================================

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the current database schema.

        Returns:
            Dictionary with schema information:
            {
                "revision": str or None,
                "initialized": bool,
                "message": str
            }
        """
        self._require_connection()

        initialized = self._is_schema_initialized()
        revision = None

        if initialized:
            try:
                if self.connection_string is None:
                    raise ValueError("connection_string is required")
                engine = create_engine(self.connection_string)
                with engine.connect() as conn:
                    context = MigrationContext.configure(conn)
                    revision = context.get_current_revision()
            except Exception:
                pass

        message = f"Schema initialized: {initialized}"
        if revision:
            message += f" (revision: {revision})"

        return {
            "revision": revision,
            "initialized": initialized,
            "message": message,
        }

    # ============================================================================
    # Schema Operations
    # ============================================================================

    def _get_or_create_data_contract(
        self,
        contract_name: str,
        version: str,
        status: str = "active",
        description: Optional[str] = None,
    ) -> int:
        """Get or create a data_contract record with validated name."""
        # Validate contract name
        from pycharter.shared.name_validator import validate_name
        contract_name = validate_name(contract_name, field_name="contract_name")
        """
        Get or create a data_contract record.

        Args:
            contract_name: Data contract name
            version: Contract version
            status: Contract status (default: "active")
            description: Optional description

        Returns:
            Data contract ID
        """
        self._require_connection()
        conn = self._get_connection()

        with conn.cursor() as cur:
            # Try to get existing data contract
            cur.execute(
                f"""
                SELECT id FROM {self._table_name("data_contracts")}
                WHERE name = %s AND version = %s
                """,
                (contract_name, version),
            )

            row = cur.fetchone()
            if row:
                return row[0]

            # Create new data contract (schema_id will be set later)
            cur.execute(
                f"""
                INSERT INTO {self._table_name("data_contracts")} 
                    (id, name, version, status, description)
                VALUES (gen_random_uuid(), %s, %s, %s, %s)
                RETURNING id
                """,
                (contract_name, version, status, description),
            )

            data_contract_id = cur.fetchone()[0]
            conn.commit()
            return data_contract_id

    def store_schema(
        self,
        schema_name: str,
        schema: Dict[str, Any],
        version: str,
    ) -> str:
        """
        Store a schema in PostgreSQL.

        Args:
            schema_name: Name/identifier for the schema (used as data_contract name)
            schema: JSON Schema dictionary
            version: Required version string (must match schema["version"] if present)

        Returns:
            Schema ID as string

        Raises:
            ValueError: If version is missing or doesn't match schema version
        """
        self._require_connection()
        conn = self._get_connection()

        # Schema artifact version is independent of data contract version
        # Extract schema artifact version from schema itself, or use a default
        schema_artifact_version = schema.get("version")
        if not schema_artifact_version:
            # If schema doesn't have a version, use the provided version as fallback
            # but add it to the schema dict for consistency
            schema = dict(schema)
            schema["version"] = version
            schema_artifact_version = version
        else:
            # Ensure schema dict has the version field
            if "version" not in schema:
                schema = dict(schema)
                schema["version"] = schema_artifact_version

        # Get or create data contract (uses data contract version, independent of schema artifact version)
        data_contract_id = self._get_or_create_data_contract(
            contract_name=schema_name,
            version=version,  # This is the data contract version
            description=schema.get("description"),
        )

        # Get title from schema or use schema_name
        # Validate both schema_name and title
        from pycharter.shared.name_validator import validate_name
        
        schema_name = validate_name(schema_name, field_name="schema_name")
        title = schema.get("title") or schema_name
        if title:
            title = validate_name(str(title), field_name="schema.title")

        with conn.cursor() as cur:
            # Check if schema with same title and version already exists (globally unique)
            # Use schema artifact version, not data contract version
            cur.execute(
                f"""
                SELECT id FROM {self._table_name("schemas")}
                WHERE title = %s AND version = %s
                """,
                (title, schema_artifact_version),
            )

            existing = cur.fetchone()

            if existing:
                # Prevent overwriting existing schemas - raise error instead
                raise ValueError(
                    f"Schema with title '{title}' and version '{schema_artifact_version}' already exists. "
                    f"Cannot create duplicate artifacts. Use a different version number."
                )
            else:
                # Insert new schema (use schema artifact version)
                cur.execute(
                    f"""
                    INSERT INTO {self._table_name("schemas")} 
                        (id, title, data_contract_id, version, schema_data)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (title, data_contract_id, schema_artifact_version, json.dumps(schema)),
                )
                schema_id = cur.fetchone()[0]

            # Update data_contract with schema_id (no version field - UUID is sufficient)
            cur.execute(
                f"""
                UPDATE {self._table_name("data_contracts")}
                SET schema_id = %s
                WHERE id = %s
                """,
                (schema_id, data_contract_id),
            )

            conn.commit()
            return str(schema_id)

    def get_schema(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a schema by ID and optional version.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, returns latest version)

        Returns:
            Schema dictionary with version included, or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if version:
                    cur.execute(
                        f"""
                        SELECT schema_data, version 
                        FROM {self._table_name("schemas")}
                        WHERE id = %s AND version = %s
                        """,
                        (schema_id, version),
                    )
                else:
                    cur.execute(
                        f"""
                        SELECT schema_data, version 
                        FROM {self._table_name("schemas")}
                        WHERE id = %s 
                        ORDER BY version DESC 
                        LIMIT 1
                        """,
                        (schema_id,),
                    )

                row = cur.fetchone()
                if not row:
                    return None

                schema_data = self._parse_jsonb(row["schema_data"])
                stored_version = row.get("version")

                # Ensure schema has version
                if "version" not in schema_data:
                    schema_data = dict(schema_data)
                    schema_data["version"] = stored_version or "1.0.0"

                return schema_data
        except Exception as e:
            # Rollback on error to prevent transaction issues
            conn.rollback()
            raise

    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all stored schemas."""
        self._require_connection()
        conn = self._get_connection()

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT s.id, s.title, s.version, dc.name as data_contract_name
                FROM {self._table_name("schemas")} s
                LEFT JOIN {self._table_name("data_contracts")} dc 
                    ON s.data_contract_id = dc.id
                ORDER BY s.title, s.version
                """
            )
            return [
                {
                    "id": str(row["id"]),
                    "name": row.get("data_contract_name") or row.get("title"),
                    "title": row.get("title"),
                    "version": row.get("version"),
                }
                for row in cur.fetchall()
            ]

    # ============================================================================
    # Metadata Operations - Helper Methods
    # ============================================================================

    def _get_or_create_owner(self, cur: Any, owner_id: str) -> str:
        """
        Get or create an owner by ID (string).
        
        Args:
            cur: Database cursor
            owner_id: Owner identifier
            
        Returns:
            Owner ID
        """
        cur.execute(
            f"SELECT id FROM {self._table_name('owners')} WHERE id = %s",
            (owner_id,),
        )
        existing = cur.fetchone()
        if not existing:
            # Create owner with just the ID (name defaults to id)
            cur.execute(
                f"""
                INSERT INTO {self._table_name('owners')} (id, name)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (owner_id, owner_id),
            )
        return owner_id

    def _get_or_create_system(self, cur: Any, system_name: str) -> str:
        """
        Get or create a system by name, return system UUID.
        
        Args:
            cur: Database cursor
            system_name: System name
            
        Returns:
            System UUID as string
        """
        cur.execute(
            f"SELECT id FROM {self._table_name('systems')} WHERE name = %s",
            (system_name,),
        )
        existing = cur.fetchone()
        if existing:
            return str(existing[0])
        # Create new system
        cur.execute(
            f"""
            INSERT INTO {self._table_name('systems')} (id, name)
            VALUES (gen_random_uuid(), %s)
            RETURNING id
            """,
            (system_name,),
        )
        return str(cur.fetchone()[0])

    def _get_or_create_domain(self, cur: Any, domain_name: str) -> str:
        """
        Get or create a domain by name, return domain UUID.
        
        Args:
            cur: Database cursor
            domain_name: Domain name
            
        Returns:
            Domain UUID as string
        """
        cur.execute(
            f"SELECT id FROM {self._table_name('domains')} WHERE name = %s",
            (domain_name,),
        )
        existing = cur.fetchone()
        if existing:
            return str(existing[0])
        # Create new domain
        cur.execute(
            f"""
            INSERT INTO {self._table_name('domains')} (id, name)
            VALUES (gen_random_uuid(), %s)
            RETURNING id
            """,
            (domain_name,),
        )
        return str(cur.fetchone()[0])

    def _clear_metadata_relationships(self, cur: Any, metadata_id: str) -> None:
        """
        Clear all existing relationships for a metadata record.
        
        Args:
            cur: Database cursor
            metadata_id: Metadata record ID
        """
        join_tables = [
            'metadata_record_business_owners',
            'metadata_record_bu_sme',
            'metadata_record_it_application_owners',
            'metadata_record_it_sme',
            'metadata_record_support_lead',
            'metadata_record_system_pulls',
            'metadata_record_system_pushes',
            'metadata_record_system_sources',
            'metadata_record_domains',
        ]
        for table in join_tables:
            cur.execute(
                f"DELETE FROM {self._table_name(table)} WHERE metadata_record_id = %s",
                (metadata_id,),
            )

    def _store_ownership_relationship(
        self, cur: Any, metadata_id: str, owner_id: str, relationship_type: str
    ) -> None:
        """
        Store an ownership relationship in the appropriate join table.
        
        Args:
            cur: Database cursor
            metadata_id: Metadata record ID
            owner_id: Owner ID
            relationship_type: Type of relationship (business_owners, bu_sme, etc.)
        """
        table_map = {
            'business_owners': 'metadata_record_business_owners',
            'bu_sme': 'metadata_record_bu_sme',
            'it_application_owners': 'metadata_record_it_application_owners',
            'it_sme': 'metadata_record_it_sme',
            'support_lead': 'metadata_record_support_lead',
        }
        
        table = table_map.get(relationship_type)
        if not table:
            raise ValueError(f"Unknown ownership relationship type: {relationship_type}")
        
        self._get_or_create_owner(cur, owner_id)
        cur.execute(
            f"""
            INSERT INTO {self._table_name(table)}
            (id, metadata_record_id, owner_id)
            VALUES (gen_random_uuid(), %s, %s)
            ON CONFLICT (metadata_record_id, owner_id) DO NOTHING
            """,
            (metadata_id, owner_id),
        )

    def _store_system_relationship(
        self, cur: Any, metadata_id: str, system_name: str, relationship_type: str
    ) -> None:
        """
        Store a system relationship in the appropriate join table.
        
        Args:
            cur: Database cursor
            metadata_id: Metadata record ID
            system_name: System name
            relationship_type: Type of relationship (pulls_from, pushes_to, system_sources)
        """
        table_map = {
            'pulls_from': 'metadata_record_system_pulls',
            'pushes_to': 'metadata_record_system_pushes',
            'system_sources': 'metadata_record_system_sources',
        }
        
        table = table_map.get(relationship_type)
        if not table:
            raise ValueError(f"Unknown system relationship type: {relationship_type}")
        
        system_id = self._get_or_create_system(cur, system_name)
        cur.execute(
            f"""
            INSERT INTO {self._table_name(table)}
            (id, metadata_record_id, system_id)
            VALUES (gen_random_uuid(), %s, %s::uuid)
            ON CONFLICT (metadata_record_id, system_id) DO NOTHING
            """,
            (metadata_id, system_id),
        )

    def _get_metadata_relationships(
        self, cur: Any, metadata_record_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve all relationships for a metadata record.
        
        Args:
            cur: Database cursor
            metadata_record_id: Metadata record ID
            
        Returns:
            Dictionary containing all relationship data
        """
        relationships: Dict[str, Any] = {}

        # Get system relationships
        system_queries = {
            'pulls_from': (
                'metadata_record_system_pulls',
                'SELECT s.name FROM {table} mrsp JOIN {systems} s ON mrsp.system_id = s.id WHERE mrsp.metadata_record_id = %s ORDER BY s.name'
            ),
            'pushes_to': (
                'metadata_record_system_pushes',
                'SELECT s.name FROM {table} mrsp JOIN {systems} s ON mrsp.system_id = s.id WHERE mrsp.metadata_record_id = %s ORDER BY s.name'
            ),
            'system_sources': (
                'metadata_record_system_sources',
                'SELECT s.name FROM {table} mrss JOIN {systems} s ON mrss.system_id = s.id WHERE mrss.metadata_record_id = %s ORDER BY s.name'
            ),
        }
        
        for key, (table, query_template) in system_queries.items():
            cur.execute(
                query_template.format(
                    table=self._table_name(table),
                    systems=self._table_name('systems')
                ),
                (metadata_record_id,),
            )
            results = [r["name"] for r in cur.fetchall()]
            if results:
                relationships[key] = results

        # Get ownership relationships
        ownership_queries = {
            'business_owners': 'metadata_record_business_owners',
            'bu_sme': 'metadata_record_bu_sme',
            'it_application_owners': 'metadata_record_it_application_owners',
            'it_sme': 'metadata_record_it_sme',
            'support_lead': 'metadata_record_support_lead',
        }
        
        for key, table in ownership_queries.items():
            cur.execute(
                f"""
                SELECT o.id
                FROM {self._table_name(table)} mrt
                JOIN {self._table_name('owners')} o ON mrt.owner_id = o.id
                WHERE mrt.metadata_record_id = %s
                ORDER BY o.id
                """,
                (metadata_record_id,),
            )
            results = [r["id"] for r in cur.fetchall()]
            if results:
                relationships[key] = results

        # Get domain (only one domain per metadata_record)
        cur.execute(
            f"""
            SELECT d.name
            FROM {self._table_name("metadata_record_domains")} mrd
            JOIN {self._table_name("domains")} d ON mrd.domain_id = d.id
            WHERE mrd.metadata_record_id = %s
            LIMIT 1
            """,
            (metadata_record_id,),
        )
        domain_row = cur.fetchone()
        if domain_row:
            relationships["domain"] = domain_row["name"]

        return relationships

    def _store_metadata_relationships(
        self, cur: Any, metadata_id: str, metadata: Dict[str, Any]
    ) -> None:
        """
        Store all relationships from metadata dictionary.
        
        Args:
            cur: Database cursor
            metadata_id: Metadata record ID
            metadata: Metadata dictionary containing relationship data
        """
        # Extract ownership fields (check both top-level and nested in "ownership")
        ownership = metadata.get("ownership", {})
        if not isinstance(ownership, dict):
            ownership = {}

        # Helper to get ownership field from either top-level metadata or ownership dict
        def get_ownership_field(field_name: str, default=None):
            if field_name in metadata:
                return metadata.get(field_name, default)
            return ownership.get(field_name, default)

        # Store ownership relationships
        ownership_types = [
            'business_owners', 'bu_sme', 'it_application_owners', 
            'it_sme', 'support_lead'
        ]
        for relationship_type in ownership_types:
            owners = get_ownership_field(relationship_type, [])
            if isinstance(owners, list):
                for owner_id in owners:
                    if isinstance(owner_id, str):
                        self._store_ownership_relationship(
                            cur, metadata_id, owner_id, relationship_type
                        )

        # Store system relationships
        system_relationship_types = ['pulls_from', 'pushes_to', 'system_sources']
        for relationship_type in system_relationship_types:
            systems = metadata.get(relationship_type, [])
            if isinstance(systems, list):
                for system_name in systems:
                    if isinstance(system_name, str):
                        self._store_system_relationship(
                            cur, metadata_id, system_name, relationship_type
                        )

        # Store domain (only one domain per metadata_record)
        domain = metadata.get("domain")
        if isinstance(domain, str):
            domain_id = self._get_or_create_domain(cur, domain)
            # Delete existing domain relationship first
            cur.execute(
                f"DELETE FROM {self._table_name('metadata_record_domains')} WHERE metadata_record_id = %s",
                (metadata_id,),
            )
            cur.execute(
                f"""
                INSERT INTO {self._table_name('metadata_record_domains')}
                (id, metadata_record_id, domain_id)
                VALUES (gen_random_uuid(), %s, %s::uuid)
                """,
                (metadata_id, domain_id),
            )

    # ============================================================================
    # Metadata Operations
    # ============================================================================

    def store_metadata(
        self,
        schema_id: str,
        metadata: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store additional metadata.

        Args:
            schema_id: Schema identifier
            metadata: Metadata dictionary
            version: Optional version string (if None, uses schema version)

        Returns:
            Metadata record ID
        """
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id, name, and version from schema/data_contract
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT s.data_contract_id, s.version, dc.name as data_contract_name
                FROM {self._table_name("schemas")} s
                JOIN {self._table_name("data_contracts")} dc 
                    ON s.data_contract_id = dc.id
                WHERE s.id = %s
                """,
                (schema_id,),
            )

            row = cur.fetchone()
            if not row:
                raise ValueError(f"Schema not found: {schema_id}")

            data_contract_id = row["data_contract_id"]
            schema_version = row["version"]
            data_contract_name = row["data_contract_name"]

            # Use provided version or schema version
            if not version:
                version = schema_version

        # Extract metadata fields
        from pycharter.shared.name_validator import validate_name, normalize_name
        
        title = metadata.get("title")
        if not title:
            # Generate a normalized title from schema_id if not provided
            title = normalize_name(f"metadata_for_{schema_id}") or "metadata"
        # Normalize and validate the title
        normalized_title = normalize_name(str(title))
        if not normalized_title:
            raise ValueError(f"metadata.title '{title}' cannot be normalized to a valid name. Must contain only lowercase alphanumerics and underscores.")
        title = validate_name(normalized_title, field_name="metadata.title")
        status = metadata.get("status", "active")
        description = metadata.get("description")
        governance_rules = metadata.get("governance_rules")

        self._require_connection()
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Check if metadata_record with same title and version already exists (globally unique)
            cur.execute(
                f"""
                SELECT id FROM {self._table_name("metadata_records")}
                WHERE title = %s AND version = %s
                """,
                (title, version),
            )

            existing = cur.fetchone()

            if existing:
                # Prevent overwriting existing metadata - raise error instead
                raise ValueError(
                    f"Metadata with title '{title}' and version '{version}' already exists. "
                    f"Cannot create duplicate artifacts. Use a different version number."
                )
            else:
                # Insert new metadata_record
                cur.execute(
                    f"""
                    INSERT INTO {self._table_name("metadata_records")} (
                        id, title, data_contract_id, version, status, description, 
                        governance_rules
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        title,
                        data_contract_id,
                        version,
                        status,
                        description,
                        json.dumps(governance_rules) if governance_rules else None,
                    ),
                )
                metadata_id = cur.fetchone()[0]

            # Update data_contract with metadata_record_id (no version field - UUID is sufficient)
            cur.execute(
                f"""
                UPDATE {self._table_name("data_contracts")}
                SET metadata_record_id = %s
                WHERE id = %s
                """,
                (metadata_id, data_contract_id),
            )

            # Clear existing relationships and store new ones
            self._clear_metadata_relationships(cur, metadata_id)
            self._store_metadata_relationships(cur, metadata_id, metadata)

            conn.commit()
            return str(metadata_id)

    def get_metadata(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses latest version)

        Returns:
            Metadata dictionary or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            # Get metadata_record via schema -> data_contract
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if version:
                    cur.execute(
                        f"""
                        SELECT mr.*
                        FROM {self._table_name("metadata_records")} mr
                        JOIN {self._table_name("schemas")} s 
                            ON mr.data_contract_id = s.data_contract_id
                        WHERE s.id = %s AND mr.version = %s
                        ORDER BY mr.version DESC
                        LIMIT 1
                        """,
                        (schema_id, version),
                    )
                else:
                    cur.execute(
                        f"""
                        SELECT mr.*
                        FROM {self._table_name("metadata_records")} mr
                        JOIN {self._table_name("schemas")} s 
                            ON mr.data_contract_id = s.data_contract_id
                        WHERE s.id = %s
                        ORDER BY mr.version DESC
                        LIMIT 1
                        """,
                        (schema_id,),
                    )

                row = cur.fetchone()
                if not row:
                    return None

                metadata_record_id = row["id"]

                # Reconstruct metadata dictionary with all basic fields
                metadata = {
                    "title": row.get("title"),
                    "status": row.get("status"),
                    "type": row.get("type"),
                    "description": row.get("description"),
                    "version": row.get("version"),
                    "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                    "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
                    "created_by": row.get("created_by"),
                    "updated_by": row.get("updated_by"),
                }

                # Add JSON fields
                if row.get("governance_rules"):
                    metadata["governance_rules"] = self._parse_jsonb(
                        row["governance_rules"]
                    )

                # Get all relationships
                relationships = self._get_metadata_relationships(cur, metadata_record_id)
                metadata.update(relationships)

                return metadata
        except Exception as e:
            # Rollback on error to prevent transaction issues
            conn.rollback()
            raise

    # ============================================================================
    # Coercion Rules Operations
    # ============================================================================

    def store_coercion_rules(
        self,
        schema_id: str,
        coercion_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store coercion rules for a schema.

        Args:
            schema_id: Schema identifier
            coercion_rules: Dictionary of coercion rules
            version: Optional version string (if None, uses schema version)

        Returns:
            Rule ID or identifier
        """
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id, name, and version from schema/data_contract
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT s.data_contract_id, s.version, s.title, dc.name as data_contract_name
                FROM {self._table_name("schemas")} s
                JOIN {self._table_name("data_contracts")} dc 
                    ON s.data_contract_id = dc.id
                WHERE s.id = %s
                """,
                (schema_id,),
            )

            row = cur.fetchone()
            if not row:
                raise ValueError(f"Schema not found: {schema_id}")

            data_contract_id = row["data_contract_id"]
            schema_version = row["version"]
            schema_title = row["title"]
            data_contract_name = row["data_contract_name"]

            # Use provided version or schema version
            if not version:
                version = schema_version

        # Create title for coercion rules - normalize to follow naming convention
        from pycharter.shared.name_validator import normalize_name
        title = normalize_name(f"{schema_title}_coercion_rules")
        if not title:
            title = normalize_name(f"{schema_title}_coercion") or normalize_name(schema_title) or "coercion_rules"
        # Validate the normalized title
        from pycharter.shared.name_validator import validate_name
        title = validate_name(title, field_name="coercion_rules.title")

        self._require_connection()
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Check if coercion_rules with same title and version already exists (globally unique)
            cur.execute(
                f"""
                SELECT id FROM {self._table_name("coercion_rules")}
                WHERE title = %s AND version = %s
                """,
                (title, version),
            )

            existing = cur.fetchone()

            if existing:
                # Prevent overwriting existing coercion rules - raise error instead
                raise ValueError(
                    f"Coercion rules with title '{title}' and version '{version}' already exists. "
                    f"Cannot create duplicate artifacts. Use a different version number."
                )
            else:
                # Insert new coercion_rules
                cur.execute(
                    f"""
                    INSERT INTO {self._table_name("coercion_rules")} (
                        id, title, data_contract_id, version, rules, schema_id
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        title,
                        data_contract_id,
                        version,
                        json.dumps(coercion_rules),
                        schema_id,
                    ),
                )
                rule_id = cur.fetchone()[0]

            # Update data_contract with coercion_rules_id
            cur.execute(
                f"""
                UPDATE {self._table_name("data_contracts")}
                SET coercion_rules_id = %s
                WHERE id = %s
                """,
                (rule_id, data_contract_id),
            )
            conn.commit()
            return str(rule_id)

    def get_coercion_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve coercion rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses schema version)

        Returns:
            Dictionary of coercion rules, or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            # Get data_contract_id from schema
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT data_contract_id, version
                    FROM {self._table_name("schemas")}
                    WHERE id = %s
                    """,
                    (schema_id,),
                )

                row = cur.fetchone()
                if not row:
                    return None

                data_contract_id = row["data_contract_id"]
                schema_version = row["version"]

                # Use provided version or schema version
                if not version:
                    version = schema_version

                # Get coercion rules
                cur.execute(
                    f"""
                    SELECT rules
                    FROM {self._table_name("coercion_rules")}
                    WHERE data_contract_id = %s AND version = %s
                    """,
                    (data_contract_id, version),
                )

                row = cur.fetchone()
                if not row:
                    return None

                return self._parse_jsonb(row["rules"])
        except Exception as e:
            # Rollback on error to prevent transaction issues
            conn.rollback()
            raise

    # ============================================================================
    # Validation Rules Operations
    # ============================================================================

    def store_validation_rules(
        self,
        schema_id: str,
        validation_rules: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """
        Store validation rules for a schema.

        Args:
            schema_id: Schema identifier
            validation_rules: Dictionary of validation rules
            version: Optional version string (if None, uses schema version)

        Returns:
            Rule ID or identifier
        """
        self._require_connection()
        conn = self._get_connection()

        # Get data_contract_id, name, and version from schema/data_contract
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT s.data_contract_id, s.version, s.title, dc.name as data_contract_name
                FROM {self._table_name("schemas")} s
                JOIN {self._table_name("data_contracts")} dc 
                    ON s.data_contract_id = dc.id
                WHERE s.id = %s
                """,
                (schema_id,),
            )

            row = cur.fetchone()
            if not row:
                raise ValueError(f"Schema not found: {schema_id}")

            data_contract_id = row["data_contract_id"]
            schema_version = row["version"]
            schema_title = row["title"]
            data_contract_name = row["data_contract_name"]

            # Use provided version or schema version
            if not version:
                version = schema_version

        # Create title for validation rules - normalize to follow naming convention
        from pycharter.shared.name_validator import normalize_name
        title = normalize_name(f"{schema_title}_validation_rules")
        if not title:
            title = normalize_name(f"{schema_title}_validation") or normalize_name(schema_title) or "validation_rules"
        # Validate the normalized title
        from pycharter.shared.name_validator import validate_name
        title = validate_name(title, field_name="validation_rules.title")

        self._require_connection()
        conn = self._get_connection()
        with conn.cursor() as cur:
            # Check if validation_rules with same title and version already exists (globally unique)
            cur.execute(
                f"""
                SELECT id FROM {self._table_name("validation_rules")}
                WHERE title = %s AND version = %s
                """,
                (title, version),
            )

            existing = cur.fetchone()

            if existing:
                # Prevent overwriting existing validation rules - raise error instead
                raise ValueError(
                    f"Validation rules with title '{title}' and version '{version}' already exists. "
                    f"Cannot create duplicate artifacts. Use a different version number."
                )
            else:
                # Insert new validation_rules
                cur.execute(
                    f"""
                    INSERT INTO {self._table_name("validation_rules")} (
                        id, title, data_contract_id, version, rules, schema_id
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        title,
                        data_contract_id,
                        version,
                        json.dumps(validation_rules),
                        schema_id,
                    ),
                )
                rule_id = cur.fetchone()[0]

            # Update data_contract with validation_rules_id
            cur.execute(
                f"""
                UPDATE {self._table_name("data_contracts")}
                SET validation_rules_id = %s
                WHERE id = %s
                """,
                (rule_id, data_contract_id),
            )
            conn.commit()
            return str(rule_id)

    def get_validation_rules(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation rules for a schema.

        Args:
            schema_id: Schema identifier
            version: Optional version string (if None, uses schema version)

        Returns:
            Dictionary of validation rules, or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            # Get data_contract_id from schema
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT data_contract_id, version
                    FROM {self._table_name("schemas")}
                    WHERE id = %s
                    """,
                    (schema_id,),
                )

                row = cur.fetchone()
                if not row:
                    return None

                data_contract_id = row["data_contract_id"]
                schema_version = row["version"]

                # Use provided version or schema version
                if not version:
                    version = schema_version

                # Get validation rules
                cur.execute(
                    f"""
                    SELECT rules
                    FROM {self._table_name("validation_rules")}
                    WHERE data_contract_id = %s AND version = %s
                    """,
                    (data_contract_id, version),
                )

                row = cur.fetchone()
                if not row:
                    return None

                return self._parse_jsonb(row["rules"])
        except Exception as e:
            # Rollback on error to prevent transaction issues
            conn.rollback()
            raise

    def get_coercion_rules_by_id(
        self, coercion_rules_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve coercion rules directly by their UUID.

        Args:
            coercion_rules_id: Coercion rules UUID

        Returns:
            Coercion rules dictionary or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT rules
                    FROM {self._table_name("coercion_rules")}
                    WHERE id = %s
                    """,
                    (coercion_rules_id,),
                )

                row = cur.fetchone()
                if not row:
                    return None

                return self._parse_jsonb(row["rules"])
        except Exception as e:
            conn.rollback()
            raise

    def get_validation_rules_by_id(
        self, validation_rules_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation rules directly by their UUID.

        Args:
            validation_rules_id: Validation rules UUID

        Returns:
            Validation rules dictionary or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT rules
                    FROM {self._table_name("validation_rules")}
                    WHERE id = %s
                    """,
                    (validation_rules_id,),
                )

                row = cur.fetchone()
                if not row:
                    return None

                return self._parse_jsonb(row["rules"])
        except Exception as e:
            conn.rollback()
            raise

    def get_metadata_by_id(
        self, metadata_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata directly by its UUID.

        Args:
            metadata_id: Metadata record UUID

        Returns:
            Metadata dictionary or None if not found
        """
        self._require_connection()
        conn = self._get_connection()

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT *
                    FROM {self._table_name("metadata_records")}
                    WHERE id = %s
                    """,
                    (metadata_id,),
                )

                row = cur.fetchone()
                if not row:
                    return None

                metadata_record_id = row["id"]

                # Reconstruct metadata dictionary with all basic fields
                metadata = {
                    "title": row.get("title"),
                    "status": row.get("status"),
                    "type": row.get("type"),
                    "description": row.get("description"),
                    "version": row.get("version"),
                    "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                    "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
                    "created_by": row.get("created_by"),
                    "updated_by": row.get("updated_by"),
                }

                # Add JSON fields
                if row.get("governance_rules"):
                    metadata["governance_rules"] = self._parse_jsonb(
                        row["governance_rules"]
                    )

                # Get all relationships
                relationships = self._get_metadata_relationships(cur, metadata_record_id)
                metadata.update(relationships)

                return metadata
        except Exception as e:
            conn.rollback()
            raise
