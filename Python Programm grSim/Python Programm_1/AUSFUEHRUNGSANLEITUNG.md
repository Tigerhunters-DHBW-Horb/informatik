# Ausfuehrungsanleitung

Diese Anleitung beschreibt, welche Python-Dateien eigenstaendige Programme sind, wie sie gestartet werden und welche Einstellungen vor dem Start geprueft werden muessen.

## 1. Vorbereitung

### Simulator und Netzwerk

Starte zuerst grSim und pruefe, ob SSL-Vision-Daten gesendet werden. Die Programme verwenden standardmaessig:

- SSL-Vision-Multicast: `224.5.23.2`, UDP-Port `10020`
- grSim-Befehle: UDP-Port `20011`

Der Rechner, auf dem Python laeuft, muss den Simulator im Netzwerk erreichen koennen. Firewall-Regeln und Netzwerkschnittstellen muessen UDP- und Multicast-Verkehr erlauben.

### Python und Pakete

Oeffne PowerShell im Projektordner `Python Programm_1`. Falls du im uebergeordneten Projektordner stehst, wechsle mit:

```powershell
cd ".\Python Programm_1"
```

Optional kannst du eine virtuelle Umgebung erstellen und aktivieren:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installiere die benoetigten Pakete mit dem Python-Interpreter, den du spaeter zum Starten verwendest:

```powershell
python -m pip install numpy matplotlib filterpy pynput protobuf
```

## 2. Programme starten

Starte jeweils nur das Programm, das du gerade testen moechtest. Die Kommandos werden aus `Python Programm_1` ausgefuehrt.

### `main.py` - Roboter faehrt zum Ball

```powershell
python main.py
```

Vor dem Start in `main.py` pruefen:

- `VM_IP`: Adresse des Rechners mit grSim (voreingestellt: `192.168.42.41`)
- `ROBOTER_ID`: Roboter-ID (voreingestellt: `1`)
- `TEAM_GELB`: `True` fuer Gelb, `False` fuer Blau

Das Programm empfaengt Vision-Daten und sendet fortlaufend Fahrbefehle. Es steuert den Roboter zum Ball und soll in etwa 120 mm Abstand anhalten. Mit `Ctrl+C` beenden; dabei wird ein Stoppbefehl gesendet.

### `steuerung.py` - manuelle Tastatursteuerung

```powershell
python steuerung.py
```

Pruefe vorher `VM_IP`, `ROBOTER_ID` und `TEAM_GELB` in der Datei. Die aktuelle IP-Adresse ist `192.168.0.115`. Die Steuerung verwendet `pynput` und sendet wiederholt Befehle:

- `W` / `S`: vorwaerts / rueckwaerts
- `A` / `D`: seitwaerts links / rechts
- `Q` / `E`: links / rechts drehen
- `Leertaste`: stoppen
- `ESC`: beenden und den Roboter stoppen

### `test_sender.py` - einzelne Fahrbefehle testen

```powershell
python test_sender.py
```

Pruefe in der Datei `VM_IP` (aktuell `192.168.95.255`), `ROBOTER_ID` (aktuell `0`) und `TEAM_GELB`. Waehle im Terminal einen Fahrmodus. Der gewaehlte Befehl wird anschliessend wiederholt gesendet, bis du `Ctrl+C` drueckst. Beim Beenden sendet das Skript einen Stoppbefehl.

### `test_receiver.py` - Vision-Empfang pruefen

```powershell
python test_receiver.py
```

Das Skript zeigt empfangene Ball- und Roboterpositionen an. Es sendet keine Fahrbefehle. Beenden mit `Ctrl+C`.

### Kalman-Filter-Simulationen

```powershell
python KF_Ball.py
python KF_Roboter.py
```

Die Skripte simulieren verrauschte Messungen und zeigen den Filterverlauf als Plot. Sie steuern keinen Roboter. Zum Schliessen das Plotfenster schliessen.

## 3. Module nicht einzeln starten

Die folgenden Dateien sind Bausteine, die von anderen Skripten importiert werden. Sie haben keinen eigenen Programmeinstieg:

- `Kommunikation.py`
- `WeltModell.py`
- `geometrie.py`
- `Bewegungen.py`
- `Verhalten.py`
- `Strategie.py`
- die Dateien in `protos/`

Diese Module also nicht mit `python Modulname.py` als Programm starten. Insbesondere ist `Strategie.py` noch nicht fertig implementiert.

## 4. Wichtige Hinweise

- `main.py`, `steuerung.py` und `test_sender.py` koennen denselben Roboter bewegen. Fuehre immer nur eines dieser Steuerprogramme gleichzeitig aus, sonst koennen sich die Befehle gegenseitig ueberschreiben.
- Die IP-Adressen in den Skripten unterscheiden sich. Aendere die jeweilige `VM_IP` passend zu deinem Netzwerk; das Aendern in `main.py` aktualisiert nicht automatisch die anderen Dateien.
- Verwende dieselbe virtuelle Umgebung fuer Installation und Ausfuehrung. Bei `ModuleNotFoundError` zuerst pruefen, ob das Paket in genau diesem Interpreter installiert ist.
- Der Ordner `protos/` muss neben den Skripten erhalten bleiben. Er enthaelt die generierten Module fuer SSL- und grSim-Nachrichten.