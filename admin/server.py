#!/usr/bin/env python3
"""pontshoOS admin backend — accepts authenticated writes to content.json.

Trust boundary: this process does NOT implement authentication itself.
It must only ever be reached through the nginx location that applies
`auth_basic` (see nginx-admin.conf.example) and must bind to loopback
only (BIND=127.0.0.1, the default) so it is unreachable directly from
the internet. If you run this anywhere that isn't behind that nginx
location, anyone who can reach it can overwrite the site's content.

Stdlib only — no pip install needed on the VM.
"""
import json
import os
import re
import shutil
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTENT_PATH = os.environ.get('CONTENT_PATH', os.path.join(os.path.dirname(__file__), '..', 'content.json'))
BIND = os.environ.get('BIND', '127.0.0.1')
PORT = int(os.environ.get('PORT', '8787'))
MAX_BODY_BYTES = 2_000_000  # 2MB — content.json is a few KB; this is a generous ceiling

ID_RE = re.compile(r'^[a-z0-9-]{1,64}$')
HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{3,8}$')
LABEL_RE = re.compile(r'^.{1,4}$', re.S)


def err(msg):
    return (False, msg)


def is_str_list(v, max_items=40, max_len=6000):
    if not isinstance(v, list) or len(v) > max_items:
        return False
    return all(isinstance(x, str) and 0 < len(x) <= max_len for x in v)


def validate_project(p, seen_ids):
    if not isinstance(p, dict):
        return err('project entries must be objects')
    for field in ('id', 'name', 'full', 'year', 'color', 'label'):
        if not isinstance(p.get(field), str) or not p[field]:
            return err('project missing/invalid field: ' + field)
    if not ID_RE.match(p['id']):
        return err('project id must be lowercase letters/digits/hyphens: ' + p['id'])
    if p['id'] in seen_ids:
        return err('duplicate project id: ' + p['id'])
    seen_ids.add(p['id'])
    if not HEX_COLOR_RE.match(p['color']):
        return err('project color must be a hex color, e.g. #e8863c (got: ' + p['color'] + ')')
    if not LABEL_RE.match(p['label']):
        return err('project label must be 1-4 characters: ' + p['id'])
    if len(p['name']) > 80 or len(p['full']) > 160 or len(p['year']) > 20:
        return err('project text field too long: ' + p['id'])
    icon = p.get('icon')
    if icon:
        if not isinstance(icon, str) or not (icon.startswith('http://') or icon.startswith('https://')):
            return err('project icon must be empty or a URL starting with http:// or https://: ' + p['id'])
        if len(icon) > 2000:
            return err('project icon url too long: ' + p['id'])
    if not is_str_list(p.get('tags', []), max_items=12, max_len=40):
        return err('project tags must be a list of short strings: ' + p['id'])
    if not is_str_list(p.get('desc', []), max_items=10):
        return err('project desc must be a non-empty list of strings: ' + p['id'])
    if len(p.get('desc', [])) == 0:
        return err('project desc must have at least one paragraph: ' + p['id'])
    if not is_str_list(p.get('highlights', []), max_items=12, max_len=300):
        return err('project highlights must be a list of strings: ' + p['id'])
    links = p.get('links', [])
    if not isinstance(links, list) or len(links) > 8:
        return err('project links must be a list (max 8): ' + p['id'])
    for lk in links:
        if not isinstance(lk, dict):
            return err('project link entries must be objects: ' + p['id'])
        label, url = lk.get('label'), lk.get('url')
        if not isinstance(label, str) or not (0 < len(label) <= 60):
            return err('project link label invalid: ' + p['id'])
        if not isinstance(url, str) or not (url.startswith('http://') or url.startswith('https://')):
            return err('project link url must start with http:// or https://: ' + p['id'])
        if len(url) > 2000:
            return err('project link url too long: ' + p['id'])
    return (True, None)


def validate_post(post):
    if not isinstance(post, dict):
        return err('post entries must be objects')
    for field in ('title', 'date', 'tag'):
        if not isinstance(post.get(field), str) or not post[field]:
            return err('post missing/invalid field: ' + field)
    if len(post['title']) > 200 or len(post['date']) > 30 or len(post['tag']) > 30:
        return err('post text field too long: ' + post['title'][:40])
    if not is_str_list(post.get('pars', []), max_items=30):
        return err('post pars must be a non-empty list of strings: ' + post['title'])
    if len(post.get('pars', [])) == 0:
        return err('post must have at least one paragraph: ' + post['title'])
    return (True, None)


def validate_content(data):
    if not isinstance(data, dict):
        return err('body must be a JSON object')
    for key in ('projects', 'posts', 'skills', 'contact'):
        if key not in data:
            return err('missing top-level key: ' + key)

    projects = data['projects']
    if not isinstance(projects, list) or len(projects) > 100:
        return err('projects must be a list (max 100)')
    seen_ids = set()
    for p in projects:
        ok, msg = validate_project(p, seen_ids)
        if not ok:
            return err(msg)

    posts = data['posts']
    if not isinstance(posts, list) or len(posts) > 500:
        return err('posts must be a list (max 500)')
    for post in posts:
        ok, msg = validate_post(post)
        if not ok:
            return err(msg)

    if not is_str_list(data['skills'], max_items=40, max_len=60):
        return err('skills must be a list of short strings')

    contact = data['contact']
    if not isinstance(contact, dict):
        return err('contact must be an object')
    for field in ('email', 'github', 'linkedin'):
        if not isinstance(contact.get(field), str) or len(contact[field]) > 200:
            return err('contact missing/invalid field: ' + field)

    return (True, None)


def write_content_atomic(data):
    final_path = os.path.abspath(CONTENT_PATH)
    tmp_path = final_path + '.tmp'
    bak_path = final_path + '.bak'
    if os.path.exists(final_path):
        shutil.copyfile(final_path, bak_path)
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp_path, final_path)


class Handler(BaseHTTPRequestHandler):
    server_version = 'pontshoOS-admin/1.0'

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - - [%s] %s\n' % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/healthz':
            self._send_json(200, {'ok': True})
            return
        self._send_json(404, {'ok': False, 'error': 'not found'})

    def do_POST(self):
        if self.path != '/save':
            self._send_json(404, {'ok': False, 'error': 'not found'})
            return

        length = int(self.headers.get('Content-Length', '0') or '0')
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {'ok': False, 'error': 'body missing or too large'})
            return

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._send_json(400, {'ok': False, 'error': 'invalid JSON: ' + str(e)})
            return

        ok, msg = validate_content(data)
        if not ok:
            self._send_json(400, {'ok': False, 'error': msg})
            return

        try:
            write_content_atomic(data)
        except OSError as e:
            self._send_json(500, {'ok': False, 'error': 'write failed: ' + str(e)})
            return

        print('%s content.json saved by %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), self.client_address[0]))
        self._send_json(200, {'ok': True})


def main():
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    print('pontshoOS admin backend listening on %s:%d, writing %s' % (BIND, PORT, os.path.abspath(CONTENT_PATH)))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
