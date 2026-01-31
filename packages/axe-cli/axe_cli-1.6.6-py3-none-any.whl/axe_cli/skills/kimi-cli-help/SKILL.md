---
name: axe-cli-help
description: Answer Axe Code CLI usage, configuration, and troubleshooting questions. Use when user asks about Axe Code CLI installation, setup, configuration, slash commands, keyboard shortcuts, MCP integration, providers, environment variables, how something works internally, or any questions about Axe Code CLI itself.
---

# Axe Code CLI Help

Help users with Axe Code CLI questions by consulting documentation and source code.

## Strategy

1. **Prefer official documentation** for most questions
2. **Read local source** when in axe-cli project itself, or when user is developing with axe-cli as a library (e.g., importing from `axe_cli` in their code)
3. **Clone and explore source** for complex internals not covered in docs - **ask user for confirmation first**

## Documentation

Base URL: `https://moonshotai.github.io/axe-cli/`

Fetch documentation index to find relevant pages:

```
https://moonshotai.github.io/axe-cli/llms.txt
```

### Page URL Pattern

- English: `https://moonshotai.github.io/axe-cli/en/...`
- Chinese: `https://moonshotai.github.io/axe-cli/zh/...`

### Topic Mapping

| Topic | Page |
|-------|------|
| Installation, first run | `/en/guides/getting-started.md` |
| Config files | `/en/configuration/config-files.md` |
| Providers, models | `/en/configuration/providers.md` |
| Environment variables | `/en/configuration/env-vars.md` |
| Slash commands | `/en/reference/slash-commands.md` |
| CLI flags | `/en/reference/axe-command.md` |
| Keyboard shortcuts | `/en/reference/keyboard.md` |
| MCP | `/en/customization/mcp.md` |
| Agents | `/en/customization/agents.md` |
| Skills | `/en/customization/skills.md` |
| FAQ | `/en/faq.md` |

## Source Code

Repository: `https://github.com/MoonshotAI/axe-cli`

When to read source:

- In axe-cli project directory (check `pyproject.toml` for `name = "axe-cli"`)
- User is importing `axe_cli` as a library in their project
- Question about internals not covered in docs (ask user before cloning)
