import csv
import datetime
import os
import math
import re
import socket
import statistics
import struct
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle
from matplotlib.widgets import Button, TextBox
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
MESSUNGS_ORDNER = "Messungen"
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


def berechne_statistik(messwerte):
    if not messwerte:
        return {}

    zeiten = [messwert[0] for messwert in messwerte]
    x_werte = [messwert[1] for messwert in messwerte]
    y_werte = [messwert[2] for messwert in messwerte]
    winkel = [messwert[3] for messwert in messwerte if math.isfinite(messwert[3])]
    konfidenzen = [messwert[4] for messwert in messwerte]

    werte = {
        "sample_count": len(messwerte),
        "duration_s": zeiten[-1] - zeiten[0],
        "x_mean_mm": statistics.fmean(x_werte),
        "y_mean_mm": statistics.fmean(y_werte),
        "confidence_mean": statistics.fmean(konfidenzen),
    }

    if len(messwerte) > 1:
        x_mittel = werte["x_mean_mm"]
        y_mittel = werte["y_mean_mm"]
        werte["x_std_mm"] = statistics.stdev(x_werte)
        werte["y_std_mm"] = statistics.stdev(y_werte)
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
        werte.update(
            {
                "position_rms_2d_mm": radial_rms,
                "max_distance_mm": max_abstand,
                "rate_hz": rate,
                "interval_jitter_ms": (
                    statistics.stdev(intervalle) * 1000
                    if len(intervalle) > 1
                    else None
                ),
                "confidence_std": statistics.stdev(konfidenzen),
            }
        )

    if len(winkel) > 1:
        sin_mittel = statistics.fmean(math.sin(wert) for wert in winkel)
        cos_mittel = statistics.fmean(math.cos(wert) for wert in winkel)
        resultant = min(1.0, math.hypot(sin_mittel, cos_mittel))
        werte["orientation_mean_deg"] = math.degrees(
            math.atan2(sin_mittel, cos_mittel)
        )
        werte["orientation_circular_std_deg"] = (
            math.degrees(math.sqrt(-2.0 * math.log(resultant)))
            if resultant > 0
            else float("inf")
        )
    elif winkel:
        werte["orientation_mean_deg"] = math.degrees(winkel[0])
        werte["orientation_circular_std_deg"] = None

    return werte


def berechne_kennwerte(messwerte):
    if not messwerte:
        return "Noch keine Messwerte"

    werte = berechne_statistik(messwerte)
    x_mittel = werte["x_mean_mm"]
    y_mittel = werte["y_mean_mm"]
    zeiten = [messwert[0] for messwert in messwerte]

    if len(messwerte) > 1:
        x_std = werte["x_std_mm"]
        y_std = werte["y_std_mm"]
        position_text = (
            f"X: {x_mittel:.1f} +/- {x_std:.1f} mm   "
            f"Y: {y_mittel:.1f} +/- {y_std:.1f} mm"
        )
        streuung_text = (
            f"2D RMS: {werte['position_rms_2d_mm']:.1f} mm   "
            f"Max. Abstand zum Mittel: {werte['max_distance_mm']:.1f} mm"
        )
        empfang_text = (
            f"Rate: {werte['rate_hz']:.1f} Hz   "
            f"Zeit-Jitter: "
            f"{werte['interval_jitter_ms']:.2f} ms"
            if werte["interval_jitter_ms"] is not None
            else f"Rate: {werte['rate_hz']:.1f} Hz   Zeit-Jitter: n/a"
        )
        konfidenz_text = (
            f"SSL-Konfidenz: {werte['confidence_mean']:.3f} "
            f"+/- {werte['confidence_std']:.3f}"
        )
    else:
        position_text = f"X: {x_mittel:.1f} mm   Y: {y_mittel:.1f} mm"
        streuung_text = "Streuung: mindestens 2 Messwerte erforderlich"
        empfang_text = "Rate: wird berechnet, sobald weitere Messwerte eintreffen"
        konfidenz_text = f"SSL-Konfidenz: {werte['confidence_mean']:.3f}"

    if werte.get("orientation_circular_std_deg") is not None:
        rotation_text = (
            f"Rotation: {werte['orientation_mean_deg']:.1f} +/- "
            f"{werte['orientation_circular_std_deg']:.1f} Grad "
            "(Kreis-Std.)"
        )
    elif werte.get("orientation_mean_deg") is not None:
        rotation_text = f"Rotation: {werte['orientation_mean_deg']:.1f} Grad"
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


