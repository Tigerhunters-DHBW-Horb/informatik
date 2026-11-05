#include <WiFi.h>
#include <WiFiUdp.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

// WLAN-Zugangsdaten des vom PC bereitgestellten Hotspots eintragen.
const char *WIFI_SSID = "robocup";
const char *WIFI_PASSWORD = "tigerhunters";

constexpr uint8_t ROBOT_ID = 0;
constexpr uint16_t UDP_PORT = 4210;
constexpr uint8_t PROTOCOL_VERSION = 1;
constexpr uint32_t NUCLEO_BAUD_RATE = 115200;
constexpr int NUCLEO_UART_RX_PIN = 5;
constexpr int NUCLEO_UART_TX_PIN = 4;
constexpr size_t HEADER_SIZE = 12;
constexpr size_t COMMAND_SIZE = 13;
constexpr size_t MAX_PACKET_SIZE = HEADER_SIZE + 255 * COMMAND_SIZE;

WiFiUDP udp;
HardwareSerial NucleoSerial(1);
uint16_t lastSequence = 0;
uint32_t lastSessionId = 0;
bool hasLastSequence = false;

uint16_t readUint16(const uint8_t *data) {
  return (static_cast<uint16_t>(data[0]) << 8) | data[1];
}

uint32_t readUint32(const uint8_t *data) {
  return (static_cast<uint32_t>(data[0]) << 24) |
         (static_cast<uint32_t>(data[1]) << 16) |
         (static_cast<uint32_t>(data[2]) << 8) |
         static_cast<uint32_t>(data[3]);
}

float readFloat32(const uint8_t *data) {
  const uint32_t bits = readUint32(data);
  float value;
  memcpy(&value, &bits, sizeof(value));
  return value;
}

void onRobotCommand(float vx, float vy, float omega) {
  Serial.printf("ID %u: vx=%.3f m/s, vy=%.3f m/s, omega=%.3f rad/s\n",
                ROBOT_ID, vx, vy, omega);
  NucleoSerial.printf("RBT1,%u,%.6f,%.6f,%.6f\n",
                      ROBOT_ID, vx, vy, omega);
}

void processPacket(const uint8_t *packet, size_t length) {
  if (length < HEADER_SIZE ||
      memcmp(packet, "RBT1", 4) != 0 ||
      packet[4] != PROTOCOL_VERSION) {
    return;
  }

  const uint32_t sessionId = readUint32(packet + 5);
  const uint16_t sequence = readUint16(packet + 9);
  const uint8_t count = packet[11];
  if (count == 0 || length != HEADER_SIZE + count * COMMAND_SIZE) {
    return;
  }

  bool found = false;
  float selectedVx = 0.0f;
  float selectedVy = 0.0f;
  float selectedOmega = 0.0f;
  bool seenIds[256] = {};

  for (uint8_t index = 0; index < count; ++index) {
    const uint8_t *command = packet + HEADER_SIZE + index * COMMAND_SIZE;
    const uint8_t id = command[0];
    if (seenIds[id]) {
      return;
    }
    seenIds[id] = true;

    const float vx = readFloat32(command + 1);
    const float vy = readFloat32(command + 5);
    const float omega = readFloat32(command + 9);
    if (!isfinite(vx) || !isfinite(vy) || !isfinite(omega)) {
      return;
    }

    if (id == ROBOT_ID) {
      selectedVx = vx;
      selectedVy = vy;
      selectedOmega = omega;
      found = true;
    }
  }

  if (hasLastSequence && sessionId == lastSessionId &&
      static_cast<int16_t>(sequence - lastSequence) <= 0) {
    return;
  }
  lastSessionId = sessionId;
  lastSequence = sequence;
  hasLastSequence = true;

  if (found) {
    onRobotCommand(selectedVx, selectedVy, selectedOmega);
  }
}

void setup() {
  Serial.begin(115200);
  NucleoSerial.begin(
      NUCLEO_BAUD_RATE, SERIAL_8N1, NUCLEO_UART_RX_PIN, NUCLEO_UART_TX_PIN);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.printf("Verbinde mit PC-Hotspot \"%s\"", WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }

  Serial.printf("\nVerbunden. ESP32-IP: %s\n", WiFi.localIP().toString().c_str());
  if (udp.begin(UDP_PORT) == 0) {
    Serial.printf("Fehler: UDP-Port %u konnte nicht geöffnet werden.\n", UDP_PORT);
    while (true) {
      delay(1000);
    }
  }
  Serial.printf("Empfange UDP-Broadcasts auf Port %u, Roboter-ID %u\n",
                UDP_PORT, ROBOT_ID);
  Serial.printf("Leite Befehle per UART1 (TX GPIO %d, %lu Baud) an den Nucleo weiter\n",
                NUCLEO_UART_TX_PIN,
                static_cast<unsigned long>(NUCLEO_BAUD_RATE));
}

void loop() {
  const int packetSize = udp.parsePacket();
  if (packetSize <= 0) {
    return;
  }

  if (static_cast<size_t>(packetSize) > MAX_PACKET_SIZE) {
    while (udp.available()) {
      udp.read();
    }
    return;
  }

  uint8_t packet[MAX_PACKET_SIZE];
  const int bytesRead = udp.read(packet, sizeof(packet));
  if (bytesRead != packetSize) {
    return;
  }

  processPacket(packet, static_cast<size_t>(bytesRead));
}
