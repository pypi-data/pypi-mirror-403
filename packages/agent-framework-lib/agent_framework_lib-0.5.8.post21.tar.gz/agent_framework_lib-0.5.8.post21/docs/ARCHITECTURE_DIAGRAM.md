# Agent Framework - Architecture Diagram

Ce document présente l'architecture complète de l'Agent Framework sous forme de diagrammes Mermaid.

## 1. Vue d'ensemble de l'Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        UI[Modern UI / Chat Interface]
        API_Client[API Client]
    end

    subgraph Web["🌐 Web Layer (FastAPI)"]
        Server[server.py<br/>FastAPI Application]
        AdminRouter[Admin Router<br/>User/Session Management]
        Auth[Authentication<br/>Basic Auth / API Key]
    end

    subgraph Core["⚙️ Core Layer (Framework-Agnostic)"]
        AgentInterface[AgentInterface<br/>Abstract Contract]
        BaseAgent[BaseAgent<br/>Abstract Base Class]
        AgentProvider[AgentManager<br/>+ ManagedAgentProxy]
        StateManager[StateManager<br/>State Persistence]
        ModelClients[ModelClientFactory<br/>Multi-Provider LLM]
        ModelConfig[ModelConfigManager<br/>Configuration]
        ESConfigProvider[ElasticsearchConfigProvider<br/>Dynamic Config]
    end

    subgraph Implementations["🔧 Implementations"]
        LlamaIndex[LlamaIndexAgent<br/>LlamaIndex Framework]
        Microsoft[MicrosoftAgent<br/>Microsoft Agent Framework]
        Custom[Custom Agents<br/>Your Implementation]
    end

    subgraph Session["💾 Session Layer"]
        SessionStorage[SessionStorageInterface]
        MemoryStorage[MemorySessionStorage<br/>Development]
        MongoStorage[MongoDBSessionStorage<br/>Production]
        ESStorage[ElasticsearchSessionStorage<br/>Production + Search]
    end

    subgraph Storage["📁 File Storage"]
        FileManager[FileStorageManager]
        LocalStorage[LocalFileStorage]
        S3Storage[S3FileStorage]
        MinIOStorage[MinIOFileStorage]
    end

    subgraph Skills["🎯 Skills System"]
        SkillRegistry[SkillRegistry]
        SkillsMixin[SkillsMixin]
        BuiltinSkills[Built-in Skills<br/>Chart, PDF, Mermaid...]
    end

    subgraph Memory["🧠 Memory System"]
        MemoryManager[MemoryManager]
        MemoryMixin[MemoryMixin]
        MemoriProvider[MemoriProvider<br/>SQL-based]
        GraphitiProvider[GraphitiProvider<br/>Knowledge Graph]
    end

    subgraph Monitoring["📊 Monitoring"]
        CircuitBreaker[ElasticsearchCircuitBreaker]
        ErrorHandler[ErrorHandler]
        PerformanceMonitor[PerformanceMonitor]
        ESLogging[ElasticsearchLoggingHandler]
    end

    subgraph LLM["🤖 LLM Providers"]
        OpenAI[OpenAI<br/>GPT-4, GPT-4o]
        Anthropic[Anthropic<br/>Claude 3]
        Gemini[Google Gemini]
    end

    %% Client to Web
    UI --> Server
    API_Client --> Server

    %% Web Layer
    Server --> Auth
    Server --> AdminRouter
    Server --> AgentProvider

    %% Core connections
    AgentProvider --> AgentInterface
    AgentProvider --> StateManager
    AgentProvider --> SessionStorage
    AgentInterface --> BaseAgent
    BaseAgent --> ModelClients
    BaseAgent --> SkillsMixin
    BaseAgent --> MemoryMixin
    ModelClients --> ModelConfig
    ModelConfig --> ESConfigProvider

    %% Implementations
    BaseAgent --> LlamaIndex
    BaseAgent --> Microsoft
    BaseAgent --> Custom

    %% Session Storage
    SessionStorage --> MemoryStorage
    SessionStorage --> MongoStorage
    SessionStorage --> ESStorage

    %% File Storage
    Server --> FileManager
    FileManager --> LocalStorage
    FileManager --> S3Storage
    FileManager --> MinIOStorage

    %% Skills
    SkillsMixin --> SkillRegistry
    SkillRegistry --> BuiltinSkills

    %% Memory
    MemoryMixin --> MemoryManager
    MemoryManager --> MemoriProvider
    MemoryManager --> GraphitiProvider

    %% Monitoring
    ESStorage --> CircuitBreaker
    ESConfigProvider --> CircuitBreaker
    Server --> ErrorHandler
    Server --> PerformanceMonitor
    ErrorHandler --> ESLogging

    %% LLM Providers
    ModelClients --> OpenAI
    ModelClients --> Anthropic
    ModelClients --> Gemini

    classDef core fill:#e1f5fe,stroke:#01579b
    classDef impl fill:#f3e5f5,stroke:#4a148c
    classDef storage fill:#e8f5e9,stroke:#1b5e20
    classDef monitoring fill:#fff3e0,stroke:#e65100
    classDef llm fill:#fce4ec,stroke:#880e4f

    class AgentInterface,BaseAgent,AgentProvider,StateManager,ModelClients,ModelConfig,ESConfigProvider core
    class LlamaIndex,Microsoft,Custom impl
    class SessionStorage,MemoryStorage,MongoStorage,ESStorage,FileManager,LocalStorage,S3Storage,MinIOStorage storage
    class CircuitBreaker,ErrorHandler,PerformanceMonitor,ESLogging monitoring
    class OpenAI,Anthropic,Gemini llm