def speichere_messung(
    dateipfad, rohe_messungen, statistiken, messdauer_s, aufloesung_hz
):
    team = "gelb" if TEAM_GELB else "blau"

    with open(dateipfad, "w", newline="", encoding="utf-8-sig") as datei:
        writer = csv.writer(datei, delimiter=";")
        writer.writerow(["Einzelmessungen"])
        writer.writerow(
            [
                "Messung",
                "Zeitpunkt",
                "Zeit seit Messbeginn (s)",
                "Roboter-ID",
                "Team",
                "X (mm)",
                "Y (mm)",
                "Rotation (rad)",
                "Rotation (Grad)",
                "SSL-Konfidenz",
                "Aufloesung (Hz)",
            ]
        )
        for messnummer, messung in enumerate(rohe_messungen, start=1):
            elapsed, zeitpunkt, x, y, phi, konfidenz = messung
            writer.writerow(
                [
                    messnummer,
                    zeitpunkt,
                    f"{elapsed:.6f}",
                    ROBOTER_ID,
                    team,
                    f"{x:.3f}",
                    f"{y:.3f}",
                    f"{phi:.6f}" if math.isfinite(phi) else "",
                    f"{math.degrees(phi):.3f}" if math.isfinite(phi) else "",
                    f"{konfidenz:.6f}",
                    f"{aufloesung_hz:.3f}",
                ]
            )

        writer.writerow([])
        writer.writerow(["Kennwerte der gesamten Messung"])
        writer.writerow(["Kennwert", "Wert", "Einheit"])
        zusammenfassung = [
            ("Roboter-ID", ROBOTER_ID, ""),
            ("Team", team, ""),
            ("Vorgegebene Messdauer", messdauer_s, "s"),
            ("Ziel-Aufloesung", aufloesung_hz, "Hz"),
            ("Anzahl Messwerte", statistiken.get("sample_count"), ""),
            ("Messwertzeitraum", statistiken.get("duration_s"), "s"),
            ("X-Mittelwert", statistiken.get("x_mean_mm"), "mm"),
            ("X-Standardabweichung", statistiken.get("x_std_mm"), "mm"),
            ("Y-Mittelwert", statistiken.get("y_mean_mm"), "mm"),
            ("Y-Standardabweichung", statistiken.get("y_std_mm"), "mm"),
            ("Positionsstreuung 2D RMS", statistiken.get("position_rms_2d_mm"), "mm"),
            ("Maximaler Abstand zum Mittel", statistiken.get("max_distance_mm"), "mm"),
            ("Rotationsmittelwert", statistiken.get("orientation_mean_deg"), "Grad"),
            (
                "Rotations-Standardabweichung (kreisfoermig)",
                statistiken.get("orientation_circular_std_deg"),
                "Grad",
            ),
            ("Empfangsrate", statistiken.get("rate_hz"), "Hz"),
            ("Zeit-Jitter", statistiken.get("interval_jitter_ms"), "ms"),
            ("SSL-Konfidenz Mittelwert", statistiken.get("confidence_mean"), ""),
            (
                "SSL-Konfidenz Standardabweichung",
                statistiken.get("confidence_std"),
                "",
            ),
        ]
        for name, wert, einheit in zusammenfassung:
            if isinstance(wert, float):
                wert = f"{wert:.6f}"
            writer.writerow([name, "" if wert is None else wert, einheit])


