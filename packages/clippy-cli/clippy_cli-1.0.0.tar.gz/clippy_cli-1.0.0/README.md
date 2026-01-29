# clippy 📎

> A Linux-first CLI assistant that actually helps you get shit done.

**clippy** is a modular, terminal-native helper designed for Linux and security workflows. It prioritizes **deterministic logic first** (parsing, heuristics, local knowledge) and uses **AI only to fill the gaps** when needed.

This is **not** a chatbot wrapper. It is a real CLI tool that respects Unix philosophy.

---

## Philosophy

- **Linux-first**
- **Local logic > AI**
- **AI is optional and explicit**
- **Modular & extensible**
- **Pipe / stdin / redirection friendly**
- **No GUI, no fluff**

If it breaks shell workflows, it doesn’t belong here.

---

## Project Structure

```
clippy/
├── clippy/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   ├── config.py       # ~/.config/clippy/config.yml
│   ├── core/           # Core subcommands
│   │   ├── explain.py  # Explain commands (hybrid logic + AI)
│   │   ├── why.py      # Diagnose errors
│   │   ├── note.py     # Knowledge base / Obsidian
│   │   ├── lab.py      # Automation / lab setup
│   │   └── gen.py      # Payload / snippet generators
│   └── utils/          # Shared helpers
│       ├── shell.py
│       ├── parsing.py
│       ├── fs.py
│       └── ai.py       # AI backend interface
├── pyproject.toml
└── README.md
```

---

## Installation (Development)

```bash
git clone <repo>
cd clippy
pip install -e .
```

---

## Commands

### `clippy explain`
Explain Linux commands and one-liners.

```bash
clippy explain "find / -perm -4000 2>/dev/null"
```

- Deterministic parsing first
- Shell-aware explanations
- Security context
- AI backend only if needed

---

### `clippy why`
Diagnose errors (pipe-aware).

```bash
gcc test.c 2>&1 | clippy why
```

---

### `clippy note`
Search and extend personal notes.

```bash
clippy note suid
```

---

### `clippy lab`
Automate lab environments.

```bash
clippy lab malware
```

---

### `clippy gen`
Generate payloads and snippets.

```bash
clippy gen reverse-shell bash
```

---

## Configuration

The configuration file is located at `~/.config/clippy/config.yml`. It is created automatically on first run.

**Default Configuration (Safe & Explicit):**
```yaml
ai:
  enabled: false
  backend: azure
  confidence_threshold: 0.6

knowledge:
  use_man_pages: true
  user_knowledge_dir: ~/.config/clippy/knowledge
```

### AI Contract
- **Disabled by default**: AI never runs unless `ai.enabled` is `true`.
- **Silent Failure**: Network or API errors are suppressed by default to preserve CLI utility.
- **Augmentation**: AI only runs when local confidence is below `confidence_threshold`.
- **Backend**: Azure AI Inference via GitHub Models (microsoft/Phi-4)
- **Authentication**: Requires `GITHUB_TOKEN` in `.env` or environment variables

**Setting up authentication:**

Linux / macOS:
```bash
export GITHUB_TOKEN="your_token_here"
```

Windows (PowerShell):
```powershell
$env:GITHUB_TOKEN="your_token_here"
```

---

## Knowledge Resolution Order

Clippy resolves commands in the following strict order:

1.  **Built-in Knowledge**: Static definitions (fastest, most trusted).
2.  **User Knowledge**: Custom definitions in `~/.config/clippy/knowledge`.
3.  **System Man Pages**: Standard Linux manual pages (read-only).
4.  **AI (Optional)**: Only if enabled and confidence is low.

---

## Non-Goals

- **No Auto-Learning**: Clippy does not "learn" from your usage to avoid drift.
- **No Telemetry**: No usage data is sent anywhere.
- **No Background Agents**: Clippy only runs when you type a command.

---

## Status

**Stable v1.0.0**

This project adheres to Semantic Versioning.

---

## License

MIT

---

## Why “clippy”?

Because this one is finally useful.
