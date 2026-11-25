using System;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Kontrollzentrum.Models;
using Kontrollzentrum.Services;

namespace Kontrollzentrum.ViewModels;

public partial class ÜbersichtViewModel : ViewModelBase
{
    [ObservableProperty]
    private string multicastAddress = "224.5.23.2";

    [ObservableProperty]
    private int port = 10020;

    [ObservableProperty]
    private bool isReceiving;

    [ObservableProperty]
    private string status = "Gestoppt";

    [ObservableProperty]
    private string? errorMessage;

    [ObservableProperty]
    private double packetsPerSecond;

    [ObservableProperty]
    private double kilobytesPerSecond;

    [ObservableProperty]
    private long totalPackets;

    [ObservableProperty]
    private long totalBytes;

    public bool CanEditConnection => !IsReceiving;

    partial void OnIsReceivingChanged(bool value)
    {
        OnPropertyChanged(nameof(CanEditConnection));
    }

    [RelayCommand(IncludeCancelCommand = true)]
    private async Task StartReceptionAsync(
        CancellationToken cancellationToken)
    {
        ErrorMessage = null;

        if (!IPAddress.TryParse(
                MulticastAddress,
                out IPAddress? address))
        {
            ErrorMessage = "Die IP-Adresse ist ungültig.";
            return;
        }

        byte[] addressBytes = address.GetAddressBytes();

        if (addressBytes.Length != 4 ||
            addressBytes[0] is < 224 or > 239)
        {
            ErrorMessage =
                "Bitte eine IPv4-Multicast-Adresse eingeben.";
            return;
        }

        if (Port is < 1 or > 65535)
        {
            ErrorMessage =
                "Der Port muss zwischen 1 und 65535 liegen.";
            return;
        }

        PacketsPerSecond = 0;
        KilobytesPerSecond = 0;
        TotalPackets = 0;
        TotalBytes = 0;

        IsReceiving = true;
        Status = "Empfang gestartet / warte auf Daten";

        var progress = new Progress<VisionReceptionStatistics>(
            statistics =>
            {
                Dispatcher.UIThread.Post(() =>
                {
                    // Verspätete Updates nach dem Stoppen ignorieren.
                    if (!IsReceiving ||
                        cancellationToken.IsCancellationRequested)
                    {
                        return;
                    }

                    PacketsPerSecond =
                        statistics.PacketsPerSecond;

                    KilobytesPerSecond =
                        statistics.KilobytesPerSecond;

                    TotalPackets = statistics.TotalPackets;
                    TotalBytes = statistics.TotalBytes;

                    Status = statistics.PacketsPerSecond > 0
                        ? "Daten werden empfangen"
                        : "Warte auf Daten";
                });
            });

        try
        {
            var receiver = new SslVisionReceiver();

            await Task.Run(
                () => receiver.RunAsync(
                    address,
                    Port,
                    progress,
                    cancellationToken),
                cancellationToken);
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
            // Regulärer Abbruch über den Stop-Befehl.
        }
        catch (Exception exception)
        {
            ErrorMessage = exception.Message;
        }
        finally
        {
            IsReceiving = false;

            PacketsPerSecond = 0;
            KilobytesPerSecond = 0;

            Status = ErrorMessage is null
                ? "Gestoppt"
                : "Empfang fehlgeschlagen";
        }
    }
}