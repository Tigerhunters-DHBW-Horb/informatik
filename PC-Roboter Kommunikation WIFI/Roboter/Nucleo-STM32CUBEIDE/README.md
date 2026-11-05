# Nucleo ESP32 receiver (STM32CubeIDE)

Import this folder into STM32CubeIDE as an existing project. It targets the
NUCLEO-H753ZI and receives the ASCII drive-command lines forwarded by the
ESP32-C6:

```text
RBT1,<ID>,<vx>,<vy>,<omega>\n
```

The project uses the Nucleo BSP COM1 interface on USART3 for the ST-LINK Virtual
COM Port, matching the working motor-test project. ESP32 data is received
separately on USART1_RX/PB7. Both UARTs use 115200 baud, 8 data bits, no parity,
one stop bit, and no hardware flow control.

## Import, build, and flash

1. In STM32CubeIDE, select **File > Import > Existing Projects into Workspace**.
2. Select this folder as the root directory and import `Nucleo-ESP32-Receiver`.
3. Build the **Debug** configuration.
4. Connect the Nucleo by USB and use **Run > Debug** or **Run > Run** to program
   the board through ST-LINK.
5. Open the ST-LINK Virtual COM Port at **115200 baud, 8N1**, then reset the
   board. The startup banner should appear, followed by parsed ESP32 commands.

The project includes the STM32CubeH7 HAL and Nucleo BSP sources copied from the
existing motor-test project, so the IDE project does not depend on external
source paths. The `.ioc` file describes the H753ZI, USART3/VCP pins, and the
basic clock/peripheral configuration. `main.c` is application code; avoid
regenerating CubeMX code over it unless the receiver callbacks and BSP
initialization are preserved.

## ESP32 UART connection

| ESP32-C6-Zero | NUCLEO-H753ZI |
|---|---|
| GPIO4 / UART1 TX | PB7 / USART1_RX |
| GND | GND |

PD8 / USART3_TX and PD9 / USART3_RX are connected to the ST-LINK VCP. Do not
connect the ESP TX to PD8 or PD9; the ST-LINK VCP uses those pins.

The UART receiver and line parser are in `Core/Src/nucleo_receiver.c`. Valid
records are printed as `ID <id>: vx=... m/s, vy=... m/s, omega=... rad/s`.
