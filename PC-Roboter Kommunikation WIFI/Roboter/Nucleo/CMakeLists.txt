cmake_minimum_required(VERSION 3.22)

project(nucleo_h753zi_receiver C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(STM32CUBE_H7_PATH "$ENV{STM32CUBE_H7_PATH}" CACHE PATH
    "Root directory of the STM32CubeH7 firmware package")
if(NOT STM32CUBE_H7_PATH AND DEFINED ENV{STM32CUBE_H7_PATH})
  set(STM32CUBE_H7_PATH "$ENV{STM32CUBE_H7_PATH}" CACHE PATH
      "Root directory of the STM32CubeH7 firmware package" FORCE)
endif()
if(NOT STM32CUBE_H7_PATH OR
   NOT EXISTS "${STM32CUBE_H7_PATH}/Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal.c")
  message(FATAL_ERROR
    "Set STM32CUBE_H7_PATH to the STM32CubeH7 firmware package directory.")
endif()

set(CMSIS_DIR "${STM32CUBE_H7_PATH}/Drivers/CMSIS")
set(DEVICE_DIR "${CMSIS_DIR}/Device/ST/STM32H7xx")
set(HAL_DIR "${STM32CUBE_H7_PATH}/Drivers/STM32H7xx_HAL_Driver")
set(BSP_DIR "${STM32CUBE_H7_PATH}/Drivers/BSP/STM32H7xx_Nucleo")
set(LINKER_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/STM32H753ZITX_FLASH.ld")

find_program(STM32_PROGRAMMER_CLI
  NAMES STM32_Programmer_CLI
  REQUIRED
  DOC "Path to STM32CubeProgrammer command-line executable"
)

set(HAL_SOURCES
  "${HAL_DIR}/Src/stm32h7xx_hal.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_cortex.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_dma.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_dma_ex.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_exti.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_flash.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_flash_ex.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_gpio.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_pwr.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_pwr_ex.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_rcc.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_rcc_ex.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_uart.c"
  "${HAL_DIR}/Src/stm32h7xx_hal_uart_ex.c"
)

add_executable(nucleo_h753zi_receiver.elf
  Core/Src/main.c
  Core/Src/nucleo_receiver.c
  "${BSP_DIR}/stm32h7xx_nucleo.c"
  "${DEVICE_DIR}/Source/Templates/system_stm32h7xx.c"
  "${DEVICE_DIR}/Source/Templates/gcc/startup_stm32h753xx.s"
  ${HAL_SOURCES}
)

target_include_directories(nucleo_h753zi_receiver.elf PRIVATE
  Core/Inc
  "${CMSIS_DIR}/Include"
  "${DEVICE_DIR}/Include"
  "${HAL_DIR}/Inc"
  "${HAL_DIR}/Inc/Legacy"
  "${BSP_DIR}"
)

target_compile_definitions(nucleo_h753zi_receiver.elf PRIVATE
  USE_HAL_DRIVER
  STM32H753xx
)

target_compile_options(nucleo_h753zi_receiver.elf PRIVATE
  $<$<COMPILE_LANGUAGE:C>:-Wall>
  $<$<COMPILE_LANGUAGE:C>:-Wextra>
  $<$<COMPILE_LANGUAGE:C>:-Werror=return-type>
  $<$<COMPILE_LANGUAGE:C>:-ffunction-sections>
  $<$<COMPILE_LANGUAGE:C>:-fdata-sections>
  -mcpu=cortex-m7
  -mthumb
  -mfpu=fpv5-d16
  -mfloat-abi=hard
)

target_link_options(nucleo_h753zi_receiver.elf PRIVATE
  -mcpu=cortex-m7
  -mthumb
  -mfpu=fpv5-d16
  -mfloat-abi=hard
  --specs=nano.specs
  --specs=nosys.specs
  "-T${LINKER_SCRIPT}"
  -Wl,--gc-sections
  -Wl,--print-memory-usage
  "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/nucleo_h753zi_receiver.map"
)

set_target_properties(nucleo_h753zi_receiver.elf PROPERTIES
  LINK_DEPENDS "${LINKER_SCRIPT}"
)

add_custom_target(flash
  COMMAND "${STM32_PROGRAMMER_CLI}" -c port=SWD -w
          "$<TARGET_FILE:nucleo_h753zi_receiver.elf>" -v -rst
  DEPENDS nucleo_h753zi_receiver.elf
  USES_TERMINAL
  COMMENT "Flashing NUCLEO-H753ZI through ST-LINK"
)