```

## 2. Flux de Traitement d'un Message

```mermaid
sequenceDiagram
    participant Client
    participant Server as FastAPI Server
    participant Auth as Authentication
    participant AM as AgentManager
    participant Proxy as ManagedAgentProxy
    participant Agent as Agent Instance
    participant Session as SessionStorage
    participant LLM as LLM Provider

    Client->>Server: POST /message
    Server->>Auth: Validate credentials
    Auth-->>Server: User authenticated

    Server->>AM: get_agent(session_id, agent_class, user_id)
    
    AM->>AM: Create agent instance
    AM->>Session: load_session(user_id, session_id)
    Session-->>AM: SessionData (config, metadata)
    
    AM->>AM: Get dynamic config from ES
    AM->>Agent: configure_session(config)
    
    AM->>Session: load_agent_state(session_id)
    Session-->>AM: Agent state
    AM->>Agent: load_state(state)
    
    AM->>Proxy: Wrap agent in proxy
    AM-->>Server: ManagedAgentProxy

    Server->>Proxy: handle_message(session_id, input)
    Proxy->>Agent: handle_message(session_id, input)
    
    Agent->>Agent: Build query from input
    Agent->>LLM: Process with tools
    LLM-->>Agent: Response
    
    Agent-->>Proxy: StructuredAgentOutput
    Proxy->>AM: save_agent_state(session_id, agent)
    AM->>Session: save_agent_state(session_id, state)
    
    Proxy-->>Server: StructuredAgentOutput
    Server->>Session: Persist messages
    Server-->>Client: SessionMessageResponse
```

## 3. Architecture des Agents

```mermaid
classDiagram
    class AgentInterface {
        <<abstract>>
        +get_metadata() Dict
        +get_state() Dict
        +load_state(state: Dict)
        +get_system_prompt() str
        +get_current_model(session_id) str
        +configure_session(config: Dict)
        +handle_message(session_id, input) Output
        +handle_message_stream(session_id, input) AsyncGenerator
    }

    class BaseAgent {
        <<abstract>>
        -agent_id: str
        -name: str
        -description: str
        -_session_system_prompt: str
        -_session_model_config: Dict
        -_enable_skills: bool
        +get_agent_prompt()* str
        +get_agent_tools()* List
        +initialize_agent(model, prompt, tools)*
        +create_fresh_context()* Any
        +serialize_context(ctx)* Dict
        +deserialize_context(state)* Any
        +run_agent(query, ctx, stream)* str|AsyncGenerator
        +process_streaming_event(event) Dict
    }

    class SkillsMixin {
        -_skill_registry: SkillRegistry
        +register_builtin_skills()
        +get_skill_tools() List
        +get_all_registered_skill_tools() List
        +get_skills_summary() Dict
    }

    class MemoryMixin {
        -_memory_manager: MemoryManager
        -_memory_config: MemoryConfig
        +get_memory_config() MemoryConfig
        +_ensure_memory_initialized() bool
        +memory_enabled: bool
    }

    class LlamaIndexAgent {
        -_agent_instance: FunctionAgent
        -_memory_adapter: LlamaIndexMemoryAdapter
        -_current_memory: Memory
        +create_llm(model_name) LLM
        +set_session_storage(storage)
        +configure_session_with_model(config, model)
    }

    class MicrosoftAgent {
        -_agent_instance: Agent
        +initialize_agent(model, prompt, tools)
    }

    class _ManagedAgentProxy {
        -_session_id: str
        -_real_agent: AgentInterface
        -_agent_manager: AgentManager
        +handle_message() auto-saves state
        +handle_message_stream() auto-saves state
    }

    class AgentManager {
        -_storage: SessionStorageInterface
        -_active_agents: Dict
        +get_agent(session_id, agent_class, user_id) AgentInterface
        +save_agent_state(session_id, agent)
    }

    AgentInterface <|-- BaseAgent
    BaseAgent <|-- LlamaIndexAgent
    BaseAgent <|-- MicrosoftAgent
    BaseAgent <|.. SkillsMixin
    BaseAgent <|.. MemoryMixin
    AgentInterface <|.. _ManagedAgentProxy
    AgentManager --> _ManagedAgentProxy : creates
    _ManagedAgentProxy --> AgentInterface : wraps
