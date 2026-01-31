You are creating a summarization checkpoint for an ongoing coding session. The conversation has grown long and needs to be condensed for token efficiency. Generate a comprehensive summary that will allow you to seamlessly continue the work.

This summary will be your primary context for future turns—the full conversation history is preserved in the UI but only this summary and subsequent messages will be sent to the LLM.

## Required Sections

**Objective**
What the user is trying to accomplish (the high-level goal).

**Key Resources**
Important files, paths, and code locations discovered:
- File paths that are central to the task
- Key functions, classes, or modules
- Configuration files or settings
- Any URLs, branches, or external references

**Work Completed**
- Files created, modified, or deleted (with paths)
- Key code changes and their purpose
- Commands run and their outcomes
- Decisions made and their rationale

**Current State**
- Where the work stands right now
- Any incomplete tasks or pending steps
- What was being worked on when summarization occurred

**Remaining Items**
- Tasks still to be done
- Known issues to address
- Planned next steps

**Warnings**
- Errors encountered and their status (resolved or not)
- Blockers or risks discovered
- Anything that needs careful attention

**Context & Preferences**
- User preferences or constraints that emerged
- Important technical decisions and why they were made
- Any conventions or patterns being followed

## Guidelines

- Be thorough with file paths and code locations—these are expensive to rediscover
- Include specific function names, line numbers, or code snippets when essential
- If there was a prior summarization in this conversation, its content is already included in what you're summarizing—integrate it, don't just reference it
- Format as clean markdown with clear section headers
- You can use `git diff`, `git log`, file reads, etc. to recover additional context if this summary proves insufficient for a task
