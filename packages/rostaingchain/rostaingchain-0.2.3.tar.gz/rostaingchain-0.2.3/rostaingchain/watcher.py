import time
import threading
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 1. WATCHER SYSTÈME (Pour Fichiers & Dossiers) ---
class RostaingWatcher(FileSystemEventHandler):
    def __init__(self, callback_function, directory):
        self.callback_function = callback_function
        self.directory = directory
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self, self.directory, recursive=True)
        self.observer.start()
        print(f"👁️  RostaingChain Watcher (Disk) enabled on: {self.directory}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def on_created(self, event):
        if not event.is_directory:
            print(f"⚡ New file detected: {event.src_path}")
            self.callback_function(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"🔄 File modified: {event.src_path}")
            self.callback_function(event.src_path)

# --- 2. WATCHER POLLING (Pour Bases de Données & Web) ---
class PollingWatcher:
    def __init__(self, callback_function, source_config, interval=60):
        """
        :param callback_function: The method to call for the update
        :param source_config: The config (dict) or URL (str) to monitor
        :param interval: Interval in seconds between two checks
        """
        self.callback_function = callback_function
        self.source_config = source_config
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
        print(f"🔄 Polling Watcher (DB/Web) enabled (Interval: {self.interval}s)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        while self.running:
            try:
                # Dans un scénario réel, on vérifierait un hash ou un timestamp.
                # Ici, on déclenche l'ingestion périodique pour garantir la fraîcheur.
                self.callback_function(self.source_config)
            except Exception as e:
                print(f"⚠️ Polling Error: {e}")
            
            time.sleep(self.interval)