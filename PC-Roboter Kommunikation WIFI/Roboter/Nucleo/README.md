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
3. Installiere das Firmware-Paket **STM32Cube FW_H7** mit STM32CubeMX oder dem STM32Cube-Paketmanager.
4. Öffne ein Terminal im Nucleo-Projektordner und setze `STM32CUBE_H7_PATH` auf den entpackten Paketordner, der den Unterordner `Drivers` enthält. Falls lokale `PATH`-Einträge in einer `.profile` im Nucleo-Projektordner stehen, lade sie zuerst. Starte VS Code aus diesem Terminal, damit auch CMake Tools die Umgebungsvariablen erbt:

   ```bash
   source ./.profile # nur falls die lokale Datei vorhanden ist
   export STM32CUBE_H7_PATH="$HOME/STM32Cube/Repository/STM32Cube_FW_H7_V1.12.1"
   command -v arm-none-eabi-gcc
   command -v STM32_Programmer_CLI
   code .
   ```

   Passe Versionsnummer und Pfad an die installierte FW_H7-Version an. Alternativ kann der Pfad bei der CMake-Konfiguration mit `-DSTM32CUBE_H7_PATH=/absoluter/pfad/STM32Cube_FW_H7_V1.12.1` angegeben werden.
   Beide `command -v`-Befehle müssen einen Pfad ausgeben. Das CMake-Preset verwendet Unix Makefiles und braucht daher kein separat installiertes Ninja.

Das Projekt verwendet CMake Presets. Wähle in VS Code das Preset **NUCLEO-H753ZI (STM32Cube/CMake)** und konfiguriere/build es mit CMake Tools. Alternativ im Terminal dieses Ordners:

```bash
cmake --preset nucleo-h753zi
cmake --build --preset nucleo-h753zi
cmake --build --preset nucleo-h753zi --target flash
```

Konfiguriere CMake erneut, nachdem du `source ./.profile` geladen hast; so kann CMake `STM32_Programmer_CLI` finden. Das Flash-Ziel nutzt den ST-LINK über den dabei gefundenen absoluten Programmer-Pfad. Der resultierende Build liegt unter `build-unix-makefiles/nucleo_h753zi_receiver.elf`. Der Nucleo wird nicht automatisch beim normalen Build geflasht.

## UART-Verbindung und Anzeige

Bei der NUCLEO-H753ZI ist USART3 mit dem ST-LINK Virtual COM Port verbunden:

| ESP32 | Nucleo-H753ZI |
|---|---|
| GPIO2 / UART1 TX (ESP32-C6-Zero) | PB7 / USART1_RX |
| GND | GND |

Der ESP32 sendet mit 115200 Baud, 8N1 und 3,3-V-Logik. Verbinde TX mit RX, nicht TX mit TX. USART3 (PD8/PD9) ist vollständig für den ST-LINK-VCP reserviert; verbinde den ESP-TX daher nicht mit PD8 oder PD9. USART1 empfängt die ESP32-Daten an PB7, während die Monitor-Ausgabe weiter über USART3 läuft. Der serielle Monitor muss auf 115200 Baud eingestellt sein.

1. Trage WLAN-Zugangsdaten und `ROBOT_ID` in `../ESP32/ESP32.ino` ein und flashe den ESP32.
2. Baue und flashe dieses Projekt mit dem ST-LINK.
3. Öffne in der STM32CubeIDE-for-VS-Code-Erweiterung das Serial Terminal für den ST-LINK Virtual COM Port mit 115200 Baud.
4. Starte den PC-Sender, wobei die Befehls-ID mit `ROBOT_ID` übereinstimmt:

   ```bash
   python3 udp_sender.py --broadcast <ESP32-IP> --robot 0,0.5,-0.2,0.1
   ```

Erwartete Anzeige:

```text
Nucleo-H753ZI bereit; ESP32 RX: USART1/PB7, Monitor: USART3 115200 8N1
ID 0: vx=0.500 m/s, vy=-0.200 m/s, omega=0.100 rad/s
```

Die serielle Konsole wird wie im funktionierenden Motorentest über die Nucleo-BSP (`BSP_COM_Init(COM1, ...)`, USART3-Oversampling 8) initialisiert. Die separate USART1-RX-Schnittstelle für den ESP32 verwendet PB7. Die Taktkonfiguration und HAL-Interrupt-Anbindung stehen in [`Core/Src/main.c`](./Core/Src/main.c); der zeilenorientierte UART-Empfänger ist in [`Core/Src/nucleo_receiver.c`](./Core/Src/nucleo_receiver.c).
