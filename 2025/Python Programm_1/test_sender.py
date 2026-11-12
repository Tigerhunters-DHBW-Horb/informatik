# Datei: test_sender.py

import sys
import os
import socket
import time

# Fügt den 'protos'-Ordner zum Python-Suchpfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), "protos"))

import grSim_Packet_pb2 as grSim_Packet


# --- Konfiguration ---
#VM_IP = "192.168.0.104"       # IP deiner Linux-VM --> Zuhause
#VM_IP =  "192.168.42.41"        # IP deiner Linux-VM --> VM auf eigenn pc Hohenberg
VM_IP =  "192.168.95.255"       # IP deiner Linux-VM --> VM auf Ubuntu PC Hohenberg
GRSIM_COMMAND_PORT = 20011    # grSim Command-Port

TEAM_GELB = True              # True = Gelb, False = Blau
ROBOTER_ID = 0                # Roboter-ID in grSim
# ---------------------


def sende_befehl(sock, vx, vy, vw):
    packet = grSim_Packet.grSim_Packet()

    packet.commands.isteamyellow = TEAM_GELB
    packet.commands.timestamp = time.time()

    robot_cmd = packet.commands.robot_commands.add()
    robot_cmd.id = ROBOTER_ID

    # Geschwindigkeit
    robot_cmd.veltangent = vx
    robot_cmd.velnormal = vy
    robot_cmd.velangular = vw

    # Pflichtfelder
    robot_cmd.kickspeedx = 0.0
    robot_cmd.kickspeedz = 0.0
    robot_cmd.spinner = False
    robot_cmd.wheelsspeed = False

    data_to_send = packet.SerializeToString()
    sock.sendto(data_to_send, (VM_IP, GRSIM_COMMAND_PORT))


def waehle_modus():
    print("\nWas soll der Roboter machen?")
    print("1 = vorwärts fahren")
    print("2 = drehen")
    print("3 = seitwärts fahren")
    print("4 = stoppen")
    print("5 = rückwärts fahren")

    auswahl = input("Auswahl eingeben: ")

    if auswahl == "1":
        return "vorwaerts", 1.0, 0.0, 0.0

    elif auswahl == "2":
        return "drehen", 0.0, 0.0, 3.0

    elif auswahl == "3":
        return "seitwaerts", 0.0, 1.0, 0.0

    elif auswahl == "4":
        return "stoppen", 0.0, 0.0, 0.0

    elif auswahl == "5":
        return "rueckwaerts", -1.0, 0.0, 0.0

    else:
        print("Ungültige Eingabe. Roboter wird gestoppt.")
        return "stoppen", 0.0, 0.0, 0.0


def main_sender():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("✅ grSim Test-Sender läuft")
    print(f"Sende an: {VM_IP}:{GRSIM_COMMAND_PORT}")
    print(f"Team: {'Gelb' if TEAM_GELB else 'Blau'}")
    print(f"Roboter-ID: {ROBOTER_ID}")

    modus_name, vx, vy, vw = waehle_modus()

    print(f"\nModus gewählt: {modus_name}")
    print("Mit STRG+C stoppen.")

    try:
        while True:
            sende_befehl(sock, vx, vy, vw)
            print(f"Sende: {modus_name}  vx={vx}, vy={vy}, vw={vw}", end="\r")
            time.sleep(0.02)

    except KeyboardInterrupt:
        sende_befehl(sock, 0.0, 0.0, 0.0)
        print("\nSender gestoppt. Roboter angehalten.")


if __name__ == "__main__":
    main_sender()