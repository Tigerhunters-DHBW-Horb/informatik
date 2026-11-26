using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using Avalonia.Media;

namespace Kontrollzentrum.ViewModels;

public partial class ÜbersichtViewModel : ViewModelBase
{
    [ObservableProperty]
    private int packetsPerSecond;
    [ObservableProperty]
    private IEffect? borderEffect;

    public ÜbersichtViewModel()
    {
        UDPListener.PacketsPerSecondChanged += UpdatePacketsPerSecond;
    }

    private void UpdatePacketsPerSecond(int value)
    {
        Dispatcher.UIThread.Post(() =>
        {
            PacketsPerSecond = value;
            if (value > 0)
            {
                BorderEffect = new DropShadowEffect
                {
                    Color = Colors.LimeGreen,
                    BlurRadius = 20,
                    Opacity = 0.8,
                    OffsetX = 0,
                    OffsetY = 0,
                };
            }
            else
            {
                BorderEffect = null;
            }
        });
    }
}