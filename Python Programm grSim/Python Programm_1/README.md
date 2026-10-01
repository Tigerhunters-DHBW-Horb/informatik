# SSL-Programmierung fuer grSim

Dieses Projekt verbindet einen Python-Roboter mit dem Simulator grSim. Es kann SSL-Vision-Daten empfangen, Ball- und Roboterpositionen schaetzen und Fahrbefehle an grSim senden.

## Ordnerinhalt

### Python-Module

| Datei | Aufgabe |
| --- | --- |
| `main.py` | Haupteinstiegspunkt. Empfaengt Vision-Daten, aktualisiert Ball und ausgewaehlten Roboter im Weltmodell und faehrt den Roboter mit einem einfachen P-Regler zum Ball. Sendet Befehle in einer Dauerschleife. |
| `Kommunikation.py` | UDP-Kommunikation mit SSL-Vision (Multicast) und grSim (Befehle). Enthaelt ausserdem einen Platzhalter fuer eine spaetere Hardware-Kommunikation. |
| `WeltModell.py` | Repraesentiert Ball und bis zu 16 Heim- sowie Gastroboter. Verarbeitet Messungen mit den Kalman-Filtern. |
| `geometrie.py` | Grundlegende 2D-Datentypen (`Vektor2D`, `Pose`) und Winkel-Hilfsfunktionen. |
| `KF_Ball.py` | Kalman-Filter fuer Position und Geschwindigkeit des Balls. Kann auch eigenstaendig eine verrauschte Beispieltrajektorie plotten. |
| `KF_Roboter.py` | Extended Kalman Filter fuer den Roboter. Enthaelt eine eigene Filterimplementierung, eine `filterpy`-Variante und eine Testsimulation. |
| `Bewegungen.py` | Bewegungsbausteine zum Anfahren einer Position und zum Anfahren des Balls. |
| `Verhalten.py` | Verhaltensbausteine, unter anderem Ballholen und Schussblocken; verwendet die Bewegungsbausteine. |
| `Strategie.py` | Geruest fuer eine kuenftige Strategieauswahl; die Methoden sind noch nicht implementiert. |
| `steuerung.py` | Manuelle Tastatursteuerung fuer grSim. Tasten: `W/S` vor/zurueck, `A/D` seitwaerts, `Q/E` drehen, `Leertaste` stoppen, `ESC` beenden. |
| `test_sender.py` | Interaktiver UDP-Testsender mit Auswahl einfacher Fahrbefehle. |
| `test_receiver.py` | Lauscht auf SSL-Vision-Multicast und gibt erkannte Baelle und Roboter aus. |

### Protobuf-Dateien (`protos/`)

Die Dateien `*.proto` beschreiben die Nachrichtenformate von grSim und der SSL-Schnittstellen. Die dazugehoerigen `*_pb2.py`-Dateien sind daraus generierte Python-Module, die zum Lesen und Schreiben dieser Nachrichten benoetigt werden. Die Python-Skripte importieren diese Module zur Laufzeit; der Ordner muss daher erhalten bleiben.

### Weitere Eintraege

`__pycache__/` enthaelt automatisch erzeugte Python-Bytecode-Dateien. `.DS_Store` ist eine automatisch erzeugte macOS-Datei. Beides gehoert nicht zum Programmablauf.

## Voraussetzungen

- Python 3
- Ein gestarteter und erreichbarer grSim-Simulator, der SSL-Vision-Daten sendet
- Netzwerkzugriff auf den Simulator; SSL-Vision verwendet standardmaessig Multicast `224.5.23.2` auf UDP-Port `10020`, grSim-Befehle gehen standardmaessig an UDP-Port `20011`
- Python-Pakete: `numpy`, `matplotlib`, `filterpy`, `pynput` und `protobuf`

Es gibt derzeit keine `requirements.txt` mit festgelegten Versionen. Die Pakete koennen in einem Terminal im Projektordner installiert werden:

```powershell
python -m pip install numpy matplotlib filterpy pynput protobuf
```

## Hauptroutine ausfuehren

1. Starte grSim und stelle sicher, dass SSL-Vision im Netzwerk erreichbar ist.
2. Oeffne ein Terminal im Ordner `Python Programm_1` (oder wechsle aus dem uebergeordneten Ordner mit `cd "Python Programm_1"` dorthin).
3. Pruefe in `main.py` die Konfiguration am Dateianfang:
   - `VM_IP`: IP-Adresse des Rechners bzw. der VM mit grSim (aktuell `192.168.42.41`)
   - `ROBOTER_ID`: ID des zu steuernden Roboters (aktuell `1`)
   - `TEAM_GELB`: `True` fuer das gelbe, `False` fuer das blaue Team
4. Starte das Programm:

```powershell
python main.py
```

`main.py` sendet fortlaufend Fahrbefehle. Es faehrt den konfigurierten Roboter zum Ball und haelt ungefaehr 120 mm Abstand. Beenden mit `Ctrl+C`; dabei wird ein Stoppbefehl gesendet. Starte das Programm erst, wenn IP-Adresse, Team, Roboter-ID und Simulatorverbindung stimmen.

## Weitere Startmoeglichkeiten

Die folgenden Programme werden ebenfalls aus `Python Programm_1` gestartet:

```powershell
python test_receiver.py
python test_sender.py
python steuerung.py
python KF_Ball.py
python KF_Roboter.py
```

`test_receiver.py` prueft den Vision-Empfang. `test_sender.py` und `steuerung.py` senden direkt Fahrbefehle an die jeweils in der Datei konfigurierte IP-Adresse; diese IP-Adressen muessen gegebenenfalls unabhaengig von `main.py` angepasst werden. `KF_Ball.py` und `KF_Roboter.py` zeigen die jeweiligen Filter-Simulationen als Plot.

## Aktueller Entwicklungsstand

Die aktive Hauptroutine in `main.py` implementiert momentan direkt das Anfahren des Balls. Die Klassen aus `Bewegungen.py` und `Verhalten.py` sind Bausteine fuer eine weiterentwickelte Steuerung, werden von `main.py` aber noch nicht verwendet. Auch die Strategieauswahl in `Strategie.py` und `WeltModell.verarbeite_vision_daten()` sind noch nicht implementiert.