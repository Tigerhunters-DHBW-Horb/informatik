#include "pid.h"

void pid_init(PID_Controller *pid, float kp, float ki, float kd, float out_min, float out_max) {
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    pid->integrator = 0.0f;
    pid->prev_error = 0.0f;
    pid->out_min = out_min;
    pid->out_max = out_max;
}

float pid_calculate(PID_Controller *pid, float setpoint, float measured, float dt) {
    if (dt <= 0.0001f) return 0.0f;

    float error = setpoint - measured;

    // P-Anteil
    float p_term = pid->kp * error;

    // I-Anteil mit Anti-Windup
    pid->integrator += error * dt;
    float i_term = pid->ki * pid->integrator;

    // D-Anteil
    float derivative = (error - pid->prev_error) / dt;
    float d_term = pid->kd * derivative;

    pid->prev_error = error;

    float output = p_term + i_term + d_term;

    // Begrenzung (Clamping)
    if (output > pid->out_max) {
        output = pid->out_max;
        pid->integrator -= error * dt; // Anti-Windup Rücknahme
    } else if (output < pid->out_min) {
        output = pid->out_min;
        pid->integrator -= error * dt;
    }

    return output;
}

void pid_reset(PID_Controller *pid) {
    pid->integrator = 0.0f;
    pid->prev_error = 0.0f;
}
