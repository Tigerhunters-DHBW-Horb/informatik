# SSL T3100 – ESC Bring-up-Test (Integration)

Reiner MC-Test auf der **NUCLEO-H753ZI**, ohne Vision, ohne Kickerboard.
Feste, automatische Sequenz für die 4 Antriebs-ESCs (M1–M4), Start per
Tastendruck, Not-Aus per Tastendruck, **Roboter aufgebockt**.

## Dateien
| Datei | Inhalt |
|------|--------|
| `test_config.h` | **Alle** Einstellungen (Pins, Timer, Zeiten, Limits) |
| `esc_driver.h/.c` | ESC-Treiber (TIM1-PWM, Arm, Set, Stopp) |
| `motor_test.h/.c` | Testsequenz als nicht-blockierende Zustandsmaschine |
| `battery_mon.c` | Optionaler INA226-Unterspannungsschutz (Default: aus) |

Dateien ins Projekt unter `Core/Src` bzw. `Core/Inc` kopieren.

## CubeMX-Konfiguration
1. **TIM1** → PWM Generation auf den vier Kanälen entsprechend Pinout
   (PA8=CH1, PA11=CH4, PA10=CH3, PA9=CH2). PSC/ARR setzt der Code selbst.
2. **USART3** (ST-LINK VCP, PD8/PD9) → Asynchronous, **115200** Baud.
3. **GPIO Button** PG10 → Input, Pull-Up (active-low).
4. **GPIO LED** PB0 → Output (oder gewünschten LED-Pin in `test_config.h`).
5. *(optional)* **I2C2** (PF0/PF1) für INA226, falls Batteriemonitor genutzt.

## main.c
```c
/* USER CODE BEGIN Includes */
#include "motor_test.h"
/* USER CODE END Includes */

int main(void)
{
  /* ... CubeMX-Inits (HAL_Init, Clock, MX_TIM1_Init, MX_USART3_UART_Init, ...) */

  /* USER CODE BEGIN 2 */
  motor_test_init();
  /* USER CODE END 2 */

  while (1)
  {
    /* USER CODE BEGIN 3 */
    motor_test_run();     /* nicht-blockierend, so oft wie möglich aufrufen */
    /* USER CODE END 3 */
  }
}
```

## Vor dem ersten Einschalten unbedingt prüfen
- [ ] **AM32 im Bidirectional-/3D-Mode** (sonst ist 1500 µs nicht „Stopp"
      und Rückwärts geht nicht). Per AM32-Configurator prüfen.
- [ ] **`ESC_TIM_CLOCK_HZ`** in `test_config.h` an die echte TIM1-Taktrate
      anpassen (CubeMX → Clock Configuration). Falsch = falsche Pulsbreiten!
- [ ] **Kanal-Zuordnung M1–M4** gegen die echte Verdrahtung prüfen
      (im Pinout mit „VERIFY" markiert).
- [ ] Propeller… ähm, **Räder frei** (aufgebockt), Umgebung frei.
- [ ] Erst mit `TEST_THROTTLE_MAX = 0.15` (15 %) testen, dann vorsichtig
      erhöhen.

## Ablauf
1. Reset → ESCs disarmed, LED blinkt langsam, Statusausgabe über VCP.
2. Taste → Arming (2 s) → Motor 1 vor/zurück → … → Motor 4 → alle zusammen.
3. Fertig: Dauerlicht, „PASS"-Meldung. Taste = neuer Durchlauf.
4. **Taste während des Laufs = NOT-AUS** (alle Motoren sofort Stopp).

## Spätere Erweiterung
- `CFG_ENABLE_BATTERY_MON = 1` für INA226-Unterspannungsschutz (erst wenn
  I2C2 verifiziert ist).
- Throttle-Limit für den Bodentest schrittweise anheben.
- Danach: Hall/Encoder-Feedback → echte Drehzahlmessung & -regelung.
