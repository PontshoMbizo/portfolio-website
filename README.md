# portfolio-website

Pontsho Mbizo's portfolio — "pontshoOS", a personal portfolio presented as a
desktop OS. Single self-contained `index.html` (vanilla HTML/CSS/JS, no build
step, no dependencies) rebuilt from a [Claude Design](https://claude.ai/design)
handoff.

Live at [pontsho-mbizo.co.za](https://pontsho-mbizo.co.za) — self-hosted on
the same Oracle VM as
[nikaVSimulator](https://github.com/PontshoMbizo/nikaVSimulator) and
[stmVSimulator](https://github.com/PontshoMbizo/stmVSimulator), which this
portfolio links out to (see the nikaVSimulator / STM Simulator project entries).

## Structure

- `index.html` — the site itself. One file, everything inlined; fetches
  `content.json` at load for its data.
- `content.json` — projects, blog posts, skills, contact info. Git is the
  source of truth: every deploy overwrites the live copy on the VM with
  whatever is in the repo (see "Editing content" below).
- `admin/` — the `/admin/` content-editing panel (static UI + a small Python
  stdlib-only backend). See `admin/README.md` for what it is and one-time VM
  setup.
- `deploy.sh` — runs on the VM (via the CI/CD pipeline below): pulls latest,
  copies `index.html`, `cv.pdf`, `content.json` and the admin UI into
  nginx's serving root, restarts the admin backend, health-checks.
- `.github/workflows/ci.yml` — validates the embedded JS and `content.json`
  parse cleanly, and that `admin/server.py` compiles, on every push/PR.
- `.github/workflows/deploy.yml` — on push to `main`, SSHes into the VM with a
  restricted deploy key (can only run `deploy.sh`, nothing else) and redeploys.

## Local development

It's a static file — just open `index.html` in a browser, or serve it:

```bash
python3 -m http.server 8000
```

## Deploying

Push to `main`. That's it — the GitHub Actions workflow handles the rest.
Requires these repo secrets (Settings → Secrets and variables → Actions),
shared with the nikaVSimulator/stmVSimulator repos' deploy keys:

- `DEPLOY_HOST` — the VM's IP
- `DEPLOY_USER` — `ubuntu`
- `DEPLOY_SSH_KEY` — the restricted `gha_deploy` private key (same one used by
  nikaVSimulator/stmVSimulator's deploy workflows)

## Editing content

Projects, blog posts, skills and contact info live in `content.json`, which
`index.html` fetches at load. Two ways to edit it:

- **Directly**: edit `content.json` and push. CI validates it's well-formed
  JSON; the next deploy overwrites the live file with this version. This is
  the durable way to make a content change — it survives future deploys.
- **`/admin/` panel** (once set up on the VM — see `admin/README.md`): a
  browser UI for adding/editing projects and posts, no git push needed. Handy
  for a quick fix or trying something out, but **the next `git push` to
  `main` overwrites whatever you saved there** with whatever's in the repo —
  copy any edit you want to keep back into `content.json` and commit it.

`index.html` also keeps the same data hardcoded as a fallback (used only if
`content.json` fails to fetch), so the site still renders even if that file
is ever missing or unreachable.

New projects also need one manual step if you want them in the dock (the
bottom bar): add the project's `id` to the `dockIds` array in `index.html`.
Everything else — Activities search, the Files → Projects folder, its own
window — works automatically for any project in `content.json`.
