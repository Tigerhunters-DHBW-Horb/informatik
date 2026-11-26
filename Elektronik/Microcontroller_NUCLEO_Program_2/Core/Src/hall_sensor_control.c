#include "hall_sensor_control.h"

volatile int32_t ticks[4] = {0, 0, 0, 0};
volatile uint8_t debug_hall_state[4] = {0, 0, 0, 0};
volatile float debug_distance_vl_m = 0.0f;
volatile float debug_distance_vr_m = 0.0f;
volatile float debug_distance_hl_m = 0.0f;
volatile float debug_distance_hr_m = 0.0f;
static uint8_t last_state[4] = {0, 0, 0, 0};


// Zuweisungs-Tabelle: Hall-State (1..6) zu fortlaufendem Index (0..5)
static const int8_t state_to_idx[8] = {-1, 0, 2, 1, 4, 5, 3, -1};

static uint8_t read_hall_raw(uint8_t motor_index) {
    switch (motor_index) {
        case 0: // VL (Motor 1: PA15, PF7, PF6)
            return HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_15) |
                  (HAL_GPIO_ReadPin(GPIOF, GPIO_PIN_7) << 1) |
                  (HAL_GPIO_ReadPin(GPIOF, GPIO_PIN_6) << 2);
        case 1: // VR (Motor 2: PC8, PC6, PC5)
            return HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_8) |
                  (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_6) << 1) |
                  (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_5) << 2);
        case 2: // HL (Motor 3: PG12, PG9, PE1)
            return HAL_GPIO_ReadPin(GPIOG, GPIO_PIN_12) |
                  (HAL_GPIO_ReadPin(GPIOG, GPIO_PIN_9) << 1) |
                  (HAL_GPIO_ReadPin(GPIOE, GPIO_PIN_1) << 2);
        case 3: // HR (Motor 4: PG8, PG5, PG6)
            return HAL_GPIO_ReadPin(GPIOG, GPIO_PIN_8) |
                  (HAL_GPIO_ReadPin(GPIOG, GPIO_PIN_5) << 1) |
                  (HAL_GPIO_ReadPin(GPIOG, GPIO_PIN_6) << 2);
        default: return 0;
    }
}

void hall_sensors_init(void) {
    for (int i = 0; i < 4; i++) {
        last_state[i] = read_hall_raw(i);
        debug_hall_state[i] = last_state[i];
        ticks[i] = 0;
    }
    debug_distance_vl_m = 0.0f;
    debug_distance_vr_m = 0.0f;
    debug_distance_hl_m = 0.0f;
    debug_distance_hr_m = 0.0f;
}

void hall_sensors_update(void) {
    for (int i = 0; i < 4; i++) {
        uint8_t curr_state = read_hall_raw(i);
        debug_hall_state[i] = curr_state;
        if (curr_state != last_state[i]) {
            int8_t old_idx = state_to_idx[last_state[i]];
            int8_t new_idx = state_to_idx[curr_state];

            if (old_idx != -1 && new_idx != -1) {
                int8_t diff = (new_idx - old_idx + 6) % 6;
                if (diff == 1) {
                    ticks[i]++;
                } else if (diff == 5) {
                    ticks[i]--;
                }

                if (diff == 1 || diff == 5) {
                    switch (i) {
                        case 0: debug_distance_vl_m += METERS_PER_TICK; break;
                        case 1: debug_distance_vr_m += METERS_PER_TICK; break;
                        case 2: debug_distance_hl_m += METERS_PER_TICK; break;
                        case 3: debug_distance_hr_m += METERS_PER_TICK; break;
                    }
                }
            }
            last_state[i] = curr_state;
        }
    }
}

void hall_get_velocities(float dt, float *v_vl, float *v_vr, float *v_hl, float *v_hr) {
    if (dt <= 0.0001f) return;

    // Ticks atomar auslesen und zurücksetzen
    __disable_irq();
    int32_t t_vl = ticks[0]; ticks[0] = 0;
    int32_t t_vr = ticks[1]; ticks[1] = 0;
    int32_t t_hl = ticks[2]; ticks[2] = 0;
    int32_t t_hr = ticks[3]; ticks[3] = 0;
    __enable_irq();

    // In Ist-Geschwindigkeit (m/s) umrechnen
    *v_vl = ((float)t_vl * METERS_PER_TICK) / dt;
    *v_vr = ((float)t_vr * METERS_PER_TICK) / dt;
    *v_hl = ((float)t_hl * METERS_PER_TICK) / dt;
    *v_hr = ((float)t_hr * METERS_PER_TICK) / dt;
}