```

## 4. Système de Skills

```mermaid
flowchart LR
    subgraph Agent["Agent"]
        BaseAgent2[BaseAgent]
        SkillsMixin2[SkillsMixin]
    end

    subgraph Registry["Skill Registry"]
        SkillRegistry2[SkillRegistry]
        RegisteredSkills[(Registered Skills)]
        LoadedSkills[(Loaded Skills)]
    end

    subgraph Skills["Built-in Skills"]
        subgraph Visualization
            Chart[chart<br/>Chart.js]
            Mermaid[mermaid<br/>Diagrams]
            Table[table<br/>Tables]
        end
        subgraph Document
            File[file<br/>File Ops]
            PDF[pdf<br/>PDF Gen]
            PDFImages[pdf_with_images]
            FileAccess[file_access]
        end
        subgraph Web
            WebSearch[web_search]
        end
        subgraph Multimodal
            ImageAnalysis[multimodal<br/>Image Analysis]
        end
        subgraph UI
            Form[form]
            Options[optionsblock]
            ImageDisplay[image_display]
        end
    end

    subgraph Tools["Skill Tools"]
        ListSkills[list_skills]
        LoadSkill[load_skill]
        UnloadSkill[unload_skill]
    end

    BaseAgent2 --> SkillsMixin2
    SkillsMixin2 --> SkillRegistry2
    SkillRegistry2 --> RegisteredSkills
    SkillRegistry2 --> LoadedSkills

    RegisteredSkills --> Chart
    RegisteredSkills --> Mermaid
    RegisteredSkills --> Table
    RegisteredSkills --> File
    RegisteredSkills --> PDF
    RegisteredSkills --> PDFImages
    RegisteredSkills --> FileAccess
    RegisteredSkills --> WebSearch
    RegisteredSkills --> ImageAnalysis
    RegisteredSkills --> Form
    RegisteredSkills --> Options
    RegisteredSkills --> ImageDisplay

    SkillsMixin2 --> ListSkills
    SkillsMixin2 --> LoadSkill
    SkillsMixin2 --> UnloadSkill
```

## 5. Système de Mémoire

```mermaid
flowchart TB
    subgraph Agent["Agent"]
        BaseAgent3[BaseAgent]
        MemoryMixin2[MemoryMixin]
    end

    subgraph Manager["Memory Manager"]
        MemoryManager2[MemoryManager]
        MemoryConfig2[MemoryConfig]
    end

    subgraph Providers["Memory Providers"]
        subgraph Memori["Memori Provider"]
            MemoriDB[(SQL Database)]
            MemoriFacts[Fast Fact Extraction]
        end
        subgraph Graphiti["Graphiti Provider"]
            GraphDB[(Knowledge Graph)]
            TemporalQueries[Temporal Queries]
            Relationships[Entity Relationships]
        end
    end

    subgraph Tools["Memory Tools"]
        StoreMemory[store_memory]
        RecallMemory[recall_memory]
        GetContext[get_user_context]
        ClearMemory[clear_memory]
    end

    subgraph Output["Memory Context"]
        MemoryFact[MemoryFact]
        MemoryContext2[MemoryContext]
    end

    BaseAgent3 --> MemoryMixin2
    MemoryMixin2 --> MemoryManager2
    MemoryManager2 --> MemoryConfig2

    MemoryConfig2 --> Memori
    MemoryConfig2 --> Graphiti

    MemoriDB --> MemoriFacts
    GraphDB --> TemporalQueries
    GraphDB --> Relationships

    MemoryMixin2 --> StoreMemory
    MemoryMixin2 --> RecallMemory
    MemoryMixin2 --> GetContext
    MemoryMixin2 --> ClearMemory

    RecallMemory --> MemoryFact
    GetContext --> MemoryContext2
    MemoryFact --> MemoryContext2
