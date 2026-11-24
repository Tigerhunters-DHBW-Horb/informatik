using Kontrollzentrum.Models;

namespace Kontrollzentrum.Communication;

/// <summary>Abstraction shared by grSim, SSN and mock communication implementations.</summary>
public interface ICommunicationAdapter
{
    string Name { get; }
    ConnectionStatus Status { get; }
    long ReceivedCount { get; }
    long SentCount { get; }
    double LatencyMilliseconds { get; }

    event EventHandler<CommunicationMessage>? MessageReceived;
    event EventHandler<ConnectionStatus>? StatusChanged;

    Task ConnectAsync(CancellationToken cancellationToken = default);
    Task DisconnectAsync(CancellationToken cancellationToken = default);
}
