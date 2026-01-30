# Kubepath

**Master Kubernetes in Your Terminal**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-600%2B%20passing-brightgreen.svg)]()

---

## What is Kubepath?

Kubepath is an **interactive command-line application** that teaches you Kubernetes right in your terminal. Instead of passively reading documentation or watching videos, you learn by doing — running real `kubectl` commands, debugging actual broken deployments, and building muscle memory through hands-on practice.

Whether you're a developer wanting to understand Kubernetes, a DevOps engineer looking to sharpen your skills, or someone preparing for the **CKAD (Certified Kubernetes Application Developer)** exam, Kubepath provides a structured, gamified learning experience that makes mastering Kubernetes fun and effective.

---

## Why Kubepath?

- **Learn by Doing**: Every concept is followed by hands-on practice on a real Kubernetes cluster
- **Real Debugging**: Fix actual broken deployments, not toy examples
- **Instant Feedback**: Know immediately if your commands are correct
- **AI-Powered Help**: Stuck? Get intelligent hints from Google Gemini
- **Gamified Progress**: Level up, maintain streaks, and track your journey
- **CKAD-Aligned**: Content structured around official exam domains

---

## Features

### 38 Chapters Across 6 CKAD Modules

| Module | Topics |
|--------|--------|
| **Core Concepts** | Pods, Deployments, ReplicaSets, Services |
| **Configuration** | ConfigMaps, Secrets, Environment Variables |
| **Multi-Container Pods** | Sidecar, Ambassador, Adapter patterns |
| **Observability** | Logging, Liveness & Readiness Probes, Monitoring |
| **Pod Design** | Jobs, CronJobs, Labels, Selectors, Annotations |
| **Services & Networking** | ClusterIP, NodePort, LoadBalancer, Ingress, NetworkPolicies |

### 4-Section Learning Flow

Each chapter follows a proven learning structure:

```
Concepts     ->    Learn the theory with clear explanations     [No cluster needed]
Practice     ->    Run basic kubectl commands                   [Needs cluster]
Scenarios    ->    Debug real broken deployments                [Needs cluster]
Quiz         ->    Test your knowledge                          [No cluster needed]
```

**Start without a cluster!** You can learn concepts and take quizzes immediately. Set up the hands-on environment when you're ready for practice.

### Gamification

- **12 Levels**: Progress from "Pod Seedling" to "Kubernetes Kurator"
- **Daily Streaks**: Build consistency with streak tracking
- **Score Tracking**: Earn points for correct answers, lose points for hints
- **Social Sharing**: Share your achievements on X, LinkedIn, and Instagram

### AI-Powered Hints

Stuck on a debugging scenario? Get intelligent, contextual hints powered by Google Gemini that guide you to the solution without giving away the answer.

### Auto-Updates

Kubepath automatically checks for updates when you launch it and keeps itself current via Git.

---

## Quick Start

### Prerequisites

You can start learning Kubernetes concepts **immediately** without setting up a full Kubernetes environment! The concepts, quizzes, and theory sections work without any cluster. Set up the hands-on tools later when you're ready.

#### Minimum Required (to start learning)

| Tool | Why You Need It |
|------|-----------------|
| **Python 3.12+** | Kubepath runs on Python |
| **git** | To clone and receive auto-updates |

**Check Python:**
```bash
python3 --version
```

**Install Python if needed:**
- **macOS**: `brew install python@3.12`
- **Ubuntu/Debian**: `sudo apt install python3.12`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

That's it! You can install Kubepath now and start learning concepts right away.

---

#### For Hands-On Practice (recommended, but optional to start)

To run actual `kubectl` commands and debug real deployments, you'll need a local Kubernetes cluster. Don't worry — you can set these up later when you reach the practice sections!

| Tool | What It Does |
|------|--------------|
| **Docker Desktop** | Runs containers on your computer |
| **kubectl** | The Kubernetes command-line tool (what you'll be learning!) |
| **minikube** | Creates a local Kubernetes cluster on your laptop |

<details>
<summary><strong>Click to expand setup instructions</strong></summary>

##### Docker Desktop

Docker lets you run containers — it's how Kubernetes works under the hood.

**Download**: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)

