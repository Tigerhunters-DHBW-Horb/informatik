import os
import math
import socket
import statistics
import struct
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle
from google.protobuf.message import DecodeError


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import ssl_vision_wrapper_pb2 as SSL_WrapperPacket


# --- Konfiguration ---
VISION_MULTICAST_IP = "224.5.23.2"
VISION_PORT = 10006
ROBOTER_ID = 0
TEAM_GELB = False

ANZEIGE_DAUER = 60.0  # Sekunden Zeitverlauf im Diagramm
AKTUALISIERUNG_MS = 50
# ---------------------


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
    sock.setblocking(False)
    return sock


def berechne_kennwerte(messwerte):
    if not messwerte:
        return "Noch keine Messwerte"

    zeiten = [messwert[0] for messwert in messwerte]
    x_werte = [messwert[1] for messwert in messwerte]
    y_werte = [messwert[2] for messwert in messwerte]
    winkel = [messwert[3] for messwert in messwerte if math.isfinite(messwert[3])]
    konfidenzen = [messwert[4] for messwert in messwerte]

    if len(messwerte) > 1:
        x_mittel = statistics.fmean(x_werte)
        y_mittel = statistics.fmean(y_werte)
        x_std = statistics.stdev(x_werte)
        y_std = statistics.stdev(y_werte)
        radial_rms = math.sqrt(
            statistics.fmean(
                (x - x_mittel) ** 2 + (y - y_mittel) ** 2
                for x, y in zip(x_werte, y_werte)
            )
        )
        max_abstand = max(
            math.hypot(x - x_mittel, y - y_mittel)
            for x, y in zip(x_werte, y_werte)
        )
        intervalle = [
            spaetere - fruehere for fruehere, spaetere in zip(zeiten, zeiten[1:])
        ]
        rate = (
            (len(zeiten) - 1) / (zeiten[-1] - zeiten[0])
            if zeiten[-1] > zeiten[0]
            else 0.0
        )
        jitter_text = (
            f"{statistics.stdev(intervalle) * 1000:.2f} ms"
            if len(intervalle) > 1
            else "n/a"
        )
        konfidenz_std = statistics.stdev(konfidenzen)
        position_text = (
            f"X: {x_mittel:.1f} +/- {x_std:.1f} mm   "
            f"Y: {y_mittel:.1f} +/- {y_std:.1f} mm"
        )
        streuung_text = (
            f"2D RMS: {radial_rms:.1f} mm   Max. Abstand zum Mittel: "
            f"{max_abstand:.1f} mm"
        )
        empfang_text = f"Rate: {rate:.1f} Hz   Zeit-Jitter: {jitter_text}"
        konfidenz_text = (
            f"SSL-Konfidenz: {statistics.fmean(konfidenzen):.3f} "
            f"+/- {konfidenz_std:.3f}"
        )
    else:
        position_text = f"X: {x_werte[0]:.1f} mm   Y: {y_werte[0]:.1f} mm"
        streuung_text = "Streuung: mindestens 2 Messwerte erforderlich"
        empfang_text = "Rate: wird berechnet, sobald weitere Messwerte eintreffen"
        konfidenz_text = f"SSL-Konfidenz: {konfidenzen[0]:.3f}"

    if len(winkel) > 1:
        sin_mittel = statistics.fmean(math.sin(wert) for wert in winkel)
        cos_mittel = statistics.fmean(math.cos(wert) for wert in winkel)
        resultant = min(1.0, math.hypot(sin_mittel, cos_mittel))
        winkel_mittel = math.degrees(math.atan2(sin_mittel, cos_mittel))
        winkel_std = (
            math.degrees(math.sqrt(-2.0 * math.log(resultant)))
            if resultant > 0
            else float("inf")
        )
        rotation_text = (
            f"Rotation: {winkel_mittel:.1f} +/- {winkel_std:.1f} Grad "
            "(Kreis-Std.)"
        )
    elif winkel:
        rotation_text = f"Rotation: {math.degrees(winkel[0]):.1f} Grad"
    else:
        rotation_text = "Rotation: keine Messwerte"

    return (
        f"Letzte {zeiten[-1] - zeiten[0]:.1f} s | {len(messwerte)} Messungen\n"
        f"{position_text}\n"
        f"{streuung_text}\n"
        f"{rotation_text}\n"
        f"{empfang_text}\n"
        f"{konfidenz_text}\n"
        "Hinweis: Streuung enthaelt auch Roboterbewegung; sie ist keine absolute Genauigkeit."
    )


