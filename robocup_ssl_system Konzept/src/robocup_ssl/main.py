import multiprocessing as mp

class RobocupSystem:
    def __init__(self):
        self.processes = []
        self.is_running = True
        self.config = {}

    def setup(self):
        """Lädt die System-Konfigurationen."""

    def start_processes(self):
        """Startet alle Module als separate Betriebssystem-Prozesse."""

    def shutdown(self, signum=None, frame=None):
        """Fängt Abbruchsignale ab und beendet alles sauber"""

    def run(self):
        """Hauptschleife des Orchestrators (Watchdog)."""

