# src/tsqueue/persistent_queue.py
import json
import pickle
import queue
import threading
from pathlib import Path
from typing import Any, Callable, Optional, Literal

class PersistentQueue:
    """
    Queue thread-safe avec sauvegarde automatique ou manuelle.
    Supporte JSON et Pickle pour la sérialisation.
    """

    def __init__(
        self, 
        filepath: str,
        maxsize: int = 0,
        format: Literal["json", "pickle"] = "json",
        auto_save: bool = False,
        auto_save_interval: int = 10
    ):
        """
        Args:
            filepath: Chemin du fichier de sauvegarde
            maxsize: Taille max de la queue (0 = illimité)
            format: Format de sérialisation ("json" ou "pickle")
            auto_save: Sauvegarde automatique après chaque push
            auto_save_interval: Nombre de push avant auto-save (si auto_save=True)
        """
        self._q = queue.Queue(maxsize)
        self._filepath = Path(filepath)
        self._format = format
        self._auto_save = auto_save
        self._auto_save_interval = auto_save_interval
        self._push_count = 0
        self._lock = threading.Lock()
        self._callbacks = []

        # Créer le dossier si nécessaire
        self._filepath.parent.mkdir(parents=True, exist_ok=True)

        # Charger la queue si le fichier existe
        if self._filepath.exists():
            self.load()

    def push(self, item: Any) -> None:
        """Ajoute un élément et sauvegarde si auto_save activé"""
        self._q.put(item)
        self._trigger_callbacks(item)
        
        if self._auto_save:
            self._push_count += 1
            if self._push_count >= self._auto_save_interval:
                self.save()
                self._push_count = 0

    def pop(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Récupère un élément"""
        item = self._q.get(block=block, timeout=timeout)
        if self._auto_save:
            self.save()
        return item

    def peek(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Regarde le prochain élément sans le retirer"""
        item = self._q.get(block=block, timeout=timeout)
        self._q.put(item)
        return item

    def save(self) -> None:
        """Sauvegarde la queue dans le fichier"""
        with self._lock:
            items = []
            temp_queue = queue.Queue()
            
            # Vider la queue pour récupérer tous les éléments
            while not self._q.empty():
                try:
                    item = self._q.get_nowait()
                    items.append(item)
                    temp_queue.put(item)
                except queue.Empty:
                    break
            
            # Remettre les éléments dans la queue
            while not temp_queue.empty():
                self._q.put(temp_queue.get_nowait())
            
            # Sauvegarder selon le format
            if self._format == "json":
                with open(self._filepath, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2)
            else:  # pickle
                with open(self._filepath, 'wb') as f:
                    pickle.dump(items, f)

    def load(self) -> int:
        """
        Charge la queue depuis le fichier.
        
        Returns:
            Nombre d'éléments chargés
        """
        with self._lock:
            # Vider la queue actuelle
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    break
            
            # Charger depuis le fichier
            items = []
            if self._format == "json":
                with open(self._filepath, 'r', encoding='utf-8') as f:
                    items = json.load(f)
            else:  # pickle
                with open(self._filepath, 'rb') as f:
                    items = pickle.load(f)
            
            # Remplir la queue
            for item in items:
                self._q.put(item)
            
            return len(items)

    def delete_file(self) -> None:
        """Supprime le fichier de sauvegarde"""
        if self._filepath.exists():
            self._filepath.unlink()

    def empty(self) -> bool:
        """Retourne True si la queue est vide"""
        return self._q.empty()

    def size(self) -> int:
        """Retourne le nombre d'éléments"""
        return self._q.qsize()

    def clear(self) -> None:
        """Vide la queue et sauvegarde"""
        with self._lock:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                except queue.Empty:
                    break
        if self._auto_save:
            self.save()

    def on_push(self, callback: Callable[[Any], None]) -> None:
        """Enregistre un callback appelé à chaque push"""
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Any], None]) -> bool:
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

    def _trigger_callbacks(self, item: Any) -> None:
        """Déclenche les callbacks"""
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(item)
            except Exception as e:
                print(f"Erreur dans callback: {e}")

    def __iter__(self):
        """Itérateur qui consomme la queue"""
        return self

    def __next__(self) -> Any:
        """Récupère le prochain élément"""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            raise StopIteration

    def __len__(self) -> int:
        return self.size()

    def __bool__(self) -> bool:
        return not self.empty()

    def __repr__(self) -> str:
        return (f"PersistentQueue(file='{self._filepath.name}', "
                f"size={self.size()}, format={self._format})")

    def __enter__(self):
        """Support du context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sauvegarde automatique à la sortie du context"""
        self.save()