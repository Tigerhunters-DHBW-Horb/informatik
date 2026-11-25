# KI-Kontext: Kontrollzentrum

## Projekt

`Kontrollzentrum` ist eine Desktop-Anwendung mit Avalonia UI und C# auf .NET 9 (`net9.0`). Die Oberfläche ist als Kontrollzentrum für Tigerhunters angelegt und zeigt unter anderem einen Bereich für grSim-/SSL-Vision-Datenempfang. Verwendete zentrale Pakete sind Avalonia 12.2.0, CommunityToolkit.Mvvm 8.4.2 und Material.Icons.Avalonia 3.0.2.

Bei Änderungen nur dieses Projekt betrachten; `Kontrollzentrum_KI` ist ein separates Projekt. Der derzeitige Stand ist teilweise ein UI-Prototyp: angezeigte Netzwerk- und Empfangswerte sind noch nicht an ein Datenmodell oder einen Empfänger gebunden.

## Aufbau und Ablauf

- `Program.cs` startet die Avalonia-Desktop-Anwendung.
- `App.axaml` richtet Fluent2-Styles, Material-Icons und den `ViewLocator` ein.
- `App.axaml.cs` erzeugt das `MainWindow` und setzt einen `MainViewModel` als `DataContext`.
- `Views/MainWindow.axaml` enthält das Hauptlayout, die Seitenleiste, den Theme-Schalter und den Inhaltsbereich.
- `Views/MainWindow.axaml.cs` verwaltet Theme und Seitenwechsel. Die Übersichtsseite wird wiederverwendet; weitere Inhalte sind Platzhalter.
- `Views/ÜbersichtView.axaml` ist eine überwiegend statische Übersicht mit Empfangs-/Netzwerkfeldern.
- `ViewModels/ViewModelBase.cs` erbt von `ObservableObject`; `ViewModels/MainViewModel.cs` enthält aktuell nur die beobachtbare Eigenschaft `Greeting`.
- `Models/` ist im Projekt vorgesehen, enthält derzeit aber keine Model-Klassen.

## Aktuelle wichtige Datenstruktur

Es gibt im aktuellen Projektstand **keine implementierten fachlichen Datenmodelle, DTOs oder Datenbindungen für SSL-Vision**. Die folgenden Werte existieren nur als UI-Inhalte bzw. Platzhalter in `ÜbersichtView.axaml`:

| Bereich | Angezeigte Werte / Eingaben | Aktueller Stand |
|---|---|---|
| Datenempfang (grSim / SSL-Vision) | Zeit, Pakete/s, KB/s | Noch Platzhalter (`--`) |
| Kalman Filter | Ein/Aus | Toggle ist statisch, nicht an ein ViewModel gebunden |
| Verbindung | IP-Adresse, Port | UI-Eingaben; vorbefüllt mit `127.000.000.001` und `10020`, noch nicht an Logik gebunden |

Wenn echte Datenlogik ergänzt wird, sollten die fachlichen Empfangs-/Verbindungsdaten in Models und beobachtbare UI-Zustände in ViewModels liegen; XAML sollte diese über Bindings anzeigen statt Werte direkt zu setzen.

## Hinweise für Änderungen

- Nullable Reference Types sind aktiviert.
- Bestehende Navigation und Theme-Umschaltung liegen derzeit im Code-behind von `MainWindow`.
- Die Seitenleisten-Einträge und die `SelectedIndex`-Zuordnung in `MainWindow.axaml.cs` stimmen teilweise nicht inhaltlich überein; andere Menüindizes erzeugen Platzhalter.
- Die Oberfläche enthält noch nicht implementierte Beispielbereiche („Feld 3“ usw.); nicht als vorhandene Features oder Daten ansehen.
