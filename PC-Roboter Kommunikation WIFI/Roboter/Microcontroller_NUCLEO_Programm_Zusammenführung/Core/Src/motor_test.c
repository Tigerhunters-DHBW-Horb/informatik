/**
 ******************************************************************************
 * @file    motor_test.c
 * @brief   Nicht-blockierende Testsequenz für die Antriebs-ESCs.
 *
 *  Ablauf:
 *    WAIT_START -> Tastendruck -> ARM -> Motor 1 bis 4 einzeln ->
 *    M1-M4 zusammen -> DONE
 *
 *  Tastendruck während des Laufs = NOT-AUS.
 ******************************************************************************
 */

#include "motor_test.h"
#include "esc_driver.h"

#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>


/* ==========================================================================
 * AKTIVE MOTOREN
 * --------------------------------------------------------------------------
 * Motor-Indizes:
 *
 * M1 = 0
 * M2 = 1
 * M3 = 2
 * M4 = 3
 *
 * Aktuell werden alle vier Motoren getestet.
 * ========================================================================== */

#define ACTIVE_MOTOR_COUNT   4U

static const uint8_t ACTIVE_MOTORS[ACTIVE_MOTOR_COUNT] =
{
    0U,     /* M1 */
    1U,     /* M2 */
    2U,     /* M3 */
    3U      /* M4 */
};


/* ==========================================================================
 * RICHTUNGS-VORZEICHEN
 * --------------------------------------------------------------------------
 * +1 = normale Richtung
 * -1 = invertierte Richtung
 *
 * Die Vorzeichen fuer einen gemeinsamen lokalen Test koennen hier je Motor
 * angepasst werden, falls die Verdrahtung die Drehrichtung invertiert.
 * ========================================================================== */

static const int8_t DIR_SIGN[ACTIVE_MOTOR_COUNT] =
{
    +1,     /* M1 */
    +1,     /* M2 */
    +1,     /* M3 */
    +1      /* M4 */
};


/* ==========================================================================
 * LOGGING UEBER ST-LINK VCP
 * ========================================================================== */

static void test_log(const char *fmt, ...)
{
#if CFG_ENABLE_LOG
    char buf[96];

    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if (n > 0)
    {
        HAL_UART_Transmit(&LOG_UART_HANDLE,
                          (uint8_t *)buf,
                          (uint16_t)((n < (int)sizeof(buf)) ? n : (int)sizeof(buf)),
                          50);
    }
#else
    (void)fmt;
#endif
}


/* ==========================================================================
 * TASTER ENTPRELLT
 * ========================================================================== */

static uint8_t  btn_stable   = 0;
static uint8_t  btn_last_raw = 0;
static uint32_t btn_change_t = 0;

static uint8_t button_pressed_edge(uint32_t now)
{
    uint8_t raw;

    raw = (HAL_GPIO_ReadPin(BTN_PORT, BTN_PIN) == BTN_ACTIVE_STATE) ? 1U : 0U;

    if (raw != btn_last_raw)
    {
        btn_last_raw = raw;
        btn_change_t = now;
    }

    if (((now - btn_change_t) >= BTN_DEBOUNCE_MS) &&
        (btn_stable != btn_last_raw))
    {
        btn_stable = btn_last_raw;

        if (btn_stable == 1U)
        {
            return 1U;
        }
    }

    return 0U;
}


/* ==========================================================================
 * LED-HILFSFUNKTIONEN
 * ========================================================================== */

static void led_set(uint8_t on)
{
    GPIO_PinState pin_state;

    if (on)
    {
        pin_state = LED_ACTIVE_STATE;
    }
    else
    {
        pin_state = (LED_ACTIVE_STATE == GPIO_PIN_SET) ? GPIO_PIN_RESET
                                                       : GPIO_PIN_SET;
    }

    HAL_GPIO_WritePin(LED_PORT, LED_PIN, pin_state);
}


static void led_blink(uint32_t now, uint32_t period_ms)
{
    if (((now / period_ms) & 1U) != 0U)
    {
        led_set(1U);
    }
    else
    {
        led_set(0U);
    }
}


