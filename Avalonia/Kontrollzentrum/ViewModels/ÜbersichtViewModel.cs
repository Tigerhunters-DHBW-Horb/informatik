using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using Avalonia.Media;
using System.Collections.ObjectModel;
using System.Linq;
using System.Diagnostics;
//using Kontrollzentrum.Protobuf;

namespace Kontrollzentrum.ViewModels;


public partial class ÜbersichtViewModel : ViewModelBase
{
    [ObservableProperty]
    private int packetsPerSecond;
    [ObservableProperty]
    private IEffect? borderEffect;
    public ObservableCollection<SSL_DetectionRobot_Liste> Positions { get; } = new();
    private readonly object _frameLock = new();

    private SSL_DetectionFrame? _latestPacket;
    private bool _updateScheduled;

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
        lock (_frameLock)
        {
            // Einen noch nicht verarbeiteten Frame ersetzen.
            _latestPacket = data;

            if (_updateScheduled)
                return;

            _updateScheduled = true;
        }

        Dispatcher.UIThread.Post(ProcessLatestFrame);
    }

    private void ProcessLatestFrame()
    {
        SSL_DetectionFrame? frame;

        lock (_frameLock)
        {
            frame = _latestPacket;
            _latestPacket = null;
            _updateScheduled = false;
        }

        if (frame == null)
            return;

        foreach (var robot in frame.RobotsBlue)
            UpdateRobot("Blau", robot);

        foreach (var robot in frame.RobotsYellow)
            UpdateRobot("Gelb", robot);
    }
    private void UpdateRobot(string team, SSL_DetectionRobot robot)
    {
        var position = Positions.FirstOrDefault(p =>
            p.Team == team && p.RobotId == robot.RobotId);

        if (position == null)
        {
            position = new SSL_DetectionRobot_Liste
            {
                Team = team,
                RobotId = robot.RobotId
            };

            Positions.Add(position);
        }

        position.Confidence = robot.Confidence;
        position.X = robot.X;
        position.Y = robot.Y;
        position.Orientation = robot.Orientation;
        position.PixelX = robot.PixelX;
        position.PixelY = robot.PixelY;
        position.Height = robot.Height;
        position.LastSeenTimestamp = Stopwatch.GetTimestamp();
    }
}