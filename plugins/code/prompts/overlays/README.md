# Prompt Overlays

Append-only amendments layered onto `plugins/code/prompts/prompt.md` (the
SSOT orchestrator prompt) at runtime. This directory exists so variants of
the base prompt do not require duplicating 500+ lines of identical
orchestration text.

## Why overlays exist

Before overlays, `prompt.md` and `prompt-multi-repo.md` were 99% identical
540-line files. The multi-repo variant added three small inserts (one
sentence each to the `pre-explorer` and `plan-draft-writer` launch prompts
and a NOTE block in Phase 1.4). Every edit to the base had to be mirrored
by hand and every missed mirror was a production bug in the orchestrator.

Overlays fix that by keeping `prompt.md` as the single source of truth and
expressing each variant as a small trailing amendment file.

## How assembly works

`plugins/code/scripts/setup-closedloop.sh` resolves `--prompt <name>` in
this order:

1. If `prompts/<name>.md` exists, use it directly (backward compatible).
2. Else if `prompts/overlays/<name>.overlay.md` exists, assemble
   `prompts/prompt.md` + blank line + overlay into
   `$CLOSEDLOOP_WORKDIR/.closedloop/prompt-assembled.md` and point
   `CLOSEDLOOP_PROMPT_FILE` at that file.
3. Else, fail loud with "prompt not found".

The assembler is dumb concatenation — no frontmatter, no anchors, no
templating. If the overlay file exists, its bytes are appended verbatim.

Default behavior (`--prompt prompt`) is byte-identical to today: the base
is used directly with no overlay involved.

## When to use an overlay

If your variant only **adds** instructions that can be framed as
amendments to earlier phases, write an overlay. If you need to **change**
or **remove** base content, do not use an overlay — have a conversation
about forking or refactoring the base instead.

## Authoring rules (enforced by review, not code)

- **Append-only.** Overlays never restate or contradict base lines. State
  the amendment positively.
- **Name the phase(s) amended.** Each sub-section heading references the
  phase it modifies so a reader of the assembled prompt can
  cross-reference.
- **Frame as authoritative amendments.** Use language like "take
  precedence over the base instructions for those phases when their
  trigger conditions are met" — LLMs honor late instructions better when
  framed as explicit errata.
- **One overlay per run.** Overlays do not reference or compose with
  other overlays.
- **Plain markdown only.** No frontmatter, no directives, no parsing.

## Authoring workflow

1. Draft `overlays/<name>.overlay.md`.
2. Run `cat plugins/code/prompts/prompt.md plugins/code/prompts/overlays/<name>.overlay.md > /tmp/assembled.md`
   and read the result end-to-end to verify the orchestrator will
   understand the amendments in context.
3. If replacing a hand-maintained variant, compare behaviorally: every
   rule in the old variant must be present in the new assembled output.
   Byte equality is not required.
4. Delete the hand-maintained variant in the same commit.

## Runtime contract — multi-repo overlay

The `multi-repo.overlay.md` overlay depends on env vars exported by
`setup-closedloop.sh` when `--add-dir` is passed to `run-loop.sh`:

- `CLOSEDLOOP_REPO_MAP` — pipe-separated `name=path` pairs of additional
  repositories.
- `CLOSEDLOOP_ADD_DIRS` — pipe-separated absolute paths of local peer
  repos.
- `CLOSEDLOOP_ADD_DIR_NAMES` — pipe-separated names matching
  `CLOSEDLOOP_ADD_DIRS` by index.

The overlay introduces the `@{repo-name}:path` file-reference convention
for secondary repos (primary-repo files need no prefix).

`run-loop.sh --add-dir` auto-selects `--prompt multi-repo` when the user
does not pass `--prompt` explicitly.

## Debugging

- Inspect the assembled file at
  `$CLOSEDLOOP_WORKDIR/.closedloop/prompt-assembled.md` after a run
  starts.
- To bypass the overlay, pass `--prompt prompt` — the base is used
  unchanged.
- If you see `ERROR: Prompt 'X' not found (no prompts/X.md, no
  prompts/overlays/X.overlay.md)`, the name you passed matches neither a
  direct base file nor an overlay.
