# portfolio-website

Pontsho Mbizo's portfolio — Home, Resume, Projects and a page per project.
Single self-contained `index.html` (vanilla HTML/CSS/JS, no build step, no
dependencies) built from a [Claude Design](https://claude.ai/design) canvas.
Pages are hash routes: `#/`, `#/resume`, `#/projects`, `#/projects/<id>`.

Live at [pontsho-mbizo.co.za](https://pontsho-mbizo.co.za) — self-hosted on
the same Oracle VM as
[fpgasim](https://github.com/PontshoMbizo/fpgasim) and
[mcusim](https://github.com/PontshoMbizo/mcusim), which this
portfolio links out to (see the fpgasim / mcusim project entries).

## Structure

- `index.html` — the site itself. One file, everything inlined; fetches
  `content.json` at load for its data.
- `content.json` — projects, resume, contact info. Git is the
  source of truth: every deploy overwrites the live copy on the VM with
  whatever is in the repo (see "Editing content" below).
- `deploy.sh` — runs on the VM (via the CI/CD pipeline below): pulls latest,
  copies `index.html`, `cv.pdf`, `content.json`, `favico.png` and `images/`
  into nginx's serving root, health-checks.
- `.github/workflows/ci.yml` — validates the embedded JS and `content.json`
  parse cleanly, on every push/PR.
- `.github/workflows/deploy.yml` — on push to `main`, SSHes into the VM with a
  restricted deploy key (can only run `deploy.sh`, nothing else) and redeploys.

## Local development

It's a static file, but it fetches `content.json`, so serve the folder rather
than opening `index.html` directly (browsers block that fetch over `file://`):

```bash
python3 -m http.server 8000
```

## Deploying

Push to `main`. That's it — the GitHub Actions workflow handles the rest.
Requires these repo secrets (Settings → Secrets and variables → Actions),
shared with the fpgasim/mcusim repos' deploy keys:

- `DEPLOY_HOST` — the VM's IP
- `DEPLOY_USER` — `ubuntu`
- `DEPLOY_SSH_KEY` — the restricted `gha_deploy` private key (same one used by
  fpgasim/mcusim's deploy workflows)

## Editing content

Projects, the resume and contact info live in `content.json`, which
`index.html` fetches at load. Edit `content.json` and push. CI validates
it's well-formed JSON; the next deploy overwrites the live file with this
version. (`posts` and `skills` are still in there from the old site but
aren't shown anywhere.)

The home page copy is in `index.html` itself, and so are the default contact
links, so Home still renders if `content.json` fails to load; Resume and
Projects show a notice instead.

**Projects** appear on the Projects page in array order, alternating between
the two staggered columns. Each one gets its own page at `#/projects/<id>`.
Fields:

- `id`, `name`, `blurb` (the line on its tile), `label` (shown on the tile
  until it has an image), `full`, `year`, `tags`, `links`
- `desc` + `highlights` — rendered as "Overview." and "Highlights.", or
  `sections: [{ "title", "body": [paragraphs] }]` for custom headings
- `facts: [{ "label", "value" }]` — extra rows in the grey sidebar (Role,
  Course, Team…); `year` and `tags` are added automatically
- `subtitle` — the line under the title in the hero (defaults to the part of
  `full` after the dash)

**Photos**: put files in `images/` and reference them by path, e.g.
`"image": "images/khula.jpg"`. Supported: a project's `image` (tile + hero),
a project's `gallery: [{ "src", "alt" }]` (scrolling strip), top-level
`portrait` (home page; defaults to `images/profile_picture.jpeg`), and `resume.photos: [{ "src", "alt" }]` (grid beside
the resume, hidden while empty).
