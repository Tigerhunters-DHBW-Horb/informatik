# NUCLEO-H753ZI: STM32Cube/CMake-Projekt für VS Code

Dieses Projekt empfängt die vom ESP32 über UART weitergeleiteten UDP-Fahrbefehle und zeigt sie über USART3 am ST-LINK Virtual COM Port an. Es enthält ein direkt mit CMake baubares STM32Cube-HAL-Projekt; eine CubeMX-Codegenerierung ist für den Build nicht erforderlich.

Das UART-Drahtformat ist eine ASCII-Zeile:

```text
RBT1,<ID>,<vx>,<vy>,<omega>\n
```

`vx` und `vy` sind in m/s, `omega` in rad/s. Das sind Fahrbefehle, keine SSL-Vision-Positionsdaten.

## Einmalige Voraussetzungen

1. Öffne diesen `Nucleo`-Ordner in VS Code. Empfohlen sind die Erweiterungen **STM32CubeIDE for Visual Studio Code** und **CMake Tools**.
2. Installiere über die ST-Erweiterung die CLI-Tools **Arm GNU Toolchain** und **STM32CubeProgrammer**. Stelle sicher, dass `arm-none-eabi-gcc` und `STM32_Programmer_CLI` im VS-Code-Prozess über `PATH` erreichbar sind; starte VS Code nach einer Toolchain-Installation gegebenenfalls neu.
3. Installiere das Firmware-Paket **STM32Cube FW_H7 V1.11.2** mit STM32CubeMX oder dem STM32Cube-Paketmanager.
4. Setze `STM32CUBE_H7_PATH` auf den entpackten Paketordner, der den Unterordner `Drivers` enthält. Beispiel:

   ```bash
   export STM32CUBE_H7_PATH="$HOME/STM32Cube/Repository/STM32Cube_FW_H7_V1.11.2"
   code .
   ```

   Alternativ kann der Pfad bei der CMake-Konfiguration mit `-DSTM32CUBE_H7_PATH=/absoluter/pfad/STM32Cube_FW_H7_V1.11.2` angegeben werden.

Das Projekt verwendet CMake Presets. Wähle in VS Code das Preset **NUCLEO-H753ZI (STM32Cube/CMake)** und konfiguriere/build es mit CMake Tools. Alternativ im Terminal dieses Ordners:

```bash
cmake --preset nucleo-h753zi
cmake --build --preset nucleo-h753zi
cmake --build --preset nucleo-h753zi --target flash
```

Das Flash-Ziel nutzt den ST-LINK über STM32CubeProgrammer. Der resultierende Build liegt unter `build/nucleo_h753zi_receiver.elf`. Der Nucleo wird nicht automatisch beim Build geflasht.

## UART-Verbindung und Anzeige

Bei der NUCLEO-H753ZI ist USART3 mit dem ST-LINK Virtual COM Port verbunden:

| ESP32 | Nucleo-H753ZI |
|---|---|
| GPIO17 / UART2 TX | PD9 / USART3_RX |
| GND | GND |

Der ESP32 sendet mit 115200 Baud, 8N1 und 3,3-V-Logik. Verbinde TX mit RX, nicht TX mit TX. Der Nucleo-TX liegt an PD8/USART3_TX und ist mit dem ST-LINK-VCP verbunden. Der serielle Monitor muss auf 115200 Baud eingestellt sein.

1. Trage WLAN-Zugangsdaten und `ROBOT_ID` in `../ESP32/ESP32.ino` ein und flashe den ESP32.
2. Baue und flashe dieses Projekt mit dem ST-LINK.
3. Öffne in der STM32CubeIDE-for-VS-Code-Erweiterung das Serial Terminal für den ST-LINK Virtual COM Port mit 115200 Baud.
4. Starte den PC-Sender, wobei die Befehls-ID mit `ROBOT_ID` übereinstimmt:

   ```bash
   python3 udp_sender.py --broadcast <ESP32-IP> --robot 0,0.5,-0.2,0.1
   ```

Erwartete Anzeige:

```text
Nucleo-H753ZI bereit; warte auf ESP32-Daten (USART3 115200 8N1)
ID 0: vx=0.500 m/s, vy=-0.200 m/s, omega=0.100 rad/s
```

Die UART-Initialisierung, Taktkonfiguration und HAL-Interrupt-Anbindung stehen in [`Core/Src/main.c`](./Core/Src/main.c); der zeilenorientierte UART-Empfänger ist in [`Core/Src/nucleo_receiver.c`](./Core/Src/nucleo_receiver.c).
