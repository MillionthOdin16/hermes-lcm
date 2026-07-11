import time
import tempfile
from store import MessageStore

def benchmark():
    with tempfile.TemporaryDirectory() as d:
        store = MessageStore(d + "/db.sqlite")

        messages = [{"role": "user", "content": "hello"} for _ in range(1000)]

        start = time.time()
        for _ in range(10):
            store._append_protected_batch("session_1", messages)
        end = time.time()

        print(f"Time for 10,000 inserts: {end - start:.4f}s")
        store.close()

if __name__ == "__main__":
    benchmark()
