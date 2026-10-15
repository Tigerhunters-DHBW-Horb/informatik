import os
import socket
import struct
import sys
from datetime import datetime

from google.protobuf.message import DecodeError
from google.protobuf import text_format


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import ssl_vision_wrapper_pb2 as SSL_WrapperPacket


VISION_MULTICAST_IP = "224.5.23.2"
VISION_PORT = 10006


def erstelle_empfaenger():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", VISION_PORT))
    sock.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_ADD_MEMBERSHIP,
        struct.pack(
            "=4s4s",
            socket.inet_aton(VISION_MULTICAST_IP),
            socket.inet_aton("0.0.0.0"),
        ),
    )
    return sock


def main():
    try:
        sock = erstelle_empfaenger()
    except OSError as exc:
        raise SystemExit(f"SSL-Vision-Empfaenger konnte nicht gestartet werden: {exc}") from exc

    print(
        f"SSL-Vision-Terminal lauscht auf "
        f"{VISION_MULTICAST_IP}:{VISION_PORT}."
    )
    print("Die Anzeige wird bei jedem Paket aktualisiert.")
    print("Beenden mit Ctrl+C.\n")

    paket_nummer = 0
    try:
        while True:
            data, addr = sock.recvfrom(65535)
            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            try:
                packet.ParseFromString(data)
            except DecodeError as exc:
                print(f"Ungueltiges Protobuf-Paket von {addr[0]} ignoriert: {exc}", file=sys.stderr)
                continue

            paket_nummer += 1
            empfangszeit = datetime.now().astimezone().isoformat(timespec="milliseconds")
            if sys.stdout.isatty():
                sys.stdout.write("\033[2J\033[H")
            print(
                f"SSL-Vision-Terminal | {VISION_MULTICAST_IP}:{VISION_PORT}"
            )
            print(
                f"--- Paket {paket_nummer} | {empfangszeit} | "
                f"{addr[0]}:{addr[1]} | {len(data)} Bytes ---"
            )
            inhalt = text_format.MessageToString(packet)
            print(inhalt if inhalt else "(leeres SSL-Vision-Paket)")
            print(flush=True)
    except KeyboardInterrupt:
        print("\nSSL-Vision-Empfang beendet.")
    except OSError as exc:
        raise SystemExit(f"Fehler beim SSL-Vision-Empfang: {exc}") from exc
    finally:
        sock.close()


if __name__ == "__main__":
    main()
