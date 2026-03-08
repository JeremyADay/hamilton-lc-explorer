#!/usr/bin/env python3
"""
Hamilton LC Tool - Launcher
---------------------------
- Asks whether you want Explorer (1 file) or Audit (2 files)
- Opens a native Mac file picker for each .mdb file
- Converts each .mdb to .db in the same directory as the source file
- Starts a local web server from the tool directory
- Opens the browser automatically with the correct files pre-loaded
"""

import os
import sys
import csv
import io
import sqlite3
import subprocess
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ── LOCATE THE TOOL HTML ──────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE  = os.path.join(SCRIPT_DIR, 'hamilton_lc_v2.html')

if not os.path.exists(HTML_FILE):
    print(f"\nERROR: Cannot find hamilton_lc_v2.html in:\n  {SCRIPT_DIR}")
    print("Make sure launch.py and hamilton_lc_v2.html are in the same folder.")
    input("\nPress Enter to exit.")
    sys.exit(1)

# ── CHECK MDBTOOLS ────────────────────────────────────────────────────────────
def check_mdbtools():
    result = subprocess.run(['which', 'mdb-export'], capture_output=True)
    if result.returncode != 0:
        print("\nERROR: mdb-export not found.")
        print("Install mdbtools via Homebrew:  brew install mdbtools")
        input("\nPress Enter to exit.")
        sys.exit(1)

# ── NATIVE FILE PICKER (Mac) ──────────────────────────────────────────────────
def pick_file(prompt_message):
    script = f'''
    tell application "System Events"
        activate
    end tell
    tell application "Finder"
        activate
    end tell
    set f to choose file with prompt "{prompt_message}" of type {{"mdb", "MDB"}}
    return POSIX path of f
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip()

# ── MDB TO SQLITE CONVERSION ──────────────────────────────────────────────────
def convert_mdb(mdb_path):
    db_path = os.path.splitext(mdb_path)[0] + '.db'
    print(f"\n  Converting: {os.path.basename(mdb_path)}")
    print(f"  Output:     {os.path.basename(db_path)}")

    # Export via mdbtools
    result = subprocess.run(
        ['mdb-export', mdb_path, 'LiquidClass'],
        capture_output=True
    )
    if not result.stdout:
        print(f"  ERROR: mdb-export returned no data from {mdb_path}")
        return None

    # Decode with latin-1 to handle µ symbols
    data = result.stdout.decode('latin-1')
    reader = csv.DictReader(io.StringIO(data))
    rows = list(reader)

    if not rows:
        print("  ERROR: No rows found in LiquidClass table.")
        return None

    # Write to SQLite
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cols = list(rows[0].keys())

    # Create table with all columns as TEXT (preserves all values safely)
    col_defs = ', '.join([f'"{c}" TEXT' for c in cols])
    conn.execute(f'CREATE TABLE LiquidClass ({col_defs})')

    placeholders = ', '.join(['?' for _ in cols])
    for row in rows:
        conn.execute(
            f'INSERT INTO LiquidClass VALUES ({placeholders})',
            [row.get(c, '') for c in cols]
        )

    conn.commit()
    conn.close()

    print(f"  Done: {len(rows)} liquid classes converted.")
    return db_path

# ── LOCAL WEB SERVER ──────────────────────────────────────────────────────────
class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_GET(self):
        # Special endpoint: serve any local file by absolute path
        if self.path.startswith('/localfile'):
            parsed   = urllib.parse.urlparse(self.path)
            params   = urllib.parse.parse_qs(parsed.query)
            filepath = params.get('path', [None])[0]
            if filepath and os.path.isfile(filepath):
                with open(filepath, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()
            return
        # All other requests served normally from SCRIPT_DIR
        super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress request logs

def start_server(port=5800):
    server = HTTPServer(('127.0.0.1', port), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 52)
    print("   HAMILTON LC TOOL - LAUNCHER")
    print("=" * 52)

    check_mdbtools()

    # Ask mode
    print("\nWhat would you like to do?")
    print("  1. Explorer  - browse a single instrument database")
    print("  2. Audit     - compare two instrument databases")
    print()
    choice = input("Enter 1 or 2: ").strip()

    if choice not in ('1', '2'):
        print("Invalid choice. Please run again and enter 1 or 2.")
        input("\nPress Enter to exit.")
        sys.exit(1)

    mode = 'explore' if choice == '1' else 'audit'
    db_paths = []

    # Pick files
    labels = ['System 1'] if mode == 'explore' else ['System 1', 'System 2']
    for label in labels:
        print(f"\nSelect the .mdb file for {label}...")
        mdb_path = pick_file(f"Select Hamilton MDB file for {label}")
        if not mdb_path:
            print("No file selected. Exiting.")
            input("\nPress Enter to exit.")
            sys.exit(0)

        db_path = convert_mdb(mdb_path)
        if not db_path:
            input("\nConversion failed. Press Enter to exit.")
            sys.exit(1)

        db_paths.append(db_path)

    # Build URL params
    # We pass file paths relative to the server root won't work for arbitrary
    # locations -- instead we serve the db files directly via a param with full path.
    # The HTML will fetch them from the server using a /file?path= endpoint.
    params = {'mode': mode}
    for i, p in enumerate(db_paths):
        params[f'db{i+1}'] = os.path.basename(p)
        params[f'db{i+1}_dir'] = os.path.dirname(p)

    # Start server
    port = 5800
    server = start_server(port)
    print(f"\n  Server running at http://127.0.0.1:{port}")

    # Build URL
    query = urllib.parse.urlencode(params)
    url = f"http://127.0.0.1:{port}/hamilton_lc_v2.html?{query}"

    print(f"  Opening browser...")
    webbrowser.open(url)

    print("\n  Tool is running. Close this window to stop the server.")
    print("  (or press Ctrl+C)")
    print()

    try:
        threading.Event().wait()  # Keep alive until Ctrl+C
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.shutdown()

if __name__ == '__main__':
    main()
