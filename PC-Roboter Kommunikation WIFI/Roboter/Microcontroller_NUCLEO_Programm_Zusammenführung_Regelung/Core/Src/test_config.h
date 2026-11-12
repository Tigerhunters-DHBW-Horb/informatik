/**
 ******************************************************************************
 * @file    test_config.h
 * @brief   Zentrale Konfiguration fuer den MC-only ESC-Bring-up-Test
 *          SSL RoboCup Roboter T3100 - NUCLEO-H753ZI
 *
 *  >>> HIER wird alles eingestellt. Keine "magischen Zahlen" im Code. <<<
 *
 *  Testumfang Test 1:
 *    - Nur die 4 Antriebs-ESCs (M1-M4, AM32, Standard-PWM)
 *    - Feste, automatisch ablaufende Sequenz, Start per Tastendruck
 *    - Bidirektional (Omniwheels), Roboter AUFGEBOCKT
 *    - Lokaler Test open-loop; Fernsteuerung mit Hall-Drehzahlregelung
 *    - Status nur ueber UART
 ******************************************************************************
 */
#ifndef TEST_CONFIG_H
#define TEST_CONFIG_H

#include "main.h"   /* zieht HAL + die CubeMX-Handles (htim1, huart3, ...) */

/* ==========================================================================
 * 1) SUBSYSTEM-SCHALTER
 * ========================================================================== */
#define CFG_ENABLE_DRIVE_ESCS     1   /* M1-M4 Antriebs-ESCs                 */
#define CFG_ENABLE_BATTERY_MON    0   /* INA226 Unterspannung (empfohlen=1,  */
                                      /* erst auf 1 wenn I2C2 verifiziert!)  */
#define CFG_ENABLE_LOG            1   /* UART-Statusausgabe ueber VCP        */
                                      /* 0 = aus (linkt ohne USART)          */

/* ==========================================================================
 * HALL-SENSOREN / DREHZAHLREGELUNG
 * --------------------------------------------------------------------------
 * DF45L024048-A2: 16 Pole = 8 Polpaare. Bei Auswertung aller sechs
 * Hall-Zustandswechsel je elektrischer Umdrehung ergeben sich 48 Wechsel
 * je Rotorumdrehung. Bei einem Getriebe HALL_TRANSITIONS_PER_WHEEL_REV
 * entsprechend mit dem Uebersetzungsverhaeltnis multiplizieren.
 * ========================================================================== */
#define HALL_M1_A_PORT             GPIOA
#define HALL_M1_A_PIN              GPIO_PIN_15
#define HALL_M1_B_PORT             GPIOF
#define HALL_M1_B_PIN              GPIO_PIN_7
#define HALL_M1_C_PORT             GPIOF
#define HALL_M1_C_PIN              GPIO_PIN_6

#define HALL_M2_A_PORT             GPIOC
#define HALL_M2_A_PIN              GPIO_PIN_8
#define HALL_M2_B_PORT             GPIOC
#define HALL_M2_B_PIN              GPIO_PIN_6
#define HALL_M2_C_PORT             GPIOC
#define HALL_M2_C_PIN              GPIO_PIN_5

#define HALL_M3_A_PORT             GPIOG
#define HALL_M3_A_PIN              GPIO_PIN_12
#define HALL_M3_B_PORT             GPIOG
#define HALL_M3_B_PIN              GPIO_PIN_9
#define HALL_M3_C_PORT             GPIOE
#define HALL_M3_C_PIN              GPIO_PIN_1

#define HALL_M4_A_PORT             GPIOG
#define HALL_M4_A_PIN              GPIO_PIN_8
#define HALL_M4_B_PORT             GPIOG
#define HALL_M4_B_PIN              GPIO_PIN_5
#define HALL_M4_C_PORT             GPIOG
#define HALL_M4_C_PIN              GPIO_PIN_6

#define HALL_SAMPLE_FREQ_HZ        20000U
#define HALL_SAMPLE_TIMER_TICK_HZ  1000000U
#define HALL_SAMPLE_TIMER_CLOCK_HZ 64000000UL /* TIM6, APB1 DIV1 */
#define HALL_TRANSITIONS_PER_WHEEL_REV 48U
#define HALL_WHEEL_CIRCUMFERENCE_M 0.050f
#define HALL_CONTROL_PERIOD_MS     50U
#define HALL_SPEED_FILTER_ALPHA    0.5f
#define HALL_PI_KP                 0.35f
#define HALL_PI_KI                 0.8f
#define HALL_FEEDFORWARD_GAIN      0.5f
#define HALL_MOTION_TIMEOUT_MS     2000U

/* ==========================================================================
 * 2) TIMER / PWM  (ESC-Signal = Standard-Servo-PWM 1000..2000 us)
 * --------------------------------------------------------------------------
 *  WICHTIG: ESC_TIM_CLOCK_HZ muss zur CubeMX-Clock-Configuration passen!
 *  (CubeMX -> Clock Configuration -> "APB2 timer clocks" fuer TIM1 ablesen)
 *  esc_init() berechnet daraus PSC (1 Tick = 1 us) und ARR (PWM-Frequenz).
 * ========================================================================== */
#define ESC_TIM_HANDLE            htim1            /* CubeMX-Timer-Handle     */
#define ESC_TIM_INSTANCE          TIM1
#define ESC_TIM_CLOCK_HZ          64000000UL       /* HSI 64 MHz, APB2 DIV1   */
                                                   /* -> PSC 63, ARR 19999    */
#define ESC_PWM_FREQ_HZ           50U              /* 50 Hz = sicher fuer alle*/

