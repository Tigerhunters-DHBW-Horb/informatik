#include "nucleo_receiver.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#define RX_RING_SIZE 512U
#define LINE_SIZE 96U
#define UART_TIMEOUT_MS 100U

static UART_HandleTypeDef *receiver_uart;
static uint8_t rx_byte;
static uint8_t rx_ring[RX_RING_SIZE];
static volatile uint16_t rx_head;
static volatile uint16_t rx_tail;
static volatile uint8_t rx_overflow;
static volatile uint8_t uart_error;
static char line[LINE_SIZE];
static size_t line_length;
static uint8_t line_overflow;

static int parse_decimal(const char **cursor, float *result)
{
  const char *position = *cursor;
  double value = 0.0;
  double fraction = 0.1;
  int negative = 0;
  int digits = 0;

  if (*position == '-' || *position == '+') {
    negative = *position == '-';
    ++position;
  }

  while (*position >= '0' && *position <= '9') {
    value = value * 10.0 + (double)(*position - '0');
    if (value > 1000000.0) {
      return 0;
    }
    ++position;
    ++digits;
  }

  if (*position == '.') {
    ++position;
    while (*position >= '0' && *position <= '9') {
      value += (double)(*position - '0') * fraction;
      fraction *= 0.1;
      ++position;
      ++digits;
    }
  }

  if (digits == 0 || value > 1000000.0) {
    return 0;
  }

  *result = (float)(negative ? -value : value);
  *cursor = position;
  return 1;
}

static int parse_unsigned(const char **cursor, unsigned int *result)
{
  const char *position = *cursor;
  unsigned int value = 0U;
  unsigned int digits = 0U;

  while (*position >= '0' && *position <= '9') {
    const unsigned int digit = (unsigned int)(*position - '0');
    if (value > (255U - digit) / 10U) {
      return 0;
    }
    value = value * 10U + digit;
    ++position;
    ++digits;
  }

  if (digits == 0U) {
    return 0;
  }

  *result = value;
  *cursor = position;
  return 1;
}

static void send_text(const char *text)
{
  if (receiver_uart == NULL) {
    return;
  }

  (void)HAL_UART_Transmit(receiver_uart, (uint8_t *)text,
                          (uint16_t)strlen(text), UART_TIMEOUT_MS);
}

static void format_milli(char *output, size_t output_size, float value)
{
  const int32_t milli =
      (int32_t)(value * 1000.0f + (value < 0.0f ? -0.5f : 0.5f));
  const char *sign = milli < 0 ? "-" : "";
  const uint32_t magnitude =
      milli < 0 ? (uint32_t)(-(int64_t)milli) : (uint32_t)milli;

  (void)snprintf(output, output_size, "%s%lu.%03lu", sign,
                 (unsigned long)(magnitude / 1000U),
                 (unsigned long)(magnitude % 1000U));
}

static void process_line(const char *input)
{
  const char *cursor = input;
  unsigned int robot_id = 0U;
  float vx;
  float vy;
  float omega;
  char output[128];
  char vx_text[24];
  char vy_text[24];
  char omega_text[24];

  if (strncmp(cursor, "RBT1,", 5U) != 0) {
    send_text("Fehler: ungueltiger ESP32-Datensatz\n");
    return;
  }
  cursor += 5;

  if (!parse_unsigned(&cursor, &robot_id) || *cursor++ != ',' ||
      !parse_decimal(&cursor, &vx) || *cursor++ != ',' ||
      !parse_decimal(&cursor, &vy) || *cursor++ != ',' ||
      !parse_decimal(&cursor, &omega) || *cursor != '\0' ||
      !isfinite(vx) || !isfinite(vy) || !isfinite(omega)) {
    send_text("Fehler: ungueltiger ESP32-Datensatz\n");
    return;
  }

  format_milli(vx_text, sizeof(vx_text), vx);
  format_milli(vy_text, sizeof(vy_text), vy);
  format_milli(omega_text, sizeof(omega_text), omega);
  (void)snprintf(output, sizeof(output),
                 "ID %u: vx=%s m/s, vy=%s m/s, omega=%s rad/s\n",
                 robot_id, vx_text, vy_text, omega_text);
  send_text(output);
}

HAL_StatusTypeDef NucleoReceiver_Init(UART_HandleTypeDef *uart)
{
  if (uart == NULL) {
    return HAL_ERROR;
  }

  receiver_uart = uart;
  rx_head = 0U;
  rx_tail = 0U;
  rx_overflow = 0U;
  uart_error = 0U;
  line_length = 0U;
  line_overflow = 0U;
  return HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U);
}

void NucleoReceiver_RxCpltCallback(UART_HandleTypeDef *uart)
{
  if (uart != receiver_uart) {
    return;
  }

  const uint16_t next = (uint16_t)((rx_head + 1U) % RX_RING_SIZE);
  if (next == rx_tail) {
    rx_overflow = 1U;
  } else {
    rx_ring[rx_head] = rx_byte;
    rx_head = next;
  }

  if (HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U) != HAL_OK) {
    uart_error = 1U;
  }
}

void NucleoReceiver_ErrorCallback(UART_HandleTypeDef *uart)
{
  if (uart == receiver_uart) {
    uart_error = 1U;
  }
}

void NucleoReceiver_Poll(void)
{
  if (receiver_uart == NULL) {
    return;
  }

  if (uart_error != 0U) {
    uart_error = 0U;
    (void)HAL_UART_AbortReceive(receiver_uart);
    if (HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U) != HAL_OK) {
      uart_error = 1U;
      return;
    }
    send_text("Fehler: UART-Empfang wurde neu gestartet\n");
  }

  if (rx_overflow != 0U) {
    rx_overflow = 0U;
    rx_tail = rx_head;
    line_length = 0U;
    line_overflow = 0U;
    send_text("Fehler: UART-Empfangspuffer voll\n");
  }

  while (rx_tail != rx_head) {
    const uint8_t value = rx_ring[rx_tail];
    rx_tail = (uint16_t)((rx_tail + 1U) % RX_RING_SIZE);

    if (value == '\r') {
      continue;
    }

    if (value == '\n') {
      if (line_overflow != 0U) {
        send_text("Fehler: ESP32-Datensatz zu lang\n");
      } else {
        line[line_length] = '\0';
        process_line(line);
      }
      line_length = 0U;
      line_overflow = 0U;
      continue;
    }

    if (line_length + 1U < LINE_SIZE) {
      line[line_length++] = (char)value;
    } else {
      line_overflow = 1U;
    }
  }
}
