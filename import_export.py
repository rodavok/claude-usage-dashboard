#!/usr/bin/env python3
"""Assemble a claude.ai data export into the flat files the dashboard expects.

Since mid-2026 the export arrives as a manifest plus several zips
(conversations-NNN.zip, projects-000.zip, light_metadata-000.zip) instead of
one flat bundle. The JSON schema inside is unchanged - conversations are just
split across parts, and projects are one file per project.

The manifest's export_urls sit behind a Cloudflare browser challenge and your
claude.ai login, so they cannot be fetched from a script. --fetch opens them in
your default browser instead, waits for the downloads, and moves them here.
Links expire 24 hours after the export is created and may work only once.

Usage:
    python3 import_export.py                 # zips in the current directory
    python3 import_export.py --fetch         # download from the newest manifest-*.json first
    python3 import_export.py --zip-dir DIR --output-dir DIR
"""

import argparse
import glob
import json
import os
import shutil
import tempfile
import time
import webbrowser
import zipfile

# Zips the claude.ai export ships, by category prefix
EXPORT_ZIP_PATTERNS = ('conversations-*.zip', 'projects-*.zip', 'light_metadata-*.zip')


def find_export_zips(zip_dir):
    """Return the claude.ai export zips present in zip_dir, sorted."""
    found = []
    for pattern in EXPORT_ZIP_PATTERNS:
        found.extend(glob.glob(os.path.join(zip_dir, pattern)))
    return sorted(found)


def needs_assembly(zip_dir, output_dir):
    """True if export zips are present and newer than the assembled conversations.json."""
    zips = find_export_zips(zip_dir)
    if not zips:
        return False
    assembled = os.path.join(output_dir, 'conversations.json')
    if not os.path.exists(assembled):
        return True
    return max(os.path.getmtime(z) for z in zips) > os.path.getmtime(assembled)


