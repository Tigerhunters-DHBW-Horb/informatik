using System.Diagnostics;
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Kontrollzentrum.Models;

namespace Kontrollzentrum.Services;

public sealed class SslVisionReceiver
{
    public async Task RunAsync(
        IPAddress multicastAddress,
        int port,
        IProgress<VisionReceptionStatistics> progress,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(multicastAddress);
        ArgumentNullException.ThrowIfNull(progress);

        if (multicastAddress.AddressFamily != AddressFamily.InterNetwork)
        {
            throw new ArgumentException(
                "Es wird eine IPv4-Multicast-Adresse benötigt.",
                nameof(multicastAddress));
        }

        byte firstOctet = multicastAddress.GetAddressBytes()[0];

        if (firstOctet is < 224 or > 239)
        {
            throw new ArgumentException(
                "Die Adresse muss im IPv4-Multicast-Bereich liegen.",
                nameof(multicastAddress));
        }

        if (port is < 1 or > 65535)
        {
            throw new ArgumentOutOfRangeException(nameof(port));
        }

        using var udpClient = new UdpClient(AddressFamily.InterNetwork);

        // Erlaubt auf unterstützten Plattformen das Teilen des Ports.
        // Das genaue Verhalten ist betriebssystemabhängig.
        udpClient.ExclusiveAddressUse = false;
        udpClient.Client.SetSocketOption(
            SocketOptionLevel.Socket,
            SocketOptionName.ReuseAddress,
            true);

        udpClient.Client.ReceiveBufferSize = 4 * 1024 * 1024;

        udpClient.Client.Bind(
            new IPEndPoint(IPAddress.Any, port));

        udpClient.JoinMulticastGroup(multicastAddress);

        long totalPackets = 0;
        long totalBytes = 0;

        Task receiveTask = ReceiveLoopAsync();
        Task statisticsTask = StatisticsLoopAsync();

        await Task.WhenAll(receiveTask, statisticsTask)
            .ConfigureAwait(false);

        async Task ReceiveLoopAsync()
        {
            try
            {
                while (!cancellationToken.IsCancellationRequested)
                {
                    UdpReceiveResult result =
                        await udpClient.ReceiveAsync(cancellationToken)
                            .ConfigureAwait(false);

                    Interlocked.Increment(ref totalPackets);

                    Interlocked.Add(
                        ref totalBytes,
                        result.Buffer.Length);

                    // Hier später SSL-Vision-Protobuf dekodieren.
                }
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
                // Reguläres Stoppen.
            }
            finally
            {
                // Beendet auch die Statistikschleife, falls der
                // Empfang durch einen Fehler endet.
                receiveFinished.TrySetResult(true);
            }
        }

        async Task StatisticsLoopAsync()
        {
            var stopwatch = Stopwatch.StartNew();

            long previousPackets = 0;
            long previousBytes = 0;
            TimeSpan previousTime = stopwatch.Elapsed;

            using var timer = new PeriodicTimer(
                TimeSpan.FromSeconds(1));

            try
            {
                while (true)
                {
                    Task<bool> tickTask =
                        timer.WaitForNextTickAsync(cancellationToken)
                            .AsTask();

                    Task completed = await Task.WhenAny(
                        tickTask,
                        receiveFinished.Task).ConfigureAwait(false);

                    if (completed == receiveFinished.Task)
                    {
                        break;
                    }

                    if (!await tickTask.ConfigureAwait(false))
                    {
                        break;
                    }

                    long packets = Interlocked.Read(ref totalPackets);
                    long bytes = Interlocked.Read(ref totalBytes);

                    TimeSpan currentTime = stopwatch.Elapsed;
                    double seconds =
                        (currentTime - previousTime).TotalSeconds;

                    if (seconds <= 0)
                    {
                        continue;
                    }

                    progress.Report(new VisionReceptionStatistics(
                        PacketsPerSecond:
                            (packets - previousPackets) / seconds,
                        KilobytesPerSecond:
                            (bytes - previousBytes) / seconds / 1000.0,
                        TotalPackets: packets,
                        TotalBytes: bytes));

                    previousPackets = packets;
                    previousBytes = bytes;
                    previousTime = currentTime;
                }
            }
            catch (OperationCanceledException)
                when (cancellationToken.IsCancellationRequested)
            {
                // Reguläres Stoppen.
            }
        }
    }

    private readonly TaskCompletionSource<bool> receiveFinished =
        new(TaskCreationOptions.RunContinuationsAsynchronously);
}