#ifndef NUCLEO_RECEIVER_H
#define NUCLEO_RECEIVER_H

#include "stm32h7xx_hal.h"

HAL_StatusTypeDef NucleoReceiver_Init(UART_HandleTypeDef *uart);
void NucleoReceiver_Poll(void);
void NucleoReceiver_RxCpltCallback(UART_HandleTypeDef *uart);
void NucleoReceiver_ErrorCallback(UART_HandleTypeDef *uart);

#endif