/* ==========================================================================
 * SEGMENT-DEFINITION
 * ========================================================================== */

typedef struct
{
    float    target;
    uint32_t dur_ms;
    uint8_t  is_ramp;
} seg_t;


#define M  (TEST_THROTTLE_MAX)


/* Einzelmotor-Sequenz:
 * vorwaerts, stopp, rueckwaerts, stopp
 */
static const seg_t k_motor_seq[] =
{
    { +M, TEST_RAMP_MS,  1U },
    { +M, TEST_HOLD_MS,  0U },
    {  0, TEST_RAMP_MS,  1U },
    {  0, TEST_PAUSE_MS, 0U },

#if TEST_BIDIRECTIONAL
    { -M, TEST_RAMP_MS,  1U },
    { -M, TEST_HOLD_MS,  0U },
    {  0, TEST_RAMP_MS,  1U },
    {  0, TEST_PAUSE_MS, 0U },
#endif
};

#define N_MOTOR_SEG  (sizeof(k_motor_seq) / sizeof(k_motor_seq[0]))


/* Gemeinsame Sequenz:
 * M1 und M4 zusammen vorwaerts und rueckwaerts.
 */
static const seg_t k_all_seq[] =
{
    { +M, TEST_RAMP_MS,  1U },
    { +M, TEST_HOLD_MS,  0U },
    {  0, TEST_RAMP_MS,  1U },
    {  0, TEST_PAUSE_MS, 0U },

#if TEST_BIDIRECTIONAL
    { -M, TEST_RAMP_MS,  1U },
    { -M, TEST_HOLD_MS,  0U },
    {  0, TEST_RAMP_MS,  1U },
    {  0, TEST_PAUSE_MS, 0U },
#endif
};

#define N_ALL_SEG  (sizeof(k_all_seq) / sizeof(k_all_seq[0]))


#define ALL_MOTORS  0xFFU


/* ==========================================================================
 * ZUSTANDSMASCHINE
 * ========================================================================== */

typedef enum
{
    ST_WAIT_START = 0,
    ST_ARM,
    ST_MOTOR_SEQ,
    ST_ALL_SEQ,
    ST_DONE,
    ST_REMOTE,
    ST_ESTOP
} test_state_t;


static test_state_t state;
static uint32_t     phase_start;
static uint16_t     seg_idx;
static uint8_t      motor_idx;
static float        from_val;
static uint32_t     remote_last_command;
static uint8_t      remote_active;
static uint8_t      remote_lockout;


/* ==========================================================================
 * MOTORWERT ANWENDEN
 * ========================================================================== */

static void apply_val(uint8_t motor_sel, float v)
{
    if (motor_sel == ALL_MOTORS)
    {
        /*
         * Gemeinsamer Test:
         * Alle vier Motoren bekommen das Signal.
         */
        for (uint8_t i = 0U; i < ACTIVE_MOTOR_COUNT; i++)
        {
            esc_set_signed(ACTIVE_MOTORS[i], v * (float)DIR_SIGN[i]);
        }
    }
    else
    {
        /*
         * Einzelmotor-Test:
         * Motor wird ohne DIR_SIGN getestet.
         */
        esc_set_signed(motor_sel, v);
    }
}


/* Alle Motoren sicher stoppen.
 * Auch M2 und M3 werden auf 1500 us gesetzt.
 */
static void all_stop_safe(void)
{
    esc_all_stop();
}


/* ==========================================================================
 * SEGMENTE AUSFUEHREN
 * ========================================================================== */

static uint8_t run_segments(uint32_t now,
                            const seg_t *list,
                            uint16_t n,
                            uint8_t motor_sel)
{
    const seg_t *s;
    uint32_t elapsed;
    float v;

    s = &list[seg_idx];
    elapsed = now - phase_start;

    if (s->is_ramp)
    {
        if (elapsed >= s->dur_ms)
        {
            v = s->target;
        }
        else
        {
            v = from_val +
                (s->target - from_val) *
                ((float)elapsed / (float)s->dur_ms);
        }
    }
    else
    {
        v = s->target;
    }

    apply_val(motor_sel, v);

    if (elapsed >= s->dur_ms)
    {
        from_val = s->target;
        phase_start = now;
        seg_idx++;

        if (seg_idx >= n)
        {
            seg_idx = 0U;
            return 1U;
        }
    }

    return 0U;
}


