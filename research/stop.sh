#!/bin/bash
# Stop the background collector.
cd "$(dirname "$0")" || exit 1
PIDF=data/collector.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  kill "$(cat "$PIDF")" && echo "stopped PID $(cat "$PIDF")"
  rm -f "$PIDF"
else
  echo "not running (no live PID file)."
  rm -f "$PIDF"
fi
