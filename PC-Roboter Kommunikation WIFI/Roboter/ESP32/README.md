# ESP32: UDP-Empfänger

Dieses Arduino-Projekt verbindet sich als WLAN-Station mit dem PC-Hotspot und lauscht auf UDP-Port `4210`. Die Zugangsdaten stehen am Anfang von [`ESP32.ino`](./ESP32.ino); `ROBOT_ID` muss pro Roboter eindeutig gesetzt werden. Alle ESP32 empfangen denselben Broadcast, aber jeder ruft `onRobotCommand` nur mit den Geschwindigkeiten seines eigenen IDs auf.

1. Öffne `ESP32.ino` in der Arduino IDE und wähle ein passendes ESP32-Board.
2. Trage SSID und Passwort des PC-Hotspots sowie die Roboter-ID ein.
3. Lade das Programm hoch und öffne den seriellen Monitor mit `115200` Baud.
4. Starte den PC-Sender aus [`../../PC/README.md`](../../PC/README.md).

Für Befehle mit der konfigurierten Roboter-ID gibt `onRobotCommand(vx, vy, omega)` die Werte auf dem USB-Seriell-Monitor aus und leitet sie zusätzlich über UART2 an den Nucleo-H753ZI weiter. Die UART-Zeile lautet `RBT1,<ID>,<vx>,<vy>,<omega>\n`; `VX` und `VY` sind in m/s, `OMEGA` in rad/s. Die UART läuft mit 115200 Baud, 8N1, TX auf ESP32-GPIO17 und RX auf GPIO16. Für die reine Weiterleitung wird nur TX benötigt.

Verbinde GPIO17 mit USART3_RX (PD9) am Nucleo und verbinde die Masseleitungen. Details zur Einrichtung des Nucleo-CMake-Projekts und zur Anzeige über den ST-LINK Virtual COM Port stehen in [`../Nucleo/README.md`](../Nucleo/README.md).

Der PC muss den Hotspot aktiv halten. Die ESP32 erhalten ihre IP-Adresse per DHCP; für Broadcasts muss der Sender die passende Hotspot-Subnetzadresse verwenden, falls `255.255.255.255` nicht weitergeleitet wird. Als Test kann der PC-Sender auch direkt an die ESP32-IP senden.
