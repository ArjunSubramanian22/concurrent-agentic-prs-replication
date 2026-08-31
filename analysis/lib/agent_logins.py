"""Frozen extra agent logins. The snapshot `user` column is the primary set."""
from __future__ import annotations

# Logins that are agents even if they somehow miss the AIDev-pop user column.
# Keep this list small and explicit. Adding a login after pre-registration is a
# deviation and must be logged in ANALYSIS_PLAN.md §12.
EXTRA_AGENT_LOGINS = frozenset(
    {
        "copilot",
        "github-copilot[bot]",
        "devin-ai-integration[bot]",
        "google-labs-jules[bot]",
        "google-labs-jules",
        "chatgpt-codex-connector[bot]",
        "cursor[bot]",
        "claude[bot]",
        "claude-code[bot]",
    }
)

# Non-agent bots. A PR from these logins is neither human nor agent; it is
# author_unknown (exclusion rule 7) unless the login is also an AIDev agent.
NON_AGENT_BOT_LOGINS = frozenset(
    {
        "dependabot[bot]",
        "renovate[bot]",
        "greenkeeper[bot]",
        "pre-commit-ci[bot]",
        "github-actions[bot]",
        "imgbot[bot]",
        "allcontributors[bot]",
        "semantic-release-bot",
        "snyk-bot",
        "codecov[bot]",
        "netlify[bot]",
        "vercel[bot]",
        "whitesource-bolt[bot]",
        "mergify[bot]",
        "sonarcloud[bot]",
        "deepsource-autofix[bot]",
    }
)
