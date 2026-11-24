namespace Kontrollzentrum.Models;

public sealed class CommunicationMessage
{
    public DateTime Timestamp { get; init; } = DateTime.UtcNow;
    public required string Source { get; init; }
    public required string Destination { get; init; }
    public required string MessageType { get; init; }
    public required string Payload { get; init; }
    public bool IsError { get; init; }
}

public sealed class StatusCardModel
{
    public required string Title { get; init; }
    public required string Status { get; init; }
    public required string Value { get; init; }
    public required string Detail { get; init; }
    public ConnectionStatus State { get; init; }
}
