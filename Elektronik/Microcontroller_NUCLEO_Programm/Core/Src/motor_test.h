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

#endif /* MOTOR_TEST_H */
