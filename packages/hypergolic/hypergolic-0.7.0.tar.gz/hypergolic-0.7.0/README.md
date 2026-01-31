# Hypergolic

A powerful AI coding assistant with command-line tool access for macOS.

> 🚀 Fast, focused, and built for developers who ship.

## Features

- Execute shell commands on macOS
- Read and write files with surgical precision
- Navigate directories and explore projects
- Screenshot capture for visual context
- Code review integration for quality assurance
- Session branches for safe code modifications
- Multi-layered prompt system for personalized behavior

## Installation

### 1. Configure Environment Variables

Hypergolic requires three environment variables to connect to your LLM provider:

```bash
export HYPERGOLIC_API_KEY=your-api-key
export HYPERGOLIC_BASE_URL=https://api.anthropic.com
export HYPERGOLIC_MODEL=claude-opus-4-5-20251101
```

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) for persistence.

### 2. Install uv

UV (python package manager) is a requirement. Run:
`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 3. Install with uv

```bash
uv tool install hypergolic
```

This installs `h` as a globally available command.

## Usage

Navigate to any repo with an active git setup and run:

```bash
h
```

This launches an interactive TUI where you can chat with the AI assistant. The assistant can:

- Read and modify files in your project
- Run shell commands
- Search through codebases
- Take screenshots for visual debugging
- Commit changes and request code reviews

### Workflow

1. **Start a session** — Run `h` from your project directory
2. **Describe your task** — The assistant will explore your codebase and implement changes
3. **Review changes** — The assistant works on a session branch, making changes you can review
4. **Merge when ready** — After code review, changes merge back to your original branch

## Getting Started Tips

### Be Specific

The more context you provide, the better the results. Instead of "fix the bug", try "the login form submits twice when clicking the button rapidly — add debouncing".

### Encourage Planning

In your prompting, tell the AI to think through what it wants to do
first and then offer feedback on the plan before telling it to proceed.

### Use Screenshots

For UI issues, the assistant can take screenshots. Just mention "take a screenshot" or describe what you're seeing visually.

### Customize Behavior

Create `~/.hypergolic/user_prompt.md` for personal preferences that apply to all projects, or `AGENTS.md` in your repo root for project-specific instructions.

You're encouraged to develop these files frequently and significantly.
A rule I follow is that when the AI does something I don't want it to,
I ask it to ideate with me on how best to change the prompt to not
do that again.

## Architecture

Hypergolic creates a session branch for each coding session. This keeps your work organized and allows you to review changes before merging. After code review, changes can be merged back into the original branch.

But it also means that sometimes stuff isn't committed at the end of
a session. If you find you're missing work, it's probably somewhere
in your git session branches. Luckily, Hypergolic is very good at
helping you find and recover these.

## Danger Zone

Hypergolic leverages a custom suite of tools that give it plenty of
power. It can take screenshots, control your mac via AppleScript, and
issue command line subprocesses. These are gated behind an approval
workflow that will ask you for permission to run these commands.

If you trust the AI more than I do, you can enable `ENV_ALL_TOOLS_AUTO_APPROVE=true` in your shell to avoid these
approval modals. A word of caution that this could theoretically let
the AI delete your OS, retrieve passwords, message your contacts, or
any number of other things.

## Built With

- Python 3.14+
- [Anthropic Claude API](https://www.anthropic.com/)
- [Textual](https://textual.textualize.io/) for the TUI
- [uv](https://docs.astral.sh/uv/) for dependency management

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - See LICENSE file for details.
