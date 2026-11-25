using Avalonia;
using Avalonia.Controls;
using Kontrollzentrum.Views;
using Avalonia.Interactivity;
using Avalonia.Styling;
using System;
using System.Diagnostics;
using System.Threading.Tasks;

// namespace Kontrollzentrum;
namespace Kontrollzentrum.Views;

public partial class MainWindow : Window
{
    // Die Views einmal erstellen und beim Wechsel wiederverwenden.
    private readonly ÜbersichtView _overviewView = new();

    public MainWindow()
    {
        InitializeComponent();

        ThemeSwitch.IsChecked = Application.Current?.ActualThemeVariant == ThemeVariant.Dark;
        UpdateThemeIcon();
        ThemeSwitch.IsCheckedChanged += OnThemeSwitchChanged;

        // Erst nach dem Laden des XAML auf Auswahländerungen reagieren.
        SidebarMenu.SelectionChanged += OnMenuSelectionChanged;

        // Die bereits im XAML ausgewählte Seite anzeigen.
        ShowSelectedPage();
    }

    private void OnThemeSwitchChanged(object? sender, RoutedEventArgs e)
    {
        UpdateThemeIcon();

        if (Application.Current is { } application)
        {
            application.RequestedThemeVariant = ThemeSwitch.IsChecked == true
                ? ThemeVariant.Dark
                : ThemeVariant.Light;
        }
    }

    private void UpdateThemeIcon()
    {
        var isDark = ThemeSwitch.IsChecked == true;
        DarkThemeIcon.IsVisible = isDark;
        LightThemeIcon.IsVisible = !isDark;
    }

    private void OnMenuSelectionChanged(
        object? sender,
        SelectionChangedEventArgs e)
    {
        ShowSelectedPage();
    }

    private void ShowSelectedPage()
    {
        PageContent.Content = SidebarMenu.SelectedIndex switch
        {
            0 => _overviewView,
            1 => CreatePlaceholder("Match"),
            2 => CreatePlaceholder("Devices"),
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