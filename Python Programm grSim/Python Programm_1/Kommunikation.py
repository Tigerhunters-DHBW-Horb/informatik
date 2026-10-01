import socket
import struct
import sys
import os
import time

# Protobuf Pfad setzen
sys.path.append(os.path.join(os.path.dirname(__file__), 'protos'))

try:
    import ssl_vision_wrapper_pb2 as SSL_WrapperPacket
    import grSim_Packet_pb2 as grSim_Packet
except ImportError as exc:
    raise ImportError(
        f"Protobuf-Import fehlgeschlagen: {exc}. "
        'Installiere protobuf in der aktiven Umgebung mit: '
        'python -m pip install "protobuf>=3.20"'
    ) from exc


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

        # Befehls-Sender Unicast
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.grsim_addr = (self.vm_ip, command_port)

        print(f"Kommunikation bereit.")
        print(f"Vision-Port: {vision_port}")
        print(f"Command-Ziel: {self.vm_ip}:{command_port}")

    def empfange_paket(self):
        try:
            data, addr = self.recv_sock.recvfrom(65536)

            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            packet.ParseFromString(data)

            return packet

        except BlockingIOError:
            # Kein Paket verfügbar, ist normal bei non-blocking socket
            return None

        except Exception as e:
            print(f"Fehler beim Empfangen: {e}")
            return None

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