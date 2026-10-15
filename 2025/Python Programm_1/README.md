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
| `vision_terminal.py` | Gibt jedes empfangene SSL-Vision-Paket vollstaendig als lesbaren Protobuf-Text im Terminal aus. |

### Protobuf-Dateien (`protos/`)

Die Dateien `*.proto` beschreiben die Nachrichtenformate von grSim und der SSL-Schnittstellen. Die dazugehoerigen `*_pb2.py`-Dateien sind daraus generierte Python-Module, die zum Lesen und Schreiben dieser Nachrichten benoetigt werden. Die Python-Skripte importieren diese Module zur Laufzeit; der Ordner muss daher erhalten bleiben.

### Weitere Eintraege

`__pycache__/` enthaelt automatisch erzeugte Python-Bytecode-Dateien. `.DS_Store` ist eine automatisch erzeugte macOS-Datei. Beides gehoert nicht zum Programmablauf.

## Voraussetzungen

- Python 3
- Ein gestarteter und erreichbarer grSim-Simulator, der SSL-Vision-Daten sendet
- Netzwerkzugriff auf den Simulator; SSL-Vision verwendet Multicast `224.5.23.2` auf UDP-Port `10006`, grSim-Befehle gehen standardmaessig an UDP-Port `20011`
- Python-Pakete: `numpy`, `matplotlib`, `filterpy`, `pynput` und `protobuf`

Es gibt derzeit keine `requirements.txt` mit festgelegten Versionen. Die Pakete koennen in einem Terminal im Projektordner installiert werden:

```powershell
python -m pip install numpy matplotlib filterpy pynput protobuf
```

## Hauptroutine ausfuehren

1. Starte grSim und stelle sicher, dass SSL-Vision im Netzwerk erreichbar ist.
2. Oeffne ein Terminal im Ordner `Python Programm_1` (oder wechsle aus dem uebergeordneten Ordner mit `cd "Python Programm_1"` dorthin).
3. Pruefe in `main.py` die Konfiguration am Dateianfang:
   - `VM_IP`: IP-Adresse des Rechners mit grSim (aktuell `127.0.0.1`, also derselbe Rechner)
   - `ROBOTER_ID`: ID des zu steuernden Roboters (aktuell `4`)
   - `TEAM_GELB`: `True` fuer das gelbe, `False` fuer das blaue Team
   - `VISION_MULTICAST_IP` und `VISION_PORT`: SSL-Vision Multicast-Adresse und UDP-Port (standardmaessig `224.5.23.2:10006`)
4. Starte das Programm:

```powershell
python main.py
```

`main.py` empfängt SSL-Vision-Daten und sendet fortlaufend Fahrbefehle. Es fährt den konfigurierten Roboter zum Ball und hält ungefähr 120 mm Abstand. Die Debug-Anzeige wird einmal pro Sekunde aktualisiert und leert dafür das Terminal. Sind Ball- oder Robotermessungen länger als 0,5 Sekunden veraltet, wird der Roboter gestoppt, bis wieder frische Messungen eintreffen. Beenden mit `Ctrl+C`; dabei wird ein Stoppbefehl gesendet. Starte das Programm erst, wenn IP-Adresse, Team, Roboter-ID und Simulatorverbindung stimmen.

Beim Start öffnet sich außerdem ein Live-Diagramm: Es vergleicht die von SSL-Vision gemessenen X-/Y-Positionen und Roboterorientierung des ausgewählten Roboters sowie die Ballposition mit den jeweiligen Kalman-Filter-Ausgaben (letzte 10 Sekunden). Die Spielfeldansicht markiert Roboter und Ball; ein grüner Pfeil zeigt Richtung und relative Stärke des aktuellen Fahrbefehls. Der Text darunter enthält die Sollgeschwindigkeit und die tatsächlich gesendeten lokalen X-/Y-Geschwindigkeiten. Das Plotfenster zu schließen beendet das Programm und sendet einen Stoppbefehl. Dafür muss eine grafische Desktop-Sitzung verfügbar sein.

## Weitere Startmoeglichkeiten

Die folgenden Programme werden ebenfalls aus `Python Programm_1` gestartet:

```powershell
python test_receiver.py
python vision_terminal.py
python test_sender.py
python steuerung.py
python KF_Ball.py
python KF_Roboter.py
```

`test_receiver.py` prueft den Vision-Empfang und zeigt erkannte Objekte an. `vision_terminal.py` gibt alle empfangenen SSL-Vision-Pakete als Text aus. Beide Programme verwenden standardmaessig Multicast `224.5.23.2` auf UDP-Port `10006`. `test_sender.py` und `steuerung.py` senden direkt Fahrbefehle an die jeweils in der Datei konfigurierte IP-Adresse; diese IP-Adressen muessen gegebenenfalls unabhaengig von `main.py` angepasst werden. `KF_Ball.py` und `KF_Roboter.py` zeigen die jeweiligen Filter-Simulationen als Plot.

## Aktueller Entwicklungsstand

Die aktive Hauptroutine in `main.py` implementiert momentan direkt das Anfahren des Balls. Die Klassen aus `Bewegungen.py` und `Verhalten.py` sind Bausteine fuer eine weiterentwickelte Steuerung, werden von `main.py` aber noch nicht verwendet. Auch die Strategieauswahl in `Strategie.py` und `WeltModell.verarbeite_vision_daten()` sind noch nicht implementiert.