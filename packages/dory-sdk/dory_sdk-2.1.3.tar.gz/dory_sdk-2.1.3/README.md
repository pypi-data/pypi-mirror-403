# Dory SDK for Python

A Python SDK for building stateful processors with **zero-downtime migration**, **graceful shutdown**, and **state transfer** on Kubernetes.

## What Does This SDK Do For You?

| Feature | Without Dory SDK | With Dory SDK |
|---------|------------------|---------------|
| Pod shutdown | App killed, state lost | State saved automatically, restored on new pod |
| Node maintenance | Downtime, manual intervention | Zero-downtime migration to new node |
| Crash recovery | Start from scratch | Resume from last checkpoint |
| Health monitoring | DIY implementation | Built-in `/healthz`, `/ready`, `/metrics` |

---

## Quick Start (Choose Your Style)

### Option A: Minimal (7 lines)

```python
from dory import DoryApp, BaseProcessor, stateful

class MyApp(BaseProcessor):
    counter = stateful(0)  # Auto-saved and restored!

    async def run(self):
        async for _ in self.run_loop(interval=1):
            self.counter += 1

if __name__ == "__main__":
    DoryApp().run(MyApp)
```

### Option B: Function-Based (6 lines)

```python
from dory.simple import processor, state

counter = state(0)

@processor
async def main(ctx):
    async for _ in ctx.run_loop(interval=1):
        counter.value += 1
```

### Option C: Full Control

```python
from dory import DoryApp, BaseProcessor, ExecutionContext

class MyApp(BaseProcessor):
    def __init__(self, context: ExecutionContext):
        super().__init__(context)
        self.counter = 0

    async def startup(self):
        self.context.logger().info("Starting...")

    async def run(self):
        while not self.context.is_shutdown_requested():
            self.counter += 1
            await asyncio.sleep(1)

    async def shutdown(self):
        self.context.logger().info(f"Final count: {self.counter}")

    def get_state(self):
        return {"counter": self.counter}

    async def restore_state(self, state):
        self.counter = state.get("counter", 0)

if __name__ == "__main__":
    DoryApp().run(MyApp)
```

---

## Installation

```bash
pip install dory-sdk[production]
```

---

## CLI Tool

The SDK includes a CLI for generating Kubernetes manifests:

```bash
# Initialize a new project with all files
dory init my-app --image my-app:latest

# Output:
#   Created main.py
#   Created Dockerfile
#   Created k8s/rbac.yaml
#   Created k8s/deployment.yaml

# Generate specific manifests
dory generate rbac --name my-app
dory generate deployment --name my-app --image my-app:latest
dory generate all --name my-app --image my-app:latest

# Validate configuration
dory validate
```

---

## Deployment Options

### Option 1: Helm Chart

```bash
helm install my-app ./helm/dory-processor \
  --set name=my-app \
  --set image.repository=my-app \
  --set image.tag=latest
```

With values file:
```bash
helm install my-app ./helm/dory-processor -f values.yaml
```

### Option 2: CLI Generated Manifests

```bash
dory init my-app --image my-app:latest
kubectl apply -f k8s/
```

### When to Use Which

| Choose | When |
|--------|------|
| **Helm** | Need release management, rollback, existing Helm workflow |
| **CLI** | Quick start, simple deployments |
| **Orchestrator** | Production deployments with dynamic pod management |

---

## Sidecar Mode (No SDK Required)

Don't want to integrate the SDK? Use **sidecar mode** - your app runs unchanged, a lightweight sidecar handles Kubernetes health endpoints.

### What You Get

| Feature | With SDK | Sidecar Mode |
|---------|----------|--------------|
| Health endpoints | Yes | Yes |
| Graceful shutdown | Yes | Yes |
| State migration | Yes | **No** |
| Zero code changes | No | **Yes** |

### Deploy with Sidecar

**Using Helm:**
```bash
helm install my-app ./helm/dory-processor \
  --set image.repository=your-app \
  --set image.tag=latest \
  --set sidecar.enabled=true
```

**Using Orchestrator:**

Configure `use_sidecar: true` in your `runtime_config_template` - the orchestrator automatically injects the sidecar container.

### How It Works

```
┌─────────────────────────────────────────┐
│                  Pod                     │
│  ┌─────────────┐    ┌────────────────┐  │
│  │  Your App   │    │  Dory Sidecar  │  │
│  │  (no SDK)   │    │                │  │
│  │             │    │  /healthz ←────┼──┼── K8s liveness
│  │  port 8081 ←┼────┼→ /ready   ←────┼──┼── K8s readiness
│  │             │    │  /prestop ←────┼──┼── K8s preStop
│  │             │    │  /metrics      │  │
│  └─────────────┘    └────────────────┘  │
└─────────────────────────────────────────┘
```

