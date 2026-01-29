import json
import os
import threading

class GeneVault:
    """
    Persistent memory for learned recovery strategies.
    """
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r") as f:
            return json.load(f)

    def save(self):
        with self.lock:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2)

    def get(self, fingerprint):
        return self.data.get(fingerprint)

    def store(self, fingerprint, strategy_name):
        self.data[fingerprint] = {
            "strategy": strategy_name
        }
        self.save()