def erstelle_dashboard():
    team_name = "Gelb" if TEAM_GELB else "Blau"
    team_farbe = "#f2c94c" if TEAM_GELB else "#4c8bf5"
    robot_feld = "robots_yellow" if TEAM_GELB else "robots_blue"

    sock = erstelle_empfaenger()
    startzeit = time.monotonic()
    historie = deque()
    letzter_empfang = None
    feld_laenge, feld_breite = 12000, 9000

    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    fig.suptitle(
        f"SSL-Vision Live-Dashboard — {team_name}er Roboter {ROBOTER_ID}",
        fontsize=15,
        fontweight="bold",
    )
    layout = fig.add_gridspec(
        4,
        2,
        width_ratios=(1.25, 1),
        height_ratios=(1, 1, 1, 1.1),
    )
    ax_feld = fig.add_subplot(layout[:, 0])
    ax_x = fig.add_subplot(layout[0, 1])
    ax_y = fig.add_subplot(layout[1, 1], sharex=ax_x)
    ax_phi = fig.add_subplot(layout[2, 1], sharex=ax_x)
    ax_kennwerte = fig.add_subplot(layout[3, 1])
    ax_kennwerte.axis("off")
    ax_kennwerte.set_title("Kennwerte (rollierende 60 s)", loc="left")
    kennwerte_text = ax_kennwerte.text(
        0,
        0.92,
        "Warte auf Messwerte...",
        transform=ax_kennwerte.transAxes,
        va="top",
        family="monospace",
        fontsize=9,
    )
    diagramme = (
        (ax_x, "X-Position (mm)", "#2d9cdb"),
        (ax_y, "Y-Position (mm)", "#27ae60"),
        (ax_phi, "Rotation (Grad)", "#9b51e0"),
    )

    for ax, label, farbe in diagramme:
        ax.set_ylabel(label, color=farbe)
        ax.grid(True, alpha=0.25)
        ax.tick_params(axis="y", labelcolor=farbe)
    ax_phi.set_xlabel("Zeit seit Programmstart (s)")

    linie_x, = ax_x.plot([], [], color="#2d9cdb", linewidth=1.5)
    linie_y, = ax_y.plot([], [], color="#27ae60", linewidth=1.5)
    linie_phi, = ax_phi.plot([], [], color="#9b51e0", linewidth=1.5)
    linien = (linie_x, linie_y, linie_phi)

    ax_feld.set_title("Position und Ausrichtung auf dem Spielfeld")
    ax_feld.set_xlabel("X (mm)")
    ax_feld.set_ylabel("Y (mm)")
    ax_feld.set_aspect("equal", adjustable="box")
    ax_feld.grid(True, alpha=0.15)

    feld = Rectangle(
        (-feld_laenge / 2, -feld_breite / 2),
        feld_laenge,
        feld_breite,
        facecolor="#176b45",
        edgecolor="white",
        linewidth=2,
    )
    ax_feld.add_patch(feld)
    ax_feld.plot(
        [0, 0],
        [-feld_breite / 2, feld_breite / 2],
        color="white",
        linewidth=1,
    )
    kreis = Circle((0, 0), radius=500, fill=False, edgecolor="white", linewidth=1)
    ax_feld.add_patch(kreis)
    roboter_punkt = Circle(
        (0, 0), radius=100, facecolor=team_farbe, edgecolor="black", zorder=4
    )
    ax_feld.add_patch(roboter_punkt)
    richtung, = ax_feld.plot([], [], color="white", linewidth=3, zorder=5)
    id_text = ax_feld.text(0, 0, "", ha="center", va="center", zorder=6)
    status_text = ax_feld.text(
        0.02,
        0.98,
        "Warte auf SSL-Vision-Daten...",
        transform=ax_feld.transAxes,
        va="top",
        color="white",
        bbox={"facecolor": "black", "alpha": 0.55, "pad": 5},
    )

    def update(_frame):
        nonlocal letzter_empfang, feld_laenge, feld_breite
        packets = 0
        while packets < 500:
            try:
                data, _addr = sock.recvfrom(65536)
            except BlockingIOError:
                break
            packets += 1

            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            try:
                packet.ParseFromString(data)
            except DecodeError as exc:
                print(f"Ungueltiges SSL-Vision-Protobuf-Paket ignoriert: {exc}")
                continue

            if packet.HasField("geometry"):
                feld_info = packet.geometry.field
                feld_laenge = feld_info.field_length
                feld_breite = feld_info.field_width
                feld.set_bounds(
                    -feld_laenge / 2,
                    -feld_breite / 2,
                    feld_laenge,
                    feld_breite,
                )
                kreis.set_radius(min(feld_laenge, feld_breite) / 9)
                ax_feld.set_xlim(-feld_laenge / 2 - 300, feld_laenge / 2 + 300)
                ax_feld.set_ylim(-feld_breite / 2 - 300, feld_breite / 2 + 300)

            if not packet.HasField("detection"):
                continue

            detection = packet.detection
            for robot in getattr(detection, robot_feld):
                if not robot.HasField("robot_id") or robot.robot_id != ROBOTER_ID:
                    continue

                elapsed = time.monotonic() - startzeit
                phi = (
                    robot.orientation
                    if robot.HasField("orientation")
                    else float("nan")
                )
                historie.append(
                    (elapsed, robot.x, robot.y, phi, robot.confidence)
                )
                letzter_empfang = elapsed
                break

        jetzt = time.monotonic() - startzeit
        while historie and jetzt - historie[0][0] > ANZEIGE_DAUER:
            historie.popleft()

        if historie:
            _, x, y, phi, _konfidenz = historie[-1]
            roboter_punkt.center = (x, y)
            id_text.set_position((x, y))
            id_text.set_text(str(ROBOTER_ID))

            if math.isfinite(phi):
                pfeil_laenge = min(feld_laenge, feld_breite) * 0.055
                richtung.set_data(
                    [x, x + pfeil_laenge * math.cos(phi)],
                    [y, y + pfeil_laenge * math.sin(phi)],
                )
                rotation_text = f"{math.degrees(phi):.1f}°"
            else:
                richtung.set_data([], [])
                rotation_text = "nicht verfuegbar"

            alter = jetzt - letzter_empfang if letzter_empfang is not None else 0
            status = "LIVE" if alter < 1.0 else f"KEIN NEUES SIGNAL ({alter:.1f} s)"
            status_text.set_text(
                f"{status}\nX: {x:.0f} mm   Y: {y:.0f} mm\n"
                f"Rotation: {rotation_text}"
            )

            werte = list(historie)
            zeiten = [wert[0] for wert in werte]
            linien[0].set_data(zeiten, [wert[1] for wert in werte])
            linien[1].set_data(zeiten, [wert[2] for wert in werte])
            linien[2].set_data(
                zeiten,
                [
                    math.degrees(wert[3])
                    if math.isfinite(wert[3])
                    else float("nan")
                    for wert in werte
                ],
            )
            kennwerte_text.set_text(berechne_kennwerte(werte))
            for ax in (ax_x, ax_y, ax_phi):
                ax.relim()
                ax.autoscale_view(scalex=False, scaley=True)
        elif letzter_empfang is None:
            status_text.set_text(
                f"Warte auf Roboter {ROBOTER_ID} ({team_name}) "
                f"auf {VISION_MULTICAST_IP}:{VISION_PORT}..."
            )

        linke_grenze = max(0.0, jetzt - ANZEIGE_DAUER)
        rechte_grenze = max(ANZEIGE_DAUER, jetzt)
        ax_phi.set_xlim(linke_grenze, rechte_grenze)
        return (
            *linien,
            roboter_punkt,
            richtung,
            id_text,
            status_text,
            kennwerte_text,
        )

    def beim_schliessen(_event):
        sock.close()

    fig.canvas.mpl_connect("close_event", beim_schliessen)
    animation = FuncAnimation(
        fig, update, interval=AKTUALISIERUNG_MS, blit=False, cache_frame_data=False
    )
    return fig, animation, sock.close


def main():
    fig = None
    schliesse_empfaenger = None
    try:
        fig, _animation, schliesse_empfaenger = erstelle_dashboard()
        print(
            f"SSL-Vision-Dashboard lauscht auf "
            f"{VISION_MULTICAST_IP}:{VISION_PORT}."
        )
        plt.show()
    except KeyboardInterrupt:
        print("\nDashboard wird beendet.")
    except OSError as exc:
        raise SystemExit(f"Dashboard konnte nicht gestartet werden: {exc}") from exc
    finally:
        if fig is not None:
            plt.close(fig)
        if schliesse_empfaenger is not None:
            schliesse_empfaenger()


if __name__ == "__main__":
    main()
