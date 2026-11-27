using System;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Google.Protobuf;

namespace Kontrollzentrum;

public class UDPListener
{
    private const int listenPort = 10006;
    private static int packetCount = 0;
    private static double packetsPerSecond = 0;
    public static event Action<int>? PacketsPerSecondChanged;
    public static event Action<SSL_DetectionFrame>? DataReceived;


    public static void StartListener()
    {
        UdpClient listener = new UdpClient(listenPort);
        IPEndPoint groupEP = new IPEndPoint(IPAddress.Any, listenPort);

        long TimeStamp = Stopwatch.GetTimestamp();

        try
        {
            listener.Client.ReceiveTimeout = 1000;

            while (true)
            {
                try
                {
                    byte[] bytes = listener.Receive(ref groupEP);
                    packetCount++;

                    SSL_WrapperPacket data = SSL_WrapperPacket.Parser.ParseFrom(bytes);
                    if (data.Detection != null)
                    {
                        DataReceived?.Invoke(data.Detection);
                    }

                    //Console.WriteLine(data);
                }
                catch (SocketException e)
                {
                    if (e.SocketErrorCode != SocketError.TimedOut)
                        throw;
                }
                catch (InvalidProtocolBufferException e)
                {
                    Console.WriteLine($"Ungültiges Protobuf-Paket: {e.Message}");
                }

                double elapsedSeconds = Stopwatch.GetElapsedTime(TimeStamp).TotalSeconds;

                if (elapsedSeconds >= 1.0)
                {
                    packetsPerSecond = packetCount / elapsedSeconds;

                    PacketsPerSecondChanged?.Invoke((int)packetsPerSecond);

                    TimeStamp = Stopwatch.GetTimestamp();
                    packetCount = 0;
                }
            }
        }
        catch (SocketException e)
        {
            Console.WriteLine(e);
        }
        finally
        {
            listener.Close();
        }
    }
}