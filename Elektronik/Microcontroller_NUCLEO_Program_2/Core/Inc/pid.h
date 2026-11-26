#ifndef PID_H
#define PID_H

typedef struct {
    float kp;
    float ki;
    float kd;
    float integrator;
    float prev_error;
    float out_min;
    float out_max;
} PID_Controller;

void pid_init(PID_Controller *pid, float kp, float ki, float kd, float out_min, float out_max);
float pid_calculate(PID_Controller *pid, float setpoint, float measured, float dt);
void pid_reset(PID_Controller *pid);

#endif
