# src/tsqueue/queue.py
import queue
import threading
from typing import Any, Callable, Optional, Iterator

class TSQueue:
    """Thread-safe queue ultra simple mais puissante"""

    def __init__(self, maxsize=0):
        self._q = queue.Queue(maxsize)
        self._callbacks = []
        self._lock = threading.Lock()

    def push(self, item: Any) -> None:
        """Ajoute un élément à la queue et déclenche les callbacks"""
        self._q.put(item)
        self._trigger_callbacks(item)

    def pop(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Récupère un élément de la queue"""
        return self._q.get(block=block, timeout=timeout)

    def peek(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """
        Regarde le prochain élément sans le retirer de la queue.
        
        Note: L'élément est temporairement retiré puis remis,
        donc d'autres threads peuvent le voir pendant ce temps.
        """
        item = self._q.get(block=block, timeout=timeout)
        self._q.put(item)
        return item

    def empty(self) -> bool:
        """Retourne True si la queue est vide"""
        return self._q.empty()

    def size(self) -> int:
        """Retourne le nombre d'éléments dans la queue"""
        return self._q.qsize()

    def clear(self) -> None:
        """Vide complètement la queue"""
        with self._lock:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    break

    def on_push(self, callback: Callable[[Any], None]) -> None:
        """
        Enregistre un callback qui sera appelé à chaque push.
        
        Args:
            callback: Fonction qui prend l'élément ajouté en paramètre
        
        Example:
            q = TSQueue()
            q.on_push(lambda item: print(f"Ajouté: {item}"))
            q.push(42)  # Affiche: "Ajouté: 42"
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Any], None]) -> bool:
        """
        Retire un callback précédemment enregistré.
        
        Returns:
            True si le callback a été trouvé et retiré, False sinon
        """
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

    def _trigger_callbacks(self, item: Any) -> None:
        """Déclenche tous les callbacks enregistrés"""
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(item)
            except Exception as e:
                # On ignore les erreurs des callbacks pour ne pas bloquer la queue
                print(f"Erreur dans callback: {e}")

    def __iter__(self) -> Iterator[Any]:
        """
        Retourne un itérateur qui pop des éléments jusqu'à ce que la queue soit vide.
        
        Warning: Cet itérateur consomme les éléments de la queue !
        
        Example:
            q = TSQueue()
            q.push(1)
            q.push(2)
            q.push(3)
            for item in q:
                print(item)  # Affiche 1, 2, 3 (et vide la queue)
        """
        return self

    def __next__(self) -> Any:
        """Récupère le prochain élément ou lève StopIteration si vide"""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            raise StopIteration

    def __len__(self) -> int:
        """Permet d'utiliser len(q) pour obtenir la taille"""
        return self.size()

    def __bool__(self) -> bool:
        """Permet d'utiliser if q: pour vérifier si non vide"""
        return not self.empty()

    def __repr__(self) -> str:
        """Représentation string de la queue"""
        return f"TSQueue(size={self.size()}, callbacks={len(self._callbacks)})"