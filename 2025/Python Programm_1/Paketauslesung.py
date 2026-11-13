import argparse
from dataclasses import dataclass
from datetime import datetime
import os
import socket
import struct
import sys
import time

from google.protobuf.message import DecodeError


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import ssl_vision_wrapper_pb2 as SSL_WrapperPacket


VISION_MULTICAST_IP = "224.5.23.2"
VISION_PORT = 10020
GROSSES_PAKET_BYTES = 1000


@dataclass
class PaketBeispiel:
    nummer: int
    data: bytes
    packet: object
    adresse: tuple
    empfangszeit: str
    fehler: str = ""


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
    return sock


def beschreibe_paket(packet):
    teile = []
    if packet.HasField("geometry"):
        geometry = packet.geometry
        feld = geometry.field
        teile.append(
            "Felddefinition "
            f"(Spielfeld={feld.field_length} x {feld.field_width} mm, "
            f"Tore={feld.goal_width} x {feld.goal_depth} mm, "
            f"Linien={len(feld.field_lines)}, "
            f"Kreisbögen={len(feld.field_arcs)}, "
            f"Kamerakalibrierungen={len(geometry.calib)})"
        )
        liniennamen = [linie.name for linie in feld.field_lines]
        bogen_namen = [bogen.name for bogen in feld.field_arcs]
        if liniennamen:
            teile.append(f"Liniennamen: {', '.join(liniennamen)}")
        if bogen_namen:
            teile.append(f"Kreisbogen-Namen: {', '.join(bogen_namen)}")
        if geometry.calib:
            teile.append(
                "Kamera-IDs: "
                + ", ".join(str(kamera.camera_id) for kamera in geometry.calib)
            )
        if geometry.HasField("models"):
            modellnamen = [
                name
                for name in ("straight_two_phase", "chip_fixed_loss")
                if geometry.models.HasField(name)
            ]
            teile.append(
                "Ballmodelle: " + (", ".join(modellnamen) or "keine")
            )
    if packet.HasField("detection"):
        detection = packet.detection
        teile.append(
            "Erkennung "
            f"(Frame={detection.frame_number}, Kamera={detection.camera_id}, "
            f"Aufnahmezeit={detection.t_capture:.6f}, "
            f"Sendezeit={detection.t_sent:.6f}, "
            f"Bälle={len(detection.balls)}, "
            f"Roboter blau={len(detection.robots_blue)}, "
            f"Roboter gelb={len(detection.robots_yellow)})"
        )
    return " + ".join(teile) if teile else "keine bekannten Wrapper-Daten"


def beschreibe_positionen(packet):
    if not packet.HasField("detection"):
        return []

    detection = packet.detection
    zeilen = []
    for ball_nummer, ball in enumerate(detection.balls, start=1):
        zeilen.append(
            f"Ball {ball_nummer}: x={ball.x:.1f}, y={ball.y:.1f} mm"
        )

    for team_name, roboter_liste in (
        ("Blau", detection.robots_blue),
        ("Gelb", detection.robots_yellow),
    ):
        for roboter in roboter_liste:
            robot_id = (
                str(roboter.robot_id)
                if roboter.HasField("robot_id")
                else "unbekannt"
            )
            orientierung = (
                f", Winkel={roboter.orientation:.3f} rad"
                if roboter.HasField("orientation")
                else ""
            )
            zeilen.append(
                f"Roboter {team_name} ID {robot_id}: "
                f"x={roboter.x:.1f}, y={roboter.y:.1f} mm"
                f"{orientierung}"
            )
    return zeilen


def sammle_pakete(sock, dauer):
    pakete = []
    anzahl_ungueltiger_pakete = 0
    ende = time.monotonic() + dauer

    try:
        while True:
            restzeit = ende - time.monotonic()
            if restzeit <= 0:
                break
            sock.settimeout(min(restzeit, 0.25))
            try:
                data, adresse = sock.recvfrom(65535)
            except socket.timeout:
                continue

            empfangszeit = datetime.now().astimezone().isoformat(
                timespec="milliseconds"
            )
            packet = SSL_WrapperPacket.SSL_WrapperPacket()
            fehler = ""
            try:
                packet.ParseFromString(data)
            except DecodeError as exc:
                anzahl_ungueltiger_pakete += 1
                fehler = str(exc)
                packet = None

            pakete.append(
                PaketBeispiel(
                    len(pakete) + 1,
                    data,
                    packet,
                    adresse,
                    empfangszeit,
                    fehler,
                )
            )
    except KeyboardInterrupt:
        print("\nAufnahme vorzeitig beendet; werte alle bisherigen Pakete aus.")

    statistik = {
        "gesamt": len(pakete),
        "kleine": sum(
            len(beispiel.data) <= GROSSES_PAKET_BYTES for beispiel in pakete
        ),
        "grosse": sum(
            len(beispiel.data) > GROSSES_PAKET_BYTES for beispiel in pakete
        ),
        "ungueltige": anzahl_ungueltiger_pakete,
    }
    return pakete, statistik


