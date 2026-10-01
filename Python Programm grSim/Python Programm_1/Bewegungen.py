import math
from abc import ABC, abstractmethod
from WeltModell import WeltModell
from geometrie import Pose


class BasisBewegung(ABC):
    def __init__(self, welt_model: WeltModell):
        self.welt_model = welt_model

    @abstractmethod
    def ausfuehren_bewegung(self, robot_id: int):
        pass

    @abstractmethod
    def fertig(self, robot_id: int) -> bool:
        pass


class PositionAnfahren(BasisBewegung):
    def __init__(self, welt_model: WeltModell):
        super().__init__(welt_model)
        self.ziel_pose = None

        # Sehr ruhige Werte für ersten stabilen Test
        self.toleranz_distanz = 80.0   # mm
        self.kp_linear = 0.4
        self.kp_winkel = 1.0

        self.max_v_mms = 400.0         # 400 mm/s = 0.4 m/s
        self.max_v_phi = 1.5           # rad/s

        print("Bewegung: PositionAnfahren sehr stabil bereit!")

    def set_ziel(self, x: float, y: float, theta: float):
        self.ziel_pose = Pose(x, y, theta)

    def ausfuehren_bewegung(self, robot_id: int):
        if self.ziel_pose is None:
            return 0.0, 0.0, 0.0

        ich = self.welt_model.roboter_heim[robot_id]

        if not ich.ist_aktiv:
            return 0.0, 0.0, 0.0

        ist_pos = ich.pose.position
        ist_phi = ich.pose.orientierung

        dx = self.ziel_pose.position.x - ist_pos.x
        dy = self.ziel_pose.position.y - ist_pos.y

        abstand = math.hypot(dx, dy)

        # Winkel vom Roboter zum Zielpunkt
        winkel_zum_ziel = math.atan2(dy, dx)

        # Winkelfehler normalisieren auf -pi bis +pi
        winkelfehler_ziel = winkel_zum_ziel - ist_phi
        winkelfehler_ziel = math.atan2(
            math.sin(winkelfehler_ziel),
            math.cos(winkelfehler_ziel)
        )

        # Drehgeschwindigkeit
        v_phi = winkelfehler_ziel * self.kp_winkel
        v_phi = max(-self.max_v_phi, min(self.max_v_phi, v_phi))

        # Wenn Ziel erreicht ist: stoppen
        if abstand < self.toleranz_distanz:
            return 0.0, 0.0, 0.0

        # Wenn Roboter stark falsch steht: erst drehen, nicht fahren
        if abs(winkelfehler_ziel) > 0.6:
            return 0.0, 0.0, v_phi

        # Vorwärts fahren, sobald er ungefähr richtig ausgerichtet ist
        vx_local = min(self.max_v_mms, abstand * self.kp_linear)

        # Erstmal kein Seitwärtsfahren, dadurch fährt er viel stabiler
        vy_local = 0.0

        return vx_local, vy_local, v_phi

    def fertig(self, robot_id: int) -> bool:
        if self.ziel_pose is None:
            return True

        ich = self.welt_model.roboter_heim[robot_id]

        if not ich.ist_aktiv:
            return False

        abstand = ich.pose.position.distanz_zu(self.ziel_pose.position)
        return abstand < self.toleranz_distanz


class BallAnnehmen(BasisBewegung):
    def __init__(self, welt_model: WeltModell):
        super().__init__(welt_model)
        self.anfahren = PositionAnfahren(welt_model)

    def ausfuehren_bewegung(self, robot_id: int):
        ball = self.welt_model.ball
        roboter = self.welt_model.roboter_heim[robot_id]

        if not ball.ist_aktiv or not roboter.ist_aktiv:
            return 0.0, 0.0, 0.0

        ball_pos = ball.pose.position
        ich_pos = roboter.pose.position

        winkel_zum_ball = math.atan2(
            ball_pos.y - ich_pos.y,
            ball_pos.x - ich_pos.x
        )

        self.anfahren.set_ziel(
            ball_pos.x,
            ball_pos.y,
            winkel_zum_ball
        )

        return self.anfahren.ausfuehren_bewegung(robot_id)

    def fertig(self, robot_id: int) -> bool:
        return self.anfahren.fertig(robot_id)