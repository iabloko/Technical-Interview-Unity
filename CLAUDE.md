# CLAUDE.md

This repo is a knowledge base for preparing for a Unity / C# technical interview. Notes are written in Russian as `.md` files, grouped into sections (`01-csharp`, `02-architecture`, ...). Each file starts with a `[← К содержанию](../README.md)` link and ends with `---`. A new file is registered by adding a link in `README.md`.

## Writing style

- **Technically precise terms only.** No analogies, metaphors, everyday comparisons, or colloquialisms ("blob", "rough", "hard-wired", "hangs in memory", "bookkeeping", etc.). If a concept has an established name, use it.
- Describe the **actual mechanism**, not the impression of it. Instead of "unloading is rough" — state what the API does (what it scans, what it unloads, under which conditions).
- No filler: only what matters for the interview. Short statements, tables for comparisons, minimal code snippets.
- Every claim must be verifiable and correct. If there's a nuance or limitation, state it rather than oversimplifying into something false.
- English technical terms (ref-counting, serialized, async, CDN) are fine when they are the platform's standard terminology.

## Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from Andrej Karpathy's observations on LLM coding pitfalls.

> Tradeoff: these guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Remove imports/variables/functions that *your* changes made unused; don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Goal-driven execution

Define success criteria. Loop until verified.

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan with a verification check per step. Strong success criteria let you loop independently; weak criteria ("make it work") require constant clarification.
