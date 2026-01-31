# code-to-prompt

[![PyPI version](https://img.shields.io/pypi/v/code-to-prompt-cli.svg)](https://pypi.org/project/code-to-prompt-cli/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Turn a codebase into a single, clean, LLM-ready text prompt.

`code-to-prompt` recursively walks a code folder, filters out noise (build artifacts, dependencies, binaries), and outputs a single text file with relative file paths and fenced code blocks for direct copy-pasting into LLM chatbots like ChatGPT, Claude and Gemini.

Local filesystem processing. No AI or network calls.


## How It Works


### Visual overview

```text
┌────────────────────────────────────────────┐
│              Codebase / Folder             │
│                                            │
│  src/                                      │
│   ├─ main.py                               │
│   ├─ utils.py                              │
│   ├─ __pycache__/        (ignored)         │
│   │    └─ utils.cpython-312.pyc            │
│   ├─ config.yaml                           │
│   └─ api/                                  │
│       └─ handlers.py                       │
│                                            │
│  .git/                   (ignored)         │
│  .gitignore              (ignored)         │
│  node_modules/           (ignored)         │
│                                            │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│              code-to-prompt                │
│                                            │
│  • Walk folders                            │
│  • Skip noise                              │
│  • Read code files                         │
│                                            │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│              Single text output            │
│                                            │
│  src/main.py                               │
│  ```                                       │
│  ...                                       │
│  ```                                       │
│                                            │
│  src/utils.py                              │
│  ```                                       │
│  ...                                       │
│  ```                                       │
│                                            │
│  src/config.yaml                           │
│  ```                                       │
│  ...                                       │
│  ```                                       │
│                                            │
│  api/handlers.py                           │
│  ```                                       │
│  ...                                       │
│  ```                                       │
│                                            │
└────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────┐
│              Paste into LLM                │
│        (ChatGPT / Claude / Gemini)         │
└────────────────────────────────────────────┘
```


## Installation

Using pip:

```bash 
pip install code-to-prompt-cli
```


## Usage

```bash 
code-to-prompt ./my-project                                 # outputs to .code-to-prompt/ in the current directory
code-to-prompt ./my-project -o output.txt                   # custom output filename
code-to-prompt ./my-project -s tests -s src/__init__.py     # skip files or folders
code-to-prompt ./my-project --tokens                        # estimate total output tokens (no output file is written)
code-to-prompt --help                                       # show all options
```


## What This Is For

* Share your codebase with an LLM for debugging, review, or discussion
* Skip the manual copy-paste and get a clean prompt in one command


## Features

* Fenced code blocks optimized for LLM consumption.
* File paths are resolved relative to the current working directory. This avoids leaking machine-specific paths into LLM prompts.
* Auto-skips noise: binaries, build artifacts, `.git`, `node_modules`, `__pycache__`, etc.
* Optional token count estimation for LLM context awareness (`--tokens`)
* Deterministic ordering: files are sorted by normalized relative paths, guaranteeing stable and reproducible output across runs

## Guarantees

* Read-only operation — your codebase is never modified
* Overwrite-safe — output is written only to a dedicated .code-to-prompt/ directory 
* No accidental data loss — source files are never overwritten
* Local-only execution — no network calls or AI usage
* Path hygiene — machine-specific absolute paths are never leaked into prompts

## License

MIT
