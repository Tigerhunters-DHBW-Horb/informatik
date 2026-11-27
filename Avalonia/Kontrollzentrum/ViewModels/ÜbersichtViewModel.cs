using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using Avalonia.Media;
using System.Collections.ObjectModel;
//using Kontrollzentrum.Protobuf;

namespace Kontrollzentrum.ViewModels;


public partial class ÜbersichtViewModel : ViewModelBase
{
    [ObservableProperty]
    private int packetsPerSecond;
    [ObservableProperty]
    private IEffect? borderEffect;
    public ObservableCollection<SSL_DetectionRobot_Liste> Positions { get; } = new();

    public ÜbersichtViewModel()
    {
        UDPListener.PacketsPerSecondChanged += UpdatePacketsPerSecond;
        UDPListener.DataReceived += UpdatePositions;
    }

    private void UpdatePacketsPerSecond(int value)
    {
        Dispatcher.UIThread.Post(() =>
        {
            PacketsPerSecond = value;
            if (value > 0)
            {
                BorderEffect = new DropShadowEffect
                {
                    Color = Colors.LimeGreen,
                    BlurRadius = 20,
                    Opacity = 0.8,
                    OffsetX = 0,
                    OffsetY = 0,
                };
            }
            else
            {
                BorderEffect = null;
            }
        });
    }

    private void UpdatePositions(SSL_DetectionFrame data)
    {
        Dispatcher.UIThread.Post(() =>
        {
            Positions.Clear();

            foreach (SSL_DetectionRobot robot in data.RobotsYellow)
            {
                AddRobot(robot, "Gelb");
            }

            foreach (SSL_DetectionRobot robot in data.RobotsBlue)
            {
                AddRobot(robot, "Blau");
            }
        });
    }
    private void AddRobot(SSL_DetectionRobot robot, string team)
    {
        Positions.Add(new SSL_DetectionRobot_Liste
        {
            Team = team,
            Confidence = robot.Confidence,
            RobotId = robot.RobotId,
            X = robot.X,
            Y = robot.Y,
            Orientation = robot.Orientation,
            PixelX = robot.PixelX,
            PixelY = robot.PixelY,
            Height = robot.Height
        });
    }
}