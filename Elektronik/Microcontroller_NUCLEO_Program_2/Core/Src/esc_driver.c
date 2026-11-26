/**
 ******************************************************************************
 * @file    esc_driver.c
 * @brief   Treiber fuer die 4 Antriebs-ESCs (AM32, Standard-PWM) an TIM1
 ******************************************************************************
 */
#include "esc_driver.h"

/* Motor-Index -> TIM1-Kanal (Reihenfolge wie in test_config.h dokumentiert) */
static const uint32_t s_esc_channel[ESC_MOTOR_COUNT] = {
    ESC_CH_M1,
    ESC_CH_M2,
    ESC_CH_M3,
    ESC_CH_M4,
};

/* ------------------------------------------------------------------------ */
static uint16_t clamp_pulse(uint16_t us)
{
    if (us < ESC_PULSE_MIN_US) us = ESC_PULSE_MIN_US;
    if (us > ESC_PULSE_MAX_US) us = ESC_PULSE_MAX_US;
    return us;
}

/* ------------------------------------------------------------------------ */
void esc_init(void)
{
    /* PSC so, dass 1 Timer-Tick = 1 us  -> bequeme us-Aufloesung der CCR */
    uint32_t psc = (ESC_TIM_CLOCK_HZ / 1000000UL) - 1UL;
    /* ARR aus gewuenschter PWM-Frequenz (Tick = 1 us)                    */
    uint32_t arr = (1000000UL / ESC_PWM_FREQ_HZ) - 1UL;

    __HAL_TIM_SET_PRESCALER(&ESC_TIM_HANDLE, psc);
    __HAL_TIM_SET_AUTORELOAD(&ESC_TIM_HANDLE, arr);

    for (uint8_t m = 0; m < ESC_MOTOR_COUNT; ++m) {
        __HAL_TIM_SET_COMPARE(&ESC_TIM_HANDLE, s_esc_channel[m],
                              ESC_PULSE_STOP_US);
        HAL_TIM_PWM_Start(&ESC_TIM_HANDLE, s_esc_channel[m]);
    }

    /* TIM1 ist ein Advanced-Control-Timer: ohne Main-Output (MOE) kommt
     * KEIN Signal an den Pins an. Daher explizit aktivieren.             */
    __HAL_TIM_MOE_ENABLE(&ESC_TIM_HANDLE);

    esc_all_stop();
}

/* ------------------------------------------------------------------------ */
void esc_set_pulse_us(uint8_t motor, uint16_t pulse_us)
{
    if (motor >= ESC_MOTOR_COUNT) return;
    __HAL_TIM_SET_COMPARE(&ESC_TIM_HANDLE, s_esc_channel[motor],
                          clamp_pulse(pulse_us));
}

/* ------------------------------------------------------------------------ */
void esc_set_signed(uint8_t motor, float value)
{
    /* auf erlaubtes Throttle-Fenster begrenzen */
    if (value >  TEST_THROTTLE_MAX) value =  TEST_THROTTLE_MAX;
    if (value < -TEST_THROTTLE_MAX) value = -TEST_THROTTLE_MAX;

#if !TEST_BIDIRECTIONAL
    if (value < 0.0f) value = 0.0f;   /* Rueckwaerts gesperrt */
#endif

    /* Stopp = 1500 us, +-1.0 entspricht +-500 us */
    float pulse = (float)ESC_PULSE_STOP_US + value * 500.0f;
    esc_set_pulse_us(motor, (uint16_t)(pulse + 0.5f));
}

/* ------------------------------------------------------------------------ */
void esc_all_stop(void)
{
    for (uint8_t m = 0; m < ESC_MOTOR_COUNT; ++m) {
        esc_set_pulse_us(m, ESC_PULSE_STOP_US);
    }
}
