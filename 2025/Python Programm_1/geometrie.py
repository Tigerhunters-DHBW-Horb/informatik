import math

class Vektor2D:
    """Stellt einen 2D-Vektor oder einen Punkt auf dem Spielfeld dar."""
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, anderer: 'Vektor2D') -> 'Vektor2D':
        """Addiert zwei Vektoren: v1 + v2"""
        return Vektor2D(self.x + anderer.x, self.y + anderer.y)
        
    def __sub__(self, anderer: 'Vektor2D') -> 'Vektor2D':
        """Subtrahiert zwei Vektoren: v1 - v2"""
        return Vektor2D(self.x - anderer.x, self.y - anderer.y)
        
    def skaliere(self, skalar: float) -> 'Vektor2D':
        """Multipliziert den Vektor mit einer Zahl."""
        return Vektor2D(self.x * skalar, self.y * skalar)
        
    def distanz_zu(self, anderer: 'Vektor2D') -> float:
        """Berechnet den euklidischen Abstand zu einem anderen Punkt."""
        return math.dist((self.x, self.y), (anderer.x, anderer.y))
        
    def laenge(self) -> float:
        """Berechnet die Länge des Vektors (Abstand zum Nullpunkt)."""
        return math.hypot(self.x, self.y)

    def __repr__(self):
        """Erlaubt eine schöne Textausgabe beim Printen, z.B. print(mein_vektor)."""
        return f"Vektor2D(x={self.x:.2f}, y={self.y:.2f})"

class Pose:
    """Stellt die 2D-Pose eines Objekts dar (Position + Orientierung)."""
    def __init__(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0):
        # Die Position wird als Vektor2D-Objekt gespeichert
        self.position: Vektor2D = Vektor2D(x, y)
        # Die Orientierung (Blickrichtung) in Radiant (rad)
        self.orientierung: float = theta

    def __repr__(self):
        return f"Pose(x={self.position.x:.2f}, y={self.position.y:.2f}, phi={self.orientierung:.2f}rad)"

# --- Hilfsfunktionen für die gesamte Software ---

def normalisiere_winkel(winkel: float) -> float:
    """
    Hält den Winkel immer im Bereich von -PI bis +PI.
    Verhindert, dass der Roboter sich 'unnötig im Kreis dreht'.
    """
    return math.atan2(math.sin(winkel), math.cos(winkel))

def grad_zu_rad(grad: float) -> float:
    """Konvertiert Grad in Radiant."""
    return grad * (math.pi / 180.0)

def rad_zu_grad(rad: float) -> float:
    """Konvertiert Radiant in Grad."""
    return rad * (180.0 / math.pi)




# import math

# class Vektor2D:
#     def __init__(self, x: float = 0.0, y: float = 0.0):
#         self.x = x
#         self.y = y

#     def __add__(self, anderer: 'Vektor2D') -> 'Vektor2D':
#         return Vektor2D(self.x + anderer.x, self.y + anderer.y)
        
#     def __sub__(self, anderer: 'Vektor2D') -> 'Vektor2D':
#         return Vektor2D(self.x - anderer.x, self.y - anderer.y)
        
#     def skaliere(self, skalar: float) -> 'Vektor2D':
#         return Vektor2D(self.x * skalar, self.y * skalar)
        
#     def distanz_zu(self, anderer: 'Vektor2D') -> float:
#         return math.dist((self.x, self.y), (anderer.x, anderer.y))
        
#     def laenge(self) -> float:
#         return math.hypot(self.x, self.y)

# class Pose:
#     """Stellt die 2D-Pose eines Objekts dar (Position + Orientierung)."""
#     def __init__(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0):
#         self.position: Vektor2D = Vektor2D(x, y)
#         self.orientierung: float = theta # Winkel in rad