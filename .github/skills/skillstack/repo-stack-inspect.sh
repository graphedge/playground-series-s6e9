#!/bin/sh
# repo-stack-inspect.sh — deterministic stack fingerprint for agent synthesis
#
# Usage:
#   repo-stack-inspect.sh --path DIR [--slug SLUG] [--json-out FILE] [--focus LENS] [--strict-focus] [--check]

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
TARGET_PATH=
SLUG=
JSON_OUT=
CHECK=0
FOCUS_ARGS=
STRICT_FOCUS=0

usage() {
    cat <<'EOF'
Usage: repo-stack-inspect.sh --path DIR [--slug SLUG] [--json-out FILE] [--focus LENS] [--strict-focus] [--check]

Fingerprint a local repository for stack-inspect synthesis.
  --path DIR       repository root to inspect (required)
  --slug SLUG      repository slug (default: basename of path)
  --json-out FILE  write fingerprint JSON (default: stdout)
  --focus LENS     focus lens: playwright, cdp, persistent-profile, ci, all-patterns (repeatable)
  --strict-focus   fail when explicit focus lenses match no signals
  --check          validate fixture fingerprint under tests/fixtures/repo-stack-inspect/
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --path)
            [ "$#" -ge 2 ] || { echo "repo-stack-inspect: --path needs a value" >&2; exit 2; }
            TARGET_PATH=$2
            shift 2
            ;;
        --slug)
            [ "$#" -ge 2 ] || { echo "repo-stack-inspect: --slug needs a value" >&2; exit 2; }
            SLUG=$2
            shift 2
            ;;
        --json-out)
            [ "$#" -ge 2 ] || { echo "repo-stack-inspect: --json-out needs a value" >&2; exit 2; }
            JSON_OUT=$2
            shift 2
            ;;
        --focus)
            [ "$#" -ge 2 ] || { echo "repo-stack-inspect: --focus needs a value" >&2; exit 2; }
            FOCUS_ARGS="$FOCUS_ARGS --focus $2"
            shift 2
            ;;
        --strict-focus)
            STRICT_FOCUS=1
            shift
            ;;
        --check)
            CHECK=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "repo-stack-inspect: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

command -v python3 >/dev/null 2>&1 || {
    echo "repo-stack-inspect: python3 is required (standard library only)" >&2
    exit 1
}

if [ "$CHECK" -eq 1 ]; then
    FIXTURE="$REPO_ROOT/tests/fixtures/repo-stack-inspect/sample-bash"
    EXPECTED="$FIXTURE/expected-fingerprint.json"
    [ -d "$FIXTURE" ] || { echo "repo-stack-inspect: fixture missing: $FIXTURE" >&2; exit 1; }
    [ -f "$EXPECTED" ] || { echo "repo-stack-inspect: expected fingerprint missing: $EXPECTED" >&2; exit 1; }
    TARGET_PATH=$FIXTURE
    SLUG=sample-bash
    TEMP=$(mktemp "${TMPDIR:-/tmp}/stack-inspect-check.XXXXXX.json")
    trap 'rm -f "$TEMP"' EXIT HUP INT TERM
    JSON_OUT=$TEMP
fi

[ -n "$TARGET_PATH" ] || { echo "repo-stack-inspect: --path is required" >&2; exit 2; }
TARGET_PATH=$(CDPATH= cd -- "$TARGET_PATH" 2>/dev/null && pwd -P) ||
    { echo "repo-stack-inspect: path does not exist: $TARGET_PATH" >&2; exit 1; }

if [ -z "$SLUG" ]; then
    SLUG=$(basename "$TARGET_PATH")
fi

python3 "$SCRIPT_DIR/repo-stack-inspect.py" \
    --path "$TARGET_PATH" \
    --slug "$SLUG" \
    --json-out "${JSON_OUT:--}" \
    $FOCUS_ARGS \
    ${STRICT_FOCUS:+--strict-focus}

if [ "$CHECK" -eq 1 ]; then
    if ! python3 - "$TEMP" "$EXPECTED" <<'PY'
import json, sys

def norm(obj):
    if isinstance(obj, dict):
        return {k: norm(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [norm(v) for v in obj]
    return obj

got = norm(json.load(open(sys.argv[1])))
want = norm(json.load(open(sys.argv[2])))
for key in ("slug", "manifests", "ci_workflows", "primary_language", "execution_evidence", "entry_points"):
    if got.get(key) != want.get(key):
        print(f"FAIL: fingerprint mismatch on {key}: {got.get(key)!r} != {want.get(key)!r}")
        sys.exit(1)
print("PASS: fixture fingerprint matches expected")
PY
    then
        exit 1
    fi
fi
