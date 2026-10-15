import time
import math
import sys
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.widgets import Button

from Kommunikation import KommunikationGrSim
from WeltModell import WeltModell


# --- Konfiguration ---
# grSim läuft auf demselben Rechner; für einen anderen Rechner dessen IP eintragen.
VM_IP = "127.0.0.1"
ROBOTER_ID = 0
TEAM_GELB = False   
VISION_MULTICAST_IP = "224.5.23.2"
VISION_PORT = 10006


SCHLEIFENZEIT = 0.05  # 
VISION_TIMEOUT = 0.5   # Sekunden ohne frische Vision-Daten: Roboter stoppen

# Reglerwerte
KP_LINEAR = 0.4
MAX_V_MMS = 500.0      # 500 mm/s = 0.5 m/s
ABSTAND_STOPP = 120.0  # mm
ANZEIGE_DAUER = 10.0   # Sekunden Historie in den Zeitdiagrammen
ANZEIGE_HZ = 10.0      # Grafiken mit maximal 10 Hz aktualisieren
# ---------------------


def clear_terminal():
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="", flush=True)


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


class LiveVisualisierung:
    def __init__(self):
        self.startzeit = time.monotonic()
        self.naechstes_update = 0.0
        self.kompaktansicht = False
        self.robot_daten = deque()
        self.ball_daten = deque()

        self.fig, axes = plt.subplots(2, 2, figsize=(13, 8))
        self.fig.canvas.manager.set_window_title("SSL-Vision und Robotersteuerung")
        self.fig.suptitle("SSL-Vision: Rohdaten, Kalman-Filter und Fahrbefehl")
        self.ax_x, self.ax_y, self.ax_phi, self.ax_feld = axes.flat

        self.robot_x_roh, = self.ax_x.plot([], [], ".", color="tab:blue", alpha=0.45,
                                          label="Roboter SSL-Vision")
        self.robot_x_filter, = self.ax_x.plot([], [], "-", color="tab:blue",
                                              label="Roboter Kalman")
        self.ball_x_roh, = self.ax_x.plot([], [], ".", color="tab:orange", alpha=0.45,
                                          label="Ball SSL-Vision")
        self.ball_x_filter, = self.ax_x.plot([], [], "-", color="tab:orange",
                                             label="Ball Kalman")

        self.robot_y_roh, = self.ax_y.plot([], [], ".", color="tab:blue", alpha=0.45,
                                          label="Roboter SSL-Vision")
        self.robot_y_filter, = self.ax_y.plot([], [], "-", color="tab:blue",
                                              label="Roboter Kalman")
        self.ball_y_roh, = self.ax_y.plot([], [], ".", color="tab:orange", alpha=0.45,
                                          label="Ball SSL-Vision")
        self.ball_y_filter, = self.ax_y.plot([], [], "-", color="tab:orange",
                                             label="Ball Kalman")

        self.phi_roh, = self.ax_phi.plot([], [], ".", color="tab:purple", alpha=0.45,
                                        label="SSL-Vision")
        self.phi_filter, = self.ax_phi.plot([], [], "-", color="tab:purple",
                                            label="Kalman")

        for axis, title, ylabel in (
            (self.ax_x, "X-Position", "X [mm]"),
            (self.ax_y, "Y-Position", "Y [mm]"),
            (self.ax_phi, "Roboter-Ausrichtung", "Winkel [Grad]"),
        ):
            axis.set_title(title)
            axis.set_xlabel("Zeit [s]")
            axis.set_ylabel(ylabel)
            axis.grid(True, alpha=0.3)
            axis.legend(loc="upper left", fontsize="small")

        self.ax_feld.set_title("Spielfeld und aktueller Fahrbefehl")
        self.ax_feld.set_xlabel("X [mm]")
        self.ax_feld.set_ylabel("Y [mm]")
        self.ax_feld.set_aspect("equal", adjustable="box")
        self.ax_feld.set_xlim(-1600, 1600)
        self.ax_feld.set_ylim(-1050, 1050)
        self.ax_feld.add_patch(Rectangle((-1600, -1050), 3200, 2100,
                                         fill=False, color="black", linewidth=1))
        self.ax_feld.plot([0, 0], [-1050, 1050], color="gray", linewidth=0.7)
        self.ax_feld.add_patch(Circle((0, 0), 500, fill=False,
                                      color="gray", linewidth=0.7))
        self.ax_feld.grid(True, alpha=0.2)
        self.feld_status = self.ax_feld.text(
            0.02, 0.02, "Warte auf Vision-Daten",
            transform=self.ax_feld.transAxes, va="bottom"
        )
        self.roboter_marker, = self.ax_feld.plot([], [], "o", color="tab:blue",
                                                markersize=9, label="Roboter (gefiltert)")
        self.ball_roh_marker, = self.ax_feld.plot([], [], "x", color="tab:orange",
                                                 markersize=8, label="Ball (SSL-Vision)")
        self.ball_filter_marker, = self.ax_feld.plot([], [], "o", color="tab:orange",
                                                    markersize=5, label="Ball (Kalman)")
        self.roboter_heading = None
        self.fahrbefehl_pfeil = None
        self.ax_feld.legend(loc="upper left", fontsize="small")
        self.fig.tight_layout(rect=(0, 0.02, 1, 0.90))
        self.ax_start = self.fig.add_axes([0.84, 0.92, 0.12, 0.05])
        self.start_knopf = Button(self.ax_start, "Start")
        self.start_knopf.on_clicked(self._zeige_feldansicht)
        plt.show(block=False)

    def _zeige_feldansicht(self, _event):
        self.kompaktansicht = True
        for axis in (self.ax_x, self.ax_y, self.ax_phi):
            axis.set_visible(False)

        self.ax_feld.set_position([0.04, 0.10, 0.92, 0.80])
        self.ax_feld.set_title("Roboterposition, Ausrichtung und Geschwindigkeit")
        self.fig.suptitle("Roboter live verfolgen")
        self.ax_feld.get_legend().remove()
        self.ball_roh_marker.set_data([], [])
        self.ball_filter_marker.set_data([], [])
        self.start_knopf.label.set_text("Feldansicht aktiv")
        self.start_knopf.set_active(False)
        self.fig.canvas.draw_idle()

    def add_robot_measurement(self, timestamp, raw, filtered):
        if not self.kompaktansicht:
            self.robot_daten.append((timestamp, *raw, *filtered))

    def add_ball_measurement(self, timestamp, raw, filtered):
        if not self.kompaktansicht:
            self.ball_daten.append((timestamp, *raw, *filtered))

    @staticmethod
    def _update_time_lines(lines, samples, x_index, filtered_index, start):
        if samples:
            times = [sample[0] - start for sample in samples]
            lines[0].set_data(times, [sample[x_index] for sample in samples])
            lines[1].set_data(times, [sample[filtered_index] for sample in samples])

    def update(self, now, robot, ball, raw_ball, command_x, command_y, vx, vy, vphi):
        if not plt.fignum_exists(self.fig.number):
            return False
        if now < self.naechstes_update:
            return True
        self.naechstes_update = now + 1.0 / ANZEIGE_HZ
        if not self.kompaktansicht:
            cutoff_time = now - ANZEIGE_DAUER
            while self.robot_daten and self.robot_daten[0][0] < cutoff_time:
                self.robot_daten.popleft()
            while self.ball_daten and self.ball_daten[0][0] < cutoff_time:
                self.ball_daten.popleft()

            self._update_time_lines(
                (self.robot_x_roh, self.robot_x_filter), self.robot_daten, 1, 4,
                self.startzeit
            )
            self._update_time_lines(
                (self.ball_x_roh, self.ball_x_filter), self.ball_daten, 1, 3,
                self.startzeit
            )
            self._update_time_lines(
                (self.robot_y_roh, self.robot_y_filter), self.robot_daten, 2, 5,
                self.startzeit
            )
            self._update_time_lines(
                (self.ball_y_roh, self.ball_y_filter), self.ball_daten, 2, 4,
                self.startzeit
            )

            if self.robot_daten:
                times = [sample[0] - self.startzeit for sample in self.robot_daten]
                self.phi_roh.set_data(
                    times,
                    [math.degrees(sample[3]) for sample in self.robot_daten]
                )
                self.phi_filter.set_data(
                    times,
                    [math.degrees(sample[6]) for sample in self.robot_daten]
                )

            cutoff = now - self.startzeit - ANZEIGE_DAUER
            for axis in (self.ax_x, self.ax_y, self.ax_phi):
                axis.set_xlim(
                    max(0.0, cutoff),
                    max(ANZEIGE_DAUER, now - self.startzeit)
                )
                axis.relim()
                axis.autoscale_view(scalex=False, scaley=True)

        if robot is not None:
            rx, ry, heading = robot
            self.roboter_marker.set_data([rx], [ry])
            if self.roboter_heading is not None:
                self.roboter_heading.remove()
            self.roboter_heading = self.ax_feld.annotate(
                "", xy=(rx + 180 * math.cos(heading), ry + 180 * math.sin(heading)),
                xytext=(rx, ry),
                arrowprops={"arrowstyle": "->", "color": "tab:blue", "lw": 2}
            )
            if self.fahrbefehl_pfeil is not None:
                self.fahrbefehl_pfeil.remove()
            speed = math.hypot(command_x, command_y)
            if speed > 0:
                arrow_length = 1200.0 * min(speed / MAX_V_MMS, 1.0)
                self.fahrbefehl_pfeil = self.ax_feld.annotate(
                    "", xy=(rx + arrow_length * command_x / speed,
                            ry + arrow_length * command_y / speed),
                    xytext=(rx, ry),
                    arrowprops={"arrowstyle": "-|>", "color": "tab:green", "lw": 2}
                )
            self.feld_status.set_text(
                f"Roboter {ROBOTER_ID} | Position: ({rx:.0f}, {ry:.0f}) mm\n"
                f"Ausrichtung (blau): {math.degrees(heading):.0f}° | "
                f"Geschwindigkeit (grün): {speed:.0f} mm/s "
                f"({speed / 1000:.2f} m/s), "
                f"Richtung {math.degrees(math.atan2(command_y, command_x)):.0f}°"
            )
        if not self.kompaktansicht and raw_ball is not None:
            self.ball_roh_marker.set_data([raw_ball[0]], [raw_ball[1]])
        if not self.kompaktansicht and ball is not None:
            self.ball_filter_marker.set_data([ball[0]], [ball[1]])

        self.fig.canvas.draw_idle()
        plt.pause(0.001)
        return plt.fignum_exists(self.fig.number)


