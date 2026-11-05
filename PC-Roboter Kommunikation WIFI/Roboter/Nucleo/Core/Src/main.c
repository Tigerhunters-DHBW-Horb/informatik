#include "main.h"
#include "nucleo_receiver.h"
#include "stm32h7xx_nucleo.h"

UART_HandleTypeDef huart1;
static COM_InitTypeDef bsp_com_init;

static void SystemClock_Config(void);
static void MX_USART1_UART_Init(void);
static void Error_Handler(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();

  bsp_com_init.BaudRate = 115200U;
  bsp_com_init.WordLength = COM_WORDLENGTH_8B;
  bsp_com_init.StopBits = COM_STOPBITS_1;
  bsp_com_init.Parity = COM_PARITY_NONE;
  bsp_com_init.HwFlowCtl = COM_HWCONTROL_NONE;
  if (BSP_COM_Init(COM1, &bsp_com_init) != BSP_ERROR_NONE) {
    Error_Handler();
  }
  MX_USART1_UART_Init();

  if (NucleoReceiver_Init(&huart1, &hcom_uart[COM1]) != HAL_OK) {
    Error_Handler();
  }

  static const uint8_t startup_message[] =
      "Nucleo-H753ZI bereit; ESP32 RX: USART1/PB7, Monitor: USART3 115200 8N1\r\n";
  if (HAL_UART_Transmit(&hcom_uart[COM1], (uint8_t *)startup_message,
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

  if (HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY) != HAL_OK) {
    Error_Handler();
  }
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);
  while (!__HAL_PWR_GET_FLAG(PWR_FLAG_VOSRDY)) {
  }

  oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  oscillator.HSIState = RCC_HSI_DIV1;
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
  if (HAL_RCC_ClockConfig(&clocks, FLASH_LATENCY_1) != HAL_OK) {
    Error_Handler();
  }
}

static void MX_USART1_UART_Init(void)
{
  GPIO_InitTypeDef gpio = {0};

  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_USART1_CLK_ENABLE();

  gpio.Pin = GPIO_PIN_7;
  gpio.Mode = GPIO_MODE_AF_PP;
  gpio.Pull = GPIO_PULLUP;
  gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
  gpio.Alternate = GPIO_AF7_USART1;
  HAL_GPIO_Init(GPIOB, &gpio);

  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200U;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_8;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK) {
    Error_Handler();
  }

  HAL_NVIC_SetPriority(USART1_IRQn, 5U, 0U);
  HAL_NVIC_EnableIRQ(USART1_IRQn);
}

void USART1_IRQHandler(void)
{
  HAL_UART_IRQHandler(&huart1);
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
  if (hcom_uart[COM1].Instance != NULL) {
    (void)HAL_UART_Transmit(&hcom_uart[COM1], (uint8_t *)error_message,
                            sizeof(error_message) - 1U, 100U);
  }
  while (1) {
  }
}
