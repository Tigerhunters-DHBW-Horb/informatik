#ifndef KINEMATICS_H
#define KINEMATICS_H

#include <stdint.h>

#ifndef DEBUG_H
#define DEBUG_H

// Debug-Geschwindigkeiten der 4 Motoren
extern volatile float debug_v_vl;
extern volatile float debug_v_vr;
extern volatile float debug_v_hl;
extern volatile float debug_v_hr;
extern volatile float debug_v_vl_roh;
extern volatile float debug_v_vr_roh;
extern volatile float debug_v_hl_roh;
extern volatile float debug_v_hr_roh;
extern volatile float debug_target_v_vl;
extern volatile float debug_target_v_vr;
extern volatile float debug_target_v_hl;
extern volatile float debug_target_v_hr;
extern volatile uint32_t debug_pwm_vl;
extern volatile uint32_t debug_pwm_vr;
extern volatile uint32_t debug_pwm_hl;
extern volatile uint32_t debug_pwm_hr;

#endif // DEBUG_H


// Struktur für Soll-Geschwindigkeiten der 4 Räder (m/s)
typedef struct {
    float vl;
    float vr;
    float hl;
    float hr;
} WheelSpeeds;

// Reine Kinematik-Berechnung (Soll-Geschwindigkeiten aus vx, vy, omega)
WheelSpeeds kinematics_calculate(float vx, float vy, float omega);

// Closed-Loop Fahrbefehl für die Hauptschleife
void drive_kinematics_closed_loop(float vx, float vy, float omega, float dt);
void drive_kinematics_diagonal_closed_loop(float vx, float vy, float omega, float dt);

void stop_robot(void);
uint32_t constrain_pwm(float pwm_val);

#endif
