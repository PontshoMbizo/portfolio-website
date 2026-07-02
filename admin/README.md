# pontshoOS admin

A small in-browser panel at `/admin/` for editing blog posts and projects
without hand-editing JSON or JS, and without needing a git push for every
content change.

## How it fits together

- `content.json` (repo root) is the seed/default content, and doubles as the
  live data file on the server once deployed — the admin panel reads and
  writes it directly.
- `index.html` fetches `content.json` at load and uses it in place of its
  built-in defaults. If the fetch fails for any reason, it silently falls
  back to the defaults baked into the page, so the site never breaks.
- `admin/index.html` is the editor UI — vanilla JS, no build step, no deps.
  It loads `/content.json` and POSTs the whole document back to
  `/admin/api/save` on save.
- `admin/server.py` is a tiny Python **stdlib-only** backend. Its only job is
  to validate the posted JSON (required fields, safe id/color formats, link
  URLs must be http(s)) and atomically rewrite `content.json`, keeping one
  `.bak` copy of the previous version.
- **Authentication is handled entirely by nginx** (`auth_basic`), not by
  `server.py`. The backend has no login code and trusts that anything
  reaching it already passed nginx's auth check — which is also why it binds
  to `127.0.0.1` only and must never be exposed directly.
- `deploy.sh` seeds `content.json` on the VM only if it doesn't already
  exist, so `git reset --hard` on every deploy never clobbers content you've
  edited live through the admin panel.

## One-time setup on the VM

This part can't be done from here — it needs to happen on the Oracle VM
directly (SSH in as `ubuntu`, or however you normally reach it).

1. **Password file for nginx basic auth:**
   ```bash
   sudo apt-get install -y apache2-utils   # provides htpasswd, if missing
   sudo htpasswd -c /etc/nginx/.htpasswd_pontsho_admin pontsho
   ```

2. **nginx config** — add the two `location` blocks from
   `admin/nginx-admin.conf.example` into the existing `server {}` block for
   pontsho-mbizo.com (find it under `/etc/nginx/sites-enabled/` or similar),
   then:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```
   Only actually use `/admin` once the site is served over HTTPS — basic
   auth sends the password base64-encoded, not encrypted, on every request.
   If TLS isn't set up yet, get certbot running first.

3. **Admin backend as a systemd user service:**
   ```bash
   mkdir -p ~/.config/systemd/user
   cp ~/apps/portfolio-website/admin/pontsho-admin.service ~/.config/systemd/user/
   loginctl enable-linger ubuntu   # keeps it running without an active login session
   systemctl --user daemon-reload
   systemctl --user enable --now pontsho-admin.service
   systemctl --user status pontsho-admin.service   # should say active (running)
   ```

4. **Push to `main`.** The next deploy will seed `content.json` into
   `/var/www/pontsho-mbizo/content.json` and restart the admin backend
   automatically (deploy.sh checks whether the service is enabled first, so
   it's a no-op if you haven't done step 3 yet).

5. Visit `https://pontsho-mbizo.com/admin/` (or the nip.io host over https
   once that's live), log in with the basic-auth prompt, and edit away.

## Day to day

Once set up, no git/terminal needed for content changes — open `/admin/`,
edit projects or posts, click **Save all changes**. It writes straight to
`content.json` on the VM and the live site picks it up on next page load.

Git pushes are still how you ship changes to the *site itself* (index.html,
the admin UI, or server.py) — those still go through the normal CI/CD
pipeline. Content and code are deliberately on separate tracks now.

## Recovering from a bad edit

`server.py` keeps one rolling backup: `/var/www/pontsho-mbizo/content.json.bak`
is the version before your most recent save. To roll back:
```bash
cp /var/www/pontsho-mbizo/content.json.bak /var/www/pontsho-mbizo/content.json
```
