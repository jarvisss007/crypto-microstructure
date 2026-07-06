#!/bin/bash
# Start the headless collector in the background (survives closing the terminal).
# Extra args pass through, e.g.:  ./run.sh --product ETH-USD --backtest-every 1800
cd "$(dirname "$0")" || exit 1
PY=/opt/anaconda3/bin/python
mkdir -p data
PIDF=data/collector.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "already running (PID $(cat "$PIDF")). ./stop.sh first to restart."
  exit 0
fi
nohup "$PY" collector.py "$@" >> data/collector.log 2>&1 &
echo $! > "$PIDF"
echo "started collector PID $(cat "$PIDF")"
echo "  live log:   tail -f research/data/collector.log"
echo "  backtests:  research/data/backtest_log.txt"
echo "  stop with:  ./stop.sh"