def zeige_pakete(beispiele, statistik):
    print("\n=== Einmalige Auswertung aller empfangenen Pakete ===")
    print(f"Pakete insgesamt: {statistik['gesamt']}")
    print(f"Klein (bis {GROSSES_PAKET_BYTES} Bytes): {statistik['kleine']}")
    print(f"Gross (ueber {GROSSES_PAKET_BYTES} Bytes): {statistik['grosse']}")
    print(f"Ungueltige Pakete: {statistik['ungueltige']}")

    if not beispiele:
        print("Keine gueltigen Pakete zum Anzeigen empfangen.")
        return

    letzte_positionen = {}
    for beispiel in beispiele:
        paketart = (
            "GROSSES Paket"
            if len(beispiel.data) > GROSSES_PAKET_BYTES
            else "kleines Paket"
        )
        print(
            f"\n--- Paket #{beispiel.nummer} | {paketart} | "
            f"Paketlaenge {len(beispiel.data)} Bytes | "
            f"Absender {beispiel.adresse[0]}:{beispiel.adresse[1]} | "
            f"{beispiel.empfangszeit} ---"
        )
        if beispiel.packet is None:
            print(f"Protobuf konnte nicht dekodiert werden: {beispiel.fehler}")
            continue

        print(f"Nachricht/Funktion: {beschreibe_paket(beispiel.packet)}")
        positionen = beschreibe_positionen(beispiel.packet)
        if positionen:
            print("Positionen aus genau diesem Paket:")
            for zeile in positionen:
                print(f"  - {zeile}")
            detection = beispiel.packet.detection
            for ball_nummer, ball in enumerate(detection.balls, start=1):
                letzte_positionen[("Ball", str(ball_nummer))] = (
                    beispiel.nummer,
                    f"Ball {ball_nummer}: x={ball.x:.1f}, y={ball.y:.1f} mm",
                )
            for team_name, roboter_liste in (
                ("Blau", detection.robots_blue),
                ("Gelb", detection.robots_yellow),
            ):
                for roboter in roboter_liste:
                    robot_id = (
                        str(roboter.robot_id)
                        if roboter.HasField("robot_id")
                        else "unbekannt"
                    )
                    orientierung = (
                        f", Winkel={roboter.orientation:.3f} rad"
                        if roboter.HasField("orientation")
                        else ""
                    )
                    letzte_positionen[(team_name, robot_id)] = (
                        beispiel.nummer,
                        f"Roboter {team_name} ID {robot_id}: "
                        f"x={roboter.x:.1f}, y={roboter.y:.1f} mm"
                        f"{orientierung}",
                    )
        elif beispiel.packet.HasField("geometry"):
            print(
                "Funktion: statische Feld-/Kameradefinition; "
                "keine aktuellen Roboter- oder Ballpositionen."
            )
        else:
            print("Keine Positions- oder Geometriedaten in diesem Paket.")

    if letzte_positionen:
        print("\n=== Letzte Positionsquelle je Objekt im Mitschnitt ===")
        for _, (paketnummer, position) in sorted(letzte_positionen.items()):
            print(f"Paket #{paketnummer}: {position}")


def zeichne_feld(ax, geometry):
    from matplotlib.patches import Arc, Rectangle

    feld = geometry.field
    laenge = feld.field_length
    breite = feld.field_width
    ax.add_patch(
        Rectangle(
            (-laenge / 2, -breite / 2),
            laenge,
            breite,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
        )
    )
    for linie in feld.field_lines:
        ax.plot(
            [linie.p1.x, linie.p2.x],
            [linie.p1.y, linie.p2.y],
            color="gray",
            linewidth=max(0.5, linie.thickness / 15),
            alpha=0.65,
        )
    for bogen in feld.field_arcs:
        ax.add_patch(
            Arc(
                (bogen.center.x, bogen.center.y),
                2 * bogen.radius,
                2 * bogen.radius,
                theta1=bogen.a1 * 180 / 3.141592653589793,
                theta2=bogen.a2 * 180 / 3.141592653589793,
                color="gray",
                linewidth=max(0.5, bogen.thickness / 15),
                alpha=0.65,
            )
        )
    ax.set_xlim(-laenge / 2 - 500, laenge / 2 + 500)
    ax.set_ylim(-breite / 2 - 500, breite / 2 + 500)


