# portfolio-website

Pontsho Mbizo's portfolio — "pontshoOS", a personal portfolio presented as a
desktop OS. Single self-contained `index.html` (vanilla HTML/CSS/JS, no build
step, no dependencies) rebuilt from a [Claude Design](https://claude.ai/design)
handoff.

Live at `pontsho-mbizo.com` (currently `84.8.139.133.nip.io` until the domain's
DNS is live) — self-hosted on the same Oracle VM as
[nikaVSimulator](https://github.com/PontshoMbizo/nikaVSimulator) and
[stmVSimulator](https://github.com/PontshoMbizo/stmVSimulator), which this
portfolio links out to (see the nikaVSimulator / STM Simulator project entries).

## Structure

- `index.html` — the entire site. One file, everything inlined.
- `deploy.sh` — runs on the VM (via the CI/CD pipeline below): pulls latest,
  copies `index.html` into nginx's serving root, health-checks.
- `.github/workflows/ci.yml` — validates the embedded JS parses cleanly on
  every push/PR.
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

Everything — projects, blog posts, skills, contact info — lives as plain JS
data objects near the top of the `<script>` block in `index.html` (`projects`,
`posts`, `skills`, `CONTACT`). Edit those, push, done.
