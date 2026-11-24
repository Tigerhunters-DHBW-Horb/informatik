using System.Collections.ObjectModel;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Kontrollzentrum.Communication;
using Kontrollzentrum.Models;

namespace Kontrollzentrum.ViewModels;

public partial class MainViewModel : ViewModelBase
{
    private readonly MockCommunicationAdapter _grSim = new("grSim");
    private readonly MockCommunicationAdapter _ssn = new("SSN");
    private readonly DispatcherTimer _timer = new() { Interval = TimeSpan.FromMilliseconds(500) };
    private readonly Random _random = new();
    private DateTime _startedAt = DateTime.UtcNow;

    [ObservableProperty]
    private string _selectedPage = "Overview";

    [ObservableProperty]
    private int _selectedIndex;

    [ObservableProperty]
    private string _systemStatus = "Simulation active";

    [ObservableProperty]
    private bool _isTestMode = true;

    [ObservableProperty]
    private string _grSimStatus = "Connected";

    [ObservableProperty]
    private string _ssnStatus = "Connected";

    [ObservableProperty]
    private string _packetRate = "5.7";

    [ObservableProperty]
    private string _latency = "12 ms";

    [ObservableProperty]
    private string _activeRobotCount = "6";

    [ObservableProperty]
    private string _receivedCount = "0";

    [ObservableProperty]
    private string _sentCount = "0";

    public ObservableCollection<RobotModel> Robots { get; } = new();
    public ObservableCollection<CommunicationMessage> Messages { get; } = new();
    public ObservableCollection<StatusCardModel> StatusCards { get; } = new();
    public ObservableCollection<string> NavItems { get; } = new(
        ["Overview", "grSim", "SSN", "Field View", "Robots", "Communication", "Sensors",
         "Control", "Data Analysis", "Logs", "Settings"]);

    public MainViewModel()
    {
        for (var i = 0; i < 6; i++)
        {
            var team = i < 3 ? TeamColor.Blue : TeamColor.Yellow;
            Robots.Add(new RobotModel
            {
                Id = i + 1,
                Team = team,
                X = i < 3 ? 1200 + i * 700 : 6200 - i * 600,
                Y = 1200 + (i % 3) * 1800,
                DisplayX = 35 + (i < 3 ? 1200 + i * 700 : 6200 - i * 600) / 9000.0 * 830,
                DisplayY = 30 + (1200 + (i % 3) * 1800) / 6000.0 * 540,
                RotationDegrees = i * 38,
                Velocity = 0.4 + i * 0.16,
                Connection = ConnectionStatus.Connected,
                OperationalStatus = RobotOperationalStatus.Active
            });
        }

        _grSim.MessageReceived += (_, message) => AddMessage(message);
        _ssn.MessageReceived += (_, message) => AddMessage(message);
        _timer.Tick += (_, _) => UpdateLiveState();
        _timer.Start();
        RebuildStatusCards();
    }

    [RelayCommand]
    private void Navigate(string page)
    {
        SelectedPage = page;
        SelectedIndex = NavItems.IndexOf(page);
    }

    partial void OnSelectedPageChanged(string value)
    {
        var index = NavItems.IndexOf(value);
        if (index >= 0)
            SelectedIndex = index;
    }

    [RelayCommand]
    private void ToggleTestMode()
    {
        IsTestMode = !IsTestMode;
        SystemStatus = IsTestMode ? "Simulation active" : "Real connection mode";
    }

    private void AddMessage(CommunicationMessage message)
    {
        Dispatcher.UIThread.Post(() =>
        {
            Messages.Insert(0, message);
            while (Messages.Count > 250)
                Messages.RemoveAt(Messages.Count - 1);
        });
    }

    private void UpdateLiveState()
    {
        foreach (var robot in Robots)
        {
            robot.X = Math.Clamp(robot.X + (_random.NextDouble() - 0.5) * 180, 300, 8700);
            robot.Y = Math.Clamp(robot.Y + (_random.NextDouble() - 0.5) * 150, 300, 5700);
            robot.RotationDegrees = (robot.RotationDegrees + 2.5) % 360;
            robot.LastUpdate = DateTime.UtcNow;
            robot.DisplayX = 35 + robot.X / 9000.0 * 830;
            robot.DisplayY = 30 + robot.Y / 6000.0 * 540;
        }

        GrSimStatus = _grSim.Status.ToString();
        SsnStatus = _ssn.Status.ToString();
        ReceivedCount = (_grSim.ReceivedCount + _ssn.ReceivedCount).ToString("N0");
        SentCount = (_grSim.SentCount + _ssn.SentCount).ToString("N0");
        Latency = $"{(_grSim.LatencyMilliseconds + _ssn.LatencyMilliseconds) / 2:0} ms";
        PacketRate = "5.7";
        ActiveRobotCount = Robots.Count(r => r.OperationalStatus == RobotOperationalStatus.Active).ToString();
        SystemStatus = IsTestMode ? "Simulation active" : "Real connection mode";
        RebuildStatusCards();
        OnPropertyChanged(nameof(Robots));
    }

    private void RebuildStatusCards()
    {
        StatusCards.Clear();
        StatusCards.Add(new StatusCardModel
        {
            Title = "grSim",
            Status = GrSimStatus,
            Value = $"{_grSim.ReceivedCount + _ssn.ReceivedCount:N0}",
            Detail = "messages received",
            State = _grSim.Status
        });
        StatusCards.Add(new StatusCardModel
        {
            Title = "SSN",
            Status = SsnStatus,
            Value = _ssn.ReceivedCount.ToString("N0"),
            Detail = "telemetry packets",
            State = _ssn.Status
        });
        StatusCards.Add(new StatusCardModel
        {
            Title = "Robots",
            Status = "Detected",
            Value = Robots.Count.ToString(),
            Detail = $"{ActiveRobotCount} active",
            State = ConnectionStatus.Connected
        });
        StatusCards.Add(new StatusCardModel
        {
            Title = "Latency",
            Status = "Healthy",
            Value = Latency,
            Detail = "round-trip average",
            State = ConnectionStatus.Connected
        });
    }
}
