/**
 ******************************************************************************
 * @file    esc_driver.h
 * @brief   Treiber fuer die 4 Antriebs-ESCs (AM32, Standard-PWM) an TIM1
 ******************************************************************************
 */
#ifndef ESC_DRIVER_H
#define ESC_DRIVER_H

#include "test_config.h"
#include <stdint.h>

/**
 * @brief Initialisiert TIM1 (PSC/ARR aus config), startet PWM auf allen
 *        Kanaelen und legt alle ESCs auf Stopp-Pegel.
 *        Aktiviert ausserdem den Main Output (MOE) - bei TIM1 zwingend!
 */
void esc_init(void);

/**
 * @brief Setzt einen Motor ueber einen vorzeichenbehafteten Wert.
 * @param motor 0..ESC_MOTOR_COUNT-1
 * @param value -1.0 = volle Rueckwaerts, 0.0 = Stopp, +1.0 = volle Vorwaerts.
 *              Wird intern auf +-TEST_THROTTLE_MAX begrenzt.
 */
void esc_set_signed(uint8_t motor, float value);

/** @brief Setzt direkt eine Pulsbreite (us) auf einen Motor (geklemmt). */
void esc_set_pulse_us(uint8_t motor, uint16_t pulse_us);

/** @brief Alle Motoren sofort auf Stopp-Pegel. */
void esc_all_stop(void);

#endif /* ESC_DRIVER_H */
