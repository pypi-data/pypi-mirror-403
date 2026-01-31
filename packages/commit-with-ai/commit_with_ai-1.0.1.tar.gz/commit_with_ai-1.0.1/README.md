# Git Auto-Commit with Gemini API

AI-powered git commit message generator using Gemini API's structured JSON output.

## What It Does

Analyzes your staged git changes and generates 5 Conventional Commits-compliant commit message suggestions using Gemini AI. Select one or enter your own.

## Installation

### Via PyPI (Recommended)

```bash
# Use uvx (no installation required)
uvx commit-with-ai

# Or install globally
pip install commit-with-ai
```

### From Source

```bash
# Clone the repository
git clone https://github.com/chenwei791129/commit-with-ai.git
cd commit-with-ai

# Run directly with uv
uv run commit_with_ai.py
```

## Setup

### 1. Configure API Key

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

For persistent configuration, add to your shell profile (~/.bashrc, ~/.zshrc):

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 2. Configure Git Alias

```bash
# If installed via pip
git config --global alias.ac '!commit-with-ai'

# Or if using uvx (no installation)
git config --global alias.ac '!uvx commit-with-ai'

# Or if running from source
git config --global alias.ac '!/your-script-path/commit-with-ai/commit_with_ai.py'
```

## Usage

```bash
git add <files>
git ac
```

## Example

```
Analyzing staged changes...
Generating commit message options with Gemini API...

======================================================================
Select a commit message:
======================================================================
1. feat(auth): add user authentication system
2. feat: implement login and registration flow
3. chore(deps): add authentication dependencies
4. docs: update README with auth setup instructions
5. refactor(auth): restructure authentication module
6. Enter custom message
7. Cancel
======================================================================

Enter selection [1-7]:
```

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