The sidecar:
- Responds to Kubernetes health probes
- Optionally monitors your app's port/health endpoint
- Handles graceful shutdown signals

### Sidecar Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DORY_APP_PORT` | - | Your app's port (optional monitoring) |
| `DORY_APP_HEALTH_PATH` | - | Your app's health endpoint to check |
| `DORY_APP_PRESTOP_PATH` | - | Your app's shutdown endpoint to call |
| `DORY_READY_REQUIRES_APP` | false | Fail /ready if app doesn't respond |

### Build the Sidecar Image

The sidecar is maintained in the [orchestrator repository](../orchestrator/sidecar/). See the sidecar README for build and push instructions.

```bash
cd ../orchestrator/sidecar
docker build --platform linux/amd64 -t dory-sidecar:latest .
```

---

## Integration Guide

### Step 1: Install SDK

```bash
pip install dory-sdk[production]
```

### Step 2: Write Your Processor

**Minimal (with `@stateful`):**
```python
from dory import DoryApp, BaseProcessor, stateful

class MyApp(BaseProcessor):
    # These are automatically saved/restored
    counter = stateful(0)
    data = stateful(dict)

    async def run(self):
        async for i in self.run_loop(interval=1):
            self.counter += 1

if __name__ == "__main__":
    DoryApp().run(MyApp)
```

**That's it!** The SDK handles:
- `get_state()` - auto-generated from `@stateful` vars
- `restore_state()` - auto-generated from `@stateful` vars
- `startup()` - default no-op
- `shutdown()` - default no-op

### Step 3: Deploy to Kubernetes

**Option A: Use CLI**
```bash
dory init my-app --image my-app:latest
kubectl apply -f k8s/
```

**Option B: Use Helm**
```bash
helm install my-app ./helm/dory-processor --set image.repository=my-app
```

**Option C: Manual Setup**

1. Create RBAC:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-state-manager
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-state-manager
subjects:
- kind: ServiceAccount
  name: my-app
roleRef:
  kind: Role
  name: my-app-state-manager
  apiGroup: rbac.authorization.k8s.io
```

2. Create Deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      serviceAccountName: my-app
      terminationGracePeriodSeconds: 35
      containers:
      - name: my-app
        image: my-app:latest
        env:
        - name: DORY_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: DORY_POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
        lifecycle:
          preStop:
            httpGet:
              path: /prestop
              port: 8080
```

---

## Features

### `@stateful` Decorator

Mark variables for automatic state management:

```python
from dory import BaseProcessor, stateful

class MyApp(BaseProcessor):
    # Simple values
    counter = stateful(0)
    name = stateful("default")

    # Mutable defaults (use factory)
    data = stateful(dict)    # Creates new dict for each instance
    items = stateful(list)   # Creates new list for each instance

    async def run(self):
        # Just use them normally - SDK handles save/restore
        self.counter += 1
        self.data["key"] = "value"
```

### `run_loop()` Helper

Simplifies the shutdown check pattern:

```python
# Instead of:
async def run(self):
    while not self.context.is_shutdown_requested():
        self.counter += 1
        await asyncio.sleep(1)

# Use:
async def run(self):
    async for i in self.run_loop(interval=1):
        self.counter += 1
        print(f"Iteration {i}")
```

### Function-Based API

For simple apps that don't need a class:

```python
from dory.simple import processor, state

counter = state(0)
sessions = state(dict)

@processor
async def main(ctx):
    logger = ctx.logger()

    async for i in ctx.run_loop(interval=1):
        counter.value += 1
        logger.info(f"Count: {counter.value}")
```

### ExecutionContext

Access pod metadata and utilities:

```python
async def run(self):
    ctx = self.context

    # Logging with pod context
    ctx.logger().info("Processing...")

    # Pod metadata
    print(f"Pod: {ctx.pod_name}")
    print(f"Namespace: {ctx.pod_namespace}")
    print(f"Processor ID: {ctx.processor_id}")
    print(f"Restart count: {ctx.attempt_number}")

    # App config (env vars except DORY_*)
    config = ctx.config()
    model_path = config.get("MODEL_PATH")

    # Shutdown detection
    while not ctx.is_shutdown_requested():
        if ctx.is_migration_imminent():
            print("Migration coming, finishing batch...")
        await process()
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DORY_HEALTH_PORT` | 8080 | Health server port |
| `DORY_LOG_LEVEL` | INFO | Log level |
| `DORY_LOG_FORMAT` | json | Log format (json/text) |
| `DORY_STATE_BACKEND` | configmap | State storage backend |
| `DORY_STARTUP_TIMEOUT_SEC` | 30 | Startup timeout |
| `DORY_SHUTDOWN_TIMEOUT_SEC` | 30 | Shutdown timeout |

