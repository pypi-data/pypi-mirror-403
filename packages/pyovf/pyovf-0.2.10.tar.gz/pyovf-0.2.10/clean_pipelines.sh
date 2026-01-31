#!/bin/sh
# delete-old-gitlab-pipelines.sh
# Zsh-compatible (POSIX sh) script to delete GitLab pipelines older than N days.

set -eu

# ----------------------------
# Config (can be overridden by env)
# ----------------------------
: "${GITLAB_URL:=https://gitlab.flavio.be}"   # or https://gitlab.com
: "${PROJECT_ID:=16}"                             # required
: "${PRIVATE_TOKEN:=$GITLAB_TOKEN}"                          # required (PAT with api scope)
: "${DAYS:=0}"                                 # delete pipelines older than this
: "${PER_PAGE:=100}"                            # 20..100
: "${DRY_RUN:=1}"                               # 1 = dry-run, 0 = actually delete
: "${SLEEP_SEC:=0}"                             # throttle deletes if needed (e.g. 0.2)

# Optional: delete only certain pipeline statuses (comma-separated), empty = all
# e.g. STATUSES="failed,canceled,skipped"
: "${STATUSES:=failed,canceled,skipped}"

usage() {
  cat <<EOF
Usage:
  GITLAB_URL=... PROJECT_ID=... PRIVATE_TOKEN=... [DAYS=90] [DRY_RUN=1] ./delete-old-gitlab-pipelines.sh

Required env:
  PROJECT_ID        GitLab numeric project ID
  PRIVATE_TOKEN     Personal Access Token with 'api' scope
Optional env:
  GITLAB_URL        GitLab base URL (default: https://gitlab.example.com)
  DAYS              Age threshold in days (default: 90)
  PER_PAGE          Pagination size (default: 100)
  DRY_RUN           1 = list only, 0 = delete (default: 1)
  SLEEP_SEC         Delay between deletes (default: 0)
  STATUSES          Filter statuses (e.g. "failed,canceled") default: all

Examples:
  # Dry-run (prints what would be deleted)
  GITLAB_URL=https://gitlab.com PROJECT_ID=123 PRIVATE_TOKEN=xxx DAYS=120 DRY_RUN=1 ./delete-old-gitlab-pipelines.sh

  # Actually delete
  GITLAB_URL=https://gitlab.com PROJECT_ID=123 PRIVATE_TOKEN=xxx DAYS=120 DRY_RUN=0 ./delete-old-gitlab-pipelines.sh
EOF
}

if [ -z "$PROJECT_ID" ] || [ -z "$PRIVATE_TOKEN" ]; then
  usage >&2
  echo "ERROR: PROJECT_ID and PRIVATE_TOKEN are required." >&2
  exit 1
fi

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

# Pick JSON parser: jq preferred, python fallback
JSON_MODE=""
if need_cmd jq; then
  JSON_MODE="jq"
elif need_cmd python3; then
  JSON_MODE="py"
else
  echo "ERROR: Need 'jq' or 'python3' to parse GitLab API JSON." >&2
  exit 1
fi

# Date arithmetic: GNU date (Linux) or BSD date (macOS)
# We compute cutoff epoch = now - DAYS*86400
now_epoch="$(date +%s)"
cutoff_epoch="$((now_epoch - (DAYS * 86400)))"

# Build optional status query
# GitLab API supports 'status=' filter, but only one at a time; we'll filter client-side for multiple.
statuses_csv="$STATUSES"

api_get() {
  # args: path (starting with /api/...)
  # Returns JSON on success, empty string on error
  tmpresponse="/tmp/gitlab_response.$$"
  tmptmp="/tmp/gitlab_tmp.$$"
  
  # Write response body to tmpresponse, headers go to /tmp/gitlab_headers.$$
  http_code=$(curl -sS --max-time 10 -D /tmp/gitlab_headers.$$ -o "$tmpresponse" \
    --header "PRIVATE-TOKEN: $PRIVATE_TOKEN" \
    -w "%{http_code}" \
    "$GITLAB_URL$1")
  
  # Check status
  if [ "${http_code:0:1}" = "2" ]; then
    cat "$tmpresponse"
    return 0
  else
    print_line "API Error: HTTP $http_code" >&2
    return 1
  fi
}

api_delete() {
  # args: pipeline_id
  curl -sS -o /dev/null -w "%{http_code}" \
    --request DELETE \
    --header "PRIVATE-TOKEN: $PRIVATE_TOKEN" \
    "$GITLAB_URL/api/v4/projects/$PROJECT_ID/pipelines/$1"
}

get_next_page() {
  # Parses X-Next-Page header from /tmp/gitlab_headers.$$
  # returns next page number or empty
  awk -F': ' 'tolower($1)=="x-next-page"{gsub("\r","",$2); print $2}' /tmp/gitlab_headers.$$
}

print_line() {
  # consistent output
  # shellcheck disable=SC2059
  printf "%s\n" "$1"
}

matches_status() {
  # args: status
  # return 0 if matches, 1 otherwise
  st="$1"
  if [ -z "$statuses_csv" ]; then
    return 0
  fi
  # naive CSV match: split by comma
  oldIFS="$IFS"
  IFS=','
  for s in $statuses_csv; do
    if [ "$st" = "$s" ]; then
      IFS="$oldIFS"
      return 0
    fi
  done
  IFS="$oldIFS"
  return 1
}

extract_pipelines() {
  # Read from stdin and output TSV lines
  # This function is problematic with heredocs in certain shells
  # Solution: accept filename instead
  local jsonfile="$1"
  python3 <<PYEOF
import json
with open('$jsonfile') as f:
    data = json.load(f)
for p in data:
    pid = p.get("id","")
    created = p.get("created_at","")
    status = p.get("status","")
    ref = p.get("ref","") or ""
    url = p.get("web_url","") or ""
    print(f"{pid}\t{created}\t{status}\t{ref}\t{url}")
PYEOF
}

# Convert created_at (ISO8601) to epoch using python (portable)
iso8601_to_epoch() {
  # args: iso8601 string
  if need_cmd python3; then
    python3 - "$1" <<'PY'
import sys
from datetime import datetime, timezone
s = sys.argv[1]
# GitLab returns e.g. 2025-01-09T12:34:56.789Z
try:
    dt = datetime.fromisoformat(s.replace("Z","+00:00"))
except ValueError:
    # fallback: trim fractional seconds if needed
    if "." in s:
        base = s.split(".",1)[0] + "Z"
        dt = datetime.fromisoformat(base.replace("Z","+00:00"))
    else:
        raise
print(int(dt.replace(tzinfo=timezone.utc).timestamp()))
PY
  else
    # Should never happen since we require python3 or jq; but keep safe.
    echo "0"
  fi
}

page="1"
deleted="0"
candidates="0"

print_line "GitLab pipeline cleanup"
print_line "  URL:        $GITLAB_URL"
print_line "  PROJECT_ID:  $PROJECT_ID"
print_line "  DAYS:        $DAYS (cutoff epoch: $cutoff_epoch)"
print_line "  PER_PAGE:    $PER_PAGE"
print_line "  DRY_RUN:     $DRY_RUN"
[ -n "$STATUSES" ] && print_line "  STATUSES:    $STATUSES"

while :; do
  resp="$(api_get "/api/v4/projects/$PROJECT_ID/pipelines?per_page=$PER_PAGE&page=$page" 2>/dev/null)" || {
    # API call failed
    break
  }
  
  # Check if response is empty (no more pages)
  if [ -z "$resp" ]; then
    break
  fi
  
  # Check if response is valid JSON
  if ! echo "$resp" | grep -q '^\[' && ! echo "$resp" | grep -q '^{'; then
    print_line "ERROR: Invalid JSON response from API" >&2
    break
  fi
  
  # Empty pipeline list - normal case
  if [ "$resp" = "[]" ]; then
    break
  fi

  # Save API response to temp file for JSON extraction
  jsonfile="/tmp/gitlab_pipelines_$$.json"
  echo "$resp" > "$jsonfile"
  
  # Use temp file to avoid subshell (preserves variable changes)
  tmpfile="/tmp/pipelines_$$.txt"
  extract_pipelines "$jsonfile" > "$tmpfile" 2>/dev/null || {
    # JSON parse failed (likely malformed response)
    print_line "ERROR: Failed to parse JSON response from API" >&2
    rm -f "$tmpfile" "$jsonfile"
    break
  }
  
  rm -f "$jsonfile"  # Clean up JSON temp file

  while IFS="$(printf '\t')" read -r pid created status ref web_url; do
    [ -z "$pid" ] && continue

    if ! matches_status "$status"; then
      continue
    fi

    created_epoch="$(iso8601_to_epoch "$created")"
    if [ "$created_epoch" -lt "$cutoff_epoch" ]; then
      candidates=$((candidates + 1))
      if [ "$DRY_RUN" = "1" ]; then
        print_line "DRY-RUN: would delete pipeline id=$pid status=$status created_at=$created ref=$ref $web_url"
      else
        code="$(api_delete "$pid")" || code="000"
        if [ "$code" = "204" ] || [ "$code" = "200" ]; then
          deleted=$((deleted + 1))
          print_line "DELETED: pipeline id=$pid status=$status created_at=$created ref=$ref"
        else
          print_line "FAILED:  pipeline id=$pid status=$status created_at=$created HTTP=$code"
        fi
        # Throttle if requested
        if [ "$SLEEP_SEC" != "0" ]; then
          sleep "$SLEEP_SEC"
        fi
      fi
    fi
  done < "$tmpfile"
  
  rm -f "$tmpfile"

  next="$(get_next_page)"
  if [ -z "$next" ] || [ "$next" = "0" ]; then
    break
  fi
  page="$next"
done

rm -f /tmp/gitlab_headers.$$ /tmp/gitlab_response.$$ /tmp/pipelines_$$.txt 2>/dev/null || true

if [ "$DRY_RUN" = "1" ]; then
  print_line "Done (dry-run). Candidates older than $DAYS days: $candidates"
else
  print_line "Done. Deleted: $deleted (candidates older than $DAYS days: $candidates)"
fi