/* Pulsbreiten in Mikrosekunden */
#define ESC_PULSE_MIN_US          1000U            /* Vollgas rueckwaerts     */
#define ESC_PULSE_STOP_US         1500U            /* Stopp (Bidir/3D-Mode!)  */
#define ESC_PULSE_MAX_US          2000U            /* Vollgas vorwaerts       */

/* ==========================================================================
 * 3) MOTOR-/KANAL-ZUORDNUNG
 * --------------------------------------------------------------------------
 *  Aus dem Pinout (AF-Spalte, NICHT der Funktionsname - der war teils falsch):
 *    M1 = PA8  -> TIM1_CH1
 *    M2 = PA11 -> TIM1_CH4
 *    M3 = PA10 -> TIM1_CH3
 *    M4 = PA9  -> TIM1_CH2
 *  >>> Diese Zuordnung war im Pinout mit "VERIFY" markiert.
 *      Bitte einmal in CubeMX gegen die echte Verdrahtung pruefen! <<<
 * ========================================================================== */
#define ESC_MOTOR_COUNT           4U

#define ESC_CH_M1                 TIM_CHANNEL_1
#define ESC_CH_M2                 TIM_CHANNEL_4
#define ESC_CH_M3                 TIM_CHANNEL_3
#define ESC_CH_M4                 TIM_CHANNEL_2

/* ==========================================================================
 * 4) TEST-VERHALTEN
 * ========================================================================== */
#define TEST_BIDIRECTIONAL        1       /* 1 = vor+zurueck (Omniwheels)     */

/* Throttle-Grenze als Bruchteil (0.0 .. 1.0). 0.15 = 15 % -> aufgebockt safe.
 * Spaeter fuer Bodentest vorsichtig erhoehen.                               */
#define TEST_THROTTLE_MAX         0.15f

/* Zeiten in Millisekunden */
#define TEST_ARM_TIME_MS          2000U   /* Stopp-Pegel halten -> ESC armt   */
#define TEST_RAMP_MS              1000U   /* Dauer einer Hoch-/Runter-Rampe   */
#define TEST_HOLD_MS              1500U   /* Haltezeit bei Zielthrottle       */
#define TEST_PAUSE_MS             1000U   /* Pause zwischen Schritten         */

/* ==========================================================================
 * 5) PC-FERNSTEUERUNG
 * --------------------------------------------------------------------------
 * Das Mapping nimmt M1=vorne-links, M2=vorne-rechts, M3=hinten-links und
 * M4=hinten-rechts an. Vor der Fahrt auf dem Boden pruefen.
 * ========================================================================== */
#define REMOTE_ROBOT_ID                    0U
#define REMOTE_COMMAND_TIMEOUT_MS          300U
#define REMOTE_MAX_LINEAR_SPEED_MPS        0.5f
#define REMOTE_MAX_OMEGA_RAD_S              2.0f
#define REMOTE_M1_SIGN                     1.0f
#define REMOTE_M2_SIGN                     1.0f
#define REMOTE_M3_SIGN                    -1.0f
#define REMOTE_M4_SIGN                     1.0f

/* ==========================================================================
 * 6) BEDIENUNG / ANZEIGE
 * --------------------------------------------------------------------------
 *  Start-Button + Not-Aus: derselbe Taster.
 *    - Vor der Sequenz : Tastendruck = Start
 *    - Waehrend Lauf   : Tastendruck = NOT-AUS (sofort Stopp + Abbruch)
 *  Wir nutzen den blauen Nucleo-Button (B1 = PC13, active HIGH). Achtung:
 *  PC13 ist auf dem Custom-Board mit der Lichtschranke belegt - nur nutzen,
 *  solange die Lichtschranke nicht angeschlossen ist. Alternativ "BTN" PG10.
 * ========================================================================== */
#define BTN_PORT                  GPIOC
#define BTN_PIN                   GPIO_PIN_13
#define BTN_ACTIVE_STATE          GPIO_PIN_SET    /* blauer Nucleo-Button:    */
                                                  /* gedrueckt = HIGH         */
#define BTN_DEBOUNCE_MS           30U

/* Status-/Heartbeat-LED (Nucleo gruene LED LD1 = PB0; anpassen falls belegt) */
#define LED_PORT                  GPIOB
#define LED_PIN                   GPIO_PIN_0
#define LED_ACTIVE_STATE          GPIO_PIN_SET

/* Statusausgabe ueber die Nucleo-BSP-COM (USART3 am ST-LINK-VCP).
 * Nutzt hcom_uart[COM1], das BSP_COM_Init(COM1,...) in main() initialisiert.
 * Kein eigenes CubeMX-USART noetig.                                         */
#define LOG_UART_HANDLE           hcom_uart[COM1]
#define LOG_BAUD_INFO             115200

/* ==========================================================================
 * 7) BATTERIE-MONITOR (optional, CFG_ENABLE_BATTERY_MON)
 *    INA226 @ I2C2 (PF0=SDA, PF1=SCL). Nur Lesen + Abschaltschwelle.
 * ========================================================================== */
#define BATT_I2C_HANDLE           hi2c2
#define BATT_INA226_ADDR_7B       0x40U           /* je nach A0/A1-Beschaltung*/
#define BATT_CELLS                6U              /* 6S Lipo                  */
#define BATT_CELL_MIN_MV          3300U           /* harte Abschaltschwelle   */
#define BATT_POLL_MS              500U

/* extern-Deklarationen der CubeMX-Handles (in den jeweiligen *.c definiert) */
extern TIM_HandleTypeDef  ESC_TIM_HANDLE;
/* hcom_uart wird vom Nucleo-BSP deklariert (ueber main.h eingebunden).      */
#if CFG_ENABLE_BATTERY_MON
extern I2C_HandleTypeDef  BATT_I2C_HANDLE;
#endif

#endif /* TEST_CONFIG_H */
