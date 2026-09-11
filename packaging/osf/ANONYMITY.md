# Anonymity rules for this zip

This artifact is intended for dual-anonymous NeurIPS review.

## Must remain absent until camera-ready

- Author names, emails, affiliations, acknowledgements of named people
- Personal GitHub remotes and `github.com/CapitalUsername` links
- Zenodo (or similar) DOI badges
- Absolute home-directory paths (`/Users/…`, `/home/…`, `C:\Users\…`)
- A `.git` directory (author, email, remotes)

## Allowed

- Third-person citations of **other** groups (AIDev, AgenticFlict, SWE-bench, …)
- Third-person citation of the prior measurement study with the author list **omitted** in this zip (`Anonymous` in the bibliography; the public title is unchanged)
- GitHub **API** URLs as code (`https://api.github.com/repos/{repo}/…`) and clone URLs built from repository slugs in the data
- `Anonymous` / `Anonymous Authors` author blocks

## Checks

```bash
make audit
```

The audit greps for path leaks, `mailto:`, Zenodo badges, and personal GitHub URLs. It deliberately does not list surnames: shipping a surname as a search pattern would encode identity in the artifact.
