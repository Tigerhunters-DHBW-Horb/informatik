/**
 ******************************************************************************
 * @file    motor_test.h
 * @brief   Nicht-blockierende Testsequenz fuer die 4 Antriebs-ESCs.
 *          Start per Tastendruck, Not-Aus per Tastendruck waehrend des Laufs.
 ******************************************************************************
 */
#ifndef MOTOR_TEST_H
#define MOTOR_TEST_H

#include "test_config.h"

/** @brief Einmalig nach den CubeMX-Inits aufrufen (z. B. in main()). */
void motor_test_init(void);

/**
 * @brief Im Hauptloop ZYKLISCH und moeglichst oft aufrufen.
 *        Treibt die Zustandsmaschine, pollt den Button (Not-Aus) und gibt
 *        Status ueber UART aus. Blockiert nie.
 */
void motor_test_run(void);

/** @brief Samples all Hall inputs; call from the dedicated fast timer ISR. */
void motor_test_hall_sample(void);

/**
 * @brief Uebernimmt nach einem gueltigen PC-Fahrbefehl exklusiv die Motoren.
 *        Ungueltige Roboter-IDs, nicht-endliche Werte und ein aktiver Not-Aus
 *        werden ignoriert. Der Empfangs-Timeout stoppt die Motoren.
 */
void motor_test_remote_command(uint8_t robot_id, float vx, float vy,
                               float omega);

#endif /* MOTOR_TEST_H */
