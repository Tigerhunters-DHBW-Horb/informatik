using Avalonia.Controls;
using Avalonia.Interactivity;
using System;
using System.Diagnostics;
using System.Threading.Tasks;


using Kontrollzentrum.Services;

namespace Kontrollzentrum.Views;

public partial class MainWindow : Window
{
    
    private DateTime _lastPacketTime;
    public MainWindow()
    {
        InitializeComponent();
        StartStatusMonitor();

        var receiver = new SslVisionReceiver();
        receiver.PacketReceived += () =>
        {
            _lastPacketTime = DateTime.Now;
        };
        _ = receiver.ReceiveAsync();
    }

    private void Button_OnClick(object? sender, RoutedEventArgs e)
    {
        Debug.WriteLine("Click!");
    }

    private async void StartStatusMonitor()
{
    while (true)
    {
        if (DateTime.Now - _lastPacketTime
            < TimeSpan.FromSeconds(1))
        {
            StatusText.Text = "Empfange Daten";
        }
        else
        {
            StatusText.Text = "Keine Daten";
        }

        await Task.Delay(200);
    }
}
}