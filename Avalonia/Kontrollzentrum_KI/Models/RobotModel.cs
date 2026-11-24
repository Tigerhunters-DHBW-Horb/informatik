namespace Kontrollzentrum.Models;

public sealed class RobotModel
{
    public int Id { get; init; }
    public TeamColor Team { get; init; }
    public double X { get; set; }
    public double Y { get; set; }
    public double RotationDegrees { get; set; }
    public double Velocity { get; set; }
    public double DisplayX { get; set; }
    public double DisplayY { get; set; }
    public ConnectionStatus Connection { get; set; }
    public RobotOperationalStatus OperationalStatus { get; set; }
    public DateTime LastUpdate { get; set; } = DateTime.UtcNow;
}
