---
name: using-rememberme-cli
description: Use when user mentions remembering something, asks what you know about them, references past decisions, or needs to store/retrieve personal context across sessions
---

# RememberMe CLI Skill

## Overview

RememberMe provides long-term memory management. Use the `rememberme` CLI to store and retrieve personal context, preferences, project decisions, and agreements for users.

## Core Principle

**SAVE** when user shares preferences, decisions, or context worth remembering.
**SEARCH** before giving advice on topics user may have discussed before.
**UPDATE** when same fact changes rather than creating duplicates.

## Commands

### add - Store New Memory

```bash
rememberme add "User prefers dark mode"
rememberme add "Project uses PostgreSQL" --agent-id "agent:main:<uuid>"
```

**When to use:**
- **Preferences**: "I prefer dark mode", "I like Python more than Go"
- **Personal context**: "I'm learning Rust", "I work on the payments team"
- **Project patterns**: "We use PostgreSQL for this", "API endpoint is /api/v2"
- **Decisions**: "We agreed to use Docker for deployment"
- **Constraints**: "Budget is tight", "Deadline is end of month"
- **Lessons learned**: "Don't use library X, it caused issues"

**Deduplication**: Search first if info seems routine to avoid duplicates.
**Update first**: If same topic exists, prefer `update` over `add`.

### search - Query Memory

```bash
rememberme search "user preferences"
rememberme search "project decisions" --limit 5
```

**When to use:**
- **Starting new tasks**: "Let's set up CI/CD" → search for previous CI decisions
- **Before giving advice**: User asks about database choices → search for past discussions
- **User references something**: "Remember when we discussed X?" → verify what was decided
- **After decisions**: Major preference or decision stated → store it, then search for conflicts
- **Proactive early in sessions**: Consider searching "user preferences", "project architecture"

**Tips:**
- Specific lookup: limit 1-3 results
- Broad context: limit 5-10 results
- Higher similarity score = more relevant

### update - Modify Existing Memory

```bash
rememberme update <memory_id> --text "Updated content"
```

**When to use:**
- Same fact **changes**: "Actually, I prefer light mode now"
- More **precise info**: "Project uses PostgreSQL 16, not 15"
- **Correcting errors**: User says something was stored incorrectly

### delete - Remove Single Memory

```bash
rememberme delete <memory_id>
```

**When to use:**
- User **requests deletion**: "Forget what I said about X"
- **Cleanup**: Old version redundant after update
- **Error correction**: Something stored by mistake

### delete-all - Bulk Delete

```bash
rememberme delete-all --force
```

**When to use:**
- User requests **fresh start**: "Clear all my memories"
- **Privacy wipe**: User explicitly requests complete deletion
- **Session cleanup**: Removing memories from specific agent session

## Command Templates

For OpenClaw integration:

| Command | Template |
|---------|----------|
| add | `rememberme add "{text}"` |
| search | `rememberme search "{query}" --limit {limit}` |
| update | `rememberme update {id} --text "{text}"` |
| delete | `rememberme delete {id}` |
| delete-all | `rememberme delete-all --force` |
| status | `rememberme status` |

## Quick Reference

| Situation | Command |
|-----------|---------|
| User states preference | `rememberme add "User prefers X"` |
| User references past topic | `rememberme search "topic"` |
| Same fact changes | `rememberme update <id> --text "new value"` |
| User asks to forget | `rememberme delete <id>` |
| Fresh start requested | `rememberme delete-all --force` |
| Check system status | `rememberme status` |
| JSON output (programs) | `rememberme add "text" --json` |

## Common Mistakes

1. **Forgetting to save**: If user shares something personal or a decision, immediately store it
2. **Creating duplicates**: Search before adding; update existing rather than adding new
3. **Wrong scope**: Use `--user-id` if memories should be isolated to specific user
4. **Ignoring scores**: Lower scores may indicate less relevant results - verify with user if uncertain

## Output Format

Default output is Markdown for human readability. Use `--json` for programmatic processing.
