"""
Dory SDK CLI - Command line tools for Dory SDK.

Provides commands for:
- Generating Kubernetes manifests (RBAC, Deployment, etc.)
- Initializing new Dory projects
- Validating configuration

Usage:
    dory init my-app --image my-app:latest
    dory generate k8s --name my-app --image my-app:latest
    dory validate
"""

import argparse
import os
import sys
from pathlib import Path

from dory.cli.templates import (
    generate_rbac,
    generate_deployment,
    generate_pod,
    generate_all,
    generate_dockerfile,
    generate_processor_template,
)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new Dory project."""
    name = args.name
    output_dir = Path(args.output or ".")

    print(f"Initializing Dory project: {name}")

    # Create directories
    k8s_dir = output_dir / "k8s"
    k8s_dir.mkdir(parents=True, exist_ok=True)

    # Generate files
    files = {
        "main.py": generate_processor_template(name),
        "Dockerfile": generate_dockerfile(name),
        "k8s/rbac.yaml": generate_rbac(name, args.namespace),
        "k8s/deployment.yaml": generate_deployment(
            name=name,
            image=args.image or f"{name}:latest",
            namespace=args.namespace,
            replicas=args.replicas,
            health_port=args.health_port,
            app_port=args.app_port,
        ),
    }

    for filename, content in files.items():
        filepath = output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filepath.exists() and not args.force:
            print(f"  Skipping {filename} (already exists, use --force to overwrite)")
            continue

        filepath.write_text(content)
        print(f"  Created {filename}")

    print()
    print("Next steps:")
    print(f"  1. Edit main.py with your processor logic")
    print(f"  2. Build: docker build -t {name}:latest .")
    print(f"  3. Deploy: kubectl apply -f k8s/")
    print()

    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate Kubernetes manifests."""
    output_dir = Path(args.output or "k8s")
    output_dir.mkdir(parents=True, exist_ok=True)

    name = args.name
    image = args.image or f"{name}:latest"
    namespace = args.namespace

    if args.type == "rbac":
        content = generate_rbac(name, namespace)
        filename = "rbac.yaml"
    elif args.type == "deployment":
        content = generate_deployment(
            name=name,
            image=image,
            namespace=namespace,
            replicas=args.replicas,
            health_port=args.health_port,
            app_port=args.app_port,
        )
        filename = "deployment.yaml"
    elif args.type == "pod":
        content = generate_pod(
            name=name,
            image=image,
            namespace=namespace,
            health_port=args.health_port,
            app_port=args.app_port,
        )
        filename = "pod.yaml"
    elif args.type == "all":
        content = generate_all(
            name=name,
            image=image,
            namespace=namespace,
            replicas=args.replicas,
            health_port=args.health_port,
            app_port=args.app_port,
        )
        filename = "all.yaml"
    else:
        print(f"Unknown type: {args.type}")
        return 1

    filepath = output_dir / filename

    if filepath.exists() and not args.force:
        print(f"File {filepath} already exists. Use --force to overwrite.")
        return 1

    filepath.write_text(content)
    print(f"Generated: {filepath}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate Dory configuration."""
    from dory.config.loader import ConfigLoader

    config_file = args.config

    try:
        loader = ConfigLoader(config_file=config_file)
        config = loader.load()
        print("Configuration is valid!")
        print()
        print("Current settings:")
        for key, value in config.model_dump().items():
            print(f"  {key}: {value}")
        return 0
    except Exception as e:
        print(f"Configuration error: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="dory",
        description="Dory SDK CLI - Tools for building stateful Kubernetes processors",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new Dory project",
    )
    init_parser.add_argument(
        "name",
        help="Project/app name",
    )
    init_parser.add_argument(
        "-o", "--output",
        help="Output directory (default: current directory)",
    )
    init_parser.add_argument(
        "-i", "--image",
        help="Docker image name (default: <name>:latest)",
    )
    init_parser.add_argument(
        "-n", "--namespace",
        default="default",
        help="Kubernetes namespace (default: default)",
    )
    init_parser.add_argument(
        "--replicas",
        type=int,
        default=1,
        help="Number of replicas (default: 1)",
    )
    init_parser.add_argument(
        "--health-port",
        type=int,
        default=8080,
        help="Health server port (default: 8080)",
    )
    init_parser.add_argument(
        "--app-port",
        type=int,
        default=8081,
        help="Application port (default: 8081)",
    )
    init_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    init_parser.set_defaults(func=cmd_init)

    # generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate Kubernetes manifests",
    )
    gen_parser.add_argument(
        "type",
        choices=["rbac", "deployment", "pod", "all"],
        help="Type of manifest to generate",
    )
    gen_parser.add_argument(
        "-n", "--name",
        required=True,
        help="Application name",
    )
    gen_parser.add_argument(
        "-i", "--image",
        help="Docker image (default: <name>:latest)",
    )
    gen_parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace (default: default)",
    )
    gen_parser.add_argument(
        "--replicas",
        type=int,
        default=1,
        help="Number of replicas (default: 1)",
    )
    gen_parser.add_argument(
        "--health-port",
        type=int,
        default=8080,
        help="Health server port (default: 8080)",
    )
    gen_parser.add_argument(
        "--app-port",
        type=int,
        default=8081,
        help="Application port (default: 8081)",
    )
    gen_parser.add_argument(
        "-o", "--output",
        default="k8s",
        help="Output directory (default: k8s)",
    )
    gen_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate Dory configuration",
    )
    validate_parser.add_argument(
        "-c", "--config",
        help="Path to config file (default: dory.yaml)",
    )
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
