# SSL T3100 – ESC Bring-up-Test (Integration)

Die Anleitung fuer den Gesamtaufbau PC → ESP32 → NUCLEO → Motoren steht in
[`../../README.md`](../../README.md). Dieser Test bleibt als lokaler
Inbetriebnahmemodus im selben NUCLEO-Projekt erhalten.

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
2. **USART1 RX** (PB7) → Asynchronous, **115200** Baud; ESP32-TX an PB7,
   gemeinsame Masse.
3. **USART3** (ST-LINK VCP, PD8/PD9) → Asynchronous, **115200** Baud.
4. NUCLEO-Button PC13 → lokaler Teststart/Not-Aus; Status-LED PB0.
5. *(optional)* **I2C2** (PF0/PF1) für INA226, falls Batteriemonitor genutzt.
6. **TIM6** → Basistimer mit 20 kHz Update-Interrupt zur Hall-Abtastung.
   TIM8 bleibt fuer die Dribbler-PWM reserviert.

## main.c
```c
/* USER CODE BEGIN Includes */
#include "motor_test.h"
/* USER CODE END Includes */

int main(void)
{
  /* ... CubeMX-Inits (HAL_Init, Clock, MX_TIM1_Init, MX_TIM6_Init, ...) */

  /* USER CODE BEGIN 2 */
  motor_test_init();
  if (HAL_TIM_Base_Start_IT(&htim6) != HAL_OK)
  {
    Error_Handler();
  }
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
5. Der erste gueltige PC-Befehl uebernimmt die Motoren; danach ist der lokale
   Test bis zum Neustart gesperrt. Im Fernsteuerungsmodus verriegelt ein
   Tastendruck den Not-Aus bis zum Neustart.

## Hall-Drehzahlregelung
- Die Hall-Eingaenge aus dem Pinout werden mit TIM6 bei 20 kHz abgetastet.
  Sie werden nicht per EXTI behandelt, weil mehrere Signale dieselben
  EXTI-Leitungsnummern teilen. TIM8_CH2 bleibt fuer die Dribbler-PWM frei.
- Die Fernsteuerung verwendet die Hall-Rueckmeldung fuer eine PI-Regelung
  pro Rad. Der lokale ESC-Bring-up-Test bleibt absichtlich open-loop.
- `test_config.h` enthaelt Hall-Uebergaenge pro Radumdrehung, Radumfang und
  PI-Parameter. Der Nanotec DF45L024048-A2 hat 16 Pole; alle sechs Hall-
  Zustandswechsel pro Polpaar ergeben 48 Uebergaenge pro Motorumdrehung.
  Bei Getriebe zwischen Motor und Rad muss der Uebergangswert die
  Getriebeuebersetzung beruecksichtigen.
- Die Hall-Signalpegel muessen fuer den STM32 geeignet sein. Bei offenen
  Kollektorausgaengen einen passenden Pull-up vorsehen.

## Spätere Erweiterung
- `CFG_ENABLE_BATTERY_MON = 1` für INA226-Unterspannungsschutz (erst wenn
  I2C2 verifiziert ist).
- Throttle-Limit für den Bodentest schrittweise anheben.
