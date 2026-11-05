#include "nucleo_receiver.h"

#include "motor_test.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#define RX_RING_SIZE 512U
#define LINE_SIZE 96U
#define UART_TIMEOUT_MS 100U

static UART_HandleTypeDef *receiver_uart;
static UART_HandleTypeDef *console_uart;
static uint8_t rx_byte;
static uint8_t rx_ring[RX_RING_SIZE];
static volatile uint16_t rx_head;
static volatile uint16_t rx_tail;
static volatile uint8_t rx_overflow;
static volatile uint8_t uart_error;
static char line[LINE_SIZE];
static size_t line_length;
static uint8_t line_overflow;
static uint8_t line_invalid;

static int parse_decimal(const char **cursor, float *result)
{
    const char *position = *cursor;
    double value = 0.0;
    double fraction = 0.1;
    int negative = 0;
    unsigned int digits = 0U;

    if (*position == '-' || *position == '+')
    {
        negative = (*position == '-');
        ++position;
    }

    while (*position >= '0' && *position <= '9')
    {
        value = value * 10.0 + (double)(*position - '0');
        if (value > 1000000.0)
        {
            return 0;
        }
        ++position;
        ++digits;
    }

    if (*position == '.')
    {
        ++position;
        while (*position >= '0' && *position <= '9')
        {
            value += (double)(*position - '0') * fraction;
            fraction *= 0.1;
            ++position;
            ++digits;
        }
    }

    if (digits == 0U || value > 1000000.0)
    {
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

    while (*position >= '0' && *position <= '9')
    {
        const unsigned int digit = (unsigned int)(*position - '0');
        if (value > (255U - digit) / 10U)
        {
            return 0;
        }
        value = value * 10U + digit;
        ++position;
        ++digits;
    }

    if (digits == 0U)
    {
        return 0;
    }

    *result = value;
    *cursor = position;
    return 1;
}

static void send_text(const char *text)
{
    if (console_uart != NULL)
    {
        (void)HAL_UART_Transmit(console_uart, (uint8_t *)text,
                                (uint16_t)strlen(text), UART_TIMEOUT_MS);
    }
}

static void process_line(const char *input)
{
    const char *cursor = input;
    unsigned int robot_id = 0U;
    float vx;
    float vy;
    float omega;

    if (strncmp(cursor, "RBT1,", 5U) != 0)
    {
        send_text("Fehler: ungueltiger ESP32-Datensatz\r\n");
        return;
    }
    cursor += 5;

    if (!parse_unsigned(&cursor, &robot_id) || *cursor++ != ',' ||
        !parse_decimal(&cursor, &vx) || *cursor++ != ',' ||
        !parse_decimal(&cursor, &vy) || *cursor++ != ',' ||
        !parse_decimal(&cursor, &omega) || *cursor != '\0' ||
        !isfinite(vx) || !isfinite(vy) || !isfinite(omega))
    {
        send_text("Fehler: ungueltiger ESP32-Datensatz\r\n");
        return;
    }

    motor_test_remote_command((uint8_t)robot_id, vx, vy, omega);
}

HAL_StatusTypeDef NucleoReceiver_Init(UART_HandleTypeDef *rx_uart,
                                      UART_HandleTypeDef *tx_uart)
{
    if (rx_uart == NULL || tx_uart == NULL)
    {
        return HAL_ERROR;
    }

    receiver_uart = rx_uart;
    console_uart = tx_uart;
    rx_head = 0U;
    rx_tail = 0U;
    rx_overflow = 0U;
    uart_error = 0U;
    line_length = 0U;
    line_overflow = 0U;
    line_invalid = 0U;

    return HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U);
}

void NucleoReceiver_RxCpltCallback(UART_HandleTypeDef *uart)
{
    if (uart != receiver_uart)
    {
        return;
    }

    const uint16_t next = (uint16_t)((rx_head + 1U) % RX_RING_SIZE);
    if (next == rx_tail)
    {
        rx_overflow = 1U;
    }
    else
    {
        rx_ring[rx_head] = rx_byte;
        rx_head = next;
    }

    if (HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U) != HAL_OK)
    {
        uart_error = 1U;
    }
}

void NucleoReceiver_ErrorCallback(UART_HandleTypeDef *uart)
{
    if (uart == receiver_uart)
    {
        uart_error = 1U;
    }
}

void NucleoReceiver_Poll(void)
{
    if (receiver_uart == NULL)
    {
        return;
    }

    if (uart_error != 0U)
    {
        uart_error = 0U;
        (void)HAL_UART_AbortReceive(receiver_uart);
        if (HAL_UART_Receive_IT(receiver_uart, &rx_byte, 1U) != HAL_OK)
        {
            uart_error = 1U;
            return;
        }
        send_text("Fehler: UART-Empfang wurde neu gestartet\r\n");
    }

    if (rx_overflow != 0U)
    {
        rx_overflow = 0U;
        rx_tail = rx_head;
        line_length = 0U;
        line_overflow = 0U;
        line_invalid = 0U;
        send_text("Fehler: UART-Empfangspuffer voll\r\n");
    }

    while (rx_tail != rx_head)
    {
        const uint8_t value = rx_ring[rx_tail];
        rx_tail = (uint16_t)((rx_tail + 1U) % RX_RING_SIZE);

        if (value == '\r')
        {
            continue;
        }

        if (value == '\n')
        {
            if (line_overflow != 0U)
            {
                send_text("Fehler: ESP32-Datensatz zu lang\r\n");
            }
            else if (line_invalid != 0U)
            {
                send_text("Fehler: ungueltige Zeichen im ESP32-Datensatz\r\n");
            }
            else
            {
                line[line_length] = '\0';
                process_line(line);
            }
            line_length = 0U;
            line_overflow = 0U;
            line_invalid = 0U;
            continue;
        }

        if (value < 0x20U || value > 0x7EU)
        {
            line_invalid = 1U;
        }
        else if (line_length + 1U < LINE_SIZE)
        {
            line[line_length++] = (char)value;
        }
        else
        {
            line_overflow = 1U;
        }
    }
}
