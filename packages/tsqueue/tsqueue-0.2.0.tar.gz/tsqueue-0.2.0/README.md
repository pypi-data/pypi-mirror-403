# TSQueue

> Thread-safe queue ultra simple pour Python

---

## Description
TSQueue est un module Python léger pour gérer des queues **thread-safe** facilement.
Idéal pour les projets multi-thread où tu veux juste ajouter / retirer des éléments sans te prendre la tête avec les locks.

---

## Installation

```
pip install tsqueue
```

---

## Exemple rapide

```python
from tsqueue import TSQueue

q = TSQueue()
q.push(42)
print(q.pop())  # affiche 42
```

Avec threads :

```python
import threading
from tsqueue import TSQueue

def worker(q, n):
    q.push(n)
    print(f"Thread {n} récupéré: {q.pop()}")

q = TSQueue()
threads = [threading.Thread(target=worker, args=(q, i)) for i in range(3)]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## Licence
MIT License – voir [LICENSE](LICENSE)

---

## Liens
- GitHub : https://github.com/Nytrox-d3v/tsqueue
- PyPI : https://pypi.org/project/tsqueue/
