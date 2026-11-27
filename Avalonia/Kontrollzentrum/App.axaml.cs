using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Kontrollzentrum.ViewModels;
using Kontrollzentrum.Views;

using System.Threading.Tasks;

namespace Kontrollzentrum;

public partial class App : Application
{
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.MainWindow = new MainWindow
            {
                //DataContext = new MainViewModel(),
            };
        }

        // UDP Listener starten
        Task.Run(UDPListener.StartListener);

        base.OnFrameworkInitializationCompleted();
    }
}