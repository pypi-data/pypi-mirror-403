# kubepath Content Schema

This document describes the YAML schema for chapter content files.

## File Location

Chapter files are stored in `content/chapters/` with the naming convention:
```
{chapter_number:02d}-{chapter-slug}.yaml
```

Example: `01-kubernetes-basics.yaml`

---

## Schema Overview

Each chapter YAML file contains four main sections:

| Section | Required | Description |
|---------|----------|-------------|
| `chapter` | Yes | Chapter metadata (number, title, description) |
| `concepts` | Yes | Theory content with markdown and key points |
| `command_practice` | No | Hands-on kubectl exercises with validation |
| `scenarios` | No | Debugging challenges with broken manifests |
| `quiz` | No | Assessment questions (multiple choice, command challenges) |

---

## Chapter Metadata (Required)

```yaml
chapter:
  number: 1                           # Chapter number (positive integer)
  title: "Kubernetes Basics"          # Display title (non-empty string)
  description: "Introduction to K8s"  # Short description (optional)
```

---

## Concepts Section (Required)

Each concept should follow the Feynman teaching method:
- Simple, clear explanations
- Real-life analogies
- ASCII diagrams for visual concepts
- Key takeaways

```yaml
concepts:
  - title: "Concept Title"            # Required: concept title
    content: |                        # Required: markdown content
      **Simple explanation first** - what is this and why does it matter?

      **Real-life analogy:**
      Think of a Pod like a house. Just like roommates share a kitchen
      and bathroom, containers in a Pod share network and storage.

      **Visual diagram:**
      ```
      ┌─────────────────────────┐
      │         POD             │
      │  ┌─────┐    ┌─────┐    │
      │  │ App │    │ Log │    │
      │  └─────┘    └─────┘    │
      │    Shared Network       │
      └─────────────────────────┘
      ```

      **Key insight:** Pods are ephemeral - they can be replaced at any time.
    key_points:                       # Optional: summary points
      - "Pods are the smallest deployable unit"
      - "Containers in a Pod share network and storage"
      - "Pods are ephemeral and can be replaced"
```

---

## Command Practice Section (Optional)

Hands-on exercises where learners run kubectl commands. Each practice includes:
- Clear instructions with "why this matters"
- Command hints with memory tricks
- Validation to check success
- Points awarded on completion

```yaml
command_practice:
  - id: "cmd-01"                      # Unique identifier within chapter
    title: "Check Cluster Info"       # Display title
    instructions: |                   # Markdown instructions
      **What we're doing:** Verify your Kubernetes cluster is running.

      **Why this matters:** Before deploying apps, you need to confirm
      the cluster is healthy and accessible.

      **Memory trick:** `cluster-info` = "tell me about the cluster"

      Run this command:
    command_hint: "kubectl cluster-info"
    why_this_command: |               # Optional: explain the command
      - `kubectl` = the CLI tool for Kubernetes
      - `cluster-info` = show cluster endpoint information
      - Together: "Show me where the cluster is running"
    common_mistakes:                  # Optional: common errors
      - "Typo: 'cluser-info' instead of 'cluster-info'"
      - "Not having kubectl configured correctly"
    validation:
      type: "command_output"          # Validation type
      command: "kubectl cluster-info" # Command to run for validation
      expected_contains: "Kubernetes" # Text that must appear in output
      expected_not_contains: "error"  # Optional: text that must NOT appear
      timeout: 30                     # Optional: timeout in seconds (default 30)
    points: 10                        # Points awarded on success
```

### Validation Types

| Type | Description |
|------|-------------|
| `command_output` | Run command, check stdout contains expected text |
| `resource_exists` | Check if a K8s resource exists |
| `resource_state` | Check resource status (Running, Ready, etc.) |
| `resource_state_stable` | Check state is stable for N seconds |

---

## Scenarios Section (Optional)

Debugging challenges where learners fix broken Kubernetes deployments.
Each scenario deploys a broken manifest and guides the learner to diagnose and fix it.

```yaml
scenarios:
  - id: "scenario-01"                 # Unique identifier within chapter
    title: "Fix the ImagePullBackOff" # Display title
    description: |                    # Problem description
      A developer reported their pod won't start.
      Your mission: diagnose the issue and fix it!
    manifest: |                       # Broken YAML to deploy
      apiVersion: v1
      kind: Pod
      metadata:
        name: broken-app
        namespace: default
      spec:
        containers:
        - name: app
          image: ngnix:latest         # Typo: should be 'nginx'
    hints:                            # Progressive hints (2-3 recommended)
      - "Check the pod status with `kubectl describe pod broken-app`"
      - "Look at the Events section - what error message do you see?"
      - "The image name looks suspicious... is 'ngnix' spelled correctly?"
    solution_validation:
      type: "resource_state"          # Validation type
      resource: "pod/broken-app"      # Resource to check
      namespace: "default"            # Optional: namespace (default: default)
      state: "Running"                # Expected state
      timeout: 60                     # Optional: timeout in seconds
    points: 25                        # Points awarded on success
    hint_penalty: 5                   # Optional: points deducted per hint used
```

