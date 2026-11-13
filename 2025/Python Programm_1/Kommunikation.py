import socket
import struct
import sys
import os
import time
from collections import deque

from google.protobuf.message import DecodeError

# Protobuf Pfad setzen
sys.path.append(os.path.join(os.path.dirname(__file__), 'protos'))

try:
    import ssl_vision_wrapper_pb2 as SSL_WrapperPacket
    import grSim_Packet_pb2 as grSim_Packet
except ImportError:
    print("Fehler: Protobuf-Dateien nicht gefunden!")


class KommunikationGrSim:
    def __init__(self, vm_ip, vision_port=10020, command_port=20011):
        self.vm_ip = vm_ip

        # Vision-Empfänger Multicast
        self.recv_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )

        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind(('', vision_port))
        self.recv_sock.setblocking(False)

        mreq = struct.pack(
            "4sl",
            socket.inet_aton("224.5.23.2"),
            socket.INADDR_ANY
        )

        self.recv_sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            mreq
        )
        self._cached_geometry = None
        self._grosses_paket_eingelesen = False

        # Befehls-Sender Unicast
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.grsim_addr = (self.vm_ip, command_port)

        print(f"Kommunikation bereit.")
        print(f"Vision-Port: {vision_port}")
        print(f"Command-Ziel: {self.vm_ip}:{command_port}")

    def empfange_paket(self):
        positionspakete = deque(maxlen=4)

        while True:
            try:
                data, _ = self.recv_sock.recvfrom(65536)
            except BlockingIOError:
                break

            if len(data) > 1000:
                if not self._grosses_paket_eingelesen:
                    packet = SSL_WrapperPacket.SSL_WrapperPacket()
                    try:
                        packet.ParseFromString(data)
                    except DecodeError as exc:
                        print(
                            f"Ungueltiges Definitionspaket ignoriert: {exc}",
                            file=sys.stderr,
                        )
                        continue

                    if packet.HasField("geometry"):
                        self._cached_geometry = self._kopiere_protobuf(
                            packet.geometry
                        )
                    self._grosses_paket_eingelesen = True
                continue

            positionspakete.append(data)

        if not positionspakete:
            return None

        letztes_paket_mit_detection = None
        roboter_nach_id = {
            "robots_blue": {},
            "robots_yellow": {},
        }
        roboter_ohne_id = {
            "robots_blue": [],
            "robots_yellow": [],
        }
        letzter_ball = []

        for data in positionspakete:
            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            try:
                packet.ParseFromString(data)
            except DecodeError as exc:
                print(f"Ungueltiges Vision-Paket ignoriert: {exc}", file=sys.stderr)
                continue

            if not packet.HasField("detection"):
                continue

            letztes_paket_mit_detection = packet
            detection = packet.detection

            if detection.balls:
                letzter_ball = [
                    self._kopiere_protobuf(ball)
                    for ball in detection.balls
                ]

            for feld, roboter_liste in (
                ("robots_blue", detection.robots_blue),
                ("robots_yellow", detection.robots_yellow),
            ):
                roboter_ohne_id[feld] = [
                    self._kopiere_protobuf(roboter)
                    for roboter in roboter_liste
                    if not roboter.HasField("robot_id")
                ]

                for roboter in roboter_liste:
                    if not roboter.HasField("robot_id"):
                        continue

                    roboter_id = roboter.robot_id
                    roboter_nach_id[feld][roboter_id] = (
                        self._kopiere_protobuf(roboter)
                    )

        if letztes_paket_mit_detection is None:
            return None

        hat_positionen = (
            letzter_ball
            or any(roboter_nach_id[feld] for feld in roboter_nach_id)
            or any(roboter_ohne_id[feld] for feld in roboter_ohne_id)
        )
        if not hat_positionen:
            return None

        ergebnis = SSL_WrapperPacket.SSL_WrapperPacket()
        ergebnis.CopyFrom(letztes_paket_mit_detection)
        detection = ergebnis.detection
        del detection.balls[:]
        del detection.robots_blue[:]
        del detection.robots_yellow[:]

        for ball in letzter_ball:
            detection.balls.add().CopyFrom(ball)

        for feld in ("robots_blue", "robots_yellow"):
            for roboter in roboter_nach_id[feld].values():
                getattr(detection, feld).add().CopyFrom(roboter)
            for roboter in roboter_ohne_id[feld]:
                getattr(detection, feld).add().CopyFrom(roboter)

        if self._cached_geometry is not None:
            ergebnis.geometry.CopyFrom(self._cached_geometry)

        return ergebnis

    @staticmethod
    def _kopiere_protobuf(nachricht):
        kopie = type(nachricht)()
        kopie.CopyFrom(nachricht)
        return kopie

    def sende_roboter_befehl(
        self,
        robot_id,
        vx,
        vy,
        v_phi,
        team_gelb=False,
        kick_x=0.0,
        kick_z=0.0,
        spinner=False
    ):
        packet = grSim_Packet.grSim_Packet()

        packet.commands.timestamp = time.time()
        packet.commands.isteamyellow = team_gelb

        robot_cmd = packet.commands.robot_commands.add()

        robot_cmd.id = int(robot_id)

        # grSim erwartet hier:
        # veltangent / velnormal in m/s
        # velangular in rad/s
        robot_cmd.veltangent = float(vx)
        robot_cmd.velnormal = float(vy)
        robot_cmd.velangular = float(v_phi)

        # Kick und Spinner
        robot_cmd.kickspeedx = float(kick_x)
        robot_cmd.kickspeedz = float(kick_z)
        robot_cmd.spinner = bool(spinner)

        # False bedeutet: veltangent/velnormal/velangular benutzen
        robot_cmd.wheelsspeed = False

        try:
            self.send_sock.sendto(
                packet.SerializeToString(),
                self.grsim_addr
            )

        except Exception as e:
            print(f"Fehler beim Senden: {e}")


class KommunikationRoboter:
    """Wird später für echte Hardware verwendet."""
    def __init__(self):
        pass