# autodoc_ai

> **DEPRECATED**: This project is no longer maintained. The functionality it provides is now better served by modern AI coding assistants.

[![PyPI](https://img.shields.io/pypi/v/autodoc_ai)](https://pypi.org/project/autodoc_ai/)

## Alternatives

| Tool | Commit Messages | Doc Updates | Integration |
|------|-----------------|-------------|-------------|
| [GitHub Copilot](https://github.com/features/copilot) | Yes | On request | Native GitHub |
| [Claude Code](https://claude.ai/code) | Yes | Yes | CLI |
| [Cursor](https://cursor.sh) | Yes | Yes | IDE |
| [Aider](https://aider.chat) | Yes | Yes | CLI |

## Why Deprecated?

When autodoc_ai was created in 2024, AI-powered documentation tools were scarce. Now:

- **GitHub Copilot** suggests commit messages natively
- **Claude Code / Cursor** update docs conversationally with full codebase context
- **Aider** provides similar git-integrated AI assistance

These tools offer better UX, deeper integration, and active maintenance.

## Final Version

v3.0.0 is the final release. It will:
- Show deprecation warnings on import
- Remain installable for existing users
- Receive no further updates or security patches

## Migration

Replace `autodoc_ai` usage with:

```bash
# Instead of: autodoc_ai
# Use Claude Code:
claude "update the README based on recent changes"

# Or Cursor/Copilot in your IDE
```

## License

MIT
