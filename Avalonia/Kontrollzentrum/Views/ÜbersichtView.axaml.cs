using Avalonia.Controls;
using Kontrollzentrum.ViewModels;

namespace Kontrollzentrum.Views;

public partial class ÜbersichtView : UserControl
{
    public ÜbersichtView()
    {
        InitializeComponent();

        DataContext = new ÜbersichtViewModel();
    }
}