using System.Net.Sockets;
using Kontrollzentrum.Models;

namespace Kontrollzentrum.Communication;

/// <summary>Generates deterministic test traffic. It never attempts a real protocol connection.</summary>
public sealed class MockCommunicationAdapter : ICommunicationAdapter
{
    private readonly CancellationTokenSource _source = new();
    private readonly string _name;
    private ConnectionStatus _status = ConnectionStatus.Connected;
    private long _received;
    private long _sent;
    private double _latency = 8;

    public MockCommunicationAdapter(string name)
    {
        _name = name;
        _ = RunAsync(_source.Token);
    }

    public string Name => _name;
    public ConnectionStatus Status => _status;
    public long ReceivedCount => Interlocked.Read(ref _received);
    public long SentCount => Interlocked.Read(ref _sent);
    public double LatencyMilliseconds => _latency;
    public event EventHandler<CommunicationMessage>? MessageReceived;
    public event EventHandler<ConnectionStatus>? StatusChanged;

    public Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        _status = ConnectionStatus.Connected;
        StatusChanged?.Invoke(this, _status);
        return Task.CompletedTask;
    }

    public Task DisconnectAsync(CancellationToken cancellationToken = default)
    {
        _status = ConnectionStatus.Disconnected;
        StatusChanged?.Invoke(this, _status);
        return Task.CompletedTask;
    }

    private async Task RunAsync(CancellationToken token)
    {
        var random = new Random(HashCode.Combine(_name.GetHashCode(), Environment.ProcessId));
        while (!token.IsCancellationRequested)
        {
            try
            {
                await Task.Delay(350, token);
                if (_status != ConnectionStatus.Connected)
                    continue;

                Interlocked.Increment(ref _received);
                Interlocked.Increment(ref _sent);
                _latency = 5 + random.NextDouble() * 12;
                var isError = random.Next(30) == 0;
                MessageReceived?.Invoke(this, new CommunicationMessage
                {
                    Source = _name,
                    Destination = "Dashboard",
                    MessageType = _name == "grSim" ? "SSL_VISION_FRAME" : "SSN_TELEMETRY",
                    Payload = isError ? "mock: malformed test packet" : $"mock: sequence {_received}",
                    IsError = isError
                });
            }
            catch (TaskCanceledException) { }
        }
    }
}