```

## 6. Architecture de Stockage

```mermaid
flowchart TB
    subgraph Session["Session Storage"]
        SessionInterface[SessionStorageInterface]
        
        subgraph Backends["Storage Backends"]
            Memory[MemorySessionStorage<br/>🔧 Development]
            MongoDB[MongoDBSessionStorage<br/>🏭 Production]
            ES[ElasticsearchSessionStorage<br/>🔍 Production + Search]
        end

        subgraph Data["Data Models"]
            SessionData[SessionData<br/>Metadata, Config]
            MessageData[MessageData<br/>User/Agent Messages]
            MessageInsight[MessageInsight<br/>AI Insights]
            AgentState[Agent State<br/>Conversation Context]
        end
    end

    subgraph File["File Storage"]
        FileInterface[FileStorageInterface]
        
        subgraph FileBackends["File Backends"]
            Local[LocalFileStorage<br/>📁 Local Disk]
            S3[S3FileStorage<br/>☁️ AWS S3]
            MinIO[MinIOFileStorage<br/>🗄️ MinIO]
        end

        subgraph FileData["File Models"]
            FileMetadata[FileMetadata<br/>ID, MIME, Size...]
            MarkdownContent[Markdown Content<br/>Converted Docs]
            MultimodalData[Multimodal Data<br/>Image Analysis]
        end
    end

    SessionInterface --> Memory
    SessionInterface --> MongoDB
    SessionInterface --> ES

    SessionInterface --> SessionData
    SessionInterface --> MessageData
    SessionInterface --> MessageInsight
    SessionInterface --> AgentState

    FileInterface --> Local
    FileInterface --> S3
    FileInterface --> MinIO

    FileInterface --> FileMetadata
    FileMetadata --> MarkdownContent
    FileMetadata --> MultimodalData
```

## 7. Circuit Breaker Pattern (Elasticsearch)

```mermaid
stateDiagram-v2
    [*] --> CLOSED: Initial State

    CLOSED --> CLOSED: Success
    CLOSED --> OPEN: Failures >= Threshold

    OPEN --> OPEN: Requests Fail Fast
    OPEN --> HALF_OPEN: Recovery Timeout Elapsed

    HALF_OPEN --> CLOSED: Success (Recovery)
    HALF_OPEN --> OPEN: Failure (Reopen)

    note right of CLOSED
        Normal operation
        All requests pass through
        Failure count tracked
    end note

    note right of OPEN
        ES unavailable
        Requests fail immediately
        Use fallback storage
    end note

    note right of HALF_OPEN
        Testing recovery
        Limited requests allowed
        Single failure reopens
    end note
