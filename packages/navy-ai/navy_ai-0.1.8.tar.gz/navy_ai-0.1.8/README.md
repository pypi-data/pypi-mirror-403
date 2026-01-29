# Navy AI 🚢

<p align="center">
  <a href="https://pypi.org/project/navy-ai/">
    <img src="https://img.shields.io/pypi/v/navy-ai.svg" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/navy-ai/">
    <img src="https://img.shields.io/pypi/pyversions/navy-ai.svg" alt="Python versions">
  </a>
  <a href="https://pypi.org/project/navy-ai/">
    <img src="https://img.shields.io/pypi/dm/navy-ai.svg" alt="PyPI downloads">
  </a>
  <a href="https://github.com/Zrnge/navy-ai/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Zrnge/navy-ai.svg" alt="License">
  </a>
  <a href="https://github.com/Zrnge/navy-ai/stargazers">
    <img src="https://img.shields.io/github/stars/Zrnge/navy-ai.svg" alt="GitHub stars">
  </a>
  <a href="https://github.com/Zrnge/navy-ai/issues">
    <img src="https://img.shields.io/github/issues/Zrnge/navy-ai.svg" alt="GitHub issues">
  </a>
</p>


**Navy AI** is a terminal-based AI assistant designed for **local-first usage**, with optional cloud providers.  
It works entirely from the command line and prioritizes **privacy, cost control, and clarity**.

> 🟢 Default mode is **FREE and OFFLINE** using local AI.

---

## ✨ Features

- 🖥️ Clean, modern CLI
- 🧠 Local AI via **Ollama** (free, offline)
- ☁️ Cloud AI via **Gemini** (free tier available)
- 💳 Optional **OpenAI** support (paid, opt-in)
- 🔁 Argument mode & interactive mode
- 🎨 Styled terminal output
- 🔌 Extensible provider system
- 🔐 Secure by default (no keys in code)

---

## 📦 Installation

### Requirements
- Python **3.9+**
- (Optional) Ollama for local AI

### Install from PyPI
```bash
pip install navy-ai
```
---
### 📘 Usage Guide

Verify Installation
After installing Navy AI, verify that the CLI is available:
```bash
navy-ai --help
```
---
### 🚀 Quick Start

Navy AI works in two modes:

- Argument mode – single command
- Interactive mode – chat-style session

### 🔹 Argument Mode

Ask a question directly from the terminal:
```bash
navy-ai "what is zero trust security?"
```
Example output:
```bash
Zero Trust is a security model that assumes no implicit trust...
```

---
### 🔹 Interactive Mode

Start an interactive session:
```bash
navy-ai
```
You will see:
```bash
Navy AI >
```
Then type your questions:
```bash
Navy AI > what is a cpu
Navy AI > explain zero trust
Navy AI > exit
```
---
### 🧠 Providers Overview
| Provider   | Cost      | Internet   | Notes                        |
| ---------- | --------- | --------   | ---------------------------  |
| **Ollama** | Free      | ❌ No     | Local, offline, recommended  |
| **Gemini** | Free tier | ✅ Yes    | Google AI Studio             |
| **OpenAI** | Paid      | ✅ Yes    | Requires billing             |

🟢 Default provider is Ollama (local-first).

### Ollama (Local AI – Recommended)

Ollama allows you to run AI models locally and offline.

#### 1️⃣ Install Ollama

👉 https://ollama.com

#### 2️⃣ Pull a Model

```bash
ollama pull mistral
ollama pull qwen2.5-coder:7b
ollama pull llama3
..........
```

#### 3️⃣ Use with Navy AI

Explicit provider + model:
```bash
navy-ai --provider ollama --model mistral "what is cpu"
```
Or simply:
```bash
navy-ai "what is cpu"
```
➡️ Ollama is the default provider.

### 🟡 Gemini (Cloud AI – Free Tier)

#### 1️⃣ Create an API Key

Keys must be created from Google AI Studio:

