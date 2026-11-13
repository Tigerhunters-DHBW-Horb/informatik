import argparse
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
# VISION_PORT = 10006
VISION_PORT = 10020


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


def erstelle_argument_parser():
    parser = argparse.ArgumentParser(
        description="Empfaengt und filtert SSL-Vision-Pakete."
    )
    parser.add_argument(
        "--team",
        choices=("blue", "yellow", "both"),
        default="both",
        help="welches Roboterteam ausgegeben wird (Standard: both)",
    )
    parser.add_argument(
        "--robot-id",
        type=int,
        action="append",
        dest="robot_ids",
        help="nur diese Roboter-ID ausgeben; mehrfach verwendbar",
    )
    parser.add_argument(
        "--no-ball",
        action="store_false",
        dest="show_ball",
        help="keine Ballerkennungen ausgeben",
    )
    parser.add_argument(
        "--no-robots",
        action="store_false",
        dest="show_robots",
        help="keine Roboter ausgeben",
    )
    parser.set_defaults(show_ball=True, show_robots=True)
    return parser


def filtere_paket(packet, team, robot_ids, show_ball, show_robots=True):
    gefiltertes_paket = SSL_WrapperPacket.SSL_WrapperPacket()
    gefiltertes_paket.CopyFrom(packet)

    if not gefiltertes_paket.HasField("detection"):
        return gefiltertes_paket

    detection = gefiltertes_paket.detection
    if not show_ball:
        del detection.balls[:]

    teams = {
        "blue": ("robots_blue",),
        "yellow": ("robots_yellow",),
        "both": ("robots_blue", "robots_yellow"),
    }
    erlaubte_ids = set(robot_ids) if robot_ids else None
    for feld in ("robots_blue", "robots_yellow"):
        roboter = getattr(detection, feld)
        if not show_robots or feld not in teams[team]:
            del roboter[:]
            continue
        if erlaubte_ids is not None:
            for index in range(len(roboter) - 1, -1, -1):
                roboter_id = roboter[index].robot_id
                if not roboter[index].HasField("robot_id") or roboter_id not in erlaubte_ids:
                    del roboter[index]

    return gefiltertes_paket


def hat_anzeigedaten(packet):
    if packet.HasField("geometry"):
        return True
    if not packet.HasField("detection"):
        return False

    detection = packet.detection
    return bool(
        detection.balls
        or detection.robots_blue
        or detection.robots_yellow
    )


def main(argv=None):
    args = erstelle_argument_parser().parse_args(argv)
    try:
        sock = erstelle_empfaenger()
    except OSError as exc:
        raise SystemExit(f"SSL-Vision-Empfaenger konnte nicht gestartet werden: {exc}") from exc

    print(
        f"SSL-Vision-Terminal lauscht auf "
        f"{VISION_MULTICAST_IP}:{VISION_PORT}."
    )
    print(
        f"Filter: Team={args.team}, "
        f"Roboter-IDs={args.robot_ids or 'alle'}, "
        f"Roboter={'an' if args.show_robots else 'aus'}, "
        f"Ball={'an' if args.show_ball else 'aus'}."
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
            gefiltertes_paket = filtere_paket(
                packet,
                args.team,
                args.robot_ids,
                args.show_ball,
                args.show_robots,
            )
            if not hat_anzeigedaten(gefiltertes_paket):
                continue

            inhalt = text_format.MessageToString(gefiltertes_paket)
            if not inhalt:
                continue

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
            print(inhalt)
            print(flush=True)
    except KeyboardInterrupt:
        print("\nSSL-Vision-Empfang beendet.")
    except OSError as exc:
        raise SystemExit(f"Fehler beim SSL-Vision-Empfang: {exc}") from exc
    finally:
        sock.close()


if __name__ == "__main__":
    main()
