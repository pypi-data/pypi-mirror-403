# Comp Manager - Architecture Documentation

This document provides a comprehensive overview of the Comp Manager architecture, including system design, component interactions, data flows, and design decisions.

## Table of Contents

- [System Overview](#system-overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Architecture](#api-architecture)
- [Caching System](#caching-system)
- [Computation Lifecycle](#computation-lifecycle)
- [Serialization Architecture](#serialization-architecture)
- [Security Considerations](#security-considerations)
- [Performance Considerations](#performance-considerations)
- [Design Decisions](#design-decisions)

---

## System Overview

Comp Manager is a Flask-based REST API framework designed to manage and track long-running mathematical computations with MongoDB as the persistence layer. The system provides three core capabilities:

1. **Computation Management**: Track computation lifecycle and state
2. **Result Caching**: Cache expensive computation results in MongoDB
3. **Complex Serialization**: Serialize Python and SageMath objects to JSON

### Key Characteristics

- **Document-Oriented**: Built on MongoDB's flexible document model
- **Decorator-Based**: Simple Python decorators for caching and tracking
- **Type-Safe**: Comprehensive type hints throughout
- **Mathematical Focus**: First-class support for SageMath mathematical objects
- **RESTful**: OpenAPI/Swagger-compatible REST API

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Client]
        API_CLIENT[API Client]
        WEB[Web Browser]
    end

    subgraph "Application Layer"
        FLASK[Flask Application]
        CONNEXION[Connexion/OpenAPI]
        API[API Resources]
        DECORATORS[Decorators]
    end

    subgraph "Business Logic Layer"
        COMP[Computation Manager]
        CACHE[Cache Manager]
        SERIAL[Serialization]
    end

    subgraph "Data Layer"
        MODELS[MongoDB Models]
        QUERYSET[Custom QuerySets]
    end

    subgraph "Persistence Layer"
        MONGO[(MongoDB)]
    end

    CLI --> FLASK
    API_CLIENT --> FLASK
    WEB --> FLASK

    FLASK --> CONNEXION
    CONNEXION --> API
    API --> COMP
    API --> CACHE

    DECORATORS --> COMP
    DECORATORS --> CACHE

    COMP --> SERIAL
    CACHE --> SERIAL

    COMP --> MODELS
    CACHE --> MODELS

    MODELS --> QUERYSET
    QUERYSET --> MONGO
```

### Layers Description

1. **Client Layer**: Multiple client interfaces (CLI, API clients, web browsers)
2. **Application Layer**: Flask + Connexion for HTTP handling and routing
3. **Business Logic Layer**: Core computation and caching logic
4. **Data Layer**: MongoDB ODM with MongoEngine
5. **Persistence Layer**: MongoDB database

---

## Component Architecture

### Directory Structure and Responsibilities

```mermaid
graph LR
    subgraph "src/comp_manager"
        INIT[__init__.py<br/>App Factory]
        MAIN[__main__.py<br/>CLI Entry]
        CONFIG[config.py<br/>Configuration]
        EXT[extensions.py<br/>MongoEngine]
        VERSION[version.py<br/>Version Info]

        subgraph "api/"
            API_RES[resource.py<br/>Base Resources]
        end

        subgraph "core/"
            CORE_MODELS[models.py<br/>DB Models]
            CORE_CACHE[caching.py<br/>Cache Storage]
            CORE_DEC[decorators.py<br/>Decorators]
            CORE_QS[queryset.py<br/>QuerySets]
            CORE_STOR[storage.py<br/>Storage]
        end

        subgraph "common/"
            COM_MODELS[models.py<br/>Base Models]
        end

        subgraph "utils/"
            UTIL_API[api.py<br/>API Helpers]
            UTIL_DB[db_helpers.py<br/>DB Utils]
            UTIL_JSON[json_encoder.py<br/>JSON Base]
            UTIL_SAGE[json_encoder_sage.py<br/>Sage JSON]
            UTIL_ME[mongoengine.py<br/>ME Extensions]
            UTIL_SER[serialization.py<br/>Serialization]
            UTIL_TYPES[types_sage.py<br/>Sage Types]
        end
    end

    MAIN --> INIT
    INIT --> CONFIG
    INIT --> EXT
    INIT --> API_RES

    API_RES --> CORE_MODELS
    CORE_DEC --> CORE_CACHE
    CORE_DEC --> CORE_MODELS
    CORE_MODELS --> COM_MODELS
    CORE_MODELS --> CORE_QS
    CORE_CACHE --> CORE_STOR

    CORE_DEC --> UTIL_SER
    UTIL_SER --> UTIL_JSON
    UTIL_SAGE --> UTIL_JSON
    UTIL_SAGE --> UTIL_TYPES
    UTIL_ME --> UTIL_JSON
```

### Component Responsibilities

| Component | Responsibility | Key Classes/Functions |
|-----------|---------------|----------------------|
| **__main__.py** | CLI entry point | `main()` |
| **api/** | REST API endpoints | `MongoDBResource` |
| **core/models.py** | Database models | `DBObjectBase`, `DBObjectBaseAbstract`, `Computation`, `MongoCacheDB` |
| **core/decorators.py** | Caching & tracking | `@mongo_cache`, `@register_computation` |
| **core/caching.py** | Cache implementations | `ObjectCache`, `mongo_object_cache` |
| **common/models.py** | Shared base classes | `BaseDocument`, `HashableDocument` |
| **utils/mongoengine.py** | MongoEngine extensions | `JSONField`, `CMListField` |
| **utils/serialization.py** | Object serialization | `serialize()`, `deserialize()` |
| **utils/json_encoder.py** | Base JSON codec | `JSONEncoder`, `JSONDecoder` |
| **utils/json_encoder_sage.py** | Sage serialization | `SageJSONEncoder`, `SageJSONDecoder` |
| **version.py** | Version info | `__version__`, `version_tuple` |

---

## Data Flow

### Cached Function Call Flow

```mermaid
sequenceDiagram
    participant Client
    participant Decorator as @mongo_cache
    participant Cache as Cache Storage
    participant Function
    participant MongoDB
    participant Serializer

    Client->>Decorator: Call function(args)
    Decorator->>Decorator: Generate cache key
    Decorator->>Cache: Check cache
    Cache->>MongoDB: Query by hash

    alt Cache Hit
        MongoDB-->>Cache: Return cached data
        Cache->>Serializer: Deserialize
        Serializer-->>Decorator: Return object
        Decorator-->>Client: Return result
    else Cache Miss
        Cache-->>Decorator: Not found
        Decorator->>Function: Execute function(args)
        Function-->>Decorator: Return result
        Decorator->>Serializer: Serialize result
        Serializer-->>Decorator: Return binary data
        Decorator->>Cache: Store result
        Cache->>MongoDB: Insert document
        Decorator-->>Client: Return result
    end
```

### Computation Tracking Flow

```mermaid
sequenceDiagram
    participant Client
    participant Decorator as @register_computation
    participant Computation as Computation Model
    participant MongoDB
    participant Function

    Client->>Decorator: Call function(args)
    Decorator->>Decorator: Generate hash from args
    Decorator->>Computation: Check existing
    Computation->>MongoDB: Query by hash

    alt Already Running/Finished
        MongoDB-->>Computation: Found
        Computation-->>Decorator: Raise error or resume
    else New Computation
        MongoDB-->>Computation: Not found
        Computation->>MongoDB: Create computation (status=started)
        Decorator->>Function: Execute function

        alt Success
            Function-->>Decorator: Return result
            Decorator->>Computation: Update (status=finished)
            Computation->>MongoDB: Save
            Decorator-->>Client: Return result
        else Failure
            Function-->>Decorator: Raise exception
            Decorator->>Computation: Update (status=failed)
            Computation->>MongoDB: Save
            Decorator-->>Client: Raise exception
        end
    end
```

### API Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant Flask
    participant Connexion
    participant Resource
    participant Model
    participant MongoDB

    Client->>Flask: HTTP Request
    Flask->>Connexion: Route to endpoint
    Connexion->>Connexion: Validate against OpenAPI spec
    Connexion->>Resource: Call resource method

    alt GET Request
        Resource->>Model: Query objects
        Model->>MongoDB: Execute query
        MongoDB-->>Model: Return documents
        Model-->>Resource: Return objects
        Resource->>Resource: Serialize to dict
        Resource-->>Connexion: Return JSON
    else POST Request
        Resource->>Resource: Validate request body
        Resource->>Model: Create new document
        Model->>Model: Generate hash
        Model->>MongoDB: Save document
        MongoDB-->>Model: Return saved doc
        Model-->>Resource: Return object
        Resource->>Resource: Serialize to dict
        Resource-->>Connexion: Return JSON (201)
    end

    Connexion-->>Flask: HTTP Response
    Flask-->>Client: JSON Response
```

---

## Database Schema

### Collections Overview

```mermaid
erDiagram
    COMPUTATION {
        ObjectId _id PK
        string name
        string function_name
        string function_name_full
        binary function_pickle
        array args
        object kwargs
        datetime created_at
        datetime updated_at
        datetime started_at
        datetime finished_at
        datetime paused_at
        string message
        string pid
        string status
        string hash UK
    }

    MONGO_CACHE_DB {
        ObjectId _id PK
        string name
        string function_name
        string function_name_full
        binary result
        datetime created_at
        string hash UK
    }

    HASHABLE_DOCUMENT {
        ObjectId _id PK
        string name
        string hash UK
        datetime created_at
        datetime updated_at
    }

    COMPUTATION ||--o{ HASHABLE_DOCUMENT : inherits
    MONGO_CACHE_DB ||--o{ HASHABLE_DOCUMENT : inherits
```

### Key Indexes

| Collection | Index Fields | Type | Purpose |
|------------|-------------|------|---------|
| `computation` | `hash` | Unique | Fast lookup by computation signature |
| `computation` | `status` | Non-unique | Query by status (started, finished, etc.) |
| `computation` | `function_name_full` | Non-unique | Query by function |
| `mongo_cache_d_b` | `hash` | Unique | Fast cache key lookup |
| `mongo_cache_d_b` | `created_at` | Non-unique | TTL index for expiration (future) |

### Hash Generation

The hash field is automatically generated for documents inheriting from `HashableDocument`:

```mermaid
flowchart LR
    A[Document Data] --> B[Filter by _hash_keys]
    B --> C[Exclude _skip_keys]
    C --> D[Sort keys]
    D --> E[JSON serialize]
    E --> F[MD5 hash]
    F --> G[Hex digest]

    style A fill:#e1f5ff
    style G fill:#c8e6c9
```

**Hash Key Strategy:**
- `Computation`: Uses `function_name_full`, `args`, `kwargs`
- `MongoCacheDB`: Uses `function_name_full`, `args`, `kwargs`
- Custom models: Configure via `_hash_keys` class variable

---

## API Architecture

### Resource Pattern

```mermaid
classDiagram
    class ResourceBase {
        <<abstract>>
        +get(**kwargs) ApiResponse
        +get_by_id(id, **kwargs) ApiResponse
        +post(body) ApiResponse
        +put(id, body) ApiResponse
        +delete(id) ApiResponse
    }

    class MongoDBResource {
        -Document model
        +__init__(model)
        +get(**kwargs) ApiResponse
        +get_by_id(id, **kwargs) ApiResponse
        +post(body) ApiResponse
        +put(id, body) ApiResponse
        +delete(id) ApiResponse
    }

    class CustomResource {
        +custom_method()
    }

    ResourceBase <|-- MongoDBResource
    MongoDBResource <|-- CustomResource
```

### Endpoint Structure

```
/api/v1/
├── health                    # Health check
├── {resource}/              # Resource collection
│   ├── GET                  # List (with pagination)
│   ├── POST                 # Create
│   └── {id}/               # Specific resource
│       ├── GET             # Retrieve
│       ├── PUT             # Update
│       └── DELETE          # Delete
└── computations/           # Example resource
    ├── GET ?status=started # Filtered list
    ├── POST                # Create computation
    └── {id}/
        ├── GET             # Get computation
        ├── PUT             # Update status
        └── DELETE          # Delete computation
```

### Pagination

All list endpoints support pagination:

```json
{
  "data": [...],
  "page": 1,
  "per_page": 20,
  "total": 150,
  "pages": 8
}
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

---

## Caching System

### Cache Architecture

```mermaid
graph TB
    subgraph "Decorator Layer"
        DEC[@mongo_cache]
    end

    subgraph "Cache Manager"
        CACHE[ObjectCache]
        KEY[Key Generator]
    end

    subgraph "Storage Layer"
        MONGO_CACHE[MongoCacheDB Model]
    end

    subgraph "Serialization"
        SER[serialize/deserialize]
        PICKLE[Pickle]
        JSON[JSON]
    end

    subgraph "Database"
        MONGO[(MongoDB)]
    end

    DEC --> KEY
    KEY --> CACHE
    CACHE --> MONGO_CACHE
    DEC --> SER
    SER --> PICKLE
    SER --> JSON
    MONGO_CACHE --> MONGO
```

### Cache Key Generation

```mermaid
flowchart LR
    A[Function Name] --> D[Combine]
    B[Args] --> C[Serialize]
    E[Kwargs] --> C
    C --> D
    D --> F[Hash MD5]
    F --> G[Cache Key]

    style A fill:#e1f5ff
    style B fill:#e1f5ff
    style E fill:#e1f5ff
    style G fill:#c8e6c9
```

### Cache Workflow

1. **Cache Check**:
   - Generate cache key from function name + arguments
   - Query MongoDB for existing cache entry
   - If found and valid, deserialize and return

2. **Cache Miss**:
   - Execute original function
   - Serialize result (pickle or JSON)
   - Store in MongoDB with key and metadata
   - Return result to caller

3. **Cache Invalidation** (manual):
   ```python
   MongoCacheDB.objects(function_name='my_function').delete()
   ```

---

## Computation Lifecycle

### State Machine

```mermaid
stateDiagram-v2
    [*] --> Started: Function called
    Started --> Finished: Success
    Started --> Failed: Exception
    Started --> Paused: Manual pause
    Paused --> Started: Resume
    Failed --> [*]
    Finished --> [*]

    note right of Started
        Execution in progress
        PID tracked
    end note

    note right of Paused
        Can be resumed later
        State preserved
    end note

    note right of Failed
        Error message stored
        Stack trace available
    end note
```

### Computation Properties

Each computation tracks:

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Display name |
| `function_name` | string | Short function name |
| `function_name_full` | string | Module.qualified.name |
| `args` | array | Positional arguments (JSON) |
| `kwargs` | object | Keyword arguments (JSON) |
| `status` | enum | started, paused, finished, failed |
| `pid` | string | Process ID |
| `started_at` | datetime | Start timestamp |
| `finished_at` | datetime | Completion timestamp |
| `paused_at` | datetime | Pause timestamp |
| `message` | string | Status message or error |
| `running_time` | computed | Elapsed or total time |

### Usage Pattern

```python
@register_computation
def long_running_task(data: list[int]) -> dict:
    """This function's execution will be tracked."""
    result = complex_calculation(data)
    return result

# Automatically creates Computation document
# Updates status on completion or failure
```

---

## Serialization Architecture

### Multi-Layer Serialization

```mermaid
flowchart TB
    OBJ[Python Object]

    subgraph "Serialization Strategy"
        CHECK{Has to_json?}
        JSON_METHOD[Call to_json]
        CHECK2{Has to_dict?}
        DICT_METHOD[Call to_dict]
        CHECK3{Is Sage object?}
        SAGE_ENC[SageJSONEncoder]
        JSON_ENC[JSONEncoder]
        PICKLE[Pickle fallback]
    end

    RESULT[Serialized Data]

    OBJ --> CHECK
    CHECK -->|Yes| JSON_METHOD --> RESULT
    CHECK -->|No| CHECK2
    CHECK2 -->|Yes| DICT_METHOD --> JSON_ENC --> RESULT
    CHECK2 -->|No| CHECK3
    CHECK3 -->|Yes| SAGE_ENC --> RESULT
    CHECK3 -->|No| PICKLE --> RESULT

    style OBJ fill:#e1f5ff
    style RESULT fill:#c8e6c9
```

### Sage Object Serialization

```mermaid
classDiagram
    class JSONEncoder {
        +encode(obj)
        +default(obj)
    }

    class SageJSONEncoder {
        +default(obj)
        -ring_to_json(ring)
        -matrix_to_json(matrix)
        -vector_to_json(vector)
    }

    class JSONDecoder {
        +decode(s)
        +object_hook(obj)
    }

    class SageJSONDecoder {
        +object_hook(obj)
        -ring_from_json(data)
        -matrix_from_json(data)
        -vector_from_json(data)
    }

    JSONEncoder <|-- SageJSONEncoder
    JSONDecoder <|-- SageJSONDecoder
```

### Supported Sage Types

```mermaid
mindmap
  root((Sage Types))
    Rings
      IntegerRing
      RationalField
      RealField
      ComplexField
      NumberField
    Elements
      Integer
      Rational
      Real
      Complex
      NumberFieldElement
    Structures
      Matrix
      Vector
    Collections
      Dict with Sage keys
      Tuples
```

### Type Representation

Each Sage object is serialized with a `__type__` discriminator:

```json
{
  "__type__": "matrix",
  "base_ring": {
    "__type__": "ring",
    "name": "IntegerRing",
    "prec": 0
  },
  "entries": [["1", "2"], ["3", "4"]]
}
```

---

## Security Considerations

### Current Security Measures

1. **Input Validation**:
   - OpenAPI schema validation on all API inputs
   - Type checking with Python type hints
   - MongoEngine field validation

2. **Database Security**:
   - MongoDB connection URI via environment variables
   - No hardcoded credentials
   - Connection pooling with timeout

3. **Serialization Safety**:
   - Pickle deserialization only for trusted data
   - JSON preferred for user-facing APIs
   - Hash verification for cached data

### Security Recommendations

**For Production Deployment:**

1. **Authentication & Authorization**:
   - Add API authentication (JWT, OAuth2)
   - Implement role-based access control (RBAC)
   - Rate limiting on API endpoints

2. **Network Security**:
   - TLS/SSL for MongoDB connections
   - HTTPS only for API endpoints
   - Firewall rules for MongoDB access

3. **Data Protection**:
   - Encrypt sensitive data at rest
   - Secure key management
   - Regular security audits

4. **Input Sanitization**:
   - Validate all user inputs
   - Prevent NoSQL injection
   - Escape output in logs

---

## Performance Considerations

### Scalability Patterns

```mermaid
graph TB
    subgraph "Application Tier"
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance N]
    end

    subgraph "Cache Tier"
        REDIS[Redis Cache<br/>Future]
    end

    subgraph "Database Tier"
        MONGO_PRIMARY[MongoDB Primary]
        MONGO_SEC1[MongoDB Secondary]
        MONGO_SEC2[MongoDB Secondary]
    end

    LB[Load Balancer] --> APP1
    LB --> APP2
    LB --> APP3

    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS

    REDIS --> MONGO_PRIMARY

    MONGO_PRIMARY -.->|Replication| MONGO_SEC1
    MONGO_PRIMARY -.->|Replication| MONGO_SEC2

    style LB fill:#f9f
    style REDIS fill:#ff9
    style MONGO_PRIMARY fill:#9f9
```

### Optimization Strategies

1. **Database Optimization**:
   - Compound indexes for common queries
   - Index on frequently filtered fields
   - Connection pooling
   - Query projection to reduce data transfer

2. **Caching Strategy**:
   - MongoDB for large, persistent cache
   - Consider Redis for hot cache layer
   - Cache invalidation strategy
   - TTL indexes for automatic expiration

3. **Serialization Performance**:
   - JSON preferred over pickle for speed
   - Lazy deserialization where possible
   - Streaming for large objects

4. **API Performance**:
   - Pagination for large result sets
   - Field selection in queries
   - ETag caching for unchanged data
   - Compression for responses

### Performance Metrics

Monitor these key metrics:

- **API Response Time**: < 200ms for cached queries
- **Cache Hit Rate**: > 80% for repeated queries
- **Database Query Time**: < 50ms for indexed queries
- **Serialization Time**: < 10ms for typical objects

---

## Design Decisions

### 1. MongoDB as Primary Database

**Decision**: Use MongoDB instead of relational database

**Rationale**:
- Flexible schema for diverse computation types
- Easy to store nested/complex arguments
- JSON-like documents match Python dictionaries
- Built-in GridFS for large binary data
- Good performance for write-heavy workloads

**Trade-offs**:
- No ACID transactions across multiple documents
- Manual referential integrity
- Limited join capabilities

### 2. Decorator-Based Interface

**Decision**: Use Python decorators for caching and tracking

**Rationale**:
- Minimal code changes for existing functions
- Clear separation of concerns
- Easy to add/remove functionality
- Pythonic and familiar pattern

**Trade-offs**:
- Less obvious for newcomers
- Debugging can be harder
- Order of decorators matters

### 3. Hash-Based Uniqueness

**Decision**: Use MD5 hash of arguments for deduplication

**Rationale**:
- Fast computation
- Fixed size regardless of input
- Low collision probability for typical data
- Enables efficient lookups

**Trade-offs**:
- Not cryptographically secure (not needed)
- Requires deterministic serialization
- Hash collisions theoretically possible

### 4. Hybrid Serialization

**Decision**: Support both Pickle and JSON serialization

**Rationale**:
- Pickle for complex Python objects
- JSON for cross-language compatibility
- JSON for user-facing APIs
- Flexibility for different use cases

**Trade-offs**:
- More code complexity
- Pickle has security concerns
- Need to choose strategy per use case

### 5. OpenAPI/Connexion for API

**Decision**: Use Connexion framework with OpenAPI specs

**Rationale**:
- Automatic request/response validation
- Interactive documentation (Swagger UI)
- API-first development
- Industry standard

**Trade-offs**:
- Learning curve for OpenAPI
- Some boilerplate in spec files
- Less flexibility than pure Flask

---

## Future Architecture Enhancements

### Planned Improvements

1. **Microservices Architecture**:
   - Split into separate services (API, Worker, Cache)
   - Message queue for async computations
   - Independent scaling of components

2. **Event-Driven Design**:
   - Event bus for computation state changes
   - Webhook support for notifications
   - Real-time updates via WebSockets

3. **Advanced Caching**:
   - Multi-tier cache (Redis + MongoDB)
   - Intelligent cache warming
   - Distributed cache invalidation

4. **Observability**:
   - Distributed tracing (OpenTelemetry)
   - Metrics (Prometheus)
   - Structured logging
   - Performance profiling

5. **High Availability**:
   - MongoDB replica sets
   - Application clustering
   - Automatic failover
   - Circuit breakers

---

## Conclusion

Comp Manager's architecture is designed for:

- **Simplicity**: Easy to understand and extend
- **Flexibility**: Adaptable to different use cases
- **Performance**: Optimized for mathematical workloads
- **Maintainability**: Clean separation of concerns
- **Scalability**: Foundation for future growth

The current design supports single-instance deployment with room to grow into a distributed, highly-available system as needs evolve.

---

## References

- [MongoDB Best Practices](https://www.mongodb.com/docs/manual/administration/production-notes/)
- [Flask Application Structure](https://flask.palletsprojects.com/en/latest/patterns/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [MongoEngine Documentation](http://docs.mongoengine.org/)
- [SageMath Documentation](https://doc.sagemath.org/)

---

*Last Updated: 2026-01-06*
*Document Maintainer: Fredrik Stromberg*
