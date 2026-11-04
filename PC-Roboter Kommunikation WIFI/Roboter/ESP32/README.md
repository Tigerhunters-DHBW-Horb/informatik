# ESP32: UDP-Empfänger

Dieses Arduino-Projekt verbindet sich als WLAN-Station mit dem PC-Hotspot und lauscht auf UDP-Port `4210`. Die Zugangsdaten stehen am Anfang von [`ESP32.ino`](./ESP32.ino); `ROBOT_ID` muss pro Roboter eindeutig gesetzt werden. Alle ESP32 empfangen denselben Broadcast, aber jeder ruft `onRobotCommand` nur mit den Geschwindigkeiten seines eigenen IDs auf.

1. Öffne `ESP32.ino` in der Arduino IDE und wähle ein passendes ESP32-Board.
2. Trage SSID und Passwort des PC-Hotspots sowie die Roboter-ID ein.
3. Lade das Programm hoch und öffne den seriellen Monitor mit `115200` Baud.
4. Starte den PC-Sender aus [`../../PC/README.md`](../../PC/README.md).

Die Funktion `onRobotCommand(vx, vy, omega)` gibt die empfangenen Werte derzeit über die serielle Schnittstelle aus. Verbinde dort die vorhandene Motorsteuerung. Die Werte sind `VX` und `VY` in m/s sowie `OMEGA` in rad/s.

Der PC muss den Hotspot aktiv halten. Die ESP32 erhalten ihre IP-Adresse per DHCP; für Broadcasts muss der Sender die passende Hotspot-Subnetzadresse verwenden, falls `255.255.255.255` nicht weitergeleitet wird.
