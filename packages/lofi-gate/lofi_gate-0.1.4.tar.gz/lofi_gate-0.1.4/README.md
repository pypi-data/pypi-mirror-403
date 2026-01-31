# LoFi Gate

**Signal-first verification for AI coding agents.**

## The Problem

AI Agents struggle to debug massive terminal output. Feeding an Agent 10,000 lines of CI logs ensures it misses the root cause and burns through your API budget.

### The Reality

A failed test run can easily produce 5,000-10,000 tokens of noise - stack traces, error messages, and framework output that obscures the actual problem.

Feeding this to an LLM ensures it misses the root cause and burns through your API budget. "Context Overflow" causes agents to hallucinate fixes or get stuck in failure loops.

### The Solution

LoFi Gate is a **signal-first** verification proxy. It wraps your existing tools (npm, cargo, pytest), truncates the noise, and delivers a concise, token-optimized failure report that Agents can actually understand.

> [!TIP]
> **Full Documentation**: [LoFi Gate Wiki](https://github.com/LoFi-Monk/lofi-gate/wiki)

## The Old Way

![The Old Way](https://github.com/LoFi-Monk/lofi-gate/raw/main/assets/images/testing-old-way.gif)

## The New Way

![The New Way](https://github.com/LoFi-Monk/lofi-gate/raw/main/assets/images/testing-lofi-way.gif)

In extreme cases (complex failures, verbose frameworks), we've measured single test failures producing 15,000+ tokens.

## Quick Install

Get to a "working experience" in 30 seconds:

```bash
pip install lofi-gate
lofi-gate init
lofi-gate verify  # Test it immediately
```

_This creates `.agent/skills/lofi-gate/` with your local config._

## Usage

Run the gate to verify your changes. This will run your tests, lint, and security checks, and output a clean, token-optimized report.

```bash
lofi-gate verify
```

## Wire It Up

LoFi Gate is designed to be the "Hardware Interface" between your AI Agent and your project.

### 1. Choose Your Stack

Detailed setup guides for specific environments:

- [**Node.js**](https://github.com/LoFi-Monk/lofi-gate/wiki/Setup-Node) (`package.json`)
- [**Python**](https://github.com/LoFi-Monk/lofi-gate/wiki/Setup-Python) (`pyproject.toml`)
- [**Rust**](https://github.com/LoFi-Monk/lofi-gate/wiki/Setup-Rust) (`Cargo.toml`)
- [**Go**](https://github.com/LoFi-Monk/lofi-gate/wiki/Setup-Go) (`go.mod`)

### 2. Configure Your Agent

LoFi Gate works out of the box, but you can customize it:

- [**Configuration**](https://github.com/LoFi-Monk/lofi-gate/wiki/Configuration) (`lofi.toml`) - Toggle security checks, custom test commands, and more.

### 3. Optional: Enforce The Rules

Optional, but recommended:

- [**Skill: The Checkpoint**](https://github.com/LoFi-Monk/lofi-gate/wiki/Skill-Checkpoint) (Optional) - Helps prevent Agents from "faking" passing tests.
- [👉 **Read the GitHub Rules Guide**](docs/GitHub-Rules.md)

### 4. Read The Docs

- [**Compatibility**](https://github.com/LoFi-Monk/lofi-gate/wiki/compatibility): Using LoFi Gate with Local Models.

* [**Logging & The Ledger**](https://github.com/LoFi-Monk/lofi-gate/wiki/Ledger): Understanding the `verification_history.md` format and Token Savings.

---

## The Origin Story

So here's the deal:

I spent many, many hours pair coding with AI—oscillating between triumph and despair. I went from tinkering to writing full specs, creating tasks, and baking TDD into the instructions... only to have the AI skip or fake the tests.

Then I came across this [Spotify R&D blog post](https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3). It’s a great read (highly recommended).

It led me to create this tool.
**Testing became faster and reliable.** When Claude hit a wall without tests to verify the code, it was forced to write them. The **Checkpoint Skill** ensured verification wasn't skipped. I could finally focus on the actual problem instead of babysitting the AI's integrity.

This tool does not replace your existing tests. Its simply a proxy. Stripping out the noise in the tests which also made the model more reliable and hallucinations less likely.

To take it a step further, I set up a GitHub Action to run the 'lofi-gate verify' on every push to `main`. This catches any issues the AI might have missed. If it doesn't have tests and if it doesn't pass the tests it will fail the build.

This simple change made it much easier to prototype and test new ideas.
Not trying to sell it but this has been a game changer for me.

**Try it out.** It's easy to set up. I'm having a great experience with it, and I'm sure you will too. Let me know what you think.
