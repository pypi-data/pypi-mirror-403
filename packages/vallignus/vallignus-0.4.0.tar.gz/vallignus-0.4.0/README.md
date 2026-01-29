<div align="center">
  <img src="docs/vallignuslogo.svg" alt="Vallignus" width="200">
</div>

# Vallignus 🔥

**The Infrastructure-Grade Firewall for AI Agents**

*Because prompts are not permissions.*

Built for local agents, headless workflows, and unattended execution.

[![PyPI version](https://badge.fury.io/py/vallignus.svg)](https://badge.fury.io/py/vallignus)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Problem

AI agents are unpredictable. They can loop indefinitely, overspend on API calls in seconds, or execute dangerous network requests that compromise security.

## Solution

Vallignus is a local execution firewall that sits between your agent and the internet. It enforces **who** can run, **what** they are allowed to do, and **logs every decision**, without changing your code.

## How It Works
```
┌─────────┐      ┌───────────┐      ┌─────────────────┐
│  Agent  │ ───▶ │ Vallignus │ ───▶ │ LLM / APIs / Net│
└─────────┘      └───────────┘      └─────────────────┘
                       │
              identity + policy
              + spend limits
              + audit log
```

Every outbound request is checked against the policy before it leaves.

---

## 🚀 5-Minute Quickstart

Protect any AI agent with identity, limits, and audit - without changing your code.

### Install
```bash
pip install vallignus
```

### 1. Initialize Vallignus

Creates local authority storage and cryptographic keys.
```bash
vallignus auth init
```

This creates:
```
~/.vallignus/
  ├── agents/
  ├── policies/
  ├── keys/
  └── revoked/
```

### 2. Register an agent identity
```bash
vallignus auth create-agent \
  --agent-id support-bot \
  --owner "you@example.com"
```

An agent now has a stable identity.

### 3. Create a permission policy

Define what the agent is allowed to do.
```bash
vallignus auth create-policy \
  --policy-id support \
  --max-spend-usd 5 \
  --allowed-domains "httpbin.org"
```

This policy allows:
- up to $5 in API spend
- network access only to `httpbin.org`

Policies are versioned automatically.

### 4. Issue a signed execution token
```bash
export VALLIGNUS_TOKEN=$(vallignus auth issue-token \
  --agent-id support-bot \
  --policy-id support)
```

This token cryptographically binds:
- the agent identity
- the policy version
- an expiration time

### 5. Run your agent (no code changes)
```bash
vallignus run -- python agent.py
```

Vallignus will now:
- ✅ allow permitted requests
- ❌ block disallowed domains
- 💸 stop runaway spending
- 🧾 log every allow/deny decision with identity and policy context

---

## Example: Blocked Request

If your agent tries to access an unauthorized domain:
```json
{
  "decision": "deny",
  "agent_id": "support-bot",
  "owner": "you@example.com",
  "policy_id": "support",
  "policy_version": 1,
  "deny_reason": "domain_not_allowed"
}
```

Nothing escapes silently.

---

## What Vallignus Does

Before every network request, Vallignus asks:

> "Is this agent allowed to do this under its policy?"

- **If yes** → request proceeds
- **If no** → request is blocked and audited

All decisions are enforced locally.

---

## Why Not Just Kill the Process?

For simple local scripts, killing a process may be enough.

However many agent setups today run:
- headless or remote workloads
- long-lived background processes
- scheduled or unattended execution
- indirect network calls through libraries or subprocesses

In these cases, control often degrades into emergency shutdowns or power cuts.

Vallignus provides a safer middle layer by enforcing permissions before actions occur, rather than reacting after something goes wrong.

---

## Why Monitoring Isn't Enough

Dashboards show damage after it happens. Alerts arrive too late.

By the time you see the spike:
- the budget is already gone
- the requests already hit production
- the agent already accessed what it should not have

Prevention must sit inline, not alongside.

Vallignus gates execution before it occurs. It does not observe and report. It decides and enforces.

---

## What Vallignus is NOT

- ❌ Not a model wrapper
- ❌ Not prompt engineering
- ❌ Not surveillance
- ❌ Not cloud-hosted

Vallignus runs entirely on your machine.

---

## When to Use Vallignus

- You're building autonomous agents
- You want hard spend limits
- You need domain allowlists
- You want auditability and reproducibility
- You don't trust "just prompts"

---

## Key Commands
```bash
# Policy management
vallignus auth update-policy --policy-id X --max-spend-usd 50

# Token management
vallignus auth inspect-token <token>      # Debug token contents
vallignus auth revoke-token --jti <id>    # Instantly stop an agent

# Key rotation
vallignus auth rotate-key                 # Rotate signing keys
```

---

## Demo

![Vallignus Demo](docs/demo.png)

---

## Project Status

Vallignus is early-stage infrastructure under active development.

APIs may evolve, but core guarantees are stable:
- local-only execution
- explicit permissions
- revocable authority
- auditable decisions

---

## License

MIT
