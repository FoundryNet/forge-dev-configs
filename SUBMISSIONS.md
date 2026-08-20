# Awesome-list submissions — prepared, not yet sent

Blocked on GitHub auth: the keyring token was revoked, so `gh auth status`
reports *"The token in keyring is invalid."* Forking and opening a PR both need
credentials. Re-auth with `gh auth login` (or a `public_repo`-scoped token) and
these go out.

---

## Target 1 — PatrickJS/awesome-cursorrules (40,615 stars)

The obvious target, and the one worth the most. **A README link alone will be
rejected** — CONTRIBUTING requires a rule file committed into the repo:

> 1. Fork the repository
> 2. Create a descriptive slug (e.g. `react-typescript`)
> 3. Add the `.mdc` rule file under the `rules/` directory
> 4. Include frontmatter with `description`, `globs`, and `alwaysApply`
> 5. Update the main README.md with an entry in the appropriate category

Note it wants **`.mdc`**, not `.cursorrules`. Cursor deprecated the bare
`.cursorrules` file in favour of `.cursor/rules/*.mdc`. We now generate both;
the file to submit is:

    .cursor/rules/foundrynet-industrial-telemetry.mdc

**Submit as:** `rules/foundrynet-industrial-telemetry.mdc`

**README entry** (corrected — see the note on field count below):

```markdown
[FoundryNet Industrial Equipment](https://github.com/FoundryNet/forge-dev-configs) -
Cursor/Windsurf/Copilot rules for industrial equipment telemetry normalization.
366 canonical field names verified against the FoundryNet schema at build time.
MIT licensed.
```

**Caveat on timing:** last push to that repo was 2026-05-30, roughly three
months ago. It has 40k stars and a correspondingly deep PR queue. Expect a long
merge latency, and do not read silence as rejection.

---

## Target 2 — github/awesome-copilot (38,032 stars)

Active (pushed 2026-08-19) and it *does* accept external repositories — but not
as a list link. External entries go through a formal review workflow into
`plugins/external.json`:

> "Public external plugin submissions are GitHub-only in v1. The submitted
> plugin must live in a public GitHub repository."

Required metadata: `name`, `description`, `version`, `author.name`,
`repository`, `keywords`, `source` — with `source.source: "github"` and
`source.repo` in `owner/repo` form, pinned to an immutable commit SHA or
release tag.

**Action needed before submitting:** cut a `v1.0.0` release tag on
forge-dev-configs so there is an immutable reference to point at. Do not submit
against a moving `main`.

---

## Target 3 — jamesmurdza/awesome-ai-devtools (3,917 stars)

Active, general AI-devtools list, accepts straightforward README link entries.
Lowest effort of the three. Same corrected entry text as Target 1.

---

## Not submitting

- **SchneiderSam/awesome-windsurfrules** — 68 stars, below the >100 bar, issues
  disabled, last pushed 2025-01-10. Effectively unmaintained.
- **awesome-windsurf / awesome-ai-coding** — no repository exists at those
  names. Nothing to submit to.

---

## Correction: 366, not 408

The drafted entry said *"408 canonical fields."* That number is wrong **for this
repository** and would contradict the repo's own README on the first click.

| Number | What it actually counts |
|---:|---|
| **366** | the published canonical schema — what forge-dev-configs is built from, and what `.cursorrules` and the README both state |
| 408 | the **forge-sandbox** dictionary: the 366 published fields plus 42 the sandbox declares itself for additive and building-automation coverage |

408 belongs to a different artifact. `366` is the defensible number here, and
"verified against the schema at build time" is the stronger claim anyway —
it is the thing no other entry on that list can say.
