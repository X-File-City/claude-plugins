## Multi-Repo Amendments

The following amendments apply to specific phases defined earlier in this
prompt. They take precedence over the base instructions for those phases
when their trigger conditions are met. Apply them every iteration — they
are not optional.

### Amendment to Phase 0 (pre-exploration)

When launching `@code:pre-explorer`, append to its launch prompt:

> Additional repos context: if `CLOSEDLOOP_REPO_MAP` is set, it contains
> `name=path` pairs (pipe-separated) of additional repositories. For each
> `name=path` pair, explore that repository at the given path and write a
> `code-map-{name}.json` to `$CLOSEDLOOP_WORKDIR` capturing its structure,
> key files, and relevant patterns.

### Amendment to Phase 1 (plan drafting)

When launching `@code:plan-draft-writer`, append to its launch prompt:

> Additional repos context: if `CLOSEDLOOP_REPO_MAP` is set, it contains
> `name=path` pairs (pipe-separated) of additional repositories available
> for reference. When referencing files in secondary repos, use the
> `@{repo-name}:path` prefix convention (e.g.,
> `@my-lib:src/utils/helper.ts`). Files in the primary repo need no prefix
> — use their paths directly.

### Amendment to Phase 1.4 (cross-repo coordination)

> **NOTE (multi-repo):** Repos supplied via `--add-dir` are local and
> their tasks already belong in the primary plan. If `CLOSEDLOOP_ADD_DIRS`
> is set, it contains the paths of those local repos. When the
> cross-repo-coordinator identifies a peer whose path appears in
> `CLOSEDLOOP_ADD_DIRS`, treat that peer as `local=true` and ensure its
> tasks are placed directly in the plan (not in a separate cross-repo
> PRD). Do not generate a PRD for local peers — their work is part of
> this plan.
