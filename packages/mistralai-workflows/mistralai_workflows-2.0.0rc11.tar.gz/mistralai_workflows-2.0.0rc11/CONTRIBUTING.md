# Contributing to Workflows SDK

Everyone is more than welcome to contribute to the Workflows SDK and Abraxas service.
This guide helps ensure your contributions land smoothly and quickly.

## Before You Start

Before writing code, please:

1. **Open a Linear ticket** in [WFL Triage](https://linear.app/mistral-ai/team/WFL/triage)
2. **Ping us on Slack** in `#eng-workflows-backroom` to discuss scope

This helps us align on approach early and avoids wasted effort 🙏

## Development Setup

See [the API README.md](../abraxas/README.md) for full setup details.

For creating plugins (and associated IDE setup), see [plugins/CONTRIBUTING.md](./plugins/CONTRIBUTING.md).

## Commit Guidelines

Commit messages matter. Here's how to write them well: https://cbea.ms/git-commit/

- **Atomic commits** — One logical change per commit
- **Why/What** - Don't describe the how, but explains what changed, and most of all, why
- **Imperative mood** — "Add feature" not "Added feature"
- **Clean history** — Squash fixup commits before requesting review

A clean history makes it easier to review changes and understand the intent behind them.

## Pull Request Guidelines

You SHOULD open your PR as a draft by default.
This signals it's still a work in progress and lets you verify that the CI
passes before requesting reviews, and do a quick self-review first.

Fill out the [PR template](/.github/PULL_REQUEST_TEMPLATE.md) completely:

| Section            | What to include                                 |
|--------------------|-------------------------------------------------|
| **Context**        | Why this change matters. Link to Linear ticket. |
| **Implementation** | Key design decisions and trade-offs.            |
| **Checks/QA**      | How you tested the changes.                     |

Keep PRs focused — one feature or fix per PR.
Large PRs are harder to review and take longer to merge.
If you're working on a large feature, consider splitting it into smaller PRs.

⚠️ **When merging, make sure your squashed commit message retain all the relevant information
of your commit history**

### Code Quality Checklist

Before marking your PR as ready for review, ensure all of the following pass:

- [ ] CI passes
- [ ] Tests added for new functionality
- [ ] Docstrings updated if public API changed
- [ ] [Internal documentation](../abraxas/docs) is updated if necessary

### What We Look For

We want to **merge your contribution ASAP**. To make that happen, help us review quickly by:

- **Clear justification** — Why is this change needed? Why now?
- **Context upfront** — Link to Linear ticket, explain the problem being solved
- **Minimal scope** — One focused change, no unrelated modifications
- Tests covering new functionality
- Clean, readable code following existing patterns
  💡: The better you explain the "why" in your PR description, the faster we can approve.

### During review

**Reviewer**

- Follow this guide when leaving review comments: https://google.github.io/eng-practices/review/reviewer/comments.html#label-comment-severity
- If a conversation takes too long to resolve, don't hesitate to take it IRL **and** write a summary in the PR for posterity
- Initial review should happen in less than 24h (excluding week-ends and holidays), make sure to check for pending reviews frequently.

**Author**

- Avoid force-pushing (`git push --force`) once your commit is under review. Force-pushing rewrites history and breaks reviewers' context, making it difficult to see what changed since their last review.
- Address comments by linking to a fixup commit or a subsequent commit solving precisely that comment
- Let the comment author resolve, unless it's a clear nitpick or optional comment in which case it's ok for the PR author to resolve.
- Make sure all the conversations have been addressed before merging. After addressing a reviewer's comment, you should re-request a review from them.
- It is your responsibility to make sure you get reviews, so it's totally ok to ping reviewers reminding them to review the PR

## Writing Tests

We use pytest with async support. Tests live in `workflow_sdk/tests/`.

**Unit Tests** (most common):

- Test workflow and activity definitions
- Use `temporal_env` fixture for fast, isolated execution (in-memory Temporal with time-skipping)
- Mark async tests with `@pytest.mark.asyncio`
- Run specific tests: `uv run invoke tests -k "test_name"`

**Integration Tests**:

- Test end-to-end workflows against staging/production
- Live in `workflow_sdk/tests/integration/`
- Mark with `@pytest.mark.integration`
- Require `MISTRAL_API_KEY` and `WORKFLOWS_URL` env vars

**Guidelines**:

- Focus on high-ROI tests covering real behavior
- Keep tests simple — if they're complex, reconsider the design

## Questions?

Reach out in `#eng-workflows-backroom` — we're happy to help!