```

## 8. Multi-Provider LLM Architecture

```mermaid
flowchart TB
    subgraph Factory["ModelClientFactory"]
        CreateClient[create_client]
        CreateLlamaIndex[create_llamaindex_llm]
        ValidateModel[validate_model_support]
    end

    subgraph Config["ModelConfigManager"]
        DefaultModel[Default Model<br/>gpt-4]
        ProviderDefaults[Provider Defaults]
        APIKeys[API Keys]
    end

    subgraph Providers["LLM Providers"]
        subgraph OpenAI["OpenAI"]
            GPT5[gpt-5, gpt-5-mini, gpt-5-nano]
            GPT4[gpt-4, gpt-4-turbo]
            GPT4o[gpt-4o, gpt-4o-mini]
            GPT35[gpt-3.5-turbo, gpt-3.5-turbo-16k]
            O1[o1-preview, o1-mini]
        end
        subgraph Anthropic["Anthropic"]
            Claude45[claude-haiku-4-5-20251001<br/>claude-sonnet-4-5-20250929<br/>claude-opus-4-5-20251101]
            Claude3[claude-3-opus-20240229<br/>claude-3-sonnet-20240229<br/>claude-3-haiku-20240307]
            Claude35[claude-3-5-sonnet-20240620<br/>claude-3-5-sonnet-20241022]
            Claude2[claude-2.1, claude-2.0<br/>claude-instant-1.2]
        end
        subgraph Google["Google Gemini"]
            Gemini3[gemini-3-pro-preview]
            Gemini25[gemini-2.5-flash-preview-04-17]
            Gemini2[gemini-2.0-flash-exp]
            Gemini15[gemini-1.5-pro, gemini-1.5-flash]
            GeminiPro[gemini-pro, gemini-pro-vision]
        end
    end

    subgraph Clients["Native Clients"]
        AsyncOpenAI[AsyncOpenAI]
        AsyncAnthropic[AsyncAnthropic]
        GenAI[google.generativeai]
    end

    subgraph LlamaIndex["LlamaIndex LLMs"]
        LIOpenAI[llama_index.llms.openai]
        LIAnthropic[llama_index.llms.anthropic]
        LIGemini[llama_index.llms.gemini]
    end

    CreateClient --> Config
    CreateLlamaIndex --> Config
    Config --> ProviderDefaults
    Config --> APIKeys

    CreateClient --> AsyncOpenAI
    CreateClient --> AsyncAnthropic
    CreateClient --> GenAI

    CreateLlamaIndex --> LIOpenAI
    CreateLlamaIndex --> LIAnthropic
    CreateLlamaIndex --> LIGemini

    AsyncOpenAI --> OpenAI
    AsyncAnthropic --> Anthropic
    GenAI --> Google

    LIOpenAI --> OpenAI
    LIAnthropic --> Anthropic
    LIGemini --> Google
```

## 9. Structure des Modules

```mermaid
flowchart TB
    subgraph Package["agent_framework"]
        subgraph Core["core/"]
            agent_interface[agent_interface.py<br/>AgentInterface, Models]
            base_agent[base_agent.py<br/>BaseAgent]
            agent_provider[agent_provider.py<br/>AgentManager, Proxy]
            state_manager[state_manager.py<br/>StateManager]
            model_clients[model_clients.py<br/>ModelClientFactory]
            model_config[model_config.py<br/>ModelConfigManager]
            es_config[elasticsearch_config_provider.py]
        end

        subgraph Impl["implementations/"]
            llamaindex[llamaindex_agent.py]
            microsoft[microsoft_agent.py]
            memory_adapter[llamaindex_memory_adapter.py]
        end

        subgraph Session["session/"]
            session_storage[session_storage.py<br/>Interface + Memory/MongoDB]
            es_session[elasticsearch_session_storage.py]
        end

        subgraph Storage["storage/"]
            file_storages[file_storages.py<br/>Local/S3/MinIO]
            file_management[file_system_management.py]
            storage_optimizer[storage_optimizer.py]
        end

        subgraph Skills["skills/"]
            skills_base[base.py<br/>Skill, Registry]
            skills_mixin[agent_mixin.py<br/>SkillsMixin]
            skills_builtin[builtin/<br/>Chart, PDF, Mermaid...]
            skills_tools[tools.py]
        end

        subgraph Memory["memory/"]
            memory_base[base.py<br/>Interface, Models]
            memory_mixin[agent_mixin.py<br/>MemoryMixin]
            memory_manager[manager.py]
            memory_providers[providers/<br/>Memori, Graphiti]
        end

        subgraph Monitoring["monitoring/"]
            circuit_breaker[elasticsearch_circuit_breaker.py]
            error_handling[error_handling.py]
            error_logging[error_logging.py]
            performance[performance_monitor.py]
        end

        subgraph Web["web/"]
            server[server.py<br/>FastAPI App]
            admin_router[admin_router.py]
            admin_services[admin_services.py]
        end

        subgraph Tools["tools/"]
            chart_tools[chart_tools.py]
            pdf_tools[pdf_tools.py]
            mermaid_tools[mermaid_tools.py]
            file_tools[file_tools.py]
            web_search[web_search_tools.py]
        end

        subgraph Processing["processing/"]
            markdown[markdown_converter.py]
            multimodal[multimodal_integration.py]
            ai_content[ai_content_management.py]
        end
    end

    Core --> Impl
    Core --> Session
    Core --> Storage
    Impl --> Skills
    Impl --> Memory
    Web --> Core
    Web --> Session
    Web --> Storage
    Monitoring --> Session
    Tools --> Processing
```


*Généré automatiquement pour Agent Framework v0.6.0*