def zeige_grafik(beispiele, bildpfad=None):
    import matplotlib.pyplot as plt

    positionsbeispiele = [
        beispiel
        for beispiel in beispiele
        if beispiel.packet is not None
        and beispiel.packet.HasField("detection")
    ]
    if not positionsbeispiele:
        return

    fig, (feld_ax, paket_ax) = plt.subplots(
        1,
        2,
        figsize=(14, 7),
        gridspec_kw={"width_ratios": [2, 1]},
    )
    geometry = next(
        (
            beispiel.packet.geometry
            for beispiel in beispiele
            if beispiel.packet is not None
            and beispiel.packet.HasField("geometry")
        ),
        None,
    )
    if geometry is not None:
        zeichne_feld(feld_ax, geometry)
    else:
        feld_ax.axhline(0, color="gray", linewidth=0.8)
        feld_ax.axvline(0, color="gray", linewidth=0.8)

    for beispiel in positionsbeispiele:
        detection = beispiel.packet.detection

        if detection.robots_blue:
            feld_ax.scatter(
                [robot.x for robot in detection.robots_blue],
                [robot.y for robot in detection.robots_blue],
                marker="o",
                color="royalblue",
                edgecolors="white",
                label="Roboter Blau",
            )
            for robot in detection.robots_blue:
                robot_id = (
                    str(robot.robot_id)
                    if robot.HasField("robot_id")
                    else "?"
                )
                feld_ax.annotate(
                    f"P{beispiel.nummer} B{robot_id}",
                    (robot.x, robot.y),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                )

        if detection.robots_yellow:
            feld_ax.scatter(
                [robot.x for robot in detection.robots_yellow],
                [robot.y for robot in detection.robots_yellow],
                marker="o",
                color="gold",
                edgecolors="black",
                label="Roboter Gelb",
            )
            for robot in detection.robots_yellow:
                robot_id = (
                    str(robot.robot_id)
                    if robot.HasField("robot_id")
                    else "?"
                )
                feld_ax.annotate(
                    f"P{beispiel.nummer} G{robot_id}",
                    (robot.x, robot.y),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                )

        if detection.balls:
            feld_ax.scatter(
                [ball.x for ball in detection.balls],
                [ball.y for ball in detection.balls],
                marker="*",
                s=130,
                color="orangered",
                edgecolors="black",
                label="Ball",
            )
            for ball in detection.balls:
                feld_ax.annotate(
                    f"P{beispiel.nummer}",
                    (ball.x, ball.y),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                )

    feld_ax.set_title("Positionen aus den aufgenommenen Paketen")
    feld_ax.set_xlabel("X [mm]")
    feld_ax.set_ylabel("Y [mm]")
    feld_ax.set_aspect("equal", adjustable="box")
    feld_ax.grid(True, alpha=0.2)
    if feld_ax.collections:
        feld_ax.legend(fontsize=7, loc="best")

    paket_ax.plot(
        [beispiel.nummer for beispiel in beispiele],
        [len(beispiel.data) for beispiel in beispiele],
        marker="o",
        color="slateblue",
        linewidth=1,
    )
    paket_ax.axhline(
        GROSSES_PAKET_BYTES,
        color="darkorange",
        linestyle="--",
        label=f"Schwellwert {GROSSES_PAKET_BYTES} Bytes",
    )
    paket_ax.set_title("Laenge aller empfangenen Pakete")
    paket_ax.set_xlabel("Paketnummer")
    paket_ax.set_ylabel("Bytes")
    paket_ax.legend()
    fig.suptitle("SSL-Vision – statische Paketauswertung")
    fig.tight_layout()

    if bildpfad:
        fig.savefig(bildpfad, dpi=160, bbox_inches="tight")
        print(f"\nGrafik gespeichert: {bildpfad}")
    plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Nimmt SSL-Vision-Pakete auf und zeigt sie nach der Aufnahme "
            "einmalig als Text und statische Grafik an."
        )
    )
    parser.add_argument(
        "--dauer",
        type=float,
        default=10.0,
        help="Aufnahmedauer in Sekunden (Standard: 10)",
    )
    parser.add_argument(
        "--bild",
        help="optional: Pfad zum Speichern der statischen Grafik",
    )
    args = parser.parse_args(argv)
    if args.dauer <= 0:
        parser.error("--dauer muss groesser als 0 sein")

    try:
        sock = erstelle_empfaenger()
    except OSError as exc:
        raise SystemExit(
            f"SSL-Vision-Empfaenger konnte nicht gestartet werden: {exc}"
        ) from exc

    print(
        f"SSL-Vision-Empfang auf {VISION_MULTICAST_IP}:{VISION_PORT} "
        f"fuer {args.dauer:g} Sekunden."
    )
    print(
        "Es wird nichts laufend ausgegeben. Nach der Aufnahme werden alle "
        "Pakete ausgewertet, einschliesslich wiederholter grosser Pakete."
    )
    print("Mit Ctrl+C kann die Aufnahme vorzeitig beendet werden.")

    try:
        beispiele, statistik = sammle_pakete(sock, args.dauer)
    finally:
        sock.close()

    zeige_pakete(beispiele, statistik)
    zeige_grafik(beispiele, args.bild)


if __name__ == "__main__":
    main()
