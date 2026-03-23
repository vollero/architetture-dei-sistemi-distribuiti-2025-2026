import threading
import time
import random
 
counter = 0
lock = threading.Lock()
 
def increment(n):
    global counter
    for _ in range(n):
        lock.acquire()
        local = counter
        if random.uniform(0,1) < 0.001:
            time.sleep(0.00001)
        elif random.uniform(0,1) < 0.0001:
            time.sleep(0.0001)
        local = local + 1
        counter = local
        lock.release() 
 
threads = []
for _ in range(2):
    t = threading.Thread(target=increment, args=(500_000,))
    threads.append(t)
    t.start()
 
for t in threads:
    t.join()
 
print(f"Valore atteso: 1000000")
print(f"Valore ottenuto: {counter}")
