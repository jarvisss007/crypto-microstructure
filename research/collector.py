#!/usr/bin/env python3
"""
Headless data collector for the Crypto Microstructure Lab — no browser needed.

Connects directly to Coinbase's public WebSocket, records trades + 1/sec order-book
snapshots to a dated CSV (same schema as the in-browser recorder, so backtest.py reads it
unchanged), and periodically runs the backtest on the accumulating file, appending each
verdict to a log. Reconnects on drop. Meant to run in the background for hours/days.

    /opt/anaconda3/bin/python collector.py                       # BTC-USD, hourly backtest
    /opt/anaconda3/bin/python collector.py --product ETH-USD --backtest-every 1800
    /opt/anaconda3/bin/python collector.py --backtest-every 0    # record only, no backtest

CSV: research/data/<PRODUCT>_<YYYY-MM-DD>.csv     (rotates daily)
Log: research/data/backtest_log.txt
"""
import argparse, asyncio, json, os, subprocess, sys, time, datetime
import websockets

URL = 'wss://ws-feed.exchange.coinbase.com'
HERE = os.path.dirname(os.path.abspath(__file__))


class Collector:
    def __init__(self, args):
        self.product = args.product
        self.data_dir = args.data_dir or os.path.join(HERE, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.backtest_every = args.backtest_every
        self.cost_bps = args.cost_bps
        self.max_hours = args.max_hours
        self.start_time = time.time()
        self.bids = {}          # price -> size
        self.asks = {}
        self.book_ready = False
        self.fh = None
        self.cur_date = None
        self.n_trades = 0
        self.n_books = 0
        self.last_hb = time.time()

    # ---- file management (daily rotation) ----
    def _ensure_file(self):
        d = datetime.date.today().isoformat()
        if d != self.cur_date:
            if self.fh:
                self.fh.close()
            path = os.path.join(self.data_dir, f'{self.product}_{d}.csv')
            new = not os.path.exists(path)
            self.fh = open(path, 'a', buffering=1)   # line-buffered
            if new:
                self.fh.write('type,ts_ms,px_or_mid,qty_or_spread,extra1,extra2,extra3\n')
            self.cur_date = d
            self.cur_path = path

    def _write(self, row):
        self._ensure_file()
        self.fh.write(','.join(str(x) for x in row) + '\n')

    # ---- message handling ----
    def on_match(self, d):
        try:
            price = float(d['price']); qty = float(d['size'])
        except (KeyError, ValueError, TypeError):
            return
        isbuy = 1 if d.get('side') == 'sell' else 0   # sell-maker => taker bought
        self._write(['trade', int(time.time() * 1000), price, qty, isbuy, '', ''])
        self.n_trades += 1

    def on_snapshot(self, d):
        self.bids = {float(p): float(s) for p, s in d['bids']}
        self.asks = {float(p): float(s) for p, s in d['asks']}
        self.book_ready = True

    def on_l2(self, d):
        for side, p, s in d['changes']:
            book = self.bids if side == 'buy' else self.asks
            pr, sz = float(p), float(s)
            if sz == 0:
                book.pop(pr, None)
            else:
                book[pr] = sz

    def write_book_snapshot(self):
        if not self.book_ready or not self.bids or not self.asks:
            return
        best_bid = max(self.bids); best_ask = min(self.asks)
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        top_bids = sorted(self.bids.items(), key=lambda x: -x[0])[:20]
        top_asks = sorted(self.asks.items(), key=lambda x: x[0])[:20]
        bidvol = sum(s for _, s in top_bids)
        askvol = sum(s for _, s in top_asks)
        tot = bidvol + askvol
        book_imb = (bidvol - askvol) / tot if tot else 0.0    # SIGNED, [-1,1]
        self._write(['book', int(time.time() * 1000), round(mid, 2), round(spread, 2),
                     round(bidvol, 6), round(askvol, 6), round(book_imb, 4)])
        self.n_books += 1

    # ---- background loops ----
    async def snapshot_loop(self):
        while True:
            await asyncio.sleep(1.0)
            try:
                self.write_book_snapshot()
            except Exception as e:
                print('snapshot error:', e, flush=True)

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(30)
            print(f'[{datetime.datetime.now():%H:%M:%S}] {self.product} · '
                  f'{self.n_trades:,} trades · {self.n_books:,} book snaps · '
                  f'file {os.path.basename(getattr(self, "cur_path", "—"))}', flush=True)

    async def backtest_loop(self):
        if self.backtest_every <= 0:
            return
        while True:
            await asyncio.sleep(self.backtest_every)
            await self.run_backtest()

    async def run_backtest(self):
        path = getattr(self, 'cur_path', None)
        if not path or not os.path.exists(path):
            return
        try:
            out = subprocess.run(
                [sys.executable, os.path.join(HERE, 'backtest.py'), path,
                 '--cost-bps', str(self.cost_bps)],
                capture_output=True, text=True, timeout=300).stdout
        except Exception as e:
            out = f'backtest failed: {e}'
        log = os.path.join(self.data_dir, 'backtest_log.txt')
        with open(log, 'a') as f:
            f.write(f'\n{"="*66}\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] '
                    f'auto-backtest\n{out}\n')
        print(f'[{datetime.datetime.now():%H:%M:%S}] auto-backtest written to '
              f'{os.path.basename(log)}', flush=True)

    # ---- main connection loop (with reconnect) ----
    async def consume(self):
        sub = json.dumps({'type': 'subscribe', 'product_ids': [self.product],
                          'channels': ['matches', 'level2_batch', 'ticker']})
        while True:
            try:
                async with websockets.connect(URL, ping_interval=20, max_size=None) as ws:
                    await ws.send(sub)
                    print(f'connected · recording {self.product} → {self.data_dir}', flush=True)
                    async for raw in ws:
                        d = json.loads(raw)
                        t = d.get('type')
                        if t in ('match', 'last_match'):
                            self.on_match(d)
                        elif t == 'snapshot':
                            self.on_snapshot(d)
                        elif t == 'l2update':
                            self.on_l2(d)
            except Exception as e:
                print(f'disconnected ({e}); reconnecting in 2s…', flush=True)
                self.book_ready = False
                await asyncio.sleep(2)

    async def stop_after(self):
        """Auto-stop after --max-hours: run a final backtest, write a summary, exit cleanly."""
        if self.max_hours <= 0:
            return
        await asyncio.sleep(self.max_hours * 3600)
        print(f'reached max-hours={self.max_hours}; finalizing…', flush=True)
        await self.run_backtest()
        hrs = (time.time() - self.start_time) / 3600
        log = os.path.join(self.data_dir, 'backtest_log.txt')
        with open(log, 'a') as f:
            f.write(f'\n{"#"*66}\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] '
                    f'AUTO-STOP after {hrs:.1f}h · {self.n_trades:,} trades · '
                    f'{self.n_books:,} book snaps · file '
                    f'{os.path.basename(getattr(self, "cur_path", "—"))}\n'
                    f'Read the auto-backtest block just above for the verdict.\n{"#"*66}\n')
        print(f'auto-stopped after {hrs:.1f}h. Summary in backtest_log.txt.', flush=True)
        pidf = os.path.join(self.data_dir, 'collector.pid')
        if os.path.exists(pidf):
            os.remove(pidf)
        if self.fh:
            self.fh.close()
        os._exit(0)

    async def main(self):
        await asyncio.gather(self.consume(), self.snapshot_loop(),
                             self.heartbeat_loop(), self.backtest_loop(),
                             self.stop_after())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--product', default='BTC-USD')
    ap.add_argument('--data-dir', default=None)
    ap.add_argument('--backtest-every', type=int, default=3600,
                    help='seconds between auto-backtests (0 = off)')
    ap.add_argument('--cost-bps', type=float, default=60.0)
    ap.add_argument('--max-hours', type=float, default=0.0,
                    help='auto-stop after this many hours (0 = run until stopped)')
    args = ap.parse_args()
    c = Collector(args)
    try:
        asyncio.run(c.main())
    except KeyboardInterrupt:
        print('\nstopped.', flush=True)
        if c.fh:
            c.fh.close()


if __name__ == '__main__':
    main()