/* ==========================================================================
 * OEFFENTLICHE API
 * ========================================================================== */

void motor_test_init(void)
{
    esc_init();
    all_stop_safe();

    state = ST_WAIT_START;
    phase_start = HAL_GetTick();
    seg_idx = 0U;
    motor_idx = 0U;
    from_val = 0.0f;
    remote_last_command = phase_start;
    remote_active = 0U;
    remote_lockout = 0U;

    btn_last_raw = (HAL_GPIO_ReadPin(BTN_PORT, BTN_PIN) == BTN_ACTIVE_STATE) ? 1U : 0U;
    btn_stable   = btn_last_raw;
    btn_change_t = phase_start;

    test_log("\r\n=== SSL T3100 - ESC Bring-up-Test ===\r\n");
    test_log("Aktive Motoren: M1, M2, M3, M4\r\n");
    test_log("PWM: 1000-2000 us | Stop: 1500 us\r\n");
    test_log("Throttle-Limit: %d %%\r\n", (int)(TEST_THROTTLE_MAX * 100.0f));
    test_log("Taste: ESC-Test starten; PC-Befehl: Fernsteuerung; Taste dort = NOT-AUS.\r\n");
}


void motor_test_remote_command(uint8_t robot_id, float vx, float vy,
                              float omega)
{
    float x;
    float y;
    float rotation;
    float wheel[ESC_MOTOR_COUNT];
    float largest;

    if (robot_id != REMOTE_ROBOT_ID ||
        state == ST_ESTOP ||
        remote_lockout != 0U ||
        !isfinite(vx) || !isfinite(vy) || !isfinite(omega))
    {
        return;
    }

    if (state != ST_REMOTE)
    {
        test_log("PC-Fernsteuerung aktiv (ID %u); lokaler ESC-Test gesperrt.\r\n",
                 (unsigned)robot_id);
    }
    state = ST_REMOTE;
    remote_active = 1U;
    remote_last_command = HAL_GetTick();

    x = vx / REMOTE_MAX_LINEAR_SPEED_MPS;
    y = vy / REMOTE_MAX_LINEAR_SPEED_MPS;
    rotation = omega / REMOTE_MAX_OMEGA_RAD_S;

    /* Standard-X-Omni/Mecanum-Mischung: FL, FR, RL, RR. */
    wheel[0] = (x - y - rotation) * REMOTE_M1_SIGN;
    wheel[1] = (x + y + rotation) * REMOTE_M2_SIGN;
    wheel[2] = (x + y - rotation) * REMOTE_M3_SIGN;
    wheel[3] = (x - y + rotation) * REMOTE_M4_SIGN;

    largest = 1.0f;
    for (uint8_t motor = 0U; motor < ESC_MOTOR_COUNT; ++motor)
    {
        const float magnitude = fabsf(wheel[motor]);
        if (magnitude > largest)
        {
            largest = magnitude;
        }
    }

    for (uint8_t motor = 0U; motor < ESC_MOTOR_COUNT; ++motor)
    {
        esc_set_signed(motor, (wheel[motor] / largest) * TEST_THROTTLE_MAX);
    }
}


