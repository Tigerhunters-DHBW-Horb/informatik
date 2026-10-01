# RoboCup SSL System

## Projektueberblick

Dieses Projekt ist als Steuerungssystem fuer ein RoboCup-Small-Size-League-Team aufgebaut. Die Module sollen Eingabedaten von Vision, Schiedsrichter und Robotern verarbeiten, daraus ein Weltmodell und eine Strategie bilden und anschliessend Befehle an Roboter oder Simulator ausgeben. Die interne Kommunikation ist mit ZeroMQ vorgesehen.

## Ordner und Dateien

### `config/`

Enthaelt die YAML-Konfiguration des Systems:

- `general.yaml`: Teamfarbe und -ID, Spielfeldmasse und Basis-Port fuer ZeroMQ.
- `connections.yaml`: Netzwerkadressen und Ports fuer SSL-Vision, Referee, grSim und interne ZeroMQ-Themen.
- `control_settings.yaml`: Parameter fuer Weltmodell, Bahnplanung und Geschwindigkeits- bzw. Aktuatorgrenzen.

### `src/robocup_ssl/`

Enthaelt den Python-Quellcode der Anwendung.

- `main.py`: vorgesehener Einstiegspunkt und Orchestrator fuer den Systemstart und die Prozesse.
- `system_manager.py`: Verwaltung von System- und Spielzustand, Sicherheits-HALT und Verbindungs-Timeouts.
- `data_objects/`: gemeinsame Datenklassen fuer den Austausch zwischen Modulen.
- `mod_cyclic_inputs/`: Einlesen und Umwandeln von Vision-, Referee- und Roboter-Telemetriedaten.
- `mod_cyclic_outputs/`: Ausgabe von Steuerbefehlen, unter anderem an grSim oder ueber Funk.
- `mod_data_logger/`: Protokollierung von System- und Laufzeitdaten.
- `mod_gui/`: Visualisierung des Systems.
- `mod_pathfinding/`: Bahnplanung und Umwandlung von Zielvorgaben in Bewegungsbefehle.
- `mod_strategy/`: hierarchische Spielentscheidungen mit Plays, Tactics und Skills.
- `mod_world_model/`: Aufbereitung und Filterung der Sensordaten zu einem Weltzustand.
- `utils/`: wiederverwendbare Hilfsfunktionen, darunter Konfigurations-, Netzwerk- und Mathematikfunktionen.

Die `__init__.py`-Dateien markieren die entsprechenden Verzeichnisse als Python-Pakete.

### `tests/`

Enthaelt Dateien fuer vorgesehene Tests zu Bahnplanung, Skills und Weltmodell (`test_pathfinding.py`, `test_skills.py`, `test_world_model.py`). In diesen Dateien sind derzeit jedoch keine Tests implementiert.

### `requirements.txt`

Listet die benoetigten Python-Pakete auf: ZeroMQ, MessagePack, PyYAML, NumPy und Protocol Buffers.

## Umgebung einrichten

Im Projektstamm in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Falls PowerShell die Aktivierung wegen der Ausfuehrungsrichtlinie blockiert, kann die virtuelle Umgebung stattdessen direkt verwendet werden:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Tests ausfuehren

Mit aktivierter virtueller Umgebung:

```powershell
python -m unittest discover -s tests -v
```

Aktuell findet dieser Befehl keine Tests und endet mit Fehlercode 1 (`NO TESTS RAN`).

## Anwendung starten: aktueller Stand

Der Anwendungseinstieg ist `src/robocup_ssl/main.py`. Das Projekt ist derzeit jedoch noch nicht als lauffaehige Anwendung startbar: `RobocupSystem.setup()`, `start_processes()` und `run()` sind noch nicht implementiert, und `main.py` ruft keine Startfunktion auf. Ein Aufruf wie `python src/robocup_ssl/main.py` beendet sich daher, ohne das Steuerungssystem zu starten.

Sobald der Orchestrator und ein Programmeinstieg implementiert sind, kann das Paket aus dem Projektstamm beispielsweise so gestartet werden:

```powershell
$env:PYTHONPATH = "src"
python -m robocup_ssl.main
```

Vor einem echten Betrieb muessen ausserdem die Netzwerkwerte in `config/` zur lokalen SSL-Vision-, Referee-, Roboter- oder Simulator-Umgebung passen.