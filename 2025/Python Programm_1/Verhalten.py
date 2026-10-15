from abc import ABC, abstractmethod
from WeltModell import WeltModell
from Bewegungen import PositionAnfahren
import math


class BasisVerhalten(ABC):
    def __init__(self, welt_modell: WeltModell):
        self.welt_modell = welt_modell
        self.bewegung = PositionAnfahren(welt_modell)

    @abstractmethod
    def ist_ausfuehrbar(self) -> bool:
        pass

    @abstractmethod
    def ausfuehren_verhalten(self, robot_id: int):
        pass


class BallHolen(BasisVerhalten):
    def __init__(self, welt_modell: WeltModell):
        super().__init__(welt_modell)

        # Maße aus grSim Division B in mm
        # grSim: Length = 9.0 m, Width = 6.0 m
        self.feld_laenge = 9000.0
        self.feld_breite = 6000.0

        self.x_min = -self.feld_laenge / 2.0
        self.x_max = self.feld_laenge / 2.0
        self.y_min = -self.feld_breite / 2.0
        self.y_max = self.feld_breite / 2.0

        # Sicherheitsabstand zur Spielfeldlinie
        self.rand_sicherheit = 200.0  # mm

        # Gegnerisches Tor rechts
        self.tor_x = self.x_max
        self.tor_y = 0.0

        # Zielpunkt hinter dem Ball
        self.abstand_hinter_ball = 250.0  # mm

    def ist_ausfuehrbar(self) -> bool:
        return self.welt_modell.ball is not None and self.welt_modell.ball.ist_aktiv

    def ausfuehren_verhalten(self, robot_id: int):
        roboter = self.welt_modell.roboter_heim[robot_id]
        ball = self.welt_modell.ball

        if not roboter.ist_aktiv or not ball.ist_aktiv:
            return 0.0, 0.0, 0.0

        ball_pos = ball.pose.position
        ich_pos = roboter.pose.position

        # Richtung vom Ball zum Tor
        dx_tor = self.tor_x - ball_pos.x
        dy_tor = self.tor_y - ball_pos.y

        laenge = math.hypot(dx_tor, dy_tor)

        if laenge < 1e-6:
            richtung_x = 1.0
            richtung_y = 0.0
        else:
            richtung_x = dx_tor / laenge
            richtung_y = dy_tor / laenge

        # Ziel liegt hinter dem Ball, damit Roboter nicht direkt in den Ballmittelpunkt fährt
        ziel_x = ball_pos.x - richtung_x * self.abstand_hinter_ball
        ziel_y = ball_pos.y - richtung_y * self.abstand_hinter_ball

        # Ziel innerhalb vom Spielfeld begrenzen
        ziel_x = max(
            self.x_min + self.rand_sicherheit,
            min(self.x_max - self.rand_sicherheit, ziel_x)
        )

        ziel_y = max(
            self.y_min + self.rand_sicherheit,
            min(self.y_max - self.rand_sicherheit, ziel_y)
        )

        # Für den stabilen Test: Roboter schaut zum Zielpunkt, nicht zum Tor
        winkel_zum_ziel = math.atan2(
            ziel_y - ich_pos.y,
            ziel_x - ich_pos.x
        )

        self.bewegung.set_ziel(
            ziel_x,
            ziel_y,
            winkel_zum_ziel
        )

        return self.bewegung.ausfuehren_bewegung(robot_id)


class SchussBlocken(BasisVerhalten):
    def __init__(self, welt_modell: WeltModell):
        super().__init__(welt_modell)

        self.eigenes_tor_x = -4500.0
        self.tor_y_min = -500.0
        self.tor_y_max = 500.0

    def ist_ausfuehrbar(self) -> bool:
        return self.welt_modell.ball is not None and self.welt_modell.ball.ist_aktiv

    def ausfuehren_verhalten(self, robot_id: int):
        ball = self.welt_modell.ball
        roboter = self.welt_modell.roboter_heim[robot_id]

        if not roboter.ist_aktiv or not ball.ist_aktiv:
            return 0.0, 0.0, 0.0

        ball_pos = ball.pose.position
        ich_pos = roboter.pose.position

        ziel_x = self.eigenes_tor_x + 500.0
        ziel_y = max(self.tor_y_min, min(self.tor_y_max, ball_pos.y))

        winkel_zum_ball = math.atan2(
            ball_pos.y - ich_pos.y,
            ball_pos.x - ich_pos.x
        )

        self.bewegung.set_ziel(ziel_x, ziel_y, winkel_zum_ball)

        return self.bewegung.ausfuehren_bewegung(robot_id)