👉 https://aistudio.google.com/app/apikey

⚠️ API keys from Google Cloud Console will not work.

#### 2️⃣ Set Environment Variable

Windows (PowerShell)
```bash
setx GEMINI_API_KEY "AIzaSyXXXX"
```

macOS (Terminal)
Set the variable (temporary – current session only):
```bash
export GEMINI_API_KEY="AIzaSyXXXX"
```

Make it persistent (recommended):
For zsh (default on modern macOS):
```bash
echo 'export GEMINI_API_KEY="AIzaSyXXXX"' >> ~/.zshrc
```

For bash:
```bash
echo 'export GEMINI_API_KEY="AIzaSyXXXX"' >> ~/.bashrc
```

Restart the terminal (or run source ~/.zshrc / source ~/.bashrc).

Verify:
```bash
echo $GEMINI_API_KEY
```

Linux (Terminal)

Set the variable (temporary – current session only):
```bash
export GEMINI_API_KEY="AIzaSyXXXX"
```

Make it persistent:

For bash:
```bash
echo 'export GEMINI_API_KEY="AIzaSyXXXX"' >> ~/.bashrc
```

For zsh:
```bash
echo 'export GEMINI_API_KEY="AIzaSyXXXX"' >> ~/.zshrc
```

Restart the terminal (or run source ~/.bashrc / source ~/.zshrc).

Verify:
```bash
echo $GEMINI_API_KEY
```

#### 3️⃣ Use Gemini
```bash
navy-ai --provider gemini
```
Recommended model:
```bash
navy-ai --provider gemini --model gemini-2.5-flash
```

### 🔵 OpenAI (Optional – Paid)

OpenAI requires billing to be enabled.

#### 1️⃣ Create API Key

👉 https://platform.openai.com/api-keys

#### 2️⃣ Enable Billing

👉 https://platform.openai.com/account/billing

#### 2️⃣ Set Environment Variable

Windows (PowerShell)
```bash
setx OPENAI_API_KEY "sk-xxxx"
```

macOS (Terminal)
Set the variable (temporary – current session only):
```bash
export OPENAI_API_KEY="sk-xxxx"
```

Make it persistent (recommended):
For zsh (default on modern macOS):
```bash
echo 'export OPENAI_API_KEY="sk-xxxx"' >> ~/.zshrc
```

For bash:
```bash
echo 'export OPENAI_API_KEY="sk-xxxx"' >> ~/.bashrc
```

Restart the terminal (or run source ~/.zshrc / source ~/.bashrc).

Verify:
```bash
echo $OPENAI_API_KEY
```

Linux (Terminal)

Set the variable (temporary – current session only):
```bash
export OPENAI_API_KEY="sk-xxxx"
```

Make it persistent:

For bash:
```bash
echo 'export OPENAI_API_KEY="sk-xxxx"' >> ~/.bashrc
```

For zsh:
```bash
echo 'export OPENAI_API_KEY="sk-xxxx"' >> ~/.zshrc
```

Restart the terminal (or run source ~/.bashrc / source ~/.zshrc).

Verify:
```bash
echo $OPENAI_API_KEY
```

### 4️⃣ Use OpenAI
```bash
navy-ai --provider openai --model gpt-3.5-turbo "explain zero trust"
```
⚠️ If billing is not enabled, OpenAI may return:
```bash
429 Too Many Requests
```

### ⚙️ CLI Syntax
```bash
navy-ai [OPTIONS] [PROMPT]
```

### Options
| Option       | Description                    |
| ------------ | ------------------------------ |
| `--provider` | `ollama` | `gemini` | `openai` |
| `--model`    | Provider-specific model        |
| `--help`     | Show help                      |

### 🧪 Examples
```bash
navy-ai "hi!"

navy-ai --provider ollama --model qwen2.5-coder:7b

navy-ai --provider gemini --model gemini-2.5-flash

navy-ai --provider openai --model gpt-3.5-turbo
```
