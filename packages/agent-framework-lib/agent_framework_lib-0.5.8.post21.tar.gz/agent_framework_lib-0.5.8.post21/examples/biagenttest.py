"""
Athena Assistant agent
"""
import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Any, Dict, Optional

# Load environment variables from a `.env` file located at the project root (one level
# above the `agents/` directory). Fall back to default loader if no explicit .env file
# is found.
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from agent_framework.implementations import LlamaIndexAgent
from agent_framework.storage.file_system_management import FileStorageFactory
from agent_framework.memory import MemoryConfig


PROMPT ="""
Tu es un assistant mais surtout un conseiller expert dans l'analyse de base de données et la Business Ingtelligence. Tu as accès à une base de données Athena et tu es capable de générer des documents PDF, des diagrammes mermaid, des charts et des tabledatas les inccorporer dans des pdfs pour faire des rapports professionnels et impactant pour l'utilisateur.
Tu es également capable d'executer du code python si tu as besoins de faire des opérations.

La base données auquel tu as accès est owliance_datalake et à les tables suivantes :
jira_epic_view : epic jira il s'agit d'une view

 issue_id
string
• issue_key
string
• issue_self
string
• summary
string
• description
string
• created_date
timestamp
• updated_date
timestamp
• resolution_date
timestamp
• status
string
• status_description
string
• status_id
string
• priority
string
• priority_id
string
• issuetype
string
• issuetype_id
string
• issuetype_subtask
boolean
• issuetype_description
string
• resolution
string
• resolution_description
string
• resolution_id
string
• assignee_name
string
• assignee_displayname
string
• assignee_email
string
• assignee_key
string
• assignee_active
boolean
• reporter_name
string
• reporter_active
boolean
• reporter_displayname
string
• reporter_email
string
• creator_name
string
• creator_active
boolean
• creator_displayname
string
• creator_email
string
• project_name
string
• project_id
string
• project_key
string
• project_typekey
string
• components_list
array<string>
• versions_list
array<string>
• fix_versions_list
array<string>
• labels
array<string>
• time_original_estimate
string
• time_estimate
string
• time_spent
string
• agg_time_original_estimate
string
• agg_time_spent
string
• work_ratio
bigint
• issue_links_list
array<string>
• subtasks_list
array<string>
• comment
string
• watches
string
• votes
string
• attachment_list
array<string>
• archived_date
string
• last_viewed
string
• progress
string
• agg_progress
string
• time_tracking
string
• agg_time_estimate
string
• customfield_10000
string
• customfield_10001
string
• customfield_10002
string
• customfield_10003
string
• customfield_10004
string
• customfield_10100
string
• customfield_10101
string
• customfield_10200_list
array<string>
• customfield_10217
string
• customfield_10218
string
• customfield_10219
string
• customfield_10220
string
• customfield_10239
string
• customfield_10240
string
• customfield_10241
string
• customfield_10242
string
• customfield_10243
string
• customfield_10260
string
• customfield_10261
string
• customfield_10262
string
• customfield_10700
string
• customfield_10701_value
string
• customfield_10702
string
• customfield_10703
string
• customfield_10704
array<string>
• customfield_10705
string
• customfield_10706
string
• customfield_10707_name
string
• customfield_10708
string
• customfield_10709
timestamp
• customfield_10710
timestamp
• customfield_10711
string
• customfield_10900
string
• customfield_11003
string
• customfield_11004
string
• customfield_11005
string
• customfield_11006
string
• customfield_11100_value
string
• customfield_11101
string
• customfield_11103
string
• customfield_11108
string
• customfield_11135
string
• customfield_11401
string
• customfield_11702
string
• customfield_11716_name
string
• customfield_11717_name
string
• customfield_11806
string
• customfield_12201
string
• customfield_12202
array<string>
• customfield_12400
string
• customfield_12401
string
• customfield_12700
string
• customfield_12701_value
string
• customfield_12805
string
• customfield_12806
string
• customfield_12812
string
• customfield_12813
string
• customfield_12815 
"""