void motor_test_run(void)
{
    uint32_t now;
    uint8_t edge;

    now = HAL_GetTick();
    edge = button_pressed_edge(now);

#if CFG_ENABLE_BATTERY_MON
    extern uint8_t battery_undervoltage(uint32_t now);

    if ((state != ST_WAIT_START) &&
        (state != ST_ESTOP) &&
        battery_undervoltage(now))
    {
        all_stop_safe();
        test_log("!! UNTERSPANNUNG -> NOT-AUS\r\n");
        state = ST_ESTOP;
        return;
    }
#endif

    /*
     * Globaler NOT-AUS:
     * Wenn der Test aktiv ist und der Taster gedrueckt wird,
     * werden alle Motoren sofort gestoppt.
     */
    if (edge &&
        ((state == ST_ARM) ||
         (state == ST_MOTOR_SEQ) ||
        (state == ST_ALL_SEQ) ||
        (state == ST_REMOTE)))
    {
        all_stop_safe();
        test_log("!! NOT-AUS ausgeloest\r\n");
        if (state == ST_REMOTE)
        {
            remote_lockout = 1U;
        }
        state = ST_ESTOP;
        return;
    }

    switch (state)
    {
        case ST_WAIT_START:
            all_stop_safe();
            led_blink(now, 500U);

            if (edge)
            {
                test_log("Start. Arming...\r\n");

                from_val = 0.0f;
                seg_idx = 0U;
                motor_idx = 0U;
                phase_start = now;

                state = ST_ARM;
            }
            break;


        case ST_ARM:
            all_stop_safe();
            led_blink(now, 120U);

            if ((now - phase_start) >= TEST_ARM_TIME_MS)
            {
                test_log("Armed. Test Motor M%u...\r\n",
                         (unsigned)(ACTIVE_MOTORS[0] + 1U));

                from_val = 0.0f;
                seg_idx = 0U;
                motor_idx = 0U;
                phase_start = now;

                state = ST_MOTOR_SEQ;
            }
            break;


        case ST_MOTOR_SEQ:
            led_blink(now, 120U);

            if (run_segments(now,
                             k_motor_seq,
                             N_MOTOR_SEG,
                             ACTIVE_MOTORS[motor_idx]))
            {
                motor_idx++;
                from_val = 0.0f;
                phase_start = now;

                if (motor_idx >= ACTIVE_MOTOR_COUNT)
                {
                    test_log("Einzeltests fertig. Jetzt M1-M4 zusammen...\r\n");

                    seg_idx = 0U;
                    from_val = 0.0f;
                    phase_start = now;

                    state = ST_ALL_SEQ;
                }
                else
                {
                    test_log("Test Motor M%u...\r\n",
                             (unsigned)(ACTIVE_MOTORS[motor_idx] + 1U));
                }
            }
            break;


        case ST_ALL_SEQ:
            led_blink(now, 120U);

            if (run_segments(now,
                             k_all_seq,
                             N_ALL_SEG,
                             ALL_MOTORS))
            {
                all_stop_safe();

                test_log("=== Sequenz beendet. PASS. Taste = Neustart. ===\r\n");

                state = ST_DONE;
            }
            break;


        case ST_DONE:
            all_stop_safe();
            led_set(1U);

            if (edge)
            {
                test_log("Neustart.\r\n");

                state = ST_WAIT_START;
                phase_start = now;
                seg_idx = 0U;
                motor_idx = 0U;
                from_val = 0.0f;
            }
            break;

        case ST_REMOTE:
            if (remote_active != 0U &&
                (now - remote_last_command) >= REMOTE_COMMAND_TIMEOUT_MS)
            {
                all_stop_safe();
                remote_active = 0U;
                test_log("Fernsteuerung: Timeout, Motoren gestoppt.\r\n");
            }
            if (remote_active != 0U)
            {
                led_set(1U);
            }
            else
            {
                all_stop_safe();
                led_blink(now, 500U);
            }
            break;

        case ST_ESTOP:
        default:
            all_stop_safe();
            led_blink(now, 80U);

            if (edge && remote_lockout == 0U)
            {
                test_log("NOT-AUS quittiert. Taste = Start.\r\n");

                state = ST_WAIT_START;
                phase_start = now;
                seg_idx = 0U;
                motor_idx = 0U;
                from_val = 0.0f;
            }
            else if (edge)
            {
                test_log("Fernsteuerungs-Not-Aus verriegelt; Neustart erforderlich.\r\n");
            }
            break;
    }
}