### Config File (dory.yaml)

```yaml
health_port: 8080
log_level: INFO
log_format: json
state_backend: configmap
startup_timeout_sec: 30
shutdown_timeout_sec: 30
```

### Local Development

Test locally without Kubernetes:

```bash
DORY_STATE_BACKEND=local python main.py
```

---

## HTTP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /healthz` | Liveness probe (200=alive) |
| `GET /ready` | Readiness probe (200=ready) |
| `GET /metrics` | Prometheus metrics |
| `GET /state` | Get processor state |
| `POST /state` | Restore processor state |
| `GET /prestop` | PreStop hook handler |

---

## API Reference

### BaseProcessor Methods

| Method | Required | Description |
|--------|----------|-------------|
| `run()` | **Yes** | Main processing loop |
| `startup()` | No | Initialize resources (default: no-op) |
| `shutdown()` | No | Cleanup resources (default: no-op) |
| `get_state()` | No | Return state dict (default: `@stateful` vars) |
| `restore_state(state)` | No | Restore state (default: `@stateful` vars) |

### Helper Methods

| Method | Description |
|--------|-------------|
| `run_loop(interval)` | Async iterator with auto shutdown check |
| `is_shutting_down()` | Check if shutdown requested |

### Fault Handling Hooks (Optional)

| Method | Description |
|--------|-------------|
| `on_state_restore_failed(error)` | Handle restore errors |
| `on_rapid_restart_detected(count)` | Handle restart loops |
| `on_health_check_failed(error)` | Handle health failures |
| `reset_caches()` | Clear caches on golden reset |

---

## How State Migration Works

### Pod Shutdown
```
1. Kubernetes calls /prestop
2. SDK saves state to ConfigMap
3. Pod marked not-ready
4. Your run() exits
5. Your shutdown() called
6. Pod terminates
```

### New Pod Startup
```
1. SDK finds state in ConfigMap
2. Your startup() called
3. Your restore_state() called
4. Pod marked ready
5. Your run() starts
```

---

## Comparison: Before vs After

### Before (25+ lines)

```python
import asyncio
from dory import DoryApp, BaseProcessor, ExecutionContext

class MyApp(BaseProcessor):
    def __init__(self, context: ExecutionContext):
        super().__init__(context)
        self.counter = 0
        self.sessions = {}

    async def startup(self) -> None:
        pass

    async def run(self) -> None:
        while not self.context.is_shutdown_requested():
            self.counter += 1
            await asyncio.sleep(1)

    async def shutdown(self) -> None:
        pass

    def get_state(self) -> dict:
        return {"counter": self.counter, "sessions": self.sessions}

    async def restore_state(self, state: dict) -> None:
        self.counter = state.get("counter", 0)
        self.sessions = state.get("sessions", {})

if __name__ == "__main__":
    DoryApp().run(MyApp)
```

### After (7 lines)

```python
from dory import DoryApp, BaseProcessor, stateful

class MyApp(BaseProcessor):
    counter = stateful(0)
    sessions = stateful(dict)

    async def run(self):
        async for _ in self.run_loop(interval=1):
            self.counter += 1

if __name__ == "__main__":
    DoryApp().run(MyApp)
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Quick Reference](docs/QUICK_REFERENCE.md) | 15-minute quick start |
| [Configuration Guide](docs/CONFIGURATION_GUIDE.md) | Configuration and presets |
| [Stateful Guide](docs/STATEFUL_GUIDE.md) | Stateful processing patterns |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Advanced topics |

## Examples

| Example | Description | Pattern |
|---------|-------------|---------|
| [`minimal-processor-py`](../examples/minimal-processor-py/) | Simplest possible processor (~95 lines) | `@stateful` + `run_loop()` |
| [`dory-info-logger-py`](../examples/dory-info-logger-py/) | Full demo with HTTP dashboard | `@stateful` + fault hooks |
| [`dory-edge-logger-py`](../examples/dory-edge-logger-py/) | Edge workload with DB logging | Manual state management |

**Start here**: Use `minimal-processor-py` as a template for new processors.

## License

Apache 2.0
