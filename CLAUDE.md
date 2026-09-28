# CLAUDE.md

This repo is a knowledge base for preparing for a Unity / C# technical interview. Notes are written in Russian as `.md` files in `docs/`, grouped into sections (`docs/01-csharp`, `docs/02-architecture`, ...). Each file starts with a `[← К содержанию](../README.md)` link and ends with `---`. A new file is registered by adding a link in `docs/README.md`.

## Site

The notes are published as a site with MkDocs Material (`mkdocs.yml`), deployed to a Cloudflare Worker on push to `main` (`wrangler.jsonc` publishes only the built `site/`).

- Navigation is generated from `docs/README.md` by `hooks/readme_nav.py`: `### <section>` is a section, `- [<title>](<path>.md)` is a page. Order and titles are edited only in `docs/README.md`.
- The build runs in strict mode and fails on: a file not listed in `docs/README.md`, a broken link or anchor, a Markdown construct from the list below.
- Podcast audio: `docs/<section>/audio/<note>.mp3` adds an `<audio>` player under the title of `docs/<section>/<note>.md` (`hooks/audio.py`); an mp3 without a matching note fails the build. Max 25 MiB per file (Workers static assets limit). mp3 requests go through `worker/index.js`, which adds Range support (`206`): static assets answer Range with `200`, and iOS Safari requires `206` for `<audio>`.
- Local preview: `pip install -r requirements.txt`, then `mkdocs serve` (http://127.0.0.1:8000). `mkdocs serve` does not support Range, so audio seeking does not work there; to check audio as deployed: `mkdocs build`, then `npx wrangler dev` (http://127.0.0.1:8787).

## Markdown rules

MkDocs uses Python-Markdown, which parses some constructs differently from GitHub:

- Blank line before a list (a list directly after a text line is merged into the paragraph).
- Nested content of a list item (sub-list, quote, code, continuation text) is indented by 4 spaces.
- Blank line after a closing code fence, including inside a quote (`>` on its own line).

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
