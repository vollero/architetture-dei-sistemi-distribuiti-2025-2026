import threading
import time
 
lock_a = threading.Lock()
lock_b = threading.Lock()
 
def thread_1():
    print("T1: acquisisco lock_a")
    with lock_a:
        time.sleep(0.1)  # garantisce l'interleaving
        print("T1: provo ad acquisire lock_b...")
        with lock_b:
            print("T1: ho entrambi i lock")
 
def thread_2():
    print("T2: acquisisco lock_a")
    with lock_a:
        time.sleep(0.1)
        print("T2: provo ad acquisire lock_b...")
        with lock_b:
            print("T2: ho entrambi i lock")
 
t1 = threading.Thread(target=thread_1)
t2 = threading.Thread(target=thread_2)
t1.start(); t2.start()
 
# Timeout per evitare blocco infinito
t1.join(timeout=3)
t2.join(timeout=3)
 
if t1.is_alive() or t2.is_alive():
    print("\n*** DEADLOCK RILEVATO! ***")
    print("T1 possiede lock_a e attende lock_b")
    print("T2 possiede lock_b e attende lock_a")