def assemble(zip_dir='.', output_dir='.', verbose=True):
    """Unpack the export zips in zip_dir into flat JSON files in output_dir.

    Returns the path to the merged conversations.json, or None if no
    conversation parts were found.
    """
    zips = find_export_zips(zip_dir)
    if not zips:
        raise FileNotFoundError(
            f"No claude.ai export zips found in {os.path.abspath(zip_dir)}. "
            "Request an export from claude.ai, download the zips listed in the "
            "manifest-*.json it gives you, and place them here."
        )

    def log(msg):
        if verbose:
            print(msg)

    tmp = tempfile.mkdtemp(prefix='claude_export_')
    try:
        conversations = []
        seen = set()
        for path in zips:
            name = os.path.basename(path)
            dest = os.path.join(tmp, name[:-4])
            with zipfile.ZipFile(path) as zf:
                zf.extractall(dest)

            # conversations-NNN.zip: one conversations.json per part
            part = os.path.join(dest, 'conversations.json')
            if os.path.exists(part):
                with open(part) as f:
                    data = json.load(f)
                for conv in data:
                    if conv.get('uuid') not in seen:
                        seen.add(conv.get('uuid'))
                        conversations.append(conv)
                log(f"{name}: {len(data)} conversations")

            # projects-000.zip: one file per project, recombined into a list
            projects_dir = os.path.join(dest, 'projects')
            if os.path.isdir(projects_dir):
                projects = []
                for pfile in sorted(os.listdir(projects_dir)):
                    with open(os.path.join(projects_dir, pfile)) as f:
                        projects.append(json.load(f))
                _write(output_dir, 'projects.json', projects)
                log(f"{name}: {len(projects)} projects")

            # light_metadata-000.zip: users.json, login_history.json
            for extra in ('users.json', 'login_history.json'):
                src = os.path.join(dest, extra)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(output_dir, extra))
                    log(f"{name}: {extra}")

        if not conversations:
            return None

        conversations.sort(key=lambda c: c.get('created_at', ''))
        out = _write(output_dir, 'conversations.json', conversations)
        messages = sum(len(c.get('chat_messages', [])) for c in conversations)
        log(f"Merged {len(conversations)} conversations, {messages} messages -> {out}")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fetch_from_manifest(zip_dir='.', downloads_dir='~/Downloads', timeout=900):
    """Download the newest manifest's zips through the browser and move them into zip_dir.

    Only the categories assemble() reads are fetched. Zips from an earlier
    export are moved to previous_exports/<their manifest date>/ first.
    Returns the list of zips now in zip_dir.
    """
    manifests = sorted(glob.glob(os.path.join(zip_dir, 'manifest-*.json')), key=os.path.getmtime)
    if not manifests:
        raise FileNotFoundError(f"No manifest-*.json found in {os.path.abspath(zip_dir)}")
    manifest_path = manifests[-1]
    with open(manifest_path) as f:
        manifest = json.load(f)

    wanted = [d for d in manifest['data_files']
              if any(d['filename'].startswith(p.split('*')[0]) for p in EXPORT_ZIP_PATTERNS)]
    print(f"Using {os.path.basename(manifest_path)} ({manifest.get('created_at', '?')})")

    # Zips newer than the manifest came from it already - the links may be spent
    old_zips = find_export_zips(zip_dir)
    if old_zips and min(os.path.getmtime(z) for z in old_zips) >= os.path.getmtime(manifest_path):
        print("The zips here are newer than this manifest, so they were already downloaded "
              "from it. Skipping the download.")
        return old_zips

    # Set aside zips from an older export so the two never mix
    if old_zips:
        old_manifests = manifests[:-1]
        stamp = (os.path.basename(old_manifests[-1]).rsplit('-', 6)[-6:-3] if old_manifests else None)
        backup = os.path.join(zip_dir, 'previous_exports',
                              '-'.join(stamp) if stamp else time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(old_zips[0]))))
        os.makedirs(backup, exist_ok=True)
        for z in old_zips + old_manifests:
            shutil.move(z, os.path.join(backup, os.path.basename(z)))
        print(f"Moved {len(old_zips)} zips from the previous export to {backup}")

    downloads_dir = os.path.expanduser(downloads_dir)
    started = time.time()
    for d in wanted:
        print(f"Opening {d['filename']} in your browser...")
        webbrowser.open(d['export_url'])
        time.sleep(2)  # let the browser start each download before the next tab

    # Browsers set to ask where to save are often pointed at this folder or a
    # subfolder of it, so look there as well as in the downloads dir
    search_dirs = [downloads_dir, zip_dir] + [
        d for d in glob.glob(os.path.join(zip_dir, '*/'))
        if os.path.basename(d.rstrip('/')) not in ('previous_exports', '.git', 'venv')]

    # Firefox writes <name>.part while downloading and may add " (1)" on name clashes
    pending = {d['filename'] for d in wanted}
    deadline = started + timeout
    while pending and time.time() < deadline:
        for name in sorted(pending):
            stem = name[:-4]
            candidates = [c for sd in search_dirs
                          for c in glob.glob(os.path.join(sd, glob.escape(stem) + '*.zip'))
                          if os.path.getmtime(c) >= started - 5
                          and not os.path.exists(c + '.part')
                          and zipfile.is_zipfile(c)]
            if candidates:
                src = max(candidates, key=os.path.getmtime)
                dest = os.path.join(zip_dir, name)
                if os.path.abspath(src) != os.path.abspath(dest):
                    shutil.move(src, dest)
                pending.discard(name)
                print(f"Got {name}")
        if pending:
            time.sleep(2)

    if pending:
        raise TimeoutError(f"Still waiting on {', '.join(sorted(pending))} in {downloads_dir} or this folder. "
                           "Download them from the manifest links and place them here.")
    return find_export_zips(zip_dir)


def _write(output_dir, filename, data):
    path = os.path.join(output_dir, filename)
    with open(path, 'w') as f:
        json.dump(data, f)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--zip-dir', default='.', help='Directory holding the export zips')
    parser.add_argument('--output-dir', default='.', help='Where to write the merged JSON files')
    parser.add_argument('--fetch', action='store_true',
                        help='First download the zips listed in the newest manifest-*.json via your browser')
    parser.add_argument('--downloads-dir', default='~/Downloads',
                        help='Where your browser saves downloads (default: ~/Downloads)')
    args = parser.parse_args()
    if args.fetch:
        fetch_from_manifest(args.zip_dir, args.downloads_dir)
    assemble(args.zip_dir, args.output_dir)


if __name__ == '__main__':
    main()
