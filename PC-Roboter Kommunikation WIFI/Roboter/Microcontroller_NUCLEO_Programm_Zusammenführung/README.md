# PC-zu-Motor-Test: Gesamtaufbau

Dieses STM32CubeIDE-Projekt verbindet den vorhandenen PC-UDP-Sender, den
ESP32-UDP-zu-UART-Empfaenger und den NUCLEO-H753ZI-ESC-Test. Der Datenweg ist:

```text
PC-Python --UDP/Broadcast--> ESP32 --UART1, 115200 8N1--> NUCLEO-H753ZI
                                                              |
                                                              +--> TIM1 PWM --> ESCs M1-M4
```

## Vor dem Einschalten

- Roboter sicher aufbocken; alle vier Raeder muessen frei drehen koennen.
- ESCs muessen fuer bidirektionalen Betrieb (AM32 3D-/Bidirectional-Modus)
  konfiguriert sein. 1500 us ist sonst nicht zwingend der Stoppwert.
- Die Belegung PA8/CH1=M1, PA11/CH4=M2, PA10/CH3=M3 und PA9/CH2=M4 sowie
  die Zuordnung der Motoren zu den Radpositionen verifizieren.
- Das PC-Motorlimit ist absichtlich auf `TEST_THROTTLE_MAX = 0.15` begrenzt.
  Erst nach erfolgreichem Test schrittweise erhoehen.
- `ESC_TIM_CLOCK_HZ` muss zur realen TIM1-Taktfrequenz passen (aktuell 64 MHz).

## Verdrahtung

| ESP32-C6-Zero | NUCLEO-H753ZI |
|---|---|
| UART1 TX, GPIO4 | USART1_RX, PB7 |
| GND | GND |

Nur die ESP32-TX-Leitung ist fuer die Weiterleitung erforderlich. USART3
(PD8/PD9) bleibt der ST-LINK Virtual COM Port fuer Statusmeldungen und ist mit
115200 Baud, 8N1 zu oeffnen.

## Firmware und PC starten

1. `ESP32.ino` in der Arduino IDE oeffnen. WLAN-SSID und Passwort muessen zum
   PC-Hotspot passen; `ROBOT_ID` muss der NUCLEO-Konfiguration
   `REMOTE_ROBOT_ID` entsprechen (Vorgabe: `0`).
2. ESP32-Firmware laden und den ESP32 mit GPIO4/PB7 sowie gemeinsamer Masse
   verbinden.
3. Diesen Ordner in STM32CubeIDE als vorhandenes Projekt importieren. Debug
   bauen und auf die NUCLEO-H753ZI flashen.
4. ST-LINK Virtual COM Port mit 115200 Baud oeffnen. Die Startmeldung zeigt die
   konfigurierte Empfangsschnittstelle USART1/PB7 an.
5. PC-Hotspot aktivieren und den PC-Sender starten. Standard-Port ist UDP
   `4210`, die Roboter-ID ist `0`.

Die grafische Bedienung startet im PC-Ordner:

```bash
python3 udp_control_ui.py
```

Broadcast-IP und Roboter-ID in der Oberflaeche einstellen (Hotspot-Standard
des Senders: `10.42.0.255`, Port `4210`). `W/S` fahren in `+/-X`, `A/D` in
`+/-Y`, `Q/E` drehen in `-/+OMEGA`. Die Tasten oder Schaltflaechen waehrend der
Fahrt halten; `Esc` sendet Stopp und beendet die Uebertragung.

Alternativ ist ein Kommandozeilen-Test moeglich:

```bash
cd "PC-Roboter Kommunikation WIFI/PC"
python3 udp_sender.py --broadcast 10.42.0.255 --robot 0,0.2,0.0,0.0
```

Der Sender wiederholt den Befehl bis `Ctrl+C`; beim Beenden sendet er Stopp.
`--once` sendet nur einmal. Die NUCLEO-Firmware stoppt die ESCs nach
`REMOTE_COMMAND_TIMEOUT_MS` (300 ms), wenn keine gueltigen Befehle mehr
ankommen.

## Betriebsarten und Motor-Mischung

- Nach Reset stehen alle ESCs auf Stopp. Der blaue NUCLEO-Taster startet
  weiterhin den lokalen, automatischen ESC-Test (Einzelmotoren, danach alle
  vier Motoren).
- Der erste gueltige Befehl fuer `REMOTE_ROBOT_ID` uebernimmt die Motoren
  exklusiv fuer die PC-Fernsteuerung und bricht einen laufenden lokalen Test
  ab. Der lokale Test bleibt bis zum Neustart gesperrt.
- Im Fernsteuerungsmodus stoppt der NUCLEO-Taster alle Motoren und verriegelt
  den Not-Aus bis zum Neustart. Ein UDP-/UART-Ausfall stoppt die Motoren nach
  dem Empfangs-Timeout; danach koennen neue Befehle die Fernsteuerung wieder
  aufnehmen.
- Die Fahrbefehle werden mit der Standard-X-Omni/Mecanum-Mischung auf
  `M1=vorne-links`, `M2=vorne-rechts`, `M3=hinten-links`,
  `M4=hinten-rechts` verteilt und auf 15 % Throttle begrenzt. Die linearen
  Referenzwerte sind 0.5 m/s, die Drehreferenz 2 rad/s.
- Wenn ein Rad in die falsche Richtung laeuft, zuerst die reale Rad-/Kanal-
  Zuordnung pruefen und danach das jeweilige `REMOTE_Mx_SIGN` in
  `Core/Src/test_config.h` auf `-1.0f` setzen.

## Quellprogramme und Tests

- PC: [`../../PC/udp_sender.py`](../../PC/udp_sender.py) und
  [`../../PC/udp_control_ui.py`](../../PC/udp_control_ui.py)
- ESP32: [`../ESP32/ESP32.ino`](../ESP32/ESP32.ino)
- NUCLEO: `Core/Src/Main.c`, `Core/Src/nucleo_receiver.c`,
  `Core/Src/motor_test.c` und `Core/Src/esc_driver.c`

Die PC-Protokolltests laufen im PC-Ordner mit:

```bash
python3 -m unittest
```
