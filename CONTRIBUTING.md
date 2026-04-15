# Contributing

## Principles

- Keep changes small and reviewable.
- Use test-driven development for behavioral changes and bug fixes.
- Prefer evidence-backed decisions over intuition.
- Keep automation explainable and replayable.

## Development workflow

1. Run `scripts/bootstrap-dev.sh`.
2. Create a branch from `main`.
3. Write or update a failing test first for behavior changes.
4. Implement the smallest coherent change that makes the test pass.
5. Run `trunk check --all`, `uv run pytest`, and `uv run mypy`.
6. Commit in atomic units using Conventional Commits.

## Commit style

Commit messages must follow Conventional Commits:

```text
type(scope): short imperative summary
```

Examples:

- `chore(repo): add trunk and pre-commit baseline`
- `feat(planner): detect object store spill risk`
- `fix(cli): handle missing cluster inventory`

Keep commits isolated:

- one coherent intent per commit
- include tests with the code they validate
- avoid mixing refactors, behavior changes, and docs churn unless they are
  inseparable

## Quality gates

- `pre-commit` runs `trunk check`
- `commit-msg` runs `commitlint`
- CI runs hooks, tests, docs build, and type checks

## Style guides

- Python: PEP 8, PEP 257, PEP 484
- Docs: Microsoft Writing Style Guide
- APIs: OpenAPI 3.1 with Spectral checks
- YAML, TOML, shell, and Markdown formatting are enforced through Trunk

## Sign-off

Use Developer Certificate of Origin sign-off on commits:

```text
git commit -s
```

