# src/tsqueue/priority_queue.py
import queue
import threading
from typing import Any, Callable, Optional, Tuple

class PriorityQueue:
    """
    Queue thread-safe avec système de priorités.
    Les priorités basses sont traitées en premier (1 avant 10).
    """

    def __init__(self, maxsize: int = 0):
        self._q = queue.PriorityQueue(maxsize)
        self._callbacks = []
        self._lock = threading.Lock()
        self._counter = 0  # Pour maintenir l'ordre FIFO à priorité égale

    def push(self, item: Any, priority: int = 5) -> None:
        """
        Ajoute un élément avec une priorité.
        
        Args:
            item: L'élément à ajouter
            priority: Priorité (nombre plus petit = plus prioritaire)
        """
        with self._lock:
            count = self._counter
            self._counter += 1
        
        # Format: (priorité, compteur, élément)
        # Le compteur garantit FIFO pour les éléments de même priorité
        self._q.put((priority, count, item))
        self._trigger_callbacks(item, priority)

    def pop(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """
        Récupère l'élément le plus prioritaire.
        
        Returns:
            L'élément (sans la priorité)
        """
        priority, count, item = self._q.get(block=block, timeout=timeout)
        return item

    def pop_with_priority(self, block: bool = True, timeout: Optional[float] = None) -> Tuple[Any, int]:
        """
        Récupère l'élément avec sa priorité.
        
        Returns:
            Tuple (élément, priorité)
        """
        priority, count, item = self._q.get(block=block, timeout=timeout)
        return (item, priority)

    def peek(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Regarde l'élément le plus prioritaire sans le retirer"""
        priority, count, item = self._q.get(block=block, timeout=timeout)
        self._q.put((priority, count, item))
        return item

    def peek_with_priority(self, block: bool = True, timeout: Optional[float] = None) -> Tuple[Any, int]:
        """Regarde l'élément avec sa priorité sans le retirer"""
        priority, count, item = self._q.get(block=block, timeout=timeout)
        self._q.put((priority, count, item))
        return (item, priority)

    def empty(self) -> bool:
        """Retourne True si la queue est vide"""
        return self._q.empty()

    def size(self) -> int:
        """Retourne le nombre d'éléments"""
        return self._q.qsize()

    def clear(self) -> None:
        """Vide la queue"""
        with self._lock:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    break

    def on_push(self, callback: Callable[[Any, int], None]) -> None:
        """
        Enregistre un callback appelé à chaque push.
        Le callback reçoit (item, priority).
        
        Example:
            def log(item, priority):
                print(f"Ajouté {item} avec priorité {priority}")
            
            q = PriorityQueue()
            q.on_push(log)
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> bool:
        """Retire un callback"""
        with self._lock:
            try:
                self._callbacks.remove(callback)
                return True
            except ValueError:
                return False

    def clear_callbacks(self) -> None:
        """Retire tous les callbacks"""
        with self._lock:
            self._callbacks.clear()

    def _trigger_callbacks(self, item: Any, priority: int) -> None:
        """Déclenche les callbacks"""
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(item, priority)
            except Exception as e:
                print(f"Erreur dans callback: {e}")

    def __iter__(self):
        """Itérateur qui consomme la queue par ordre de priorité"""
        return self

    def __next__(self) -> Any:
        """Récupère le prochain élément par priorité"""
        try:
            priority, count, item = self._q.get_nowait()
            return item
        except queue.Empty:
            raise StopIteration

    def __len__(self) -> int:
        return self.size()

    def __bool__(self) -> bool:
        return not self.empty()

    def __repr__(self) -> str:
        return f"PriorityQueue(size={self.size()}, callbacks={len(self._callbacks)})"