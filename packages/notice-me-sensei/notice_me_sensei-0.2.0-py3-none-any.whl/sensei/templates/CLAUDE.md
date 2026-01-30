# Sensei Study Project

This is a sensei-managed study project with spaced repetition learning.

## Required Behavior

When the user asks about tasks, studying, learning progress, what's due, or anything related to their study plan:

1. **Always use the sensei MCP tools** (`sensei_study_*`, `sensei_artifact_*`, `sensei_assessment_*`)
2. **Never use the built-in task tools** (TaskCreate, TaskList, etc.) - those are for coding tasks, not studying
3. Check `sensei_study_list(due_before="today")` at the start of study sessions

## Current Focus

<!-- Update this as your focus evolves -->
-

## Goals

<!-- What are you trying to learn? -->
-

## Conventions

- Notes and implementations live in `topics/`
- Practice attempts go in `{topic}/practice/`
- Files are Obsidian-compatible (you can add frontmatter, tags, wikilinks)

## Quick Commands

Ask Claude:
- "What's due today?" - shows pending sensei study tasks
- "Let's study" - starts a study session
- "Quiz me on [topic]" - runs an SRS assessment
- "Create a study plan for [topic]" - creates sensei study tasks
- "Save this reference: [URL]" - saves a webpage/paper as a reference
- "Find references about [topic]" - searches saved references
- "Show my references" - lists recent references
