import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'protos'))

import socket
import struct
import time

import ssl_vision_wrapper_pb2 as SSL_WrapperPacket


# --- Konfiguration ---
VISION_MULTICAST_IP = "224.5.23.2"
VISION_PORT = 10020

AUSGABE_INTERVALL = 1.0   # Ausgabe alle 10 Sekunden
# ---------------------


def main_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(('', VISION_PORT))

    mreq = struct.pack(
        "4sl",
        socket.inet_aton(VISION_MULTICAST_IP),
        socket.INADDR_ANY
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"✅ Vision-Empfänger läuft. Lausche auf {VISION_MULTICAST_IP}:{VISION_PORT}")
    print(f"Ausgabe wird alle {AUSGABE_INTERVALL} Sekunden aktualisiert.")
    print("Drücke STRG+C zum Beenden.\n")

    letzte_ausgabe = 0

    # Hier speichern wir die zuletzt gültigen Werte
    letzter_ball = None
    letzte_gelbe_roboter = {}
    letzte_blaue_roboter = {}

    while True:
        try:
            data, addr = sock.recvfrom(65536)

            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            packet.ParseFromString(data)

            if packet.HasField('detection'):
                det = packet.detection

                # Ball merken, wenn erkannt
                if len(det.balls) > 0:
                    ball = det.balls[0]
                    letzter_ball = {
                        "x": ball.x,
                        "y": ball.y,
                        "zeit": time.time()
                    }

                # Gelbe Roboter merken, wenn erkannt
                for rob in det.robots_yellow:
                    letzte_gelbe_roboter[rob.robot_id] = {
                        "x": rob.x,
                        "y": rob.y,
                        "phi": rob.orientation,
                        "zeit": time.time()
                    }

                # Blaue Roboter merken, wenn erkannt
                for rob in det.robots_blue:
                    letzte_blaue_roboter[rob.robot_id] = {
                        "x": rob.x,
                        "y": rob.y,
                        "phi": rob.orientation,
                        "zeit": time.time()
                    }

            aktuelle_zeit = time.time()

            # Nur alle 10 Sekunden Ausgabe
            if aktuelle_zeit - letzte_ausgabe >= AUSGABE_INTERVALL:
                letzte_ausgabe = aktuelle_zeit

                print("\n==============================")
                print("=== SSL-Vision Daten ===")
                print("==============================")

                # Ball ausgeben
                if letzter_ball is not None:
                    alter = aktuelle_zeit - letzter_ball["zeit"]
                    print("\nBall:")
                    print(f"  x = {letzter_ball['x']:9.2f} mm")
                    print(f"  y = {letzter_ball['y']:9.2f} mm")
                    print(f"  letzter Empfang vor {alter:.2f} s")
                else:
                    print("\nBall: bisher nicht erkannt")

                # Gelbe Roboter ausgeben
                print("\nGelbe Roboter:")
                if len(letzte_gelbe_roboter) > 0:
                    for robot_id, rob in sorted(letzte_gelbe_roboter.items()):
                        alter = aktuelle_zeit - rob["zeit"]
                        print(
                            f"  ID {robot_id}: "
                            f"x={rob['x']:9.2f} mm, "
                            f"y={rob['y']:9.2f} mm, "
                            f"phi={rob['phi']:6.2f} rad, "
                            f"vor {alter:.2f} s"
                        )
                else:
                    print("  bisher keine gelben Roboter erkannt")

                # Blaue Roboter ausgeben
                print("\nBlaue Roboter:")
                if len(letzte_blaue_roboter) > 0:
                    for robot_id, rob in sorted(letzte_blaue_roboter.items()):
                        alter = aktuelle_zeit - rob["zeit"]
                        print(
                            f"  ID {robot_id}: "
                            f"x={rob['x']:9.2f} mm, "
                            f"y={rob['y']:9.2f} mm, "
                            f"phi={rob['phi']:6.2f} rad, "
                            f"vor {alter:.2f} s"
                        )
                else:
                    print("  bisher keine blauen Roboter erkannt")

        except KeyboardInterrupt:
            print("\nEmpfang gestoppt.")
            break

        except Exception as e:
            print(f"\nFehler beim Empfangen: {e}")
            break


if __name__ == "__main__":
    main_receiver()