After installing, make sure Docker is running (you'll see the whale icon in your menu bar/system tray).

##### kubectl

`kubectl` is the command-line tool for talking to Kubernetes.

**Install:**
- **macOS**: `brew install kubectl`
- **Ubuntu/Debian**: See [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/)
- **Windows**: `choco install kubernetes-cli` or download from the link above

**Verify:**
```bash
kubectl version --client
```

##### minikube

Minikube creates a local Kubernetes cluster on your laptop — your personal practice environment.

**Install:**
- **macOS**: `brew install minikube`
- **Ubuntu/Debian**: See [minikube.sigs.k8s.io/docs/start](https://minikube.sigs.k8s.io/docs/start/)
- **Windows**: `choco install minikube`

**Start your cluster:**
```bash
minikube start
```

This may take a few minutes the first time as it downloads the Kubernetes components.

</details>

---

### Installation

Once you have the prerequisites, installing Kubepath is simple:

```bash
# Clone the repository
git clone https://github.com/nithin-nk/kubepath.git

# Navigate to the folder
cd kubepath

# Install uv (Python package manager) if you don't have it
pip install uv
# or on macOS: brew install uv

# Install dependencies and the kubepath package
uv sync
uv pip install -e .

# Start learning!
uv run kubepath
```

That's it! You should see the Kubepath main menu.

**Troubleshooting:** If you see `ModuleNotFoundError: No module named 'kubepath'`, run:
```bash
uv pip install -e .
```

---

## Commands

```bash
# Start the interactive learning experience
uv run kubepath

# List all available chapters
uv run kubepath list

# Jump to a specific chapter
uv run kubepath start 5

# Reset progress for a chapter
uv run kubepath start 3 --reset

# Get help
uv run kubepath --help
```

---

## Learning Path

Here's what your journey looks like:

```
Chapter 1-7:   Core Concepts      ========----------------  18%
               Pods, Deployments, Services, ReplicaSets

Chapter 8-14:  Configuration      ============------------  37%
               ConfigMaps, Secrets, Resource Limits

Chapter 15-19: Multi-Container    ================--------  50%
               Sidecar, Init Containers, Ambassador

Chapter 20-26: Observability      ====================----  68%
               Probes, Logging, Debugging

Chapter 27-32: Pod Design         ========================  84%
               Jobs, CronJobs, Labels, Annotations

Chapter 33-38: Networking         ========================= 100%
               Ingress, NetworkPolicies, DNS
```

---

## Gamification

### Level Progression

| Level | Title | Points Required |
|-------|-------|-----------------|
| 1 | Pod Seedling | 0 |
| 2 | Container Cadet | 100 |
| 3 | Namespace Navigator | 300 |
| 4 | Deployment Apprentice | 600 |
| 5 | Service Scout | 1,000 |
| 6 | ConfigMap Crafter | 1,500 |
| 7 | Secret Keeper | 2,100 |
| 8 | Volume Voyager | 2,800 |
| 9 | Cluster Captain | 3,600 |
| 10 | Helm Hero | 4,500 |
| 11 | CKAD Champion | 5,500 |
| 12 | Kubernetes Kurator | 6,600 |

### Streak Tracking

Practice daily to build your streak! Kubepath tracks your consecutive days of learning and celebrates milestones at 3, 7, 14, 30, and 100 days.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google Gemini API key for AI-powered hints (optional but recommended) |
| `KUBEPATH_NO_UPDATE=1` | Disable automatic update checks |

To get a Gemini API key (free tier available):
1. Go to [ai.google.dev](https://ai.google.dev/)
2. Click "Get API Key"
3. Create a new API key
4. Set it: `export GEMINI_API_KEY="your-key-here"`

---

## Screenshots

### Main Menu
```
+-----------------------------------------------------+
|               Welcome to Kubepath!                  |
|         Master Kubernetes in Your Terminal          |
|-----------------------------------------------------|
|  Level 5: Service Scout            7-day streak     |
|  Score: 1,250 pts                                   |
|  [========--------] 250/500 to Level 6              |
+-----------------------------------------------------+
```

### Level Up Celebration
```
+=======================================================+
|                                                       |
|           *** LEVEL UP! ***                           |
|                                                       |
|      You are now a Service Scout!                     |
|                 Level 5                               |
|                                                       |
+=======================================================+
```

---

## Contributing

We welcome contributions! Whether it's:
- Fixing bugs
- Adding new chapters
- Improving documentation
- Suggesting features

Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

---

## Maintainer

**Nithin K Anil**

- Website: [nithinanil.com](https://nithinanil.com/)
- Email: nithin08anil `[at]` gmail `[dot]` com

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- The Kubernetes community for incredible documentation
- Google Gemini for AI-powered assistance
- All contributors who help make Kubepath better

---

**Ready to master Kubernetes?** Start your journey today:

```bash
git clone https://github.com/nithin-nk/kubepath.git && cd kubepath && uv sync && uv pip install -e . && uv run kubepath
```

Happy learning!
