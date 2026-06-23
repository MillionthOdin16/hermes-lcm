import time
import os
import sqlite3
import json

from store import MessageStore
import tempfile

def bench():
    with tempfile.TemporaryDirectory() as d:
        s = MessageStore(os.path.join(d, "lcm.db"))
        msgs = [{"role": "user", "content": f"hello {i}"} for i in range(1000)]
        t0 = time.time()
        s.append_batch("sess", msgs, [0]*1000)
        t1 = time.time()
        print(f"append_batch time: {t1-t0:.4f}")
bench()
