"""
Admin Services Module

This module provides service classes for admin panel operations,
including user management, KPI computation, session listing, and observability.

"""

import asyncio
import base64
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import aiohttp

from ..session.session_storage import (
    MessageData,
    get_shared_elasticsearch_client,
)
from .admin_models import (
    ConfigDetail,
    ConfigSummary,
    DashboardSetupResponse,
    KibanaConfigRequest,
    PaginatedUserList,
    SessionSummary,
    UserKPIs,
    UserSummary,
)


logger = logging.getLogger(__name__)


def _get_index_prefix() -> str:
    """Get the Elasticsearch index prefix from environment."""
    return os.getenv("ELASTICSEARCH_SESSION_INDEX_PREFIX", "agent-sessions")


class AdminUserService:
    """
    Service for admin user management operations.

    Provides methods to list users, compute KPIs, and retrieve session data
    using Elasticsearch aggregations for efficient querying.

    """

    def __init__(self) -> None:
        """Initialize the admin user service."""
        self._client = None
        self._index_prefix = _get_index_prefix()

    async def _get_client(self):  # type: ignore[no-untyped-def]
        """Get or initialize the Elasticsearch client."""
        if self._client is None:
            self._client = await get_shared_elasticsearch_client()
        return self._client

    @property
    def _metadata_index(self) -> str:
        """Get the metadata index name."""
        return f"{self._index_prefix}-metadata"

    @property
    def _messages_index(self) -> str:
        """Get the messages index name."""
        return f"{self._index_prefix}-messages"

    async def list_users(
        self,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedUserList:
        """
        List users with pagination and optional search filtering.

        Uses Elasticsearch aggregations to efficiently retrieve user summaries
        with session counts and last activity timestamps.

        Args:
            search: Optional search string for partial user_id matching (case-insensitive)
            page: Page number (1-indexed)
            page_size: Number of users per page

        Returns:
            PaginatedUserList with user summaries sorted by last activity (descending)

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN SERVICE] Elasticsearch client not available")
            return PaginatedUserList(
                users=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )

        try:
            # Build the query for filtering
            query: dict = {"match_all": {}}
            if search:
                # Use wildcard query for partial matching (case-insensitive)
                query = {
                    "wildcard": {
                        "user_id": {
                            "value": f"*{search.lower()}*",
                            "case_insensitive": True,
                        }
                    }
                }

            # First, get all unique users with their stats using aggregation
            agg_response = await client.search(
                index=self._metadata_index,
                body={
                    "size": 0,
                    "query": query,
                    "aggs": {
                        "users": {
                            "terms": {
                                "field": "user_id",
                                "size": 10000,  # Get all users
                                "order": {"last_activity": "desc"},
                            },
                            "aggs": {
                                "session_count": {"value_count": {"field": "session_id"}},
                                "last_activity": {"max": {"field": "updated_at"}},
                            },
                        },
                        "total_users": {"cardinality": {"field": "user_id"}},
                    },
                },
            )

            # Extract total count
            total = agg_response["aggregations"]["total_users"]["value"]

            # Extract user buckets
            user_buckets = agg_response["aggregations"]["users"]["buckets"]

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_buckets = user_buckets[start_idx:end_idx]

            # Build user summaries
            users = []
            for bucket in paginated_buckets:
                last_activity_ms = bucket["last_activity"]["value"]
                last_activity = None
                if last_activity_ms:
                    last_activity = datetime.fromtimestamp(last_activity_ms / 1000, tz=timezone.utc)

                users.append(
                    UserSummary(
                        user_id=bucket["key"],
                        session_count=bucket["doc_count"],
                        last_activity=last_activity,
                    )
                )

            # Calculate total pages
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            logger.debug(
                f"[ADMIN SERVICE] Listed {len(users)} users (page {page}/{total_pages}, total: {total})"
            )

            return PaginatedUserList(
                users=users,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        except Exception as e:
            logger.error(f"[ADMIN SERVICE] Failed to list users: {e}")
            return PaginatedUserList(
                users=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )

    async def get_user_kpis(
        self,
        user_id: str,
        period: Literal["day", "week", "month"] = "week",
        agent_id: str | None = None,
    ) -> UserKPIs:
        """
        Get KPIs for a specific user.

        Computes message count for the specified time period and
        determines the last connection time from the most recent message.

        Args:
            user_id: User identifier
            period: Time period for message count ("day", "week", or "month")
            agent_id: Optional agent ID to filter KPIs by specific agent

        Returns:
            UserKPIs with message count and last connection timestamp

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN SERVICE] Elasticsearch client not available")
            return UserKPIs(
                user_id=user_id,
                message_count=0,
                period=period,
                last_connection=None,
                agent_id=agent_id,
            )

        try:
            # Calculate date range based on period
            now = datetime.now(timezone.utc)
            if period == "day":
                start_date = now - timedelta(days=1)
            elif period == "week":
                start_date = now - timedelta(weeks=1)
            else:  # month
                start_date = now - timedelta(days=30)

            # Build query with optional agent_id filter
            must_clauses: list[dict] = [{"term": {"user_id": user_id}}]
            if agent_id:
                must_clauses.append({"term": {"agent_id": agent_id}})

            query = {"bool": {"must": must_clauses}}

            # Query for message count in period and last connection
            response = await client.search(
                index=self._messages_index,
                body={
                    "size": 0,
                    "query": query,
                    "aggs": {
                        "messages_in_period": {
                            "filter": {
                                "range": {
                                    "created_at": {
                                        "gte": start_date.isoformat(),
                                        "lte": now.isoformat(),
                                    }
                                }
                            }
                        },
                        "last_connection": {"max": {"field": "created_at"}},
                    },
                },
            )

            # Extract message count for the period
            message_count = response["aggregations"]["messages_in_period"]["doc_count"]

            # Extract last connection timestamp
            last_connection_ms = response["aggregations"]["last_connection"]["value"]
            last_connection = None
            if last_connection_ms:
                last_connection = datetime.fromtimestamp(last_connection_ms / 1000, tz=timezone.utc)

            logger.debug(
                f"[ADMIN SERVICE] User {user_id} KPIs (agent={agent_id}): {message_count} messages ({period}), "
                f"last connection: {last_connection}"
            )

            return UserKPIs(
                user_id=user_id,
                message_count=message_count,
                period=period,
                last_connection=last_connection,
                agent_id=agent_id,
            )

        except Exception as e:
            logger.error(f"[ADMIN SERVICE] Failed to get KPIs for user {user_id}: {e}")
            return UserKPIs(
                user_id=user_id,
                message_count=0,
                period=period,
                last_connection=None,
                agent_id=agent_id,
            )

    async def get_user_sessions(
        self, user_id: str, agent_id: str | None = None
    ) -> list[SessionSummary]:
        """
        Get all sessions for a specific user.

        Retrieves session metadata with message counts for each session.

        Args:
            user_id: User identifier
            agent_id: Optional agent ID to filter sessions

        Returns:
            List of SessionSummary objects sorted by updated_at (descending)

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN SERVICE] Elasticsearch client not available")
            return []

        try:
            # Build query with optional agent_id filter
            must_clauses: list[dict] = [{"term": {"user_id": user_id}}]
            if agent_id:
                must_clauses.append({"term": {"agent_id": agent_id}})

            query = {"bool": {"must": must_clauses}}

            # Get all sessions for the user
            sessions_response = await client.search(
                index=self._metadata_index,
                body={
                    "query": query,
                    "sort": [{"updated_at": {"order": "desc"}}],
                    "size": 10000,
                },
            )

            sessions = []
            session_ids = []

            for hit in sessions_response["hits"]["hits"]:
                source = hit["_source"]
                session_ids.append(source["session_id"])
                sessions.append(
                    {
                        "session_id": source["session_id"],
                        "session_label": source.get("session_label"),
                        "created_at": source.get("created_at"),
                        "updated_at": source.get("updated_at"),
                        "agent_id": source.get("agent_id"),
                    }
                )

            # Get message counts for all sessions in one query
            if session_ids:
                msg_count_response = await client.search(
                    index=self._messages_index,
                    body={
                        "size": 0,
                        "query": {"terms": {"session_id": session_ids}},
                        "aggs": {
                            "by_session": {
                                "terms": {"field": "session_id", "size": len(session_ids)},
                            }
                        },
                    },
                )

                # Build message count lookup
                msg_counts = {}
                for bucket in msg_count_response["aggregations"]["by_session"]["buckets"]:
                    msg_counts[bucket["key"]] = bucket["doc_count"]

                # Build final session summaries
                result = []
                for session in sessions:
                    created_at = session["created_at"]
                    updated_at = session["updated_at"]

                    # Parse timestamps
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

                    result.append(
                        SessionSummary(
                            session_id=session["session_id"],
                            session_label=session["session_label"],
                            created_at=created_at,
                            updated_at=updated_at,
                            message_count=msg_counts.get(session["session_id"], 0),
                            agent_id=session.get("agent_id"),
                        )
                    )

                logger.debug(
                    f"[ADMIN SERVICE] Retrieved {len(result)} sessions for user {user_id} "
                    f"(agent={agent_id})"
                )
                return result

            return []

        except Exception as e:
            logger.error(f"[ADMIN SERVICE] Failed to get sessions for user {user_id}: {e}")
            return []

    async def get_user_agents(self, user_id: str) -> list[str]:
        """
        Get list of unique agent IDs used by a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of unique agent IDs
        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN SERVICE] Elasticsearch client not available")
            return []

        try:
            # Aggregate unique agent_ids for this user
            response = await client.search(
                index=self._metadata_index,
                body={
                    "size": 0,
                    "query": {"term": {"user_id": user_id}},
                    "aggs": {
                        "agents": {
                            "terms": {
                                "field": "agent_id",
                                "size": 1000,
                            }
                        }
                    },
                },
            )

            agents = [
                bucket["key"]
                for bucket in response["aggregations"]["agents"]["buckets"]
                if bucket["key"]  # Filter out empty/null values
            ]

            logger.debug(f"[ADMIN SERVICE] Found {len(agents)} agents for user {user_id}")
            return agents

        except Exception as e:
            logger.error(f"[ADMIN SERVICE] Failed to get agents for user {user_id}: {e}")
            return []

    async def get_session_messages(self, session_id: str) -> list[MessageData]:
        """
        Get all messages for a specific session.

        Retrieves messages sorted by sequence_number in ascending order.

        Args:
            session_id: Session identifier

        Returns:
            List of MessageData objects in chronological order

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN SERVICE] Elasticsearch client not available")
            return []

        try:
            response = await client.search(
                index=self._messages_index,
                body={
                    "query": {"term": {"session_id": session_id}},
                    "sort": [{"sequence_number": {"order": "asc"}}],
                    "size": 10000,
                },
            )

            messages = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                msg = MessageData(**source)
                logger.debug(
                    f"[ADMIN SERVICE] Message: role={msg.role}, type={msg.message_type}, "
                    f"text_content={msg.text_content[:50] if msg.text_content else None}, "
                    f"response_text_main={msg.response_text_main[:50] if msg.response_text_main else None}"
                )
                messages.append(msg)

            logger.debug(
                f"[ADMIN SERVICE] Retrieved {len(messages)} messages for session {session_id}"
            )
            return messages

        except Exception as e:
            logger.error(f"[ADMIN SERVICE] Failed to get messages for session {session_id}: {e}")
            return []


def _get_config_index() -> str:
    """Get the Elasticsearch config index from environment."""
    return os.getenv("ELASTICSEARCH_CONFIG_INDEX", "agent-configs")


class AdminConfigService:
    """
    Service for admin configuration management operations.

    Provides methods to list and retrieve agent configurations
    from Elasticsearch.

    """

    def __init__(self) -> None:
        """Initialize the admin config service."""
        self._client = None
        self._config_index = _get_config_index()

    async def _get_client(self):  # type: ignore[no-untyped-def]
        """Get or initialize the Elasticsearch client."""
        if self._client is None:
            self._client = await get_shared_elasticsearch_client()
        return self._client

    async def list_configs(self) -> list[ConfigSummary]:
        """
        List all agent configurations from Elasticsearch.

        Retrieves all configurations with their summary fields,
        showing only the latest active version for each agent.

        Returns:
            List of ConfigSummary objects sorted by last_updated (descending)

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN CONFIG SERVICE] Elasticsearch client not available")
            return []

        try:
            # Query all configurations, sorted by updated_at descending
            response = await client.search(
                index=self._config_index,
                body={
                    "query": {"match_all": {}},
                    "sort": [{"updated_at": {"order": "desc"}}],
                    "size": 10000,
                },
            )

            configs = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                doc_id = hit["_id"]

                # Parse updated_at timestamp
                updated_at = source.get("updated_at")
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    except ValueError:
                        updated_at = None

                # Use doc_id as config_id for unique identification
                configs.append(
                    ConfigSummary(
                        config_id=doc_id,
                        agent_type=source.get("agent_type"),
                        version=str(source.get("version", "")) if source.get("version") else None,
                        last_updated=updated_at,
                    )
                )

            logger.debug(f"[ADMIN CONFIG SERVICE] Listed {len(configs)} configurations")
            return configs

        except Exception as e:
            logger.error(f"[ADMIN CONFIG SERVICE] Failed to list configs: {e}")
            return []

    async def get_config_detail(self, config_id: str) -> ConfigDetail | None:
        """
        Get full details of a specific configuration.

        Retrieves the complete configuration document including
        all configuration data as JSON.

        Args:
            config_id: Configuration document ID

        Returns:
            ConfigDetail with full configuration data, or None if not found

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN CONFIG SERVICE] Elasticsearch client not available")
            return None

        try:
            # Get document by ID
            response = await client.get(
                index=self._config_index,
                id=config_id,
            )

            source = response["_source"]

            # Parse updated_at timestamp
            updated_at = source.get("updated_at")
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except ValueError:
                    updated_at = None

            # Build config_data from the full document
            # Include the nested config object and other relevant fields
            config_data = {
                "agent_id": source.get("agent_id"),
                "config": source.get("config", {}),
                "metadata": source.get("metadata", {}),
                "active": source.get("active", False),
                "updated_by": source.get("updated_by"),
            }

            logger.debug(f"[ADMIN CONFIG SERVICE] Retrieved config detail for {config_id}")

            return ConfigDetail(
                config_id=config_id,
                agent_type=source.get("agent_type"),
                version=str(source.get("version", "")) if source.get("version") else None,
                last_updated=updated_at,
                config_data=config_data,
            )

        except Exception as e:
            # Check if it's a not found error
            error_str = str(e).lower()
            if "not found" in error_str or "404" in error_str:
                logger.debug(f"[ADMIN CONFIG SERVICE] Config not found: {config_id}")
                return None
            logger.error(f"[ADMIN CONFIG SERVICE] Failed to get config detail for {config_id}: {e}")
            return None


def _get_admin_config_index() -> str:
    """Get the Elasticsearch admin config index from environment."""
    return os.getenv("ELASTICSEARCH_ADMIN_CONFIG_INDEX", "agent-admin-config")


class AdminObservabilityService:
    """
    Service for Kibana observability operations.

    Provides methods to configure Kibana connections, check dashboard status,
    and create LLM metrics dashboards via the Kibana Saved Objects API.

    """

    # Document ID for storing Kibana configuration
    KIBANA_CONFIG_DOC_ID = "kibana-config"

    def __init__(self) -> None:
        """Initialize the admin observability service."""
        self._client: Any = None
        self._admin_config_index = _get_admin_config_index()

    async def _get_client(self) -> Any:
        """
        Get or initialize the Elasticsearch client.

        Returns:
            Elasticsearch client instance if available, None otherwise.

        """
        if self._client is None:
            self._client = await get_shared_elasticsearch_client()
        return self._client

    def _get_kibana_headers(self, config: dict[str, Any]) -> dict[str, str]:
        """
        Generate authentication headers for Kibana API calls based on config.

        Creates the appropriate Authorization header based on the authentication
        method specified in the configuration (basic auth or API key).
        Always includes the kbn-xsrf header required for Kibana API calls.

        Args:
            config: Kibana configuration dictionary containing:
                - auth_method: "basic" or "apikey"
                - username: Username for basic auth (required if auth_method is "basic")
                - password: Password for basic auth (required if auth_method is "basic")
                - api_key: API key (required if auth_method is "apikey")

        Returns:
            Dictionary of HTTP headers for Kibana API requests.

        Raises:
            ValueError: If required credentials are missing for the auth method.

        """
        headers: dict[str, str] = {
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        }

        auth_method = config.get("auth_method", "basic")

        if auth_method == "basic":
            username = config.get("username")
            password = config.get("password")

            if not username or not password:
                raise ValueError("Username and password are required for basic authentication")

            # Create Basic auth header with base64 encoded credentials
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded_credentials}"

        elif auth_method == "apikey":
            api_key = config.get("api_key")

            if not api_key:
                raise ValueError("API key is required for API key authentication")

            # Create ApiKey auth header
            headers["Authorization"] = f"ApiKey {api_key}"

        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}")

        return headers

    async def get_kibana_config(self) -> dict[str, Any] | None:
        """
        Retrieve stored Kibana configuration from Elasticsearch.

        Queries the admin config index for the Kibana configuration document.
        Returns the configuration dictionary if found, None otherwise.

        Returns:
            Dictionary containing Kibana configuration with keys:
                - url: Kibana base URL
                - auth_method: "basic" or "apikey"
                - username: Username for basic auth (if applicable)
                - password: Password for basic auth (if applicable)
                - api_key: API key (if applicable)
                - dashboard_name: Custom dashboard name
                - updated_at: Last update timestamp
                - updated_by: User who last updated the config
            Returns None if no configuration is found or on error.

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN OBSERVABILITY] Elasticsearch client not available")
            return None

        try:
            response = await client.get(
                index=self._admin_config_index,
                id=self.KIBANA_CONFIG_DOC_ID,
            )

            source = response.get("_source", {})

            # Verify this is a kibana_config document
            if source.get("type") != "kibana_config":
                logger.warning(
                    f"[ADMIN OBSERVABILITY] Document {self.KIBANA_CONFIG_DOC_ID} "
                    "is not a kibana_config type"
                )
                return None

            logger.debug("[ADMIN OBSERVABILITY] Retrieved Kibana configuration")
            return source

        except Exception as e:
            error_str = str(e).lower()
            # Handle not found case gracefully
            if "not found" in error_str or "404" in error_str:
                logger.debug("[ADMIN OBSERVABILITY] Kibana configuration not found")
                return None
            logger.error(f"[ADMIN OBSERVABILITY] Failed to retrieve Kibana config: {e}")
            return None

    async def save_kibana_config(
        self,
        config: "KibanaConfigRequest",
        updated_by: str = "admin",
    ) -> bool:
        """
        Store Kibana configuration in Elasticsearch.

        Saves the Kibana connection configuration to the admin config index.
        For MVP, credentials are stored as-is (encryption can be added later).
        Includes an updated_at timestamp for tracking changes.

        Args:
            config: KibanaConfigRequest model containing:
                - url: Kibana base URL
                - auth_method: "basic" or "apikey"
                - username: Username for basic auth (optional)
                - password: Password for basic auth (optional)
                - api_key: API key (optional)
                - dashboard_name: Custom dashboard name (optional)
            updated_by: Identifier of the user saving the config (default: "admin")

        Returns:
            True if configuration was saved successfully, False otherwise.

        """
        client = await self._get_client()
        if client is None:
            logger.error("[ADMIN OBSERVABILITY] Elasticsearch client not available")
            return False

        try:
            # Build the document body
            doc_body: dict[str, Any] = {
                "type": "kibana_config",
                "url": config.url,
                "auth_method": config.auth_method,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": updated_by,
            }

            # Add credentials based on auth method
            if config.auth_method == "basic":
                doc_body["username"] = config.username
                # For MVP, store password as-is (encryption can be added later)
                doc_body["password"] = config.password
            elif config.auth_method == "apikey":
                # For MVP, store API key as-is (encryption can be added later)
                doc_body["api_key"] = config.api_key

            # Add optional dashboard name
            if config.dashboard_name:
                doc_body["dashboard_name"] = config.dashboard_name

            # Index the document (creates or updates)
            await client.index(
                index=self._admin_config_index,
                id=self.KIBANA_CONFIG_DOC_ID,
                body=doc_body,
                refresh=True,  # Make the document immediately searchable
            )

            logger.info(f"[ADMIN OBSERVABILITY] Saved Kibana configuration for URL: {config.url}")
            return True

        except Exception as e:
            logger.error(f"[ADMIN OBSERVABILITY] Failed to save Kibana config: {e}")
            return False

    async def test_kibana_connection(
        self,
        config: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """
        Test connectivity to Kibana API.

        Makes a GET request to the Kibana status endpoint to verify
        that the connection can be established with the provided credentials.

        Args:
            config: Optional Kibana configuration dictionary. If None,
                retrieves the stored configuration using get_kibana_config().
                Expected keys:
                - url: Kibana base URL
                - auth_method: "basic" or "apikey"
                - username: Username for basic auth (if applicable)
                - password: Password for basic auth (if applicable)
                - api_key: API key (if applicable)

        Returns:
            Tuple of (success: bool, message: str) where:
                - success is True if connection was successful
                - message contains a success message or descriptive error

        """
        # Retrieve stored config if not provided
        if config is None:
            config = await self.get_kibana_config()
            if config is None:
                return (
                    False,
                    "Kibana is not configured. Please configure Kibana connection first.",
                )

        # Validate URL format
        kibana_url = config.get("url", "")
        if not kibana_url:
            return (False, "Invalid Kibana URL format. Please provide a valid HTTP/HTTPS URL.")

        # Validate URL format using regex
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(kibana_url):
            return (False, "Invalid Kibana URL format. Please provide a valid HTTP/HTTPS URL.")

        # Generate auth headers
        try:
            headers = self._get_kibana_headers(config)
        except ValueError as e:
            return (False, f"Authentication configuration error: {e}")

        # Build the status endpoint URL
        status_url = f"{kibana_url.rstrip('/')}/api/status"

        # Set timeout to 30 seconds
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(status_url, headers=headers, ssl=False) as response:
                    # Check for authentication failures
                    if response.status == 401:
                        return (False, "Authentication failed. Please verify your credentials.")
                    if response.status == 403:
                        return (False, "Authentication failed. Please verify your credentials.")

                    # Check for successful response
                    if response.status == 200:
                        logger.info(
                            f"[ADMIN OBSERVABILITY] Successfully connected to Kibana at {kibana_url}"
                        )
                        return (True, f"Successfully connected to Kibana at {kibana_url}")

                    # Handle other error status codes
                    return (
                        False,
                        f"Kibana returned unexpected status code {response.status}. "
                        f"Please verify the URL is correct.",
                    )

        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[ADMIN OBSERVABILITY] Connection error to Kibana: {e}")
            return (
                False,
                f"Cannot connect to Kibana at {kibana_url}. "
                "Please verify the URL is correct and Kibana is running.",
            )

        except aiohttp.ServerTimeoutError:
            logger.warning(f"[ADMIN OBSERVABILITY] Timeout connecting to Kibana at {kibana_url}")
            return (False, "Connection to Kibana timed out. Please try again.")

        except asyncio.TimeoutError:
            logger.warning(f"[ADMIN OBSERVABILITY] Timeout connecting to Kibana at {kibana_url}")
            return (False, "Connection to Kibana timed out. Please try again.")

        except aiohttp.InvalidURL:
            return (False, "Invalid Kibana URL format. Please provide a valid HTTP/HTTPS URL.")

        except Exception as e:
            logger.error(f"[ADMIN OBSERVABILITY] Unexpected error testing Kibana connection: {e}")
            return (
                False,
                f"Cannot connect to Kibana at {kibana_url}. "
                "Please verify the URL is correct and Kibana is running.",
            )

    async def check_dashboard_exists(
        self,
        dashboard_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if LLM metrics dashboard exists in Kibana.

        Queries the Kibana Saved Objects API to check if the specified
        dashboard exists. If found, returns the dashboard URL for direct access.

        Args:
            dashboard_id: Optional dashboard ID to check. If None, uses the
                default dashboard ID "llm-metrics-dashboard" or the dashboard
                name from stored configuration.

        Returns:
            Tuple of (exists: bool, dashboard_url: str | None) where:
                - exists is True if the dashboard was found in Kibana
                - dashboard_url contains the URL to access the dashboard if it exists,
                  None otherwise

        """
        # Retrieve stored Kibana configuration
        config = await self.get_kibana_config()
        if config is None:
            logger.debug("[ADMIN OBSERVABILITY] Kibana not configured, cannot check dashboard")
            return (False, None)

        kibana_url = config.get("url", "")
        if not kibana_url:
            logger.warning("[ADMIN OBSERVABILITY] Kibana URL not set in configuration")
            return (False, None)

        # Determine dashboard ID to check
        if dashboard_id is None:
            # Use dashboard name from config if available, otherwise use default
            dashboard_name = config.get("dashboard_name")
            if dashboard_name:
                # Convert dashboard name to ID format (lowercase, hyphens)
                dashboard_id = dashboard_name.lower().replace(" ", "-")
            else:
                dashboard_id = "llm-metrics-dashboard"

        # Generate auth headers
        try:
            headers = self._get_kibana_headers(config)
        except ValueError as e:
            logger.error(f"[ADMIN OBSERVABILITY] Authentication configuration error: {e}")
            return (False, None)

        # Build the Saved Objects API URL to check dashboard existence
        saved_objects_url = f"{kibana_url.rstrip('/')}/api/saved_objects/dashboard/{dashboard_id}"

        # Set timeout to 30 seconds
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(saved_objects_url, headers=headers, ssl=False) as response:
                    # Dashboard not found - this is expected when dashboard doesn't exist
                    if response.status == 404:
                        logger.debug(
                            f"[ADMIN OBSERVABILITY] Dashboard '{dashboard_id}' not found in Kibana"
                        )
                        return (False, None)

                    # Authentication failures
                    if response.status in (401, 403):
                        logger.warning(
                            "[ADMIN OBSERVABILITY] Authentication failed when checking dashboard"
                        )
                        return (False, None)

                    # Dashboard found
                    if response.status == 200:
                        # Construct the dashboard URL for direct access
                        dashboard_url = (
                            f"{kibana_url.rstrip('/')}/app/dashboards#/view/{dashboard_id}"
                        )
                        logger.info(
                            f"[ADMIN OBSERVABILITY] Dashboard '{dashboard_id}' exists at {dashboard_url}"
                        )
                        return (True, dashboard_url)

                    # Handle other unexpected status codes
                    logger.warning(
                        f"[ADMIN OBSERVABILITY] Unexpected status {response.status} "
                        f"when checking dashboard '{dashboard_id}'"
                    )
                    return (False, None)

        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[ADMIN OBSERVABILITY] Connection error checking dashboard: {e}")
            return (False, None)

        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
            logger.warning("[ADMIN OBSERVABILITY] Timeout checking dashboard existence")
            return (False, None)

        except Exception as e:
            logger.error(f"[ADMIN OBSERVABILITY] Unexpected error checking dashboard: {e}")
            return (False, None)

    async def create_visualization(
        self,
        viz_config: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Create a single TSVB visualization in Kibana.

        Creates or updates a visualization using the Kibana Saved Objects API.
        The visualization configuration is converted to the format expected by
        Kibana's visState JSON structure.

        Args:
            viz_config: Visualization configuration dictionary containing:
                - id: Unique identifier for the visualization
                - title: Display title for the visualization
                - type: Visualization type (e.g., "metrics" for TSVB)
                - params: TSVB configuration parameters

        Returns:
            Tuple of (success: bool, message: str) where:
                - success is True if visualization was created/updated successfully
                - message contains a success message or descriptive error

        """
        import json

        # Retrieve stored Kibana configuration
        config = await self.get_kibana_config()
        if config is None:
            return (
                False,
                "Kibana is not configured. Please configure Kibana connection first.",
            )

        kibana_url = config.get("url", "")
        if not kibana_url:
            return (False, "Kibana URL not set in configuration.")

        # Validate required fields in viz_config
        viz_id = viz_config.get("id")
        viz_title = viz_config.get("title")
        viz_type = viz_config.get("type", "metrics")
        viz_params = viz_config.get("params", {})

        if not viz_id:
            return (False, "Visualization ID is required.")

        if not viz_title:
            return (False, "Visualization title is required.")

        # Generate auth headers
        try:
            headers = self._get_kibana_headers(config)
        except ValueError as e:
            return (False, f"Authentication configuration error: {e}")

        # Build the visState JSON structure for TSVB
        # TSVB visualizations use the "metrics" type in Kibana
        vis_state = {
            "title": viz_title,
            "type": viz_type,
            "params": viz_params,
            "aggs": [],
        }

        # Build the Saved Objects API request body
        request_body = {
            "attributes": {
                "title": viz_title,
                "visState": json.dumps(vis_state),
                "uiStateJSON": "{}",
                "description": "",
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": "{}",
                },
            },
        }

        # Build the Saved Objects API URL
        # Using POST with overwrite=true to create or update
        saved_objects_url = (
            f"{kibana_url.rstrip('/')}/api/saved_objects/visualization/{viz_id}?overwrite=true"
        )

        # Set timeout to 30 seconds
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    saved_objects_url,
                    headers=headers,
                    json=request_body,
                    ssl=False,
                ) as response:
                    # Authentication failures
                    if response.status == 401:
                        return (False, "Authentication failed. Please verify your credentials.")
                    if response.status == 403:
                        return (
                            False,
                            "Authorization failed. User may not have permission to create "
                            "visualizations.",
                        )

                    # Bad request - likely invalid visualization config
                    if response.status == 400:
                        try:
                            error_body = await response.json()
                            error_message = error_body.get(
                                "message", "Invalid visualization configuration"
                            )
                        except Exception:
                            error_message = "Invalid visualization configuration"
                        return (
                            False,
                            f"Failed to create visualization '{viz_title}': {error_message}",
                        )

                    # Success - visualization created or updated
                    if response.status in (200, 201):
                        logger.info(
                            f"[ADMIN OBSERVABILITY] Successfully created visualization '{viz_title}' "
                            f"(id: {viz_id})"
                        )
                        return (True, f"Successfully created visualization '{viz_title}'")

                    # Handle other unexpected status codes
                    try:
                        error_body = await response.json()
                        error_message = error_body.get("message", f"Status code {response.status}")
                    except Exception:
                        error_message = f"Status code {response.status}"
                    return (
                        False,
                        f"Failed to create visualization '{viz_title}': {error_message}",
                    )

        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[ADMIN OBSERVABILITY] Connection error creating visualization: {e}")
            return (
                False,
                f"Cannot connect to Kibana. Please verify Kibana is running. "
                f"Failed to create visualization '{viz_title}'.",
            )

        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
            logger.warning(f"[ADMIN OBSERVABILITY] Timeout creating visualization '{viz_title}'")
            return (
                False,
                f"Connection to Kibana timed out while creating visualization '{viz_title}'. "
                "Please try again.",
            )

        except Exception as e:
            logger.error(
                f"[ADMIN OBSERVABILITY] Unexpected error creating visualization '{viz_title}': {e}"
            )
            return (
                False,
                f"Unexpected error creating visualization '{viz_title}': {e}",
            )

    async def create_dashboard(
        self,
        dashboard_config: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Create the dashboard with panel references to all visualizations.

        Creates or updates a dashboard using the Kibana Saved Objects API.
        The dashboard configuration includes panel references that link to
        previously created visualizations, with layout information (gridData).

        Args:
            dashboard_config: Dashboard configuration dictionary containing:
                - id: Unique identifier for the dashboard
                - title: Display title for the dashboard
                - panels: List of panel configurations, each containing:
                    - panelIndex: Unique index for the panel
                    - gridData: Layout information (x, y, w, h, i)
                    - panelRefName: Reference name for the panel
                    - embeddableConfig: Optional embeddable configuration
                    - type: Panel type (e.g., "visualization")
                    - id: ID of the referenced visualization

        Returns:
            Tuple of (success: bool, message: str) where:
                - success is True if dashboard was created/updated successfully
                - message contains a success message or descriptive error

        """
        import json

        # Retrieve stored Kibana configuration
        config = await self.get_kibana_config()
        if config is None:
            return (
                False,
                "Kibana is not configured. Please configure Kibana connection first.",
            )

        kibana_url = config.get("url", "")
        if not kibana_url:
            return (False, "Kibana URL not set in configuration.")

        # Validate required fields in dashboard_config
        dashboard_id = dashboard_config.get("id")
        dashboard_title = dashboard_config.get("title")
        panels = dashboard_config.get("panels", [])

        if not dashboard_id:
            return (False, "Dashboard ID is required.")

        if not dashboard_title:
            return (False, "Dashboard title is required.")

        # Generate auth headers
        try:
            headers = self._get_kibana_headers(config)
        except ValueError as e:
            return (False, f"Authentication configuration error: {e}")

        # Build the panelsJSON structure
        # Each panel references a visualization and includes layout information
        panels_json_list = []
        references = []

        for idx, panel in enumerate(panels):
            panel_index = panel.get("panelIndex", str(idx))
            grid_data = panel.get(
                "gridData", {"x": 0, "y": idx * 15, "w": 24, "h": 15, "i": str(idx)}
            )
            viz_id = panel.get("id")
            panel_type = panel.get("type", "visualization")
            embeddable_config = panel.get("embeddableConfig", {})

            # Ensure gridData has the 'i' field matching panelIndex
            if "i" not in grid_data:
                grid_data["i"] = panel_index

            # Build panel entry for panelsJSON
            panel_entry = {
                "version": "8.0.0",
                "type": panel_type,
                "gridData": grid_data,
                "panelIndex": panel_index,
                "embeddableConfig": embeddable_config,
                "panelRefName": f"panel_{panel_index}",
            }
            panels_json_list.append(panel_entry)

            # Build reference entry for the visualization
            if viz_id:
                reference_entry = {
                    "name": f"panel_{panel_index}",
                    "type": panel_type,
                    "id": viz_id,
                }
                references.append(reference_entry)

        # Build the optionsJSON structure
        options_json = {
            "useMargins": True,
            "syncColors": False,
            "hidePanelTitles": False,
        }

        # Build the Saved Objects API request body
        request_body = {
            "attributes": {
                "title": dashboard_title,
                "panelsJSON": json.dumps(panels_json_list),
                "optionsJSON": json.dumps(options_json),
                "timeRestore": False,
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": "{}",
                },
            },
            "references": references,
        }

        # Build the Saved Objects API URL
        # Using POST with overwrite=true to create or update
        saved_objects_url = (
            f"{kibana_url.rstrip('/')}/api/saved_objects/dashboard/{dashboard_id}?overwrite=true"
        )

        # Set timeout to 30 seconds
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    saved_objects_url,
                    headers=headers,
                    json=request_body,
                    ssl=False,
                ) as response:
                    # Authentication failures
                    if response.status == 401:
                        return (False, "Authentication failed. Please verify your credentials.")
                    if response.status == 403:
                        return (
                            False,
                            "Authorization failed. User may not have permission to create "
                            "dashboards.",
                        )

                    # Bad request - likely invalid dashboard config
                    if response.status == 400:
                        try:
                            error_body = await response.json()
                            error_message = error_body.get(
                                "message", "Invalid dashboard configuration"
                            )
                        except Exception:
                            error_message = "Invalid dashboard configuration"
                        return (
                            False,
                            f"Failed to create dashboard '{dashboard_title}': {error_message}",
                        )

                    # Success - dashboard created or updated
                    if response.status in (200, 201):
                        dashboard_url = (
                            f"{kibana_url.rstrip('/')}/app/dashboards#/view/{dashboard_id}"
                        )
                        logger.info(
                            f"[ADMIN OBSERVABILITY] Successfully created dashboard '{dashboard_title}' "
                            f"(id: {dashboard_id}) with {len(panels)} panels"
                        )
                        return (
                            True,
                            f"Successfully created dashboard '{dashboard_title}'. "
                            f"Access it at: {dashboard_url}",
                        )

                    # Handle other unexpected status codes
                    try:
                        error_body = await response.json()
                        error_message = error_body.get("message", f"Status code {response.status}")
                    except Exception:
                        error_message = f"Status code {response.status}"
                    return (
                        False,
                        f"Failed to create dashboard '{dashboard_title}': {error_message}",
                    )

        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[ADMIN OBSERVABILITY] Connection error creating dashboard: {e}")
            return (
                False,
                f"Cannot connect to Kibana. Please verify Kibana is running. "
                f"Failed to create dashboard '{dashboard_title}'.",
            )

        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
            logger.warning(f"[ADMIN OBSERVABILITY] Timeout creating dashboard '{dashboard_title}'")
            return (
                False,
                f"Connection to Kibana timed out while creating dashboard '{dashboard_title}'. "
                "Please try again.",
            )

        except Exception as e:
            logger.error(
                f"[ADMIN OBSERVABILITY] Unexpected error creating dashboard '{dashboard_title}': {e}"
            )
            return (
                False,
                f"Unexpected error creating dashboard '{dashboard_title}': {e}",
            )

    async def setup_full_dashboard(self) -> DashboardSetupResponse:
        """
        Orchestrate full dashboard setup process.

        Loads the dashboard configuration from the JSON file, creates all
        visualizations first, then creates the dashboard with panel references.
        Tracks progress and errors throughout the process.

        Returns:
            DashboardSetupResponse containing:
                - success: True if dashboard was created (even if some visualizations failed)
                - dashboard_url: URL to the created dashboard
                - visualizations_created: Count of successfully created visualizations
                - error: Error message if dashboard creation failed
                - details: List of step-by-step progress messages

        """
        import json
        from pathlib import Path

        details: list[str] = []
        visualizations_created = 0

        # Step 1: Check Kibana configuration
        details.append("Checking Kibana configuration...")
        config = await self.get_kibana_config()
        if config is None:
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=0,
                error="Kibana is not configured. Please configure Kibana connection first.",
                details=details,
            )
        details.append("Kibana configuration found.")

        kibana_url = config.get("url", "")
        if not kibana_url:
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=0,
                error="Kibana URL not set in configuration.",
                details=details,
            )

        # Step 2: Test Kibana connection
        details.append("Testing Kibana connection...")
        connection_success, connection_message = await self.test_kibana_connection(config)
        if not connection_success:
            details.append(f"Connection test failed: {connection_message}")
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=0,
                error=connection_message,
                details=details,
            )
        details.append("Kibana connection successful.")

        # Step 3: Load dashboard configuration from JSON file
        details.append("Loading dashboard configuration...")
        config_file_path = (
            Path(__file__).parent
            / "observability"
            / "kibana-llm-dashboard-setup.json"
        )

        try:
            with open(config_file_path) as f:
                dashboard_config = json.load(f)
        except FileNotFoundError:
            error_msg = f"Dashboard configuration file not found: {config_file_path}"
            details.append(error_msg)
            logger.error(f"[ADMIN OBSERVABILITY] {error_msg}")
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=0,
                error=error_msg,
                details=details,
            )
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in dashboard configuration file: {e}"
            details.append(error_msg)
            logger.error(f"[ADMIN OBSERVABILITY] {error_msg}")
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=0,
                error=error_msg,
                details=details,
            )

        details.append("Dashboard configuration loaded successfully.")

        # Step 4: Create all visualizations
        visualizations = dashboard_config.get("visualizations", [])
        total_visualizations = len(visualizations)
        details.append(f"Creating {total_visualizations} visualizations...")

        visualization_errors: list[str] = []

        for viz_config in visualizations:
            viz_title = viz_config.get("title", "Unknown")

            success, message = await self.create_visualization(viz_config)
            if success:
                visualizations_created += 1
                details.append(f"  ✓ Created visualization: {viz_title}")
                logger.debug(f"[ADMIN OBSERVABILITY] Created visualization: {viz_title}")
            else:
                visualization_errors.append(f"{viz_title}: {message}")
                details.append(f"  ✗ Failed to create visualization: {viz_title} - {message}")
                logger.warning(
                    f"[ADMIN OBSERVABILITY] Failed to create visualization '{viz_title}': {message}"
                )

        details.append(f"Visualizations created: {visualizations_created}/{total_visualizations}")

        # Step 5: Create the dashboard
        details.append("Creating dashboard...")
        dashboard_def = dashboard_config.get("dashboard", {})

        if not dashboard_def:
            error_msg = "Dashboard definition not found in configuration file."
            details.append(error_msg)
            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=visualizations_created,
                error=error_msg,
                details=details,
            )

        # Build dashboard config for create_dashboard method
        # Convert panel format from JSON config to expected format
        panels = []
        for panel in dashboard_def.get("panels", []):
            panels.append(
                {
                    "panelIndex": panel.get("id"),
                    "gridData": {
                        "x": panel.get("x", 0),
                        "y": panel.get("y", 0),
                        "w": panel.get("w", 24),
                        "h": panel.get("h", 15),
                        "i": panel.get("id"),
                    },
                    "id": panel.get("vizId"),
                    "type": "visualization",
                }
            )

        dashboard_create_config = {
            "id": dashboard_def.get("id", "llm-metrics-dashboard"),
            "title": dashboard_def.get("title", "LLM Metrics Dashboard"),
            "panels": panels,
        }

        dashboard_success, dashboard_message = await self.create_dashboard(dashboard_create_config)

        if not dashboard_success:
            details.append(f"Dashboard creation failed: {dashboard_message}")

            # Build error message including visualization failures if any
            error_parts = [f"Dashboard creation failed: {dashboard_message}"]
            if visualization_errors:
                error_parts.append(
                    f"Additionally, {len(visualization_errors)} visualization(s) failed to create."
                )

            return DashboardSetupResponse(
                success=False,
                dashboard_url=None,
                visualizations_created=visualizations_created,
                error=" ".join(error_parts),
                details=details,
            )

        # Build dashboard URL
        dashboard_id = dashboard_def.get("id", "llm-metrics-dashboard")
        dashboard_url = f"{kibana_url.rstrip('/')}/app/dashboards#/view/{dashboard_id}"

        details.append(f"Dashboard created successfully: {dashboard_url}")

        # Log summary
        logger.info(
            f"[ADMIN OBSERVABILITY] Dashboard setup complete. "
            f"Visualizations: {visualizations_created}/{total_visualizations}, "
            f"Dashboard URL: {dashboard_url}"
        )

        # Return success even if some visualizations failed, as long as dashboard was created
        return DashboardSetupResponse(
            success=True,
            dashboard_url=dashboard_url,
            visualizations_created=visualizations_created,
            error=(
                None
                if not visualization_errors
                else (
                    f"{len(visualization_errors)} visualization(s) failed to create: "
                    + "; ".join(visualization_errors)
                )
            ),
            details=details,
        )
