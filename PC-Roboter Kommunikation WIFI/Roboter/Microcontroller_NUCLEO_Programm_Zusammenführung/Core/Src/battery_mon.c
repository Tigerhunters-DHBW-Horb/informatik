/**
 ******************************************************************************
 * @file    battery_mon.c
 * @brief   Minimaler INA226-Unterspannungsschutz (optional).
 *          Nur aktiv, wenn CFG_ENABLE_BATTERY_MON == 1.
 *          Liest periodisch die Bus-Spannung und meldet Unterspannung.
 ******************************************************************************
 */
#include "test_config.h"

#if CFG_ENABLE_BATTERY_MON

#include <stdint.h>

#define INA226_REG_BUSVOLT   0x02U      /* LSB = 1.25 mV */

static uint32_t s_last_poll = 0;
static uint8_t  s_under     = 0;

/* gibt 1 zurueck, sobald die Akkuspannung unter der Schwelle liegt */
uint8_t battery_undervoltage(uint32_t now)
{
    if ((now - s_last_poll) < BATT_POLL_MS) {
        return s_under;             /* zwischen den Pollings letzten Stand halten */
    }
    s_last_poll = now;

    uint8_t  rx[2];
    if (HAL_I2C_Mem_Read(&BATT_I2C_HANDLE, (BATT_INA226_ADDR_7B << 1),
                         INA226_REG_BUSVOLT, I2C_MEMADD_SIZE_8BIT,
                         rx, 2, 20) != HAL_OK) {
        return s_under;             /* I2C-Fehler -> nicht faelschlich ausloesen */
    }

    uint16_t raw   = ((uint16_t)rx[0] << 8) | rx[1];
    uint32_t mv    = (uint32_t)((float)raw * 1.25f);   /* Bus-Spannung in mV */
    uint32_t limit = (uint32_t)BATT_CELLS * (uint32_t)BATT_CELL_MIN_MV;

    if (mv < limit) s_under = 1;     /* einmal getriggert -> latched           */
    return s_under;
}

#endif /* CFG_ENABLE_BATTERY_MON */