class AthenaAgent(LlamaIndexAgent):
    """Agent optimisé pour requeter une base de donnée Athena et pouvoir générer des rapports sur cette base de données."""

    def __init__(self):
        super().__init__(agent_id="bi-agent-v1",
                         name = "Business Intelligence Agent",
                         description= "Agent qui permet d'accéder de faire des analyses de Business Intelligence grâce aux données qui me sont fournis. J'ai la capacité de faire les analyses les plus poussés que vous pourriez imaginer et de créer des rapports pdf avec images, graphiques divers.")
        
        self.current_user_id = "default_user"
        self.current_session_id = None
        self.file_storage = None
        # MCP tools storage
        self.mcp_tools: List[Any] = []
        self.mcp_clients: Dict[str, Any] = {}
        self._mcp_initialized = False

    def get_memory_config(self):
        """Enable Graphiti with Neo4J."""
        return MemoryConfig.graphiti_simple(
            use_falkordb=False,
            neo4j_uri=os.getenv("NEO4J_URI", "neo4j+s://074a17d7.databases.neo4j.io"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "CvzZEGouBbvTErN2WhsGWqlCXGsuxtgokUHLQ65Fh5A"),
            environment= "dev",
            passive_injection=False,
        )
    
    async def _ensure_file_storage(self):
        if self.file_storage is None:
            self.file_storage = await FileStorageFactory.create_storage_manager()

    async def configure_session(self, session_configuration: Dict[str, Any]) -> None:
        self.current_user_id = session_configuration.get('user_id', 'default_user')
        self.current_session_id = session_configuration.get('session_id')
        await self._ensure_file_storage()
        await super().configure_session(session_configuration)

    async def _initialize_mcp_tools(self):
        """Initialize MCP tools from configured servers."""
        if self._mcp_initialized:
            return

        try:
            from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
        except ImportError:
            print("⚠️ llama-index-tools-mcp not available. Install with: uv add llama-index-tools-mcp")
            self.mcp_tools = []
            return

        print("🔌 Initializing MCP tools...")
        self.mcp_tools = []

        mcp_servers = self._get_mcp_server_config()
        if not mcp_servers:
            print("ℹ️ No MCP server configured")
            return

        for server_config in mcp_servers:
            server_name = server_config.get("name", "athena")
            try:
                print(f"🔌 Connecting to MCP server: {server_name}...")
                client = BasicMCPClient(
                    server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env", {})
                )
                self.mcp_clients[server_name] = client

                mcp_tool_spec = McpToolSpec(client=client)
                function_tools = await mcp_tool_spec.to_tool_list_async()

                if function_tools:
                    self.mcp_tools.extend(function_tools)
                    print(f"✅ {server_name}: {len(function_tools)} tools loaded")
                else:
                    print(f"⚠️ {server_name}: No tools found")
            except Exception as e:
                print(f"❌ Failed to connect to {server_name}: {e}")

        self._mcp_initialized = True
        print(f"📊 MCP Tools initialized: {len(self.mcp_tools)} tools available")

    def _get_mcp_server_config(self) -> List[Dict[str, Any]]:
        """Get MCP server configuration for AWS Athena and Python execution."""
        import platform
        
        servers = [
            {
                "name": "athena",
                "command": "npx",
                "args": ["-y", "@lishenxydlgzs/aws-athena-mcp"],
                "env": {
                    "OUTPUT_S3_PATH": os.getenv("OUTPUT_S3_PATH", "s3://aws-athena-query-results-owliance"),
                    "AWS_REGION": os.getenv("AWS_REGION", "eu-west-3"),
                    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
                    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                    "ATHENA_WORKGROUP": os.getenv("ATHENA_WORKGROUP", "primary"),
                },
            },
        ]
        
        # Add mcp-run-python server
        # Use deno on Linux (Docker) to avoid pyodide .wasm bug, uvx on macOS
        if platform.system() == "Darwin":
            # macOS: uvx works fine
            servers.append({
                "name": "python",
                "command": "uvx",
                "args": ["mcp-run-python", "stdio"],
                "env": {},
            })
        else:
            # Linux/Docker: use deno + JSR to avoid pyodide bug
            servers.append({
                "name": "python",
                "command": "deno",
                "args": [
                    "run",
                    "-N",
                    "-R=node_modules",
                    "-W=node_modules",
                    "--node-modules-dir=auto",
                    "jsr:@pydantic/mcp-run-python",
                    "stdio"
                ],
                "env": {},
            })
        
        return servers


    def get_agent_prompt(self) -> str:
        return PROMPT
    
    async def get_welcome_message(self) -> str:
        """Return a welcome message for new sessions."""
        return f"Bonjour ! Je suis {self.name}.\n\n{self.description}"

    def get_agent_tools(self) -> List[callable]:
        return []

    async def initialize_agent(self, model_name: str, system_prompt: str, tools: List[callable], **kwargs) -> None:
        await self._initialize_mcp_tools()
        all_tools = list(tools) + self.mcp_tools
        await super().initialize_agent(model_name, system_prompt, all_tools, **kwargs)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8203"))

    print("=" * 60)
    print("🚀 Starting Athena Agent Server")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'auto')}")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)

    create_basic_agent_server(
        agent_class=AthenaAgent,
        host="0.0.0.0",
        port=port,
        reload=False
    )


if __name__ == "__main__":
    main()
