"""OS-specific Kubernetes setup instructions - minikube only."""

from kubepath.console import get_console
from kubepath.k8s.detector import OSInfo


# Setup instructions - minikube only, organized by OS
SETUP_INSTRUCTIONS = {
    "macos": {
        "minikube": {
            "name": "Minikube",
            "description": "The required Kubernetes provider for kubepath",
            "prerequisites": [
                "# Install Docker Desktop first (provides the Docker driver):",
                "brew install --cask docker",
                "# Then open Docker Desktop and wait for it to start",
            ],
            "install": [
                "brew install minikube",
                "minikube start",
            ],
            "docs": "https://minikube.sigs.k8s.io/docs/start/",
        },
    },
    "linux": {
        "minikube": {
            "name": "Minikube",
            "description": "The required Kubernetes provider for kubepath",
            "prerequisites": [
                "# Install Docker (if not already installed):",
                "curl -fsSL https://get.docker.com | sh",
                "sudo usermod -aG docker $USER",
                "# Log out and log back in, then start Docker:",
                "sudo systemctl start docker",
            ],
            "install": [
                "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64",
                "sudo install minikube-linux-amd64 /usr/local/bin/minikube",
                "minikube start",
            ],
            "docs": "https://minikube.sigs.k8s.io/docs/start/",
        },
    },
    "windows": {
        "minikube": {
            "name": "Minikube",
            "description": "The required Kubernetes provider for kubepath",
            "prerequisites": [
                "# Install Docker Desktop and start it before continuing",
            ],
            "install": [
                "winget install minikube",
                "minikube start",
            ],
            "docs": "https://minikube.sigs.k8s.io/docs/start/",
        },
    },
    "wsl": {
        "minikube": {
            "name": "Minikube in WSL",
            "description": "The required Kubernetes provider for kubepath",
            "prerequisites": [
                "# Option 1: Use Docker Desktop with WSL integration (start Docker Desktop first)",
                "# Option 2: Install Docker in WSL:",
                "curl -fsSL https://get.docker.com | sh",
                "sudo usermod -aG docker $USER",
                "# Then start Docker: sudo service docker start",
            ],
            "install": [
                "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64",
                "sudo install minikube-linux-amd64 /usr/local/bin/minikube",
                "minikube start --driver=docker",
            ],
            "docs": "https://minikube.sigs.k8s.io/docs/start/",
        },
    },
}

KUBECTL_INSTALL = {
    "macos": {
        "install": [
            "brew install kubectl",
            "# Or download directly:",
            "curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/arm64/kubectl'",
            "chmod +x kubectl && sudo mv kubectl /usr/local/bin/",
        ],
        "docs": "https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/",
    },
    "linux": {
        "install": [
            "curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl'",
            "chmod +x kubectl",
            "sudo mv kubectl /usr/local/bin/",
        ],
        "docs": "https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/",
    },
    "windows": {
        "install": [
            "# Using winget:",
            "winget install -e --id Kubernetes.kubectl",
            "# Or download from:",
            "# https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe",
        ],
        "docs": "https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/",
    },
}


def show_setup_guide(os_info: OSInfo) -> None:
    """Display minikube setup instructions for the detected OS.

    Args:
        os_info: The detected operating system information.
    """
    console = get_console()

    console.print("\n[warning]Kubernetes cluster not detected[/warning]\n")
    console.print("[info]kubepath requires minikube.[/info]\n")

    # Determine which instructions to show
    if os_info.is_wsl:
        os_key = "wsl"
        os_display = "WSL"
    else:
        os_key = os_info.name
        os_display = os_info.name.capitalize()

    instructions = SETUP_INSTRUCTIONS.get(os_key, {}).get("minikube")

    if not instructions:
        console.print(f"[hint]Visit https://minikube.sigs.k8s.io/docs/start/[/hint]")
        return

    console.print(f"[chapter]Minikube Setup for {os_display}[/chapter]\n")
    console.print("[hint]Run these commands in a NEW terminal window:[/hint]\n")

    # Show prerequisites if any
    if "prerequisites" in instructions:
        console.print("[info]Prerequisites:[/info]")
        for cmd in instructions["prerequisites"]:
            if cmd.startswith("#"):
                console.print(f"  [hint]{cmd}[/hint]")
            else:
                console.print(f"  [success]$ {cmd}[/success]")
        console.print()

    # Show install commands
    console.print("[info]Install minikube:[/info]")
    for cmd in instructions.get("install", []):
        if cmd.startswith("#"):
            console.print(f"  [hint]{cmd}[/hint]")
        else:
            console.print(f"  [success]$ {cmd}[/success]")

    if "docs" in instructions:
        console.print(f"\n[hint]Docs: {instructions['docs']}[/hint]")
    console.print()
    console.print("[info]After installation completes, come back here and press Enter to retry.[/info]")


def show_minikube_required_warning(current_provider: str) -> None:
    """Display warning that kubepath requires minikube.

    Args:
        current_provider: The currently detected provider name.
    """
    console = get_console()

    console.print()
    console.print("[warning]Non-minikube cluster detected[/warning]")
    console.print(f"[hint]Current provider: {current_provider}[/hint]")
    console.print()
    console.print("[info]kubepath is designed for minikube.[/info]")
    console.print("[hint]Some features may not work with other providers.[/hint]")
    console.print()
    console.print("[hint]To switch to minikube:[/hint]")
    console.print("  [success]$ minikube start[/success]")
    console.print("  [success]$ kubectl config use-context minikube[/success]")


def show_kubectl_install(os_info: OSInfo) -> None:
    """Display kubectl installation instructions for the detected OS.

    Args:
        os_info: The detected operating system information.
    """
    console = get_console()

    console.print("\n[warning]kubectl not found[/warning]\n")

    # WSL can use Linux instructions
    os_key = "linux" if os_info.is_wsl else os_info.name

    info = KUBECTL_INSTALL.get(os_key, {})

    if not info:
        console.print("[hint]Visit https://kubernetes.io/docs/tasks/tools/ to install kubectl.[/hint]")
        return

    console.print("[info]Install kubectl:[/info]\n")

    for cmd in info.get("install", []):
        if cmd.startswith("#"):
            console.print(f"  [hint]{cmd}[/hint]")
        else:
            console.print(f"  [info]$ {cmd}[/info]")

    if "docs" in info:
        console.print(f"\n[hint]Docs: {info['docs']}[/hint]")

    # Important: remind users to restart terminal after installing
    console.print()
    console.print("[warning]After installing kubectl, close this terminal and open a new one.[/warning]")
    console.print("[hint]This ensures your PATH is updated to find the kubectl command.[/hint]")
