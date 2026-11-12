import sys
import os
import socket
import time

from pynput import keyboard

sys.path.append(os.path.join(os.path.dirname(__file__), "protos"))

import grSim_Packet_pb2 as grSim_Packet


# --- Konfiguration ---
VM_IP = "192.168.0.115"
#VM_IP =  "192.168.42.41"
GRSIM_COMMAND_PORT = 20011

TEAM_GELB = True
ROBOTER_ID = 0

# Langsame Testwerte
V_LINEAR = 0.6   # m/s
V_DREHEN = 4.0      # rad/s
SEND_RATE = 0.02    # 50 Hz
# ---------------------


gedrueckte_tasten = set()
programm_laeuft = True


def sende_befehl(sock, vx, vy, vw):
    packet = grSim_Packet.grSim_Packet()

    packet.commands.isteamyellow = TEAM_GELB
    packet.commands.timestamp = time.time()

    robot_cmd = packet.commands.robot_commands.add()
    robot_cmd.id = ROBOTER_ID

    robot_cmd.veltangent = float(vx)
    robot_cmd.velnormal = float(vy)
    robot_cmd.velangular = float(vw)

    # Wichtig: kein Kick, kein Dribbler/Spinner
    robot_cmd.kickspeedx = 0.0
    robot_cmd.kickspeedz = 0.0
    robot_cmd.spinner = False
    robot_cmd.wheelsspeed = False

    sock.sendto(packet.SerializeToString(), (VM_IP, GRSIM_COMMAND_PORT))


def berechne_geschwindigkeit():
    vx = 0.0
    vy = 0.0
    vw = 0.0

    if "w" in gedrueckte_tasten:
        vx += V_LINEAR
    if "s" in gedrueckte_tasten:
        vx -= V_LINEAR

    if "a" in gedrueckte_tasten:
        vy += V_LINEAR
    if "d" in gedrueckte_tasten:
        vy -= V_LINEAR

    if "q" in gedrueckte_tasten:
        vw += V_DREHEN
    if "e" in gedrueckte_tasten:
        vw -= V_DREHEN

    if "space" in gedrueckte_tasten:
        return 0.0, 0.0, 0.0

    return vx, vy, vw


def stoppe_roboter(sock):
    # Mehrfach Stop senden, damit grSim sicher stoppt
    for _ in range(5):
        sende_befehl(sock, 0.0, 0.0, 0.0)
        time.sleep(0.01)


def taste_gedrueckt(key):
    global programm_laeuft

    try:
        gedrueckte_tasten.add(key.char.lower())
    except AttributeError:
        if key == keyboard.Key.space:
            gedrueckte_tasten.add("space")
        elif key == keyboard.Key.esc:
            programm_laeuft = False
            return False


def taste_losgelassen(key):
    try:
        gedrueckte_tasten.discard(key.char.lower())
    except AttributeError:
        if key == keyboard.Key.space:
            gedrueckte_tasten.discard("space")


def main():
    global programm_laeuft

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("✅ Roboter-Tastatursteuerung gestartet")
    print(f"Sende an: {VM_IP}:{GRSIM_COMMAND_PORT}")
    print(f"Team: {'Gelb' if TEAM_GELB else 'Blau'}")
    print(f"Roboter-ID: {ROBOTER_ID}")
    print()
    print("Steuerung:")
    print("  W = vorwärts")
    print("  S = rückwärts")
    print("  A = seitwärts links")
    print("  D = seitwärts rechts")
    print("  Q = links drehen")
    print("  E = rechts drehen")
    print("  SPACE = stoppen")
    print("  ESC = beenden")
    print()
    print("Hinweis: V_LINEAR ist absichtlich klein, damit der Ball nicht mitgeschoben wird.")
    print()

    listener = keyboard.Listener(
        on_press=taste_gedrueckt,
        on_release=taste_losgelassen
    )
    listener.start()

    try:
        while programm_laeuft:
            vx, vy, vw = berechne_geschwindigkeit()

            sende_befehl(sock, vx, vy, vw)

            print(
                f"Tasten={gedrueckte_tasten} | "
                f"vx={vx:5.2f} m/s, "
                f"vy={vy:5.2f} m/s, "
                f"vw={vw:5.2f} rad/s",
                end="\r"
            )

            time.sleep(SEND_RATE)

    except KeyboardInterrupt:
        pass

    finally:
        stoppe_roboter(sock)
        print("\nProgramm beendet. Roboter gestoppt.")


if __name__ == "__main__":
    main()