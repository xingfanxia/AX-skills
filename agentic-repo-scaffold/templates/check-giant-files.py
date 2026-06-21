#!/usr/bin/env python3
# Giant-file gate (language-agnostic). Dependency-free. For non-JS repos (Go/Python/Rust/...).
# Run: python3 tools/verify/check_giant_files.py   (exit 1 on violation)
from pathlib import Path

# First matching marker wins; order specific -> general.
LIMITS = [
    ('/transport/', 100), ('/controllers/', 100), ('/handlers/', 100),
    ('/public/', 100), ('/cli/', 120),
    ('/core/', 250), ('/domain/', 250), ('/application/', 250), ('/adapters/', 250),
    ('/migrations/', 300), ('/tests/', 400), ('/test/', 400),
]
DEFAULT_LIMIT = 300
HARD_CAP = 500
EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.java', '.kt', '.rs', '.rb', '.php', '.cs', '.sql'}
IGNORE = ('/node_modules/', '/.git/', '/generated/', '/vendor/', '/dist/', '/build/', '/.next/')

# owner, reason, expiry per entry.
ALLOWLIST = set([
    # 'src/legacy/bigfile.py',  # @owner reason expiry=2026-12-31
])

failed = False
for path in Path('.').rglob('*'):
    if not path.is_file() or path.suffix not in EXTENSIONS:
        continue
    rel = str(path).replace('\\', '/')
    if any(p in '/' + rel + '/' for p in IGNORE) or rel in ALLOWLIST:
        continue
    loc = len(path.read_text(errors='ignore').splitlines())
    limit = DEFAULT_LIMIT
    for marker, marker_limit in LIMITS:
        if marker in '/' + rel:
            limit = marker_limit
            break
    if loc > HARD_CAP or loc > limit:
        failed = True
        print(f'{rel}: {loc} LOC > {min(limit, HARD_CAP)}. Split it or add an expiring allowlist entry.')

if failed:
    raise SystemExit(1)
print('check-giant-files: ok')
