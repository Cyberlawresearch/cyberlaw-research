# Paper draft handoff

This file defines the private handoff format for the daily paper column. It is used only on the `paper-drafts` branch and must never be treated as a public publication.

For each date `YYYY-MM-DD`, save exactly two handoff files in one atomic commit:

- `.github/editions/YYYY-MM-DD.paper.json` — small metadata/status manifest.
- `.github/editions/YYYY-MM-DD.paper.html` — the complete publication-ready article HTML.

The JSON manifest must include at least:

- `date`, `column: "paper"`
- `phase: "handoff"`
- `content_status: "content_complete"` only after the HTML and JSON have both been committed and read back successfully
- `base_main_sha`
- `page` (recommended final main path)
- verified structured bibliography
- source URLs
- homepage card text, papers-list text, archive text
- related-reading paths and timeline decision
- checks actually performed
- `draft_html_path` pointing to the matching HTML file

The research task must not report completion until it fetches both files back from `paper-drafts` and confirms that the manifest says `content_complete` and the HTML contains the expected title and full article body.

The publishing task must not conduct new research. It reads these two files, re-reads the latest `main`, applies only the paper-column changes, and publishes from the latest main without force-push.

If a handoff write fails, record the actual error when possible and report the handoff as incomplete. Do not claim that a draft exists when readback fails.
