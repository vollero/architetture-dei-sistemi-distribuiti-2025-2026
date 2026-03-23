import threading
import time
import random
 
class FineGrainedBank:
    def __init__(self):
        self.accounts = {"Alice": 1000, "Bob": 1000, "Carol": 1000}
        self.locks = {name: threading.Lock() for name in self.accounts}
    
    def transfer(self, src, dst, amount):
        # Ordine fisso per evitare deadlock (ordine alfabetico)
        first, second = sorted([src, dst])
        with self.locks[first]:
            with self.locks[second]:
                if self.accounts[src] >= amount:
                    self.accounts[src] -= amount
                    self.accounts[dst] += amount
 
bank = FineGrainedBank()
 
def random_transfers(bank, n):
    names = list(bank.accounts.keys())
    for _ in range(n):
        src, dst = random.sample(names, 2)
        bank.transfer(src, dst, random.randint(1, 100))
 
threads = [threading.Thread(target=random_transfers, args=(bank, 1000))
           for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
 
print(f"Totale: {sum(bank.accounts.values())}")  # 3000
print(f"Conti: {bank.accounts}")
