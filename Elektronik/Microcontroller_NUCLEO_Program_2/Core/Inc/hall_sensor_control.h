#ifndef HALL_SENSOR_H
#define HALL_SENSOR_H

#include <stdint.h>
#include "stm32h7xx_hal.h"

// Motordaten (Nanotec DF45L024048-A2 & Omni-Wheel)
#define TICKS_PER_REV        48.0f     // 8 Polpaare * 6 Hall-Wechsel
#define WHEEL_DIAMETER_M     0.066f    // 6.6 cm Durchmesser
#define WHEEL_CIRCUMFERENCE  (3.14159265f * WHEEL_DIAMETER_M) // ~0.2073 m
#define METERS_PER_TICK      (WHEEL_CIRCUMFERENCE / TICKS_PER_REV) // ~0.004319 m/Tick

extern volatile uint8_t debug_hall_state[4];
extern volatile float debug_distance_vl_m;
extern volatile float debug_distance_vr_m;
extern volatile float debug_distance_hl_m;
extern volatile float debug_distance_hr_m;

void hall_sensors_init(void);
void hall_sensors_update(void); // Schnell aufrufen (z.B. alle 1ms oder in SysTick)
void hall_get_velocities(float dt, float *v_vl, float *v_vr, float *v_hl, float *v_hr);

#endif
