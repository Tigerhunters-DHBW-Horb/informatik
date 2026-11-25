namespace Kontrollzentrum.Models;

public sealed record VisionReceptionStatistics(
    double PacketsPerSecond,
    double KilobytesPerSecond,
    long TotalPackets,
    long TotalBytes);