#!/usr/bin/env python3

import math
import socket
import struct
import time

import ssl_vision_detection_pb2 as detection_proto
import ssl_vision_geometry_pb2 as geometry_proto
import ssl_vision_wrapper_pb2 as wrapper_proto

# SSL-Vision-Standardadresse
MULTICAST_IP = "224.5.23.2"
PORT = 10006
PACKETS_PER_SECOND = 60

# Falls der Empfänger auf demselben Rechner läuft:
MULTICAST_IP = "127.0.0.1"
PORT = 10006

FIELD_LENGTH = 9000.0   # mm
FIELD_WIDTH = 6000.0    # mm

NUM_ROBOTS_BLUE = 11
NUM_ROBOTS_YELLOW = 11
NUM_CAMERAS = 4

def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # TTL 1: Multicast bleibt im lokalen Netzwerk
    sock.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_MULTICAST_TTL,
        struct.pack("b", 1),
    )

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def build_detection_frame(t, frame_number=0):
    frame = detection_proto.SSL_DetectionFrame()

    # Zeitstempel
    frame.frame_number = frame_number
    frame.t_sent = time.time()
    frame.t_capture = frame.t_sent - 0.01

    # Kamera simulieren
    frame.camera_id = int((t * 2.0) % NUM_CAMERAS)

    # Ball bewegt sich auf einer leicht gekrümmten Bahn
    ball_x = 1500.0 * math.sin(t * 0.8)
    ball_y = 1000.0 * math.cos(t * 0.55)

    ball = frame.balls.add()
    ball.confidence = 0.99
    ball.area = 120
    ball.x = ball_x
    ball.y = ball_y
    ball.z = 0.0
    ball.pixel_x = 640
    ball.pixel_y = 360

    # Blaue Roboter
    for robot_id in range(NUM_ROBOTS_BLUE):
        phase = t * 0.5 + robot_id * 2.0

        x = -2500.0 + robot_id * 900.0 + 300.0 * math.sin(phase)
        y = 1300.0 * math.sin(phase * 0.8)

        orientation = math.atan2(ball_y - y, ball_x - x)

        robot = frame.robots_blue.add()
        robot.robot_id = robot_id
        robot.x = x
        robot.y = y
        robot.orientation = orientation
        robot.confidence = 0.97
        robot.pixel_x = 640 + robot_id * 30
        robot.pixel_y = 360

        if hasattr(robot, "height"):
            robot.height = 150.0

    # Gelbe Roboter
    for robot_id in range(NUM_ROBOTS_YELLOW):
        phase = t * 0.65 + robot_id * 1.7

        x = 2500.0 - robot_id * 900.0 + 350.0 * math.cos(phase)
        y = 1300.0 * math.cos(phase * 0.7)

        orientation = math.atan2(ball_y - y, ball_x - x)

        robot = frame.robots_yellow.add()
        robot.robot_id = robot_id
        robot.x = x
        robot.y = y
        robot.orientation = orientation
        robot.confidence = 0.97
        robot.pixel_x = 640 - robot_id * 30
        robot.pixel_y = 360

        if hasattr(robot, "height"):
            robot.height = 150.0

    return frame

def build_geometry_data():
    geometry = geometry_proto.SSL_GeometryData()

    geometry.field.field_length = int(FIELD_LENGTH)
    geometry.field.field_width = int(FIELD_WIDTH)
    geometry.field.goal_width = 1000
    geometry.field.goal_depth = 180
    geometry.field.boundary_width = 300
    geometry.field.penalty_area_depth = 1000
    geometry.field.penalty_area_width = 2000

    geometry.field.field_lines.add(
        name="LeftTouchLine",
        p1=geometry_proto.Vector2f(
            x=-FIELD_LENGTH / 2,
            y=-FIELD_WIDTH / 2,
        ),
        p2=geometry_proto.Vector2f(
            x=-FIELD_LENGTH / 2,
            y=FIELD_WIDTH / 2,
        ),
        thickness=10.0,
    )

    geometry.field.field_lines.add(
        name="RightTouchLine",
        p1=geometry_proto.Vector2f(
            x=FIELD_LENGTH / 2,
            y=-FIELD_WIDTH / 2,
        ),
        p2=geometry_proto.Vector2f(
            x=FIELD_LENGTH / 2,
            y=FIELD_WIDTH / 2,
        ),
        thickness=10.0,
    )

    geometry.field.field_arcs.add(
        name="CenterCircle",
        center=geometry_proto.Vector2f(x=0, y=0),
        radius=500.0,
        a1=0.0,
        a2=2 * math.pi,
        thickness=10.0,
        type=geometry_proto.SSL_FieldShapeType.CenterCircle,
    )

    return geometry

def send_detection(sock, frame):
    wrapper = wrapper_proto.SSL_WrapperPacket()
    wrapper.detection.CopyFrom(frame)

    data = wrapper.SerializeToString()
    sock.sendto(data, (MULTICAST_IP, PORT))

def send_geometry(sock):
    wrapper = wrapper_proto.SSL_WrapperPacket()
    wrapper.geometry.CopyFrom(build_geometry_data())

    data = wrapper.SerializeToString()
    sock.sendto(data, (MULTICAST_IP, PORT))

def main():
    sock = create_socket()

    print(f"SSL-Vision-Simulator gestartet")
    print(f"Ziel: udp://{MULTICAST_IP}:{PORT}")
    print("Abbruch mit STRG+C")

    start_time = time.monotonic()
    last_geometry_time = 0.0
    frame_number = 0
    i = 0

    try:
        while True:
            now = time.monotonic()
            t = now - start_time

            frame = build_detection_frame(t, frame_number)
            frame_number = (frame_number + 1) % (2**32)
            send_detection(sock, frame)

            # Geometrie gelegentlich erneut senden
            if now - last_geometry_time > 1.0:
                send_geometry(sock)
                last_geometry_time = now
                print("Pakete pro Sekunde: ", i)
                i=0

            # ungefähr 60 FPS
            time.sleep(1.0 / PACKETS_PER_SECOND)
            i+=1


    except KeyboardInterrupt:
        print("Simulator beendet.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()