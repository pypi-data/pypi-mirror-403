# src/tsqueue/queue.py
import queue

class TSQueue:
    """Thread-safe queue ultra simple"""

    def __init__(self, maxsize=0):
        self._q = queue.Queue(maxsize)

    def push(self, item):
        """Ajoute un élément à la queue"""
        self._q.put(item)

    def pop(self, block=True, timeout=None):
        """Récupère un élément de la queue"""
        return self._q.get(block=block, timeout=timeout)

    def empty(self):
        """Retourne True si la queue est vide"""
        return self._q.empty()

    def size(self):
        """Retourne le nombre d'éléments dans la queue"""
        return self._q.qsize()
