# pyWATS Client/Service Architecture Diagrams

This document provides visual diagrams explaining how the pyWATS client and service processes work together, including data flows, timers, queues, and communication patterns.

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Service Process Components](#2-service-process-components)
3. [Service Lifecycle & Timers](#3-service-lifecycle--timers)
4. [Report Submission Flow (Pending Queue)](#4-report-submission-flow-pending-queue)
5. [Converter Pipeline](#5-converter-pipeline)
6. [GUI-Service Communication (IPC)](#6-gui-service-communication-ipc)
7. [Async Task System](#7-async-task-system)
8. [Event Bus & Signals](#8-event-bus--signals)
9. [Error Recovery & Retry Logic](#9-error-recovery--retry-logic)
10. [Complete Data Flow](#10-complete-data-flow)

---

## 1. High-Level Architecture

The pyWATS client uses a **two-process architecture**:

```mermaid
flowchart TB
    subgraph WATS["☁️ WATS Server"]
        API["REST API<br/>(HTTPS)"]
    end
    
    subgraph SERVICE["🖥️ Service Process<br/>(python -m pywats_client service)"]
        direction TB
        ACS["AsyncClientService<br/>(Main Controller)"]
        AW["AsyncWATS<br/>(API Client)"]
        APQ["AsyncPendingQueue<br/>(Report Queue)"]
        ACP["AsyncConverterPool<br/>(File Processing)"]
        IPC_S["IPC Server<br/>(Unix/TCP)"]
        HS["Health Server<br/>(HTTP :8080)"]
        
        ACS --> AW
        ACS --> APQ
        ACS --> ACP
        ACS --> IPC_S
        ACS --> HS
    end
    
    subgraph GUI["🖼️ GUI Process (Optional)<br/>(python -m pywats_client)"]
        direction TB
        MW["MainWindow<br/>(PySide6/Qt)"]
        IPC_C["AsyncIPCClient"]
        ATR["AsyncTaskRunner"]
        EB["EventBus"]
        
        MW --> ATR
        MW --> EB
        MW --> IPC_C
    end
    
    subgraph FILES["📁 File System"]
        WF["Watch Folders<br/>(test results)"]
        PQ["Pending Queue<br/>(/queue/*.queued)"]
        CF["Config Files<br/>(config.json)"]
    end
    
    %% Connections
    AW <--"HTTP"--> API
    APQ <--"Files"--> PQ
    ACP <--"Watchdog"--> WF
    ACS <--"Watch"--> CF
    IPC_C <--"IPC Protocol"--> IPC_S
    HS --"Health Check"--> API
    
    style SERVICE fill:#1a1a2e,stroke:#16213e,color:#fff
    style GUI fill:#16213e,stroke:#0f3460,color:#fff
    style WATS fill:#0f3460,stroke:#e94560,color:#fff
    style FILES fill:#2d2d2d,stroke:#3c3c3c,color:#fff
```

---

## 2. Service Process Components

```mermaid
flowchart TB
    subgraph AsyncClientService["AsyncClientService (Main Controller)"]
        direction TB
        
        subgraph State["Service State Machine"]
            STOPPED["STOPPED"]
            START_PENDING["START_PENDING"]
            RUNNING["RUNNING"]
            STOP_PENDING["STOP_PENDING"]
            
            STOPPED -->|"start()"| START_PENDING
            START_PENDING -->|"init complete"| RUNNING
            RUNNING -->|"stop()"| STOP_PENDING
            STOP_PENDING -->|"cleanup done"| STOPPED
        end
        
        subgraph Timers["Background Timers (asyncio Tasks)"]
            WD["🔄 Watchdog<br/>60s interval"]
            PING["📡 Ping<br/>5min interval"]
            REG["📋 Registration<br/>1hr interval"]
            CFW["📝 Config Watch<br/>5s interval"]
        end
        
        subgraph Components["Owned Components"]
            API["AsyncWATS API Client"]
            QUEUE["AsyncPendingQueue"]
            CONV["AsyncConverterPool"]
            IPC["AsyncIPCServer"]
            HEALTH["HealthServer :8080"]
        end
    end
    
    WD -->|"check health"| API
    WD -->|"check stuck files"| QUEUE
    PING -->|"verify connectivity"| API
    REG -->|"update status"| API
    CFW -->|"hot reload"| Components
    
    style AsyncClientService fill:#1a1a2e,stroke:#16213e,color:#fff
    style State fill:#16213e,stroke:#0f3460,color:#fff
    style Timers fill:#0f3460,stroke:#e94560,color:#fff
    style Components fill:#2d2d2d,stroke:#3c3c3c,color:#fff
```

---

## 3. Service Lifecycle & Timers

```mermaid
sequenceDiagram
    participant User
    participant Service as AsyncClientService
    participant API as AsyncWATS
    participant Queue as AsyncPendingQueue
    participant Conv as AsyncConverterPool
    participant IPC as IPCServer
    
    User->>Service: start()
    activate Service
    
    Note over Service: State: START_PENDING
    
    Service->>API: Initialize connection
    API-->>Service: Connected
    
    Service->>Service: Start Watchdog Timer (60s)
    Service->>Service: Start Ping Timer (5min)
    Service->>Service: Start Registration Timer (1hr)
    
    Service->>Queue: start()
    Queue-->>Service: Started
    
    Service->>Conv: start()
    Conv-->>Service: Started (file watchers active)
    
    Service->>Service: Start Config Watcher (5s)
    
    Service->>IPC: start()
    IPC-->>Service: Listening
    
    Note over Service: State: RUNNING
    
    loop Every 60 seconds
        Service->>API: Health check
        Service->>Queue: Check stuck files
        Service->>Conv: Check converter health
    end
    
    loop Every 5 minutes
        Service->>API: Ping
    end
    
    loop Every 1 hour
        Service->>API: Update registration
    end
    
    User->>Service: stop()
    Note over Service: State: STOP_PENDING
    
    Service->>Conv: stop()
    Service->>Queue: stop() [wait for in-flight]
    Service->>IPC: stop()
    Service->>API: Close connections
    
    Note over Service: State: STOPPED
    deactivate Service
```

---

## 4. Report Submission Flow (Pending Queue)

```mermaid
flowchart TB
    subgraph Input["📥 Report Sources"]
        CONV["Converter Output"]
        DIRECT["Direct API Call"]
        IMPORT["Manual Import"]
    end
    
    subgraph Queue["📂 Pending Queue"]
        direction TB
        
        subgraph Files["Queue Files"]
            QUEUED["*.queued<br/>(waiting)"]
            PROC["*.processing<br/>(in flight)"]
            COMP["*.completed<br/>(success)"]
            ERR["*.error<br/>(failed)"]
        end
        
        subgraph Watcher["File Watcher (watchdog)"]
            FW["Monitor queue folder"]
        end
        
        subgraph Processor["Submit Processor"]
            SEM["Semaphore<br/>(max 10 concurrent)"]
            SUBMIT["_submit_report()"]
        end
    end
    
    subgraph API["🌐 WATS API"]
        RS["report.submit_raw()"]
    end
    
    %% Flow
    Input -->|"Write JSON"| QUEUED
    FW -->|"Detect new file"| SEM
    SEM -->|"Acquire slot"| SUBMIT
    SUBMIT -->|"Rename"| PROC
    PROC -->|"Read + Submit"| RS
    RS -->|"Success"| COMP
    RS -->|"Failure"| ERR
    
    subgraph Retry["🔄 Retry Logic"]
        PERIODIC["Periodic Check<br/>(60s)"]
        BACKOFF["Exponential Backoff<br/>5min × 2^(n-1)"]
    end
    
    PERIODIC -->|"Find .error files"| BACKOFF
    BACKOFF -->|"Retry if eligible"| QUEUED
    
    style Queue fill:#1a1a2e,stroke:#16213e,color:#fff
    style Input fill:#0f3460,stroke:#e94560,color:#fff
    style API fill:#16213e,stroke:#0f3460,color:#fff
```

### File State Machine

```mermaid
stateDiagram-v2
    [*] --> queued: File created
    queued --> processing: Submit started
    processing --> completed: API success
    processing --> error: API failure
    error --> queued: Retry (backoff elapsed)
    error --> exhausted: Max retries (5)
    completed --> [*]: Cleanup
    exhausted --> [*]: Move to failed folder
    
    note right of processing
        Stuck detection: >30min
        Auto-reset to queued
    end note
```

---

## 5. Converter Pipeline

```mermaid
flowchart TB
    subgraph WatchFolders["📁 Watch Folders"]
        F1["C:/TestResults/Station1"]
        F2["C:/TestResults/Station2"]
        F3["C:/Archive/*.csv"]
    end
    
    subgraph Converters["🔧 Converter Pool"]
        direction TB
        
        subgraph Registration["Converter Registry"]
            CSV["CSV Converter<br/>patterns: *.csv"]
            XML["XML Converter<br/>patterns: *.xml, *.uut"]
            CUSTOM["Custom Converter<br/>patterns: *.dat"]
        end
        
        subgraph Watchers["File Watchers (watchdog)"]
            W1["Watcher 1"]
            W2["Watcher 2"]
            W3["Watcher 3"]
        end
        
        subgraph Processing["Processing Pipeline"]
            TQUEUE["Thread-safe Queue<br/>(janus)"]
            SEM["Semaphore<br/>(max 10)"]
            PROC["_process_item()"]
        end
    end
    
    subgraph Conversion["📄 Conversion Steps"]
        READ["Read File<br/>(aiofiles)"]
        CONVERT["converter.convert()<br/>(thread pool)"]
        VALIDATE["Validate Report"]
    end
    
    subgraph Output["📤 Output"]
        SUBMIT["api.report.submit()"]
        POST["Post-Process"]
    end
    
    subgraph PostActions["Post-Process Actions"]
        DELETE["DELETE: Remove source"]
        MOVE["MOVE: Archive folder"]
        ZIP["ZIP: Compress"]
        KEEP["KEEP: Leave in place"]
    end
    
    %% Connections
    F1 --> W1
    F2 --> W2
    F3 --> W3
    
    W1 & W2 & W3 -->|"File event"| TQUEUE
    TQUEUE --> SEM
    SEM --> PROC
    PROC --> READ
    READ --> CONVERT
    CONVERT --> VALIDATE
    VALIDATE --> SUBMIT
    SUBMIT -->|"Success"| POST
    
    POST --> DELETE & MOVE & ZIP & KEEP
    
    style Converters fill:#1a1a2e,stroke:#16213e,color:#fff
    style Conversion fill:#0f3460,stroke:#e94560,color:#fff
```

### Converter Sequence

```mermaid
sequenceDiagram
    participant FS as File System
    participant WD as Watchdog
    participant Q as janus Queue
    participant Pool as ConverterPool
    participant Conv as Converter
    participant API as AsyncWATS
    
    FS->>WD: File created event
    WD->>WD: Match file patterns
    
    alt Pattern matches
        WD->>Q: sync_q.put(item)
        Note over Q: Thread-safe bridge
        Q->>Pool: async_q.get()
        
        Pool->>Pool: Acquire semaphore (max 10)
        activate Pool
        
        Pool->>FS: Read file (aiofiles)
        FS-->>Pool: Content bytes
        
        Pool->>Conv: convert(content) [in thread pool]
        Conv-->>Pool: Report dict (WSJF format)
        
        Pool->>API: report.submit(report)
        
        alt Success
            API-->>Pool: Report ID
            Pool->>FS: Post-process (delete/move/archive)
        else Failure
            API-->>Pool: Error
            Pool->>FS: Move to error folder
        end
        
        Pool->>Pool: Release semaphore
        deactivate Pool
    end
```

---

## 6. GUI-Service Communication (IPC)

```mermaid
flowchart LR
    subgraph GUI["🖼️ GUI Process"]
        direction TB
        PAGE["GUI Page<br/>(e.g., Dashboard)"]
        MIXIN["AsyncAPIMixin"]
        CLIENT["AsyncIPCClient"]
    end
    
    subgraph Protocol["📡 IPC Protocol"]
        direction TB
        
        subgraph Windows["Windows"]
            TCP["TCP localhost<br/>Port: 50000 + hash"]
        end
        
        subgraph Unix["Linux/macOS"]
            SOCK["/tmp/pyWATS_Service_X.sock"]
        end
        
        MSG["Length-prefixed JSON<br/>[4 bytes len][JSON payload]"]
    end
    
    subgraph Service["🖥️ Service Process"]
        direction TB
        SERVER["AsyncIPCServer"]
        SVC["AsyncClientService"]
    end
    
    PAGE -->|"run_api_call()"| MIXIN
    MIXIN -->|"get_status()"| CLIENT
    CLIENT <-->|"Request/Response"| TCP & SOCK
    TCP & SOCK <--> SERVER
    SERVER -->|"Process command"| SVC
    SVC -->|"Response data"| SERVER
    
    style GUI fill:#16213e,stroke:#0f3460,color:#fff
    style Protocol fill:#0f3460,stroke:#e94560,color:#fff
    style Service fill:#1a1a2e,stroke:#16213e,color:#fff
```

### IPC Commands

```mermaid
sequenceDiagram
    participant GUI as GUI (AsyncIPCClient)
    participant SVC as Service (AsyncIPCServer)
    
    Note over GUI,SVC: Available Commands
    
    GUI->>SVC: {"command": "ping"}
    SVC-->>GUI: {"success": true, "data": {"pong": true}}
    
    GUI->>SVC: {"command": "get_status"}
    SVC-->>GUI: {"success": true, "data": {<br/>  "status": "Running",<br/>  "api_status": "Online",<br/>  "pending_count": 5,<br/>  "processing_count": 2<br/>}}
    
    GUI->>SVC: {"command": "get_config"}
    SVC-->>GUI: {"success": true, "data": {...config...}}
    
    GUI->>SVC: {"command": "stop"}
    SVC-->>GUI: {"success": true, "data": {"requested": true}}
    
    GUI->>SVC: {"command": "restart"}
    SVC-->>GUI: {"success": true, "data": {"requested": true}}
```

---

## 7. Async Task System

```mermaid
flowchart TB
    subgraph GUI["🖼️ Qt Main Thread"]
        PAGE["Page Component"]
        MIXIN["AsyncAPIMixin"]
    end
    
    subgraph Runner["🔄 AsyncTaskRunner"]
        direction TB
        
        subgraph BG["Background Thread"]
            LOOP["asyncio Event Loop"]
            TASKS["Task Registry"]
        end
        
        subgraph Signals["Qt Signals (Thread-safe)"]
            S1["task_started(id, name)"]
            S2["task_completed(TaskResult)"]
            S3["task_failed(TaskResult)"]
            S4["task_progress(id, %, msg)"]
            S5["task_cancelled(id)"]
        end
    end
    
    subgraph Result["📊 TaskResult"]
        R1["task_id: str"]
        R2["is_success: bool"]
        R3["result: Any"]
        R4["error: Exception"]
        R5["elapsed: float"]
    end
    
    PAGE -->|"1. User action"| MIXIN
    MIXIN -->|"2. run_async(coro)"| LOOP
    LOOP -->|"3. Execute coroutine"| TASKS
    TASKS -->|"4. Emit signal"| Signals
    Signals -->|"5. Qt event loop"| PAGE
    
    S2 & S3 --> Result
    
    style GUI fill:#16213e,stroke:#0f3460,color:#fff
    style Runner fill:#1a1a2e,stroke:#16213e,color:#fff
```

### Task Execution Flow

```mermaid
sequenceDiagram
    participant Page as GUI Page
    participant Mixin as AsyncAPIMixin
    participant Runner as AsyncTaskRunner
    participant Loop as BG Event Loop
    participant API as AsyncWATS
    
    Page->>Mixin: run_api_call(lambda api: api.asset.get_assets())
    Mixin->>Mixin: Check API type (sync/async)
    
    alt Has Async API
        Mixin->>Runner: run_async(coro, name="Loading assets...")
        Runner->>Runner: Generate task_id
        Runner->>Loop: Submit via call_soon_threadsafe
        
        activate Loop
        Loop->>API: await api.asset.get_assets()
        API-->>Loop: [Asset, Asset, ...]
        deactivate Loop
        
        Loop->>Runner: Emit task_completed signal
        Runner->>Page: on_success(result)
    else Sync API only
        Mixin->>Runner: run_async(_execute_in_thread())
        Runner->>Loop: Submit wrapped sync call
        Loop->>Loop: asyncio.to_thread(sync_call)
        Loop->>Runner: Emit task_completed
        Runner->>Page: on_success(result)
    end
```

---

## 8. Event Bus & Signals

```mermaid
flowchart TB
    subgraph EventBus["📢 EventBus (Singleton)"]
        direction TB
        
        subgraph Connection["Connection Events"]
            E1["service_connected"]
            E2["service_disconnected"]
            E3["api_connected"]
            E4["api_disconnected"]
        end
        
        subgraph Lifecycle["Lifecycle Events"]
            E5["app_starting"]
            E6["app_ready"]
            E7["app_closing"]
            E8["app_shutdown"]
        end
        
        subgraph Data["Data Change Events"]
            E9["config_changed"]
            E10["converters_changed"]
            E11["queue_updated"]
        end
        
        subgraph Queue["Queue Events"]
            E12["report_queued"]
            E13["report_submitted"]
            E14["report_failed"]
        end
    end
    
    subgraph Publishers["Publishers"]
        SVC["Service"]
        QUEUE["PendingQueue"]
        CONV["ConverterPool"]
        MW["MainWindow"]
    end
    
    subgraph Subscribers["Subscribers"]
        DASH["DashboardPage"]
        SETUP["SetupPage"]
        LOG["LogPage"]
        TRAY["SystemTray"]
    end
    
    Publishers -->|"emit()"| EventBus
    EventBus -->|"connect()"| Subscribers
    
    style EventBus fill:#1a1a2e,stroke:#16213e,color:#fff
```

### Event Flow Example

```mermaid
sequenceDiagram
    participant Conv as ConverterPool
    participant EB as EventBus
    participant Dash as DashboardPage
    participant Log as LogPage
    participant Tray as SystemTray
    
    Conv->>Conv: Report converted successfully
    Conv->>EB: emit("report_queued", report_info)
    
    par Parallel delivery
        EB->>Dash: on_report_queued(info)
        Dash->>Dash: Update queue count display
    and
        EB->>Log: on_report_queued(info)
        Log->>Log: Add log entry
    and
        EB->>Tray: on_report_queued(info)
        Tray->>Tray: Update tooltip
    end
```

---

## 9. Error Recovery & Retry Logic

```mermaid
flowchart TB
    subgraph Detection["🔍 Error Detection"]
        API_ERR["API Error<br/>(HTTP 4xx/5xx)"]
        TIMEOUT["Timeout<br/>(no response)"]
        NET_ERR["Network Error<br/>(connection lost)"]
    end
    
    subgraph Queue["📂 Queue Error Handling"]
        direction TB
        
        ERR_FILE["Create .error file"]
        ERR_INFO["Write .error.info<br/>(error details, attempts)"]
        
        subgraph Backoff["Exponential Backoff"]
            B1["Attempt 1: 5 min wait"]
            B2["Attempt 2: 10 min wait"]
            B3["Attempt 3: 20 min wait"]
            B4["Attempt 4: 40 min wait"]
            B5["Attempt 5: 80 min wait"]
            B6["Exhausted: Move to /failed"]
        end
    end
    
    subgraph Recovery["🔄 Recovery Mechanisms"]
        STUCK["Stuck File Detection<br/>(>30min in .processing)"]
        PERIODIC["Periodic Check<br/>(every 60s)"]
        RESTART["Service Restart<br/>(crash recovery)"]
    end
    
    Detection --> ERR_FILE
    ERR_FILE --> ERR_INFO
    ERR_INFO --> Backoff
    
    B1 --> B2 --> B3 --> B4 --> B5 --> B6
    
    PERIODIC -->|"Check .error files"| Backoff
    STUCK -->|"Reset to .queued"| Queue
    RESTART -->|"Scan queue folder"| Queue
    
    style Detection fill:#e94560,stroke:#0f3460,color:#fff
    style Queue fill:#1a1a2e,stroke:#16213e,color:#fff
    style Recovery fill:#16213e,stroke:#0f3460,color:#fff
```

### Retry Sequence

```mermaid
sequenceDiagram
    participant Queue as PendingQueue
    participant API as WATS API
    participant FS as File System
    
    Note over Queue: Attempt 1
    Queue->>API: Submit report
    API-->>Queue: Error 503 (Service Unavailable)
    Queue->>FS: report.queued → report.error
    Queue->>FS: Write report.error.info (attempt=1)
    
    Note over Queue: Wait 5 minutes...
    
    Note over Queue: Attempt 2 (Periodic check)
    Queue->>FS: Check .error files
    Queue->>FS: Read report.error.info
    Queue->>Queue: backoff_elapsed? (5min passed)
    Queue->>FS: report.error → report.queued
    Queue->>API: Submit report
    API-->>Queue: Error 503
    Queue->>FS: report.queued → report.error
    Queue->>FS: Update report.error.info (attempt=2)
    
    Note over Queue: Wait 10 minutes...
    
    Note over Queue: After 5 failed attempts
    Queue->>FS: Move to /failed folder
    Queue->>Queue: Log exhausted error
```

---

## 10. Complete Data Flow

```mermaid
flowchart TB
    subgraph External["🌍 External"]
        WATS["WATS Server"]
        TE["Test Equipment<br/>(creates files)"]
    end
    
    subgraph FileSystem["📁 File System"]
        WATCH["Watch Folders<br/>/results/*.csv"]
        QUEUE["Queue Folder<br/>/queue/*.queued"]
        CONFIG["Config<br/>/config/config.json"]
    end
    
    subgraph Service["🖥️ Service Process"]
        direction TB
        
        SVC["AsyncClientService"]
        
        subgraph Processing["Processing Pipeline"]
            CP["ConverterPool"]
            PQ["PendingQueue"]
        end
        
        subgraph Timers["Background Tasks"]
            T1["⏱️ Watchdog 60s"]
            T2["⏱️ Ping 5min"]
            T3["⏱️ Config 5s"]
        end
        
        API["AsyncWATS"]
        IPC["IPC Server"]
    end
    
    subgraph GUI["🖼️ GUI Process"]
        direction TB
        MW["MainWindow"]
        
        subgraph Pages["Pages"]
            DASH["Dashboard"]
            SETUP["Setup"]
            LOG["Log"]
            CONV_PAGE["Converters"]
        end
        
        CLIENT["IPC Client"]
        RUNNER["TaskRunner"]
    end
    
    %% File creation flow
    TE -->|"1. Create test file"| WATCH
    
    %% Converter flow
    WATCH -->|"2. Watchdog event"| CP
    CP -->|"3. Convert to JSON"| PQ
    
    %% Queue flow
    PQ -->|"4. Write .queued"| QUEUE
    QUEUE -->|"5. File event"| PQ
    PQ -->|"6. Submit"| API
    API -->|"7. HTTP POST"| WATS
    
    %% Config flow
    CONFIG -->|"Watch changes"| SVC
    SVC -->|"Hot reload"| Processing
    
    %% GUI flow
    MW --> CLIENT
    CLIENT <-->|"IPC"| IPC
    IPC --> SVC
    
    %% Timer flows
    T1 -->|"Health check"| API
    T2 -->|"Ping"| API
    T3 -->|"Reload"| CONFIG
    
    %% GUI page updates
    RUNNER --> Pages
    
    style External fill:#0f3460,stroke:#e94560,color:#fff
    style Service fill:#1a1a2e,stroke:#16213e,color:#fff
    style GUI fill:#16213e,stroke:#0f3460,color:#fff
    style FileSystem fill:#2d2d2d,stroke:#3c3c3c,color:#fff
```

---

## Timers & Intervals Summary

| Component | Interval | Purpose | Location |
|-----------|----------|---------|----------|
| **Watchdog** | 60s | Health checks, stuck file detection | `AsyncClientService._watchdog_loop()` |
| **Ping** | 5min | Verify WATS connectivity | `AsyncClientService._ping_loop()` |
| **Registration** | 1hr | Update client status on server | `AsyncClientService._registration_loop()` |
| **Config Watch** | 5s | Hot-reload configuration | `AsyncClientService._config_watch_loop()` |
| **Queue Check** | 60s | Process pending/error files | `AsyncPendingQueue._run_loop()` |
| **Error Retry** | 5min × 2^(n-1) | Exponential backoff for failed reports | `AsyncPendingQueue._process_error_files()` |
| **GUI Status** | 5s | Update service status display | `MainWindow._status_timer` |
| **Service Discovery** | 5s | Find running service instances | `ServiceDiscoveryAsync` |

---

## Key Concurrency Limits

| Component | Limit | Purpose |
|-----------|-------|---------|
| **PendingQueue** | 10 concurrent | Max simultaneous API submissions |
| **ConverterPool** | 10 concurrent | Max simultaneous file conversions |
| **IPC Clients** | Unlimited | No limit on GUI connections |
| **Watchdog Threads** | 1 per converter | File system monitoring |

---

## See Also

- [Component Architecture](component-architecture.md) - Package structure and dependencies
- [Client Architecture](client-architecture.md) - Technical implementation details
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues and solutions
