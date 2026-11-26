#include "kinematics.h"
#include "hall_sensor_control.h"
#include "pid.h"
#include "esc_driver.h"
#include <math.h>

#define PI 3.14159265358979323846
#define ALPHA_VL (31.0 * PI / 180.0)
#define ALPHA_VR (329.0 * PI / 180.0)
#define ALPHA_HL (135.0 * PI / 180.0)
#define ALPHA_HR (225.0 * PI / 180.0)

#define R_VORNE 0.035f
#define R_HINTEN 0.035f

/* Globale Diagnose-Variablen für Live Expressions */
volatile float debug_v_vl = 0.0f;
volatile float debug_v_vr = 0.0f;
volatile float debug_v_hl = 0.0f;
volatile float debug_v_hr = 0.0f;

volatile float debug_v_vl_roh = 0.0f;
volatile float debug_v_vr_roh = 0.0f;
volatile float debug_v_hl_roh = 0.0f;
volatile float debug_v_hr_roh = 0.0f;

volatile float debug_target_v_vl = 0.0f;
volatile float debug_target_v_vr = 0.0f;
volatile float debug_target_v_hl = 0.0f;
volatile float debug_target_v_hr = 0.0f;

/* Neu: Globale Variablen für PWM-Signale */
volatile uint32_t debug_pwm_vl = 1500;
volatile uint32_t debug_pwm_vr = 1500;
volatile uint32_t debug_pwm_hl = 1500;
volatile uint32_t debug_pwm_hr = 1500;


// PID-Regler aus main.c importieren
extern PID_Controller pid_vl, pid_vr, pid_hl, pid_hr;

static void scale_targets_to_minimum_speeds(WheelSpeeds *target)
{
    float scale = 1.0f;

    if (fabsf(target->vl) > 0.0001f) scale = fmaxf(scale, 1.3f / fabsf(target->vl));
    if (fabsf(target->vr) > 0.0001f) scale = fmaxf(scale, 1.3f / fabsf(target->vr));
    if (fabsf(target->hl) > 0.0001f) scale = fmaxf(scale, 1.0f / fabsf(target->hl));
    if (fabsf(target->hr) > 0.0001f) scale = fmaxf(scale, 1.0f / fabsf(target->hr));

    target->vl *= scale;
    target->vr *= scale;
    target->hl *= scale;
    target->hr *= scale;
}

static uint32_t pulse_for_wheel(PID_Controller *pid, uint8_t motor, float target,
                                float measured_raw, float dt)
{
    if (fabsf(target) < 0.0001f)
    {
        pid_reset(pid);
        return 1500U;
    }

    float direction = (target > 0.0f) ? 1.0f : -1.0f;
    float measured_in_target_direction = measured_raw * direction;
    float correction_us = pid_calculate(pid, fabsf(target),
                                        measured_in_target_direction, dt);
    float command_magnitude_us = 50.0f + correction_us;

    // The controller may reduce the start offset all the way to neutral,
    // but must not reverse the requested wheel direction.
    if (command_magnitude_us < 0.0f)
    {
        command_magnitude_us = 0.0f;
    }

    // VL has the opposite ESC pulse polarity to VR, HL, and HR.
    float pulse_direction = (motor == 0U) ? direction : -direction;
    return constrain_pwm(1500.0f + pulse_direction * command_magnitude_us);
}

uint32_t constrain_pwm(float pwm_val) {
    if (pwm_val > 2000.0f) return 2000;
    if (pwm_val < 1000.0f) return 1000;
    return (uint32_t)pwm_val;
}

// 1. Reine Geometrie-Transformation (vx, vy, omega -> m/s pro Rad)
WheelSpeeds kinematics_calculate(float vx, float vy, float omega) {
    WheelSpeeds ws;
    ws.vl = -sin(ALPHA_VL)*vx + cos(ALPHA_VL)*vy + R_VORNE*omega;
    ws.vr = -sin(ALPHA_VR)*vx + cos(ALPHA_VR)*vy + R_VORNE*omega;
    ws.hl = -sin(ALPHA_HL)*vx + cos(ALPHA_HL)*vy + R_HINTEN*omega;
    ws.hr = -sin(ALPHA_HR)*vx + cos(ALPHA_HR)*vy + R_HINTEN*omega;
    return ws;
}

