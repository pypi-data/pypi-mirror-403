<div align="center">
  <img src="docs/vallignuslogo.svg" alt="Vallignus" width="200">
</div>

# Vallignus 🔥

**The Infrastructure-Grade Firewall for AI Agents**

[![PyPI version](https://badge.fury.io/py/vallignus.svg)](https://badge.fury.io/py/vallignus)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Problem
AI agents are unpredictable. They can loop indefinitely, overspend on API calls in seconds, or execute dangerous network requests that compromise security.

## Solution
Vallignus is a local proxy wrapper that sits between your agent and the internet. It acts as a "Dead Man's Switch," enforcing strict infrastructure limits on your AI code.

## Installation
```bash
pip install vallignus
```

## Usage

No code changes required. Just wrap your existing run command:
```bash
vallignus run --budget 5.00 --allow "github.com,openai.com" -- python agent.py
```

## Demo

![Vallignus Demo](docs/demo.png)

## Features

* **🛡️ Spending Governor:** Automatically kills the process if API spend exceeds your limit.
* **🚦 Domain Allowlist:** Blocks all network traffic to unauthorized domains.
* **✈️ Flight Recorder:** Logs every HTTP request to `flight_log.json` for auditing.

## License

MIT