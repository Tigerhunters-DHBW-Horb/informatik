using CommunityToolkit.Mvvm.ComponentModel;

namespace Kontrollzentrum.ViewModels;

public partial class MainViewModel : ViewModelBase
{
    [ObservableProperty]
    private string _greeting = "Welcome to another Test!";
}