### Common Scenario Types

| Scenario | Broken State | Fix |
|----------|--------------|-----|
| ImagePullBackOff | Wrong image name | Fix the image name typo |
| CrashLoopBackOff | Bad command/args | Fix the container command |
| Pending | Resource limits too high | Reduce requests/limits |
| CreateContainerError | Missing ConfigMap/Secret | Create the missing resource |
| Service no endpoints | Selector mismatch | Fix label selectors |

---

## Quiz Section (Optional)

Assessment questions to test understanding. Supports multiple question types.

```yaml
quiz:
  passing_score: 70                   # Optional: percentage to pass (default 70)
  questions:
    - type: "multiple_choice"         # Question type
      question: "What is a Pod?"      # The question text
      options:                        # Answer choices (2-4 options)
        - "A single container running alone"
        - "The smallest deployable unit in Kubernetes"
        - "Another name for a node"
        - "A namespace for grouping resources"
      correct: 1                      # Index of correct answer (0-based)
      explanation: |                  # Shown after answering
        A Pod is the smallest deployable unit. Like roommates in a house,
        containers in a Pod share network and storage resources.
      points: 5                       # Points for correct answer

    - type: "command_challenge"       # Type: write a kubectl command
      question: "Write the command to list all pods in the 'production' namespace"
      expected_contains: "kubectl get pods -n production"
      alternatives:                   # Optional: other acceptable answers
        - "kubectl get po -n production"
        - "kubectl get pods --namespace production"
      hint: "Remember: -n flag specifies namespace"
      explanation: "The -n flag is shorthand for --namespace"
      points: 10

    - type: "fill_yaml"               # Type: complete YAML snippet
      question: "Complete this Pod spec to set memory limit to 256Mi"
      yaml_template: |
        resources:
          limits:
            memory: ____
      expected: "256Mi"
      explanation: "Memory is specified with Mi (mebibytes) or Gi (gibibytes)"
      points: 10

    - type: "true_false"              # Type: true/false question
      question: "Pods can be scheduled on any node in the cluster by default"
      correct: true
      explanation: "By default, the scheduler can place pods on any node unless constrained by taints, tolerations, or node selectors."
      points: 5
```

### Question Types

| Type | Description |
|------|-------------|
| `multiple_choice` | Select one correct answer from options |
| `command_challenge` | Write a kubectl command |
| `fill_yaml` | Complete a YAML snippet |
| `true_false` | True or false question |

---

## Complete Example

