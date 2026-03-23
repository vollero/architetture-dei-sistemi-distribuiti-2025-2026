import threading
import time
import random

lock = threading.Lock()
 
class Bank:
    def __init__(self):
        self.accounts = {"Alice": 1000, "Bob": 1000, "Carol": 1000}
    
    def transfer(self, src, dst, amount):
        if self.accounts[src] >= amount:
            # --- inizio sezione critica ---
            with lock:
                tmp_src = self.accounts[src]
                tmp_dst = self.accounts[dst]
                time.sleep(random.uniform(0, 0.001))  # simula latenza
                self.accounts[src] = tmp_src - amount
                self.accounts[dst] = tmp_dst + amount
            # --- fine sezione critica ---
    
    def total(self):
        return sum(self.accounts.values())
 
bank = Bank()
print(f"Saldo iniziale totale: {bank.total()}")
 
def random_transfers(bank, n):
    names = list(bank.accounts.keys())
    for _ in range(n):
        src, dst = random.sample(names, 2)
        bank.transfer(src, dst, random.randint(1, 100))
 
threads = [threading.Thread(target=random_transfers, args=(bank, 1000))
           for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
 
print(f"Saldo finale totale: {bank.total()}")
print(f"Conti: {bank.accounts}")
