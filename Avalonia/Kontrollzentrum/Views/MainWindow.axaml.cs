using Avalonia;
using Avalonia.Controls;
using Kontrollzentrum.Views;
using Avalonia.Interactivity;
using Avalonia.Styling;
using System;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Linq;
using Kontrollzentrum.ViewModels;

// namespace Kontrollzentrum;
namespace Kontrollzentrum.Views;

public partial class MainWindow : Window
{
    // Die Views einmal erstellen und beim Wechsel wiederverwenden.
    private readonly Übersicht _overviewView = new();
    private readonly Datenempfang _datenempfang = new();
    private readonly Feld _feld = new();

    public MainWindow()
    {
        InitializeComponent();
        DataContext = new ÜbersichtViewModel();

#if DEBUG
        Opened += (_, _) =>
        {
            var screens = Screens.All;
            if (screens.Count < 3)
                return; // Es sind weniger als drei Bildschirme verfügbar.

            var screen = screens[2];
            if (screen is null)
                return; // Es ist kein weiterer Bildschirm angeschlossen.

            var area = screen.WorkingArea;
            var scale = screen.Scaling;

            Position = new PixelPoint(
                area.X + (area.Width - (int)(Bounds.Width * scale)) / 20,
                area.Y + (area.Height - (int)(Bounds.Height * scale)) / 20);
        };
#endif

        // Theme Switch auf aktuellen Zustand setzen
        if (Application.Current?.ActualThemeVariant == ThemeVariant.Dark) ThemeSwitch.IsChecked = true;
        else ThemeSwitch.IsChecked = false;

        UpdateThemeIcon();

        // Funktion UpdateThemeIcon dem Button ThemeSwitch zuweisen
        ThemeSwitch.IsCheckedChanged += UpdateThemeIcon;

        // Dem Seitenmenü bei Änderung eine Funktion zuweisen
        SidebarMenu.SelectionChanged += ShowSelectedPage;

        //Ausgewählte Seite anzeigen
        ShowSelectedPage();
    }

    private void UpdateThemeIcon(object? sender = null, RoutedEventArgs? e = null)
    {

        if (ThemeSwitch.IsChecked == true)
        {
            DarkThemeIcon.IsVisible = true;
            LightThemeIcon.IsVisible = false;
        }
        else
        {
            DarkThemeIcon.IsVisible = false;
            LightThemeIcon.IsVisible = true;
        }

        if (Application.Current != null)
        {
            if (ThemeSwitch.IsChecked == true)
            {
                Application.Current.RequestedThemeVariant = ThemeVariant.Dark;
            }
            else
            {
                Application.Current.RequestedThemeVariant = ThemeVariant.Light;
            }
        }
    }

    private void ShowSelectedPage(object? sender = null, SelectionChangedEventArgs? e = null)
    {
        PageContent.Content = SidebarMenu.SelectedIndex switch
        {
            0 => _overviewView,
            1 => _datenempfang,
            2 => _feld,
            3 => CreatePlaceholder("Automations"),
            4 => CreatePlaceholder("Reports"),
            5 => CreatePlaceholder("Logbook"),
            6 => CreatePlaceholder("Help"),
            7 => CreatePlaceholder("Settings"),
            _ => null
        };
    }

    private static TextBlock CreatePlaceholder(string title)
    {
        return new TextBlock
        {
            Text = title,
            FontSize = 28
        };
    }
}