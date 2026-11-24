namespace Kontrollzentrum.Models;

public enum ConnectionStatus
{
    Disconnected,
    Connecting,
    Connected,
    Warning,
    Error
}

public enum TeamColor
{
    Blue,
    Yellow,
    Unknown
}

public enum RobotOperationalStatus
{
    Active,
    Idle,
    Warning,
    Error,
    Offline
}