```yaml
chapter:
  number: 4
  title: "Understanding Pods"
  description: "Learn about Kubernetes pods - the smallest deployable unit"

concepts:
  - title: "What is a Pod?"
    content: |
      A **Pod** is the smallest thing you can deploy in Kubernetes.

      **Real-life analogy:**
      Think of a Pod like a house. Containers are like roommates living
      in that house - they share the kitchen (network) and storage.

      ```
      ┌─────────────────────────┐
      │         POD             │
      │  ┌─────┐    ┌─────┐    │
      │  │ App │    │ Log │    │
      │  │     │    │ Sidecar│  │
      │  └──┬──┘    └──┬──┘    │
      │     └────┬─────┘       │
      │    Shared Network       │
      └─────────────────────────┘
      ```

      **Key insight:** Pods are ephemeral. Kubernetes can kill and replace
      them at any time - so don't store important data inside a pod!
    key_points:
      - "Pods are the smallest deployable unit"
      - "Containers in a Pod share network (same IP) and storage"
      - "Pods are ephemeral - they can be replaced anytime"

  - title: "Pod Lifecycle"
    content: |
      Pods go through several **states** during their life:

      ```
      Pending ──► Running ──► Succeeded
                    │              │
                    └──► Failed ◄──┘
      ```

      | State | Meaning |
      |-------|---------|
      | Pending | Waiting to be scheduled |
      | Running | At least one container is running |
      | Succeeded | All containers completed successfully |
      | Failed | At least one container failed |

      **Memory trick:** "P-R-S-F" = "Pods Run, Sometimes Fail"
    key_points:
      - "Pending means waiting for a node"
      - "Running means at least one container is up"
      - "Failed means something went wrong"

command_practice:
  - id: "cmd-01"
    title: "List All Pods"
    instructions: |
      **What we're doing:** See all pods in the default namespace.

      **Why this matters:** This is the most common command you'll use!

      **Memory trick:** `get` = "show me" | `pods` = what you want
    command_hint: "kubectl get pods"
    validation:
      type: "command_output"
      command: "kubectl get pods"
      expected_contains: "NAME"
    points: 10

  - id: "cmd-02"
    title: "Describe a Pod"
    instructions: |
      **What we're doing:** Get detailed info about a specific pod.

      **Why this matters:** When debugging, `describe` shows you events,
      conditions, and configuration details.
    command_hint: "kubectl describe pod <pod-name>"
    validation:
      type: "command_output"
      command: "kubectl describe pod nginx"
      expected_contains: "Name:"
    points: 10

scenarios:
  - id: "scenario-01"
    title: "Fix the ImagePullBackOff"
    description: |
      A team member created a pod but it's stuck in ImagePullBackOff.
      Diagnose and fix the issue!
    manifest: |
      apiVersion: v1
      kind: Pod
      metadata:
        name: broken-app
      spec:
        containers:
        - name: app
          image: ngnix:latest
    hints:
      - "Check the pod events with: kubectl describe pod broken-app"
      - "Look for 'Failed to pull image' in the events"
      - "The image name 'ngnix' has a typo - should be 'nginx'"
    solution_validation:
      type: "resource_state"
      resource: "pod/broken-app"
      state: "Running"
    points: 25

  - id: "scenario-02"
    title: "Pod Stuck in Pending"
    description: |
      Another pod won't start - this time with a different error!
    manifest: |
      apiVersion: v1
      kind: Pod
      metadata:
        name: pending-pod
      spec:
        containers:
        - name: app
          image: nginx
          resources:
            requests:
              memory: "999Gi"
    hints:
      - "Pending usually means a scheduling problem"
      - "Check events for 'Insufficient' messages"
      - "The memory request is way too high - reduce it"
    solution_validation:
      type: "resource_state"
      resource: "pod/pending-pod"
      state: "Running"
    points: 25

quiz:
  passing_score: 70
  questions:
    - type: "multiple_choice"
      question: "What is a Pod? (Think: house analogy)"
      options:
        - "A single container running alone"
        - "The smallest deployable unit - containers sharing resources"
        - "Another name for a node"
        - "A namespace for grouping"
      correct: 1
      explanation: "Like roommates in a house, containers in a Pod share network and storage."
      points: 5

    - type: "multiple_choice"
      question: "What does 'Pending' status mean?"
      options:
        - "The container crashed"
        - "Waiting to be scheduled to a node"
        - "The pod is running successfully"
        - "The image cannot be pulled"
      correct: 1
      explanation: "Pending means Kubernetes is looking for a node to run the pod."
      points: 5

    - type: "command_challenge"
      question: "Write the command to list pods in ALL namespaces"
      expected_contains: "kubectl get pods"
      alternatives:
        - "kubectl get pods -A"
        - "kubectl get pods --all-namespaces"
        - "kubectl get po -A"
      hint: "Use -A or --all-namespaces flag"
      points: 10

    - type: "multiple_choice"
      question: "ImagePullBackOff usually means..."
      options:
        - "The container crashed"
        - "Kubernetes can't download the container image"
        - "The pod is out of memory"
        - "Network is disconnected"
      correct: 1
      explanation: "Usually a typo in image name or missing registry access."
      points: 5

    - type: "true_false"
      question: "Pods can contain multiple containers"
      correct: true
      explanation: "Yes! Multi-container pods are common for sidecars, init containers, etc."
      points: 5
```

---

## Validation Rules

### Chapter Metadata
1. `chapter.number` must be a positive integer
2. `chapter.title` must be a non-empty string
3. `chapter.description` is optional

### Concepts
1. `concepts` must be a non-empty array
2. Each concept must have `title` and `content` fields
3. `key_points` is optional but must be an array of strings if present

### Command Practice
1. `command_practice` is optional
2. Each item must have: `id`, `title`, `instructions`, `command_hint`, `validation`, `points`
3. `id` must be unique within the chapter
4. `validation.type` must be one of: `command_output`, `resource_exists`, `resource_state`, `resource_state_stable`

### Scenarios
1. `scenarios` is optional
2. Each item must have: `id`, `title`, `description`, `manifest`, `hints`, `solution_validation`, `points`
3. `hints` should have 2-3 progressive hints
4. `manifest` must be valid Kubernetes YAML

### Quiz
1. `quiz` is optional
2. Each question must have: `type`, `question`, `points`
3. `multiple_choice` needs: `options` (2-4), `correct` (0-based index)
4. `command_challenge` needs: `expected_contains`
5. `fill_yaml` needs: `yaml_template`, `expected`
6. `true_false` needs: `correct` (boolean)
