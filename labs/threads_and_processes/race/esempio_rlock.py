import threading
 
class SafeList:
    def __init__(self):
        self._data = []
        self._lock = threading.RLock()  # rientrante!
    
    def append(self, item):
        with self._lock:
            self._data.append(item)
    
    def extend(self, items):
        with self._lock:
            for item in items:
                print(f"Appending {item}")
                self.append(item)  # append() acquisisce lo stesso lock
                # Con Lock normale: DEADLOCK
                # Con RLock: OK, il conteggio interno gestisce la rientranza
    
    def get_snapshot(self):
        with self._lock:
            return list(self._data)
 
safe_list = SafeList()
 
def worker(name, values):
    safe_list.extend([f"{name}:{v}" for v in values])
 
threads = [
    threading.Thread(target=worker, args=("A", range(100))),
    threading.Thread(target=worker, args=("B", range(100))),
]
for t in threads: t.start()
for t in threads: t.join()
 
print(f"Elementi totali: {len(safe_list.get_snapshot())}")  # sempre 200