static void drive_wheel_speeds_closed_loop(WheelSpeeds target, float dt,
                                           float minimum_wheel_speed,
                                           uint8_t scale_to_minimum_speeds)
{
    if (minimum_wheel_speed > 0.0f)
    {
        if (fabsf(target.vl) < minimum_wheel_speed) target.vl = 0.0f;
        if (fabsf(target.vr) < minimum_wheel_speed) target.vr = 0.0f;
        if (fabsf(target.hl) < minimum_wheel_speed) target.hl = 0.0f;
        if (fabsf(target.hr) < minimum_wheel_speed) target.hr = 0.0f;
    }

    if (scale_to_minimum_speeds)
    {
        scale_targets_to_minimum_speeds(&target);
    }
	    debug_target_v_vl = target.vl;
	    debug_target_v_vr = target.vr;
	    debug_target_v_hl = target.hl;
	    debug_target_v_hr = target.hr;

	    // Ist-Geschwindigkeiten aus Hall-Sensoren lesen
	    float v_raw_vl, v_raw_vr, v_raw_hl, v_raw_hr;
	    hall_get_velocities(dt, &v_raw_vl, &v_raw_vr, &v_raw_hl, &v_raw_hr);

	    debug_v_vl_roh = v_raw_vl;
	    debug_v_vr_roh = v_raw_vr;
	    debug_v_hl_roh = v_raw_hl;
	    debug_v_hr_roh = v_raw_hr;

	    debug_v_vl = -v_raw_vl;
	    debug_v_vr = -v_raw_vr;
	    debug_v_hl = -v_raw_hl;
	    debug_v_hr = -v_raw_hr;


    // Use the empirically measured 50 us start offset as feed-forward.
    // The PI correction can increase or decrease this offset based on speed error.
    uint32_t pwm_vl = pulse_for_wheel(&pid_vl, 0U, target.vl, v_raw_vl, dt);
    uint32_t pwm_vr = pulse_for_wheel(&pid_vr, 1U, target.vr, v_raw_vr, dt);
    uint32_t pwm_hl = pulse_for_wheel(&pid_hl, 2U, target.hl, v_raw_hl, dt);
    uint32_t pwm_hr = pulse_for_wheel(&pid_hr, 3U, target.hr, v_raw_hr, dt);

    // ERST JETZT in globale Debug-Variablen schreiben:
        debug_pwm_vl = pwm_vl;
        debug_pwm_vr = pwm_vr;
        debug_pwm_hl = pwm_hl;
        debug_pwm_hr = pwm_hr;

    // Ausführung an den Motoren
    esc_set_pulse_us(0, pwm_vl);
    esc_set_pulse_us(1, pwm_vr);
    esc_set_pulse_us(2, pwm_hl);
    esc_set_pulse_us(3, pwm_hr);
}

// Standard closed-loop command, retaining all kinematic wheel targets.
void drive_kinematics_closed_loop(float vx, float vy, float omega, float dt)
{
    WheelSpeeds target = kinematics_calculate(vx, vy, omega);
    drive_wheel_speeds_closed_loop(target, dt, 0.0f, 0U);
}

// Diagonal test: suppress near-zero wheel targets so the intended opposing
// wheel pair is active despite small angle/geometry mismatches.
void drive_kinematics_diagonal_closed_loop(float vx, float vy, float omega, float dt)
{
    WheelSpeeds target = kinematics_calculate(vx, vy, omega);
    float max_target = fmaxf(fmaxf(fabsf(target.vl), fabsf(target.vr)),
                             fmaxf(fabsf(target.hl), fabsf(target.hr)));
    drive_wheel_speeds_closed_loop(target, dt, max_target * 0.30f, 1U);
}

void stop_robot(void) {
    esc_all_stop();
}
