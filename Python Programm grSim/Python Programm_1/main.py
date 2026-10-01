import time
import math

from Kommunikation import KommunikationGrSim
from WeltModell import WeltModell


# --- Konfiguration ---
# grSim läuft auf demselben Rechner; für einen anderen Rechner dessen IP eintragen.
VM_IP = "127.0.0.1"
ROBOTER_ID = 1
TEAM_GELB = True


SCHLEIFENZEIT = 0.016  # ca. 60 Hz

# Reglerwerte
KP_LINEAR = 0.4
MAX_V_MMS = 500.0      # 500 mm/s = 0.5 m/s
ABSTAND_STOPP = 120.0  # mm
# ---------------------


def global_zu_lokal(vx_g, vy_g, phi):
    """
    Wandelt globale Feldgeschwindigkeit in lokale Roboter-Geschwindigkeit um.
    """
    vx_l = vx_g * math.cos(phi) + vy_g * math.sin(phi)
    vy_l = -vx_g * math.sin(phi) + vy_g * math.cos(phi)
    return vx_l, vy_l


def begrenze_geschwindigkeit(vx, vy, max_v):
    betrag = math.hypot(vx, vy)

    if betrag > max_v:
        faktor = max_v / betrag
        vx *= faktor
        vy *= faktor

    return vx, vy


def run_hauptprogramm():
    print("Test: Roboter fährt nur zur Ballposition.")

    kom = KommunikationGrSim(vm_ip=VM_IP)
    welt = WeltModell()

    letzte_debug_ausgabe = 0.0

    try:
        while True:
            start_zeit = time.time()

            # -----------------------------
            # 1. Vision-Daten empfangen
            # -----------------------------
            vision_paket = kom.empfange_paket()

            if vision_paket and vision_paket.HasField("detection"):
                det = vision_paket.detection

                # Ballposition speichern
                if len(det.balls) > 0:
                    ball = det.balls[0]
                    welt.ball.update_vision(ball.x, ball.y)

                # Roboterposition speichern
                roboter_liste = det.robots_yellow if TEAM_GELB else det.robots_blue

                for rob in roboter_liste:
                    if rob.robot_id == ROBOTER_ID:
                        welt.roboter_heim[ROBOTER_ID].update_vision(
                            rob.x,
                            rob.y,
                            rob.orientation
                        )

            roboter = welt.roboter_heim[ROBOTER_ID]
            ball = welt.ball

            vx_mms = 0.0
            vy_mms = 0.0
            vphi = 0.0

            # -----------------------------
            # 2. Nur zum Ball fahren
            # -----------------------------
            if ball.ist_aktiv and roboter.ist_aktiv:
                rob_pos = roboter.pose.position
                ball_pos = ball.pose.position
                phi = roboter.pose.orientierung

                dx = ball_pos.x - rob_pos.x
                dy = ball_pos.y - rob_pos.y

                abstand = math.hypot(dx, dy)

                if abstand > ABSTAND_STOPP:
                    # P-Regler im globalen Koordinatensystem
                    vx_global = dx * KP_LINEAR
                    vy_global = dy * KP_LINEAR

                    # Geschwindigkeit begrenzen
                    vx_global, vy_global = begrenze_geschwindigkeit(
                        vx_global,
                        vy_global,
                        MAX_V_MMS
                    )

                    # In lokale Roboterkoordinaten umrechnen
                    vx_mms, vy_mms = global_zu_lokal(
                        vx_global,
                        vy_global,
                        phi
                    )

                    # keine Drehung
                    vphi = 0.0
                else:
                    vx_mms = 0.0
                    vy_mms = 0.0
                    vphi = 0.0

            # -----------------------------
            # 3. Befehl senden
            # -----------------------------
            kom.sende_roboter_befehl(
                ROBOTER_ID,
                vx_mms / 1000.0,  # mm/s -> m/s
                vy_mms / 1000.0,
                vphi,
                team_gelb=TEAM_GELB
            )

            # -----------------------------
            # 4. Debug-Ausgabe
            # -----------------------------
            jetzt = time.time()
            if jetzt - letzte_debug_ausgabe >= 1.0:
                letzte_debug_ausgabe = jetzt

                print("\n--- Debug ---")
                print(f"Ball aktiv: {ball.ist_aktiv}")
                if ball.ist_aktiv:
                    print(
                        f"Ball: x={ball.pose.position.x:.1f}, "
                        f"y={ball.pose.position.y:.1f}"
                    )

                print(f"Roboter aktiv: {roboter.ist_aktiv}")
                if roboter.ist_aktiv:
                    print(
                        f"Roboter {ROBOTER_ID}: "
                        f"x={roboter.pose.position.x:.1f}, "
                        f"y={roboter.pose.position.y:.1f}, "
                        f"phi={roboter.pose.orientierung:.2f}"
                    )

                if ball.ist_aktiv and roboter.ist_aktiv:
                    print(f"Abstand zum Ball: {abstand:.1f} mm")

                print(
                    f"Befehl: vx={vx_mms / 1000.0:.2f} m/s, "
                    f"vy={vy_mms / 1000.0:.2f} m/s, "
                    f"vphi={vphi:.2f}"
                )

            # Timing
            verstrichene_zeit = time.time() - start_zeit
            time.sleep(max(0.0, SCHLEIFENZEIT - verstrichene_zeit))

    except KeyboardInterrupt:
        kom.sende_roboter_befehl(
            ROBOTER_ID,
            0.0,
            0.0,
            0.0,
            team_gelb=TEAM_GELB
        )
        print("\nProgramm beendet. Roboter gestoppt.")


if __name__ == "__main__":
    run_hauptprogramm()