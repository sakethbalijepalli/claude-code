# Claude Code Python CLI

A resilient, multi-provider AI agent command-line tool built in Python. It supports tool execution (`read_file`, `Write`, `Bash`) with automatic fallback between multiple LLM API providers (**OpenRouter**, **Anthropic**, and **Google Gemini**).

---

## Features

- **Tool Calling Support**:
  - `read_file`: Reads text from disk.
  - `Write`: Writes or updates file content.
  - `Bash`: Executes shell commands safely.
- **Multi-Provider Fallback Architecture**:
  1. **OpenRouter API** (Default)
  2. **Direct Anthropic API** (Fallback 1)
  3. **Google Gemini API** (Fallback 2)
- **Environment Management**: Automatically loads configuration from `.env` using `python-dotenv`.

---

## Setup & Installation

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/sakethbalijepalli/claude-code.git
cd claude-code
python3 -m venv .venv
source .venv/bin/activate
pip install openai anthropic google-genai python-dotenv
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GEMINI_API_KEY=AIzaSy...
```

> [!IMPORTANT]
> Never commit your `.env` file! It is ignored by git in `.gitignore`.

---

## Usage

Run the tool using the `-p` parameter:

```bash
.venv/bin/python main.py -p "Create a hello world python script and run it"
```

---

## License

MIT License
