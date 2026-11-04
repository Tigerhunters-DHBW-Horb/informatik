#!/usr/bin/env python3
"""Send robot velocity commands to ESP32 devices over UDP broadcast."""

from __future__ import annotations

import argparse
from contextlib import closing
import math
import secrets
import socket
import struct
import time
from dataclasses import dataclass
from typing import Sequence


MAGIC = b"RBT1"
PROTOCOL_VERSION = 1
UDP_PORT = 4210
HEADER = struct.Struct("!4sBIHB")
COMMAND = struct.Struct("!Bfff")


@dataclass(frozen=True)
class RobotCommand:
    robot_id: int
    vx: float
    vy: float
    omega: float


def encode_packet(
    commands: Sequence[RobotCommand], sequence: int, session_id: int = 0
) -> bytes:
    """Encode one broadcast packet containing commands for one or more robots."""
    if not 1 <= len(commands) <= 255:
        raise ValueError("Ein Paket muss 1 bis 255 Roboterbefehle enthalten.")
    if not 0 <= sequence <= 0xFFFF:
        raise ValueError("Die Sequenznummer muss zwischen 0 und 65535 liegen.")
    if not 0 <= session_id <= 0xFFFFFFFF:
        raise ValueError("Die Sitzungs-ID muss zwischen 0 und 4294967295 liegen.")

    packet = bytearray(
        HEADER.pack(MAGIC, PROTOCOL_VERSION, session_id, sequence, len(commands))
    )
    seen_ids: set[int] = set()
    for command in commands:
        if not 0 <= command.robot_id <= 255:
            raise ValueError(f"Ungültige Roboter-ID: {command.robot_id}")
        if command.robot_id in seen_ids:
            raise ValueError(f"Roboter-ID {command.robot_id} kommt mehrfach vor.")
        values = (command.vx, command.vy, command.omega)
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"Geschwindigkeiten für ID {command.robot_id} müssen endlich sein.")

        try:
            packet.extend(COMMAND.pack(command.robot_id, *values))
        except OverflowError as exc:
            raise ValueError(
                f"Geschwindigkeiten für ID {command.robot_id} liegen außerhalb des Float32-Bereichs."
            ) from exc
        seen_ids.add(command.robot_id)

    return bytes(packet)


class UdpSender:
    def __init__(self, broadcast_ip: str, port: int = UDP_PORT) -> None:
        self.address = (broadcast_ip, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sequence = 0
        self.session_id = secrets.randbits(32)

    def send(self, commands: Sequence[RobotCommand]) -> None:
        packet = encode_packet(commands, self.sequence, self.session_id)
        self.socket.sendto(packet, self.address)
        self.sequence = (self.sequence + 1) & 0xFFFF

    def close(self) -> None:
        self.socket.close()


def parse_robot(value: str) -> RobotCommand:
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "Format: ID,VX,VY,OMEGA (zum Beispiel 0,1.0,0.0,0.0)"
        )
    try:
        robot_id = int(parts[0])
        vx, vy, omega = map(float, parts[1:])
        command = RobotCommand(robot_id, vx, vy, omega)
        encode_packet([command], 0)
    except (ValueError, OverflowError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return command


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sendet UDP-Broadcast-Befehle an ESP32-Roboter."
    )
    parser.add_argument(
        "--broadcast",
        default="10.42.0.255",
        help="Broadcast-Adresse des PC-Hotspots (Standard: 10.42.0.255)",
    )
    parser.add_argument("--port", type=int, default=UDP_PORT, help=f"UDP-Port (Standard: {UDP_PORT})")
    parser.add_argument(
        "--rate",
        type=float,
        default=50.0,
        help="Sendeintervall in Paketen pro Sekunde (Standard: 50)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Befehl nur einmal senden und anschließend beenden",
    )
    parser.add_argument(
        "--robot",
        action="append",
        type=parse_robot,
        required=True,
        metavar="ID,VX,VY,OMEGA",
        help="Geschwindigkeiten in m/s und rad/s; mehrfach für mehrere Roboter",
    )
    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port muss zwischen 1 und 65535 liegen.")
    if not math.isfinite(args.rate) or args.rate <= 0:
        parser.error("--rate muss eine positive, endliche Zahl sein.")
    if len({command.robot_id for command in args.robot}) != len(args.robot):
        parser.error("Jede Roboter-ID darf nur einmal angegeben werden.")

    print(f"UDP-Broadcast an {args.broadcast}:{args.port}")
    print(f"Roboter-IDs: {', '.join(str(command.robot_id) for command in args.robot)}")
    print("Mit STRG+C beenden.")

    try:
        with closing(UdpSender(args.broadcast, args.port)) as sender:
            try:
                if args.once:
                    sender.send(args.robot)
                    return

                interval = 1.0 / args.rate
                while True:
                    start = time.monotonic()
                    sender.send(args.robot)
                    time.sleep(max(0.0, interval - (time.monotonic() - start)))
            except KeyboardInterrupt:
                sender.send(
                    [
                        RobotCommand(command.robot_id, 0.0, 0.0, 0.0)
                        for command in args.robot
                    ]
                )
                print("\nSender beendet; Stoppbefehl gesendet.")
    except OSError as exc:
        parser.error(f"UDP-Kommunikation fehlgeschlagen: {exc}")


if __name__ == "__main__":
    main()