def erstelle_dashboard():
    team_name = "Gelb" if TEAM_GELB else "Blau"
    team_farbe = "#f2c94c" if TEAM_GELB else "#4c8bf5"
    robot_feld = "robots_yellow" if TEAM_GELB else "robots_blue"

    sock = erstelle_empfaenger()
    startzeit = time.monotonic()
    historie = deque()
    letzter_empfang = None
    feld_laenge, feld_breite = 12000, 9000

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"SSL-Vision Live-Dashboard — {team_name}er Roboter {ROBOTER_ID}",
        fontsize=15,
        fontweight="bold",
        y=0.99,
    )
    layout = fig.add_gridspec(
        4,
        2,
        left=0.07,
        right=0.97,
        bottom=0.06,
        top=0.85,
        width_ratios=(1.25, 1),
        height_ratios=(1, 1, 1, 0.9),
        hspace=0.75,
        wspace=0.25,
    )
    ax_feld = fig.add_subplot(layout[:, 0])
    ax_x = fig.add_subplot(layout[0, 1])
    ax_y = fig.add_subplot(layout[1, 1], sharex=ax_x)
    ax_phi = fig.add_subplot(layout[2, 1], sharex=ax_x)
    ax_kennwerte = fig.add_subplot(layout[3, 1])
    ax_kennwerte.set_xticks([])
    ax_kennwerte.set_yticks([])
    for spine in ax_kennwerte.spines.values():
        spine.set_visible(False)
    ax_kennwerte.set_title(
        "Kennwerte (rollierende 60 s)", loc="left", pad=3
    )
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
    ax_phi.set_xlabel("Zeit seit Programmstart (s)", labelpad=3)

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
    messungs_status = fig.text(
        0.5,
        0.905,
        "Messbereit. Die CSV-Datei wird nach Ablauf der Messdauer gespeichert.",
        ha="center",
        va="center",
        fontsize=9,
    )
    ax_dauer = fig.add_axes([0.04, 0.925, 0.16, 0.035])
    ax_aufloesung = fig.add_axes([0.26, 0.925, 0.16, 0.035])
    ax_dateiname = fig.add_axes([0.48, 0.925, 0.29, 0.035])
    ax_start = fig.add_axes([0.82, 0.92, 0.15, 0.045])
    eingabe_dauer = TextBox(ax_dauer, "Dauer (s):", initial="15")
    eingabe_aufloesung = TextBox(ax_aufloesung, "Aufloesung (Hz):", initial="25")
    eingabe_dateiname = TextBox(
        ax_dateiname, "Dateiname:", initial=""
    )
    start_knopf = Button(ax_start, "Messung starten")
    messung = {
        "aktiv": False,
        "start": None,
        "dauer": 0.0,
        "aufloesung_hz": 0.0,
        "name": "",
        "rohdaten": [],
    }

    animation = None
    aufnahme_timer = fig.canvas.new_timer(interval=10)

    def verarbeite_pakete(aktualisiere_feld):
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

            if aktualisiere_feld and packet.HasField("geometry"):
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

                received_at = time.monotonic()
                elapsed = received_at - startzeit
                phi = (
                    robot.orientation
                    if robot.HasField("orientation")
                    else float("nan")
                )
                letzter_empfang = elapsed
                if messung["aktiv"]:
                    messungszeit = received_at - messung["start"]
                    if (
                        messungszeit <= messung["dauer"]
                        and messungszeit >= messung["naechste_messung"]
                    ):
                        messung["rohdaten"].append(
                            (
                                messungszeit,
                                datetime.datetime.now().astimezone().isoformat(
                                    timespec="milliseconds"
                                ),
                                robot.x,
                                robot.y,
                                phi,
                                robot.confidence,
                            )
                        )
                        messung["naechste_messung"] = (
                            messungszeit + 1.0 / messung["aufloesung_hz"]
                        )
                else:
                    historie.append(
                        (elapsed, robot.x, robot.y, phi, robot.confidence)
                    )
                break

    def beende_messung():
        messung["aktiv"] = False
        aufnahme_timer.stop()
        eingabe_dauer.set_active(True)
        eingabe_aufloesung.set_active(True)
        eingabe_dateiname.set_active(True)
        start_knopf.label.set_text("Messung starten")
        start_knopf.set_active(True)
        if animation is not None:
            animation.event_source.start()

        if not messung["rohdaten"]:
            messungs_status.set_text(
                "Messung beendet: keine passenden Robotermesswerte empfangen; "
                "es wurde keine Datei gespeichert."
            )
        else:
            statistik_eingaben = [
                (wert[0], wert[2], wert[3], wert[4], wert[5])
                for wert in messung["rohdaten"]
            ]
            statistiken = berechne_statistik(statistik_eingaben)
            zeitstempel = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            dateiname = f"{zeitstempel}_{messung['name']}.csv"
            try:
                speicherordner = os.path.join(
                    os.path.dirname(__file__), MESSUNGS_ORDNER
                )
                os.makedirs(speicherordner, exist_ok=True)
                dateipfad = os.path.join(speicherordner, dateiname)
                speichere_messung(
                    dateipfad,
                    messung["rohdaten"],
                    statistiken,
                    messung["dauer"],
                    messung["aufloesung_hz"],
                )
            except OSError as exc:
                messungs_status.set_text(
                    f"Fehler beim Speichern der Messung: {exc}"
                )
                print(f"Fehler beim Speichern der Messung: {exc}")
            else:
                messungs_status.set_text(
                    f"Messung gespeichert: {dateiname} "
                    f"({len(messung['rohdaten'])} Messwerte)"
                )
                print(f"Messung gespeichert: {dateipfad}")

        fig.canvas.draw_idle()

    def aufnahme_tick():
        verarbeite_pakete(aktualisiere_feld=False)
        if time.monotonic() - messung["start"] >= messung["dauer"]:
            beende_messung()

    aufnahme_timer.add_callback(aufnahme_tick)

    def starte_messung(_event):
        if messung["aktiv"]:
            return

        try:
            dauer = float(eingabe_dauer.text.strip())
            aufloesung_hz = float(eingabe_aufloesung.text.strip())
        except ValueError:
            messungs_status.set_text(
                "Fehler: Dauer und Aufloesung muessen Zahlen sein."
            )
            fig.canvas.draw_idle()
            return
        if not math.isfinite(dauer) or dauer <= 0:
            messungs_status.set_text("Fehler: Dauer muss groesser als 0 Sekunden sein.")
            fig.canvas.draw_idle()
            return
        if not math.isfinite(aufloesung_hz) or aufloesung_hz <= 0:
            messungs_status.set_text(
                "Fehler: Aufloesung muss groesser als 0 Hz sein."
            )
            fig.canvas.draw_idle()
            return

        name = os.path.basename(eingabe_dateiname.text.strip())
        if name.lower().endswith(".csv"):
            name = name[:-4]
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
        if not name:
            messungs_status.set_text("Fehler: Bitte einen gueltigen Dateinamen eingeben.")
            fig.canvas.draw_idle()
            return

        jetzt = time.monotonic()
        messung["aktiv"] = True
        messung["start"] = jetzt
        messung["dauer"] = dauer
        messung["aufloesung_hz"] = aufloesung_hz
        messung["naechste_messung"] = 0.0
        messung["name"] = name
        messung["rohdaten"] = []
        for eingabe in (eingabe_dauer, eingabe_aufloesung, eingabe_dateiname):
            eingabe.stop_typing()
            eingabe.set_active(False)
        start_knopf.label.set_text("Messung laeuft")
        start_knopf.set_active(False)
        messungs_status.set_text(
            f"Messung laeuft fuer {dauer:g} s mit maximal {aufloesung_hz:g} Hz. "
            "Grafik-Aktualisierung ist pausiert."
        )
        if animation is not None:
            animation.event_source.stop()
        aufnahme_timer.start()
        fig.canvas.draw_idle()

    start_knopf.on_clicked(starte_messung)

    def update(_frame):
        verarbeite_pakete(aktualisiere_feld=True)
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
        aufnahme_timer.stop()
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
