using Avalonia.Data;
using Avalonia.Media;

namespace Kontrollzentrum.ViewModels;

public class SSL_DetectionRobot_Liste
{
    public string Team { get; set; } = "";
    public float Confidence { get; set; }
    public uint RobotId { get; set; }
    public float X { get; set; }
    public float Y { get; set; }
    public float Orientation { get; set; }
    public float PixelX { get; set; }
    public float PixelY { get; set; }
    public float Height { get; set; }

    public IBrush TeamColor => Team == "Blau" ? Brushes.Blue : Brushes.Yellow;
}



