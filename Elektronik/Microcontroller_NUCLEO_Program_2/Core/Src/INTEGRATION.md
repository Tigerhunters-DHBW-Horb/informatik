# SSL T3100 – Nucleo-Ansteuerung per ESP32

Der ESP32 nimmt die Roboterbefehle per UDP entgegen und leitet sie über UART1
an die **NUCLEO-H753ZI** weiter. Die Nucleo-Firmware setzt die empfangenen
Geschwindigkeiten mit Kinematik, Hall-Sensoren und PID-Reglern in vier
Motorbefehle um.

## UART-Verbindung

| ESP32 | NUCLEO-H753ZI | Funktion |
|-------|---------------|----------|
| GPIO2 (UART1 TX) | PB7 (USART1 RX) | Befehle zum Nucleo |
| GND | GND | Gemeinsame Masse |

Die UART-Verbindung verwendet **115200 Baud, 8N1** und 3,3-V-Logik. PB7 wird
als USART1-RX mit Alternate Function 7 konfiguriert. Die Leitung zum Nucleo ist
nur empfangend; USART1-TX wird nicht verwendet.

## Befehlsformat

Der ESP32 sendet pro empfangenem Roboterbefehl eine ASCII-Zeile mit `\n`:

```text
RBT1,<roboter-id>,<vx>,<vy>,<omega>\n
```

`vx` und `vy` sind lineare Geschwindigkeiten in m/s, `omega` ist die
Drehgeschwindigkeit in rad/s. Beispiel:

```text
RBT1,0,0.500000,0.000000,0.000000
```

Die Nucleo-Firmware nimmt ID `0`, lineare Sollwerte bis ±5 m/s sowie
Drehgeschwindigkeiten bis ±6 rad/s an. Ungültige Zeilen und andere IDs werden
ignoriert. Nach 250 ms ohne gültigen Befehl wird beim nächsten 20-ms-Regeltakt
ein Stopp-Sollwert an die Motorsteuerung übergeben.

## Motorsteuerung und Inbetriebnahme

- Die UART-Befehle laufen nach dem ESC-Arm-Intervall in die bestehende
  Closed-Loop-Kinematik; Hall-Sensoren und vier PID-Regler steuern die
  einzelnen Räder.
- `TEST_THROTTLE_MAX` in `Core/Inc/test_config.h` begrenzt den ESC-Ausgang
  aktuell auf 15 %. Für erste Tests Räder freiheben und diese Begrenzung
  beibehalten.
- Vor dem Einschalten AM32-Bidirectional-/3D-Modus, TIM1-Taktfrequenz in
  `ESC_TIM_CLOCK_HZ` und die Zuordnung M1–M4 zum Pinout prüfen.
- Die ESCs erhalten nach Reset zunächst 1500 µs für drei Sekunden. Ohne
  gültige UART-Befehle bleiben die Motoren auf Stopp.
