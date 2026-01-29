# src/tsqueue/async_queue.py
import asyncio
from typing import Any, Callable, Optional, List
from collections import deque

class AsyncQueue:
    """Queue asynchrone pour asyncio avec callbacks et features avancées"""

    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._callbacks: List[Callable] = []
        self._lock = asyncio.Lock()

    async def push(self, item: Any) -> None:
        """Ajoute un élément à la queue de manière asynchrone"""
        await self._queue.put(item)
        await self._trigger_callbacks(item)

    async def pop(self, timeout: Optional[float] = None) -> Any:
        """Récupère un élément de la queue de manière asynchrone"""
        if timeout is None:
            return await self._queue.get()
        else:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)

    async def peek(self) -> Any:
        """
        Regarde le prochain élément sans le retirer.
        Lève asyncio.QueueEmpty si la queue est vide.
        """
        item = await self._queue.get()
        await self._queue.put(item)
        return item

    def empty(self) -> bool:
        """Retourne True si la queue est vide"""
        return self._queue.empty()

    def size(self) -> int:
        """Retourne le nombre d'éléments dans la queue"""
        return self._queue.qsize()

    async def clear(self) -> None:
        """Vide complètement la queue"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break

    def on_push(self, callback: Callable[[Any], Any]) -> None:
        """
        Enregistre un callback async qui sera appelé à chaque push.
        
        Args:
            callback: Fonction async qui prend l'élément en paramètre
        
        Example:
            async def log_item(item):
                print(f"Ajouté: {item}")
            
            q = AsyncQueue()
            q.on_push(log_item)
            await q.push(42)
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> bool:
        """Retire un callback"""
        try:
            self._callbacks.remove(callback)
            return True
        except ValueError:
            return False

    def clear_callbacks(self) -> None:
        """Retire tous les callbacks"""
        self._callbacks.clear()

    async def _trigger_callbacks(self, item: Any) -> None:
        """Déclenche tous les callbacks de manière asynchrone"""
        async with self._lock:
            callbacks = self._callbacks.copy()
        
        tasks = []
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(item))
                else:
                    callback(item)
            except Exception as e:
                print(f"Erreur dans callback: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def __aiter__(self):
        """Retourne un itérateur asynchrone"""
        return self

    async def __anext__(self) -> Any:
        """Récupère le prochain élément ou lève StopAsyncIteration"""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration

    def __len__(self) -> int:
        """Permet d'utiliser len(q)"""
        return self.size()

    def __bool__(self) -> bool:
        """Permet d'utiliser if q:"""
        return not self.empty()

    def __repr__(self) -> str:
        return f"AsyncQueue(size={self.size()}, callbacks={len(self._callbacks)})"