def run_hauptprogramm():
    clear_terminal()
    print("Test: Roboter fährt nur zur Ballposition.")

    kom = KommunikationGrSim(
        vm_ip=VM_IP,
        vision_port=VISION_PORT,
        vision_multicast_ip=VISION_MULTICAST_IP
    )
    welt = WeltModell()
    visualisierung = LiveVisualisierung()

    letzte_debug_ausgabe = 0.0
    letzte_ball_zeit = None
    letzter_roboter_zeit = None
    letzter_ball_roh = None
    letzter_command_global = (0.0, 0.0)

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
                    letzte_ball_zeit = time.monotonic()
                    letzter_ball_roh = (ball.x, ball.y)
                    visualisierung.add_ball_measurement(
                        letzte_ball_zeit,
                        letzter_ball_roh,
                        (welt.ball.pose.position.x, welt.ball.pose.position.y)
                    )

                # Roboterposition speichern
                roboter_liste = det.robots_yellow if TEAM_GELB else det.robots_blue

                for rob in roboter_liste:
                    if rob.robot_id == ROBOTER_ID:
                        welt.roboter_heim[ROBOTER_ID].update_vision(
                            rob.x,
                            rob.y,
                            rob.orientation
                        )
                        letzter_roboter_zeit = time.monotonic()
                        visualisierung.add_robot_measurement(
                            letzter_roboter_zeit,
                            (rob.x, rob.y, rob.orientation),
                            (
                                welt.roboter_heim[ROBOTER_ID].pose.position.x,
                                welt.roboter_heim[ROBOTER_ID].pose.position.y,
                                welt.roboter_heim[ROBOTER_ID].pose.orientierung
                            )
                        )

            roboter = welt.roboter_heim[ROBOTER_ID]
            ball = welt.ball
            jetzt_monoton = time.monotonic()
            ball_frisch = (
                letzte_ball_zeit is not None
                and jetzt_monoton - letzte_ball_zeit <= VISION_TIMEOUT
            )
            roboter_frisch = (
                letzter_roboter_zeit is not None
                and jetzt_monoton - letzter_roboter_zeit <= VISION_TIMEOUT
            )

            vx_mms = 0.0
            vy_mms = 0.0
            vphi = 0.0
            letzter_command_global = (0.0, 0.0)

            # -----------------------------
            # 2. Nur zum Ball fahren
            # -----------------------------
            if ball.ist_aktiv and roboter.ist_aktiv and ball_frisch and roboter_frisch:
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
                    letzter_command_global = (vx_global, vy_global)

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

            filtered_robot = None
            if roboter.ist_aktiv:
                filtered_robot = (
                    roboter.pose.position.x,
                    roboter.pose.position.y,
                    roboter.pose.orientierung
                )
            filtered_ball = None
            if ball.ist_aktiv:
                filtered_ball = (ball.pose.position.x, ball.pose.position.y)
            if not visualisierung.update(
                time.monotonic(),
                filtered_robot,
                filtered_ball,
                letzter_ball_roh,
                *letzter_command_global,
                vx_mms,
                vy_mms,
                vphi
            ):
                break

            # -----------------------------
            # 4. Debug-Ausgabe
            # -----------------------------
            jetzt = time.time()
            if jetzt - letzte_debug_ausgabe >= 1.0:
                letzte_debug_ausgabe = jetzt

                clear_terminal()
                print("\n--- Debug ---")
                print(f"Ball aktiv: {ball.ist_aktiv}")
                print(f"Ballmessung aktuell: {ball_frisch}")
                if ball.ist_aktiv:
                    print(
                        f"Ball: x={ball.pose.position.x:.1f}, "
                        f"y={ball.pose.position.y:.1f}"
                    )

                print(f"Roboter aktiv: {roboter.ist_aktiv}")
                print(f"Robotermessung aktuell: {roboter_frisch}")
                if roboter.ist_aktiv:
                    print(
                        f"Roboter {ROBOTER_ID}: "
                        f"x={roboter.pose.position.x:.1f}, "
                        f"y={roboter.pose.position.y:.1f}, "
                        f"phi={roboter.pose.orientierung:.2f}"
                    )

                if (
                    ball.ist_aktiv
                    and roboter.ist_aktiv
                    and ball_frisch
                    and roboter_frisch
                ):
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
        print("\nProgramm wird beendet.")
    finally:
        kom.sende_roboter_befehl(
            ROBOTER_ID,
            0.0,
            0.0,
            0.0,
            team_gelb=TEAM_GELB
        )
        kom.recv_sock.close()
        kom.send_sock.close()
        plt.close("all")
        print("Programm beendet. Roboter gestoppt.")


if __name__ == "__main__":
    run_hauptprogramm()