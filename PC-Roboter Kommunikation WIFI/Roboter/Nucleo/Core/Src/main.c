#include "main.h"
#include "nucleo_receiver.h"

UART_HandleTypeDef huart3;

static void SystemClock_Config(void);
static void MX_USART3_UART_Init(void);
static void Error_Handler(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_USART3_UART_Init();

  if (NucleoReceiver_Init(&huart3) != HAL_OK) {
    Error_Handler();
  }

  static const uint8_t startup_message[] =
      "\r\nNucleo-H753ZI bereit; warte auf ESP32-Daten (USART3 115200 8N1)\r\n";
  if (HAL_UART_Transmit(&huart3, (uint8_t *)startup_message,
                        sizeof(startup_message) - 1U, HAL_MAX_DELAY) != HAL_OK) {
    Error_Handler();
  }

  while (1) {
    NucleoReceiver_Poll();
  }
}

static void SystemClock_Config(void)
{
  RCC_OscInitTypeDef oscillator = {0};
  RCC_ClkInitTypeDef clocks = {0};

  oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  oscillator.HSIState = RCC_HSI_ON;
  oscillator.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  oscillator.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&oscillator) != HAL_OK) {
    Error_Handler();
  }

  clocks.ClockType = RCC_CLOCKTYPE_SYSCLK |
                     RCC_CLOCKTYPE_HCLK |
                     RCC_CLOCKTYPE_PCLK1 |
                     RCC_CLOCKTYPE_PCLK2 |
                     RCC_CLOCKTYPE_D1PCLK1 |
                     RCC_CLOCKTYPE_D3PCLK1;
  clocks.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  clocks.SYSCLKDivider = RCC_SYSCLK_DIV1;
  clocks.AHBCLKDivider = RCC_HCLK_DIV1;
  clocks.APB3CLKDivider = RCC_APB3_DIV1;
  clocks.APB1CLKDivider = RCC_APB1_DIV1;
  clocks.APB2CLKDivider = RCC_APB2_DIV1;
  clocks.APB4CLKDivider = RCC_APB4_DIV1;
  if (HAL_RCC_ClockConfig(&clocks, FLASH_LATENCY_4) != HAL_OK) {
    Error_Handler();
  }
}

static void MX_USART3_UART_Init(void)
{
  GPIO_InitTypeDef gpio = {0};

  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_USART3_CLK_ENABLE();

  gpio.Pin = GPIO_PIN_8 | GPIO_PIN_9;
  gpio.Mode = GPIO_MODE_AF_PP;
  gpio.Pull = GPIO_PULLUP;
  gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  gpio.Alternate = GPIO_AF7_USART3;
  HAL_GPIO_Init(GPIOD, &gpio);

  huart3.Instance = USART3;
  huart3.Init.BaudRate = 115200U;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  huart3.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart3.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart3.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart3) != HAL_OK) {
    Error_Handler();
  }

  HAL_NVIC_SetPriority(USART3_IRQn, 5U, 0U);
  HAL_NVIC_EnableIRQ(USART3_IRQn);
}

void USART3_IRQHandler(void)
{
  HAL_UART_IRQHandler(&huart3);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *uart)
{
  NucleoReceiver_RxCpltCallback(uart);
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *uart)
{
  NucleoReceiver_ErrorCallback(uart);
}

static void Error_Handler(void)
{
  static const uint8_t error_message[] = "Fataler Initialisierungsfehler\r\n";

  __disable_irq();
  if (huart3.Instance != NULL) {
    while (HAL_UART_Transmit(&huart3, (uint8_t *)error_message,
                             sizeof(error_message) - 1U, 100U) != HAL_OK) {
    }
  }
  while (1) {
  }
}
