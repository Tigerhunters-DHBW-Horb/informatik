using System;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;

namespace Kontrollzentrum.Services;


public class SslVisionReceiver
{
    private readonly UdpClient _udpClient;

    public event Action? PacketReceived;

    public SslVisionReceiver()
    {
        _udpClient = new UdpClient(10020);

        _udpClient.JoinMulticastGroup(
            IPAddress.Parse("224.5.23.2"));
    }

    public async Task ReceiveAsync()
    {
        while (true)
        {
            var result =
                await _udpClient.ReceiveAsync();

            PacketReceived?.Invoke();
        }
    }
}