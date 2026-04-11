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

## Auto-Recall (Pre-Execution)

Before responding, analyze the user's input context and search memory for relevant information. **Use judgment based on context, not rigid keyword matching.**

### Decision Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│ Does this involve:                  │
│ - User's skills/capabilities?       │
│ - User's location/environment?      │
│ - User's preferences/habits?       │
│ - Project-specific context?         │
│ - Past decisions or agreements?      │
│ - User's background/experience?     │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
     Yes               No
      │                 │
      ▼                 ▼
┌─────────────┐    Proceed
│ Construct   │
│ search query│
│ from context│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Inject results  │
│ into response   │
└─────────────────┘
```

### How to Construct Search Queries

**Identify the core aspect** the user is asking about, then search with natural phrasing:

| User Context | Search Query Examples |
|--------------|----------------------|
| Asking about skills | `"user programming language"`, `"user technical skills"`, `"user expertise"` |
| Location-related | `"user city"`, `"user location"`, `"user timezone"` |
| Project tech stack | `"user project framework"`, `"user project database"`, `"user project tech stack"` |
| Preferences | `"user preference IDE"`, `"user preferred language"`, `"user coding preference"` |
| Past decisions | `"user decision docker"`, `"user decision database"`, `"user project choice"` |
| Work context | `"user job"`, `"user role"`, `"user team"` |
| Habits | `"user习惯"`, `"user workflow"`, `"user typical approach"` |

### Examples

| User Says | Context Analysis | Auto-Recall Search |
|-----------|-----------------|-------------------|
| "用我最拿手的语言写代码" | Asks about user's best language | `rememberme search "user programming language skills"` |
| "天气怎么样" | Asks about weather (implies location) | `rememberme search "user city location"` |
| "我的项目用什么框架" | Asks about user's project framework | `rememberme search "user project framework"` |
| "上次我们选型选了什么" | Asks about past decision | `rememberme search "user project technology choice"` |
| "我之前遇到过什么问题" | Asks about user's past issues | `rememberme search "user problem history"` |
| "我喜欢在咖啡馆工作" | Mentions personal habit → store it | First search if exists, then `rememberme add "user likes working from cafe"` |

### Key Principle

**Context-driven, not keyword-driven.** If the user's question implies knowing something *about the user*, search for it. The goal is to make responses personalized without the user explicitly saying "remember that...".

## Post-Response Storage (Evaluation)

After responding, evaluate if new facts should be stored.

### When to Evaluate Storage

- User provides **new information** about themselves
- A **decision or agreement** was made
- User **corrects** previous information
- Project **technical choices** are confirmed
- **Preferences** are explicitly stated

### Evaluation Checklist

```
After each response, ask:
├── Did user share personal context? (location, job, habits)
├── Did we make a technical decision?
├── Did user express a preference?
├── Did user correct something?
└── Is this worth remembering for future sessions?
```

### Storage Decision Rules

| Condition | Action |
|-----------|--------|
| New fact, no prior memory | `rememberme add` |
| Same topic exists | `rememberme update` or skip if redundant |
| User corrected previous info | `rememberme update` |
| Temporary/one-off context | Skip storage |
| Sensitive personal data | Skip, suggest secure alternative |

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
