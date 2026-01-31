"""
Templates for generating Kubernetes manifests and project files.
"""


def generate_rbac(name: str, namespace: str = "default") -> str:
    """Generate RBAC manifest (ServiceAccount, Role, RoleBinding)."""
    return f'''# RBAC for Dory processor: {name}
# Allows the processor to manage ConfigMaps for state persistence

apiVersion: v1
kind: ServiceAccount
metadata:
  name: {name}
  namespace: {namespace}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {name}-state-manager
  namespace: {namespace}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {name}-state-manager
  namespace: {namespace}
subjects:
- kind: ServiceAccount
  name: {name}
  namespace: {namespace}
roleRef:
  kind: Role
  name: {name}-state-manager
  apiGroup: rbac.authorization.k8s.io
'''


def generate_deployment(
    name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    health_port: int = 8080,
    app_port: int = 8081,
) -> str:
    """Generate Deployment manifest with probes and PreStop hook."""
    return f'''# Deployment for Dory processor: {name}

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      serviceAccountName: {name}
      terminationGracePeriodSeconds: 35

      containers:
      - name: {name}
        image: {image}
        ports:
        - name: health
          containerPort: {health_port}
        - name: app
          containerPort: {app_port}

        env:
        # Pod metadata (required by Dory SDK)
        - name: DORY_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: DORY_POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName

        # Liveness probe - is the process alive?
        livenessProbe:
          httpGet:
            path: /healthz
            port: {health_port}
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        # Readiness probe - ready for traffic?
        readinessProbe:
          httpGet:
            path: /ready
            port: {health_port}
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        # PreStop hook - save state before shutdown
        lifecycle:
          preStop:
            httpGet:
              path: /prestop
              port: {health_port}

        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
'''


def generate_pod(
    name: str,
    image: str,
    namespace: str = "default",
    health_port: int = 8080,
    app_port: int = 8081,
) -> str:
    """Generate standalone Pod manifest (for testing)."""
    return f'''# Pod for Dory processor: {name}
# Use this for testing. For production, use Deployment.

apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  serviceAccountName: {name}
  terminationGracePeriodSeconds: 35

  containers:
  - name: {name}
    image: {image}
    ports:
    - name: health
      containerPort: {health_port}
    - name: app
      containerPort: {app_port}

    env:
    - name: DORY_POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: DORY_POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName

    livenessProbe:
      httpGet:
        path: /healthz
        port: {health_port}
      initialDelaySeconds: 10
      periodSeconds: 10

    readinessProbe:
      httpGet:
        path: /ready
        port: {health_port}
      initialDelaySeconds: 5
      periodSeconds: 5

    lifecycle:
      preStop:
        httpGet:
          path: /prestop
          port: {health_port}
'''


def generate_all(
    name: str,
    image: str,
    namespace: str = "default",
    replicas: int = 1,
    health_port: int = 8080,
    app_port: int = 8081,
) -> str:
    """Generate all manifests in a single file."""
    rbac = generate_rbac(name, namespace)
    deployment = generate_deployment(name, image, namespace, replicas, health_port, app_port)
    return f"{rbac}---\n{deployment}"


def generate_dockerfile(name: str) -> str:
    """Generate Dockerfile for a Dory processor."""
    return f'''# Dockerfile for Dory processor: {name}

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Dory SDK with Kubernetes support
RUN pip install --no-cache-dir dory-sdk[kubernetes]

# Copy application
COPY main.py .

# Expose ports (8080 for health, 8081 for app)
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the application
CMD ["python", "main.py"]
'''


def generate_processor_template(name: str) -> str:
    """Generate a template processor Python file."""
    class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    return f'''"""
{name} - A Dory-powered stateful processor.

Features:
- Zero-downtime migration
- Automatic state persistence
- Graceful shutdown
- Health monitoring

Generated by: dory init {name}
"""

import asyncio
from dory import DoryApp, BaseProcessor, stateful


class {class_name}(BaseProcessor):
    """
    Your processor implementation.

    The @stateful decorator automatically handles state save/restore.
    Just implement the run() method with your business logic.
    """

    # Stateful variables (automatically saved and restored)
    counter = stateful(0)
    data = stateful(dict)

    async def startup(self) -> None:
        """Initialize resources (optional)."""
        self.context.logger().info("Starting up...")
        # Load models, open connections, etc.

    async def run(self) -> None:
        """Main processing loop."""
        logger = self.context.logger()

        # Use run_loop() for automatic shutdown detection
        async for i in self.run_loop(interval=1):
            self.counter += 1
            logger.info(f"Iteration {{i}}: counter={{self.counter}}")

            # Your business logic here
            # ...

    async def shutdown(self) -> None:
        """Cleanup resources (optional)."""
        self.context.logger().info(f"Shutting down. Final counter: {{self.counter}}")
        # Close connections, flush buffers, etc.


if __name__ == "__main__":
    DoryApp().run({class_name})
'''


def generate_simple_processor_template(name: str) -> str:
    """Generate a minimal processor using function-based API."""
    return f'''"""
{name} - A minimal Dory processor using function-based API.

Generated by: dory init {name} --simple
"""

from dory.simple import processor, state

# State variables (automatically saved and restored)
counter = state(0)
data = state(dict)


@processor
async def main(ctx):
    """Main processing loop."""
    logger = ctx.logger()

    async for i in ctx.run_loop(interval=1):
        counter.value += 1
        logger.info(f"Iteration {{i}}: counter={{counter.value}}")

        # Your business logic here
        # ...
'''
