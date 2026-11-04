# PC: UDP-Sender für ESP32-Roboter

Aktiviere in den Netzwerkeinstellungen des PCs den WLAN-Hotspot (Access Point), lege SSID und Passwort fest und trage beide Werte in [`ESP32.ino`](../Roboter/ESP32/ESP32.ino) ein. Verbinde die ESP32-Roboter mit diesem WLAN und starte den Sender auf dem PC:

```bash
python3 udp_sender.py --robot 0,1.0,0.0,0.0
```

`VX` und `VY` sind lineare Geschwindigkeiten in m/s, `OMEGA` ist die Drehgeschwindigkeit in rad/s. Für mehrere ESP32 werden Befehle mit unterschiedlichen IDs im selben Broadcast gesendet:

```bash
python3 udp_sender.py \
  --broadcast 192.168.137.255 \
  --robot 0,1.0,0.0,0.0 \
  --robot 1,0.0,0.5,0.0
```

Die Broadcast-Adresse hängt vom Betriebssystem und der Konfiguration des PC-Hotspots ab. `255.255.255.255` ist der Standard; falls der Hotspot diesen begrenzten Broadcast nicht weiterleitet, gib mit `--broadcast` die Broadcast-Adresse des Hotspot-Subnetzes an. Erlaube gegebenenfalls ausgehende UDP-Pakete über den konfigurierten Port (Standard `4210`) in der Firewall.

Mit `--rate 100` lässt sich die Senderate auf 100 Pakete pro Sekunde setzen. `--once` sendet einen einzelnen Testdatensatz. Beim Beenden mit STRG+C wird für alle angegebenen IDs noch ein Stoppbefehl gesendet.

## Protokollversion 1

Alle mehrbyteigen Felder verwenden Network Byte Order (Big Endian). Ein UDP-Paket besteht aus:

| Feld | Größe | Bedeutung |
|---|---:|---|
| Magic | 4 Byte | ASCII `RBT1` |
| Version | 1 Byte | `1` |
| Sitzungs-ID | 4 Byte | Zufällige ID je Senderstart |
| Sequenznummer | 2 Byte | Zähler modulo 65536 innerhalb einer Sitzung |
| Anzahl Befehle | 1 Byte | Anzahl der folgenden Roboterbefehle |
| Roboterbefehl (wiederholt) | 13 Byte | ID (1 Byte), `VX`, `VY`, `OMEGA` (je IEEE-754-Float32) |

Jeder ESP32 empfängt den Broadcast, sucht den Eintrag mit seiner konfigurierten Roboter-ID und ignoriert die Einträge der anderen Roboter. Die Sitzungs-ID erlaubt einen Neustart des PC-Senders, ohne dass der ESP32 alte Sequenznummern als neueste Befehle missversteht. Für eine andere Nutzdatenstruktur muss die Protokollversion angepasst werden.

## Tests

```bash
python3 -m unittest
```
