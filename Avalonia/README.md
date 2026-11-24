# Kontrollzentrum veröffentlichen

Das Projekt befindet sich in `Kontrollzentrum` und zielt derzeit auf .NET 9 (`net9.0`). Die folgenden Befehle im Terminal im Ordner `Avalonia` ausführen.

## Windows

Für einen normalen 64-Bit-Windows-PC:

```powershell
dotnet publish .\Kontrollzentrum\Kontrollzentrum.csproj -c Release -r win-x64 --self-contained true
```

Die Ausgabe liegt unter:

```text
Kontrollzentrum\bin\Release\net9.0\win-x64\publish\
```

Zum Starten `Kontrollzentrum.exe` aus diesem Ordner öffnen. Beim Weitergeben den gesamten `publish`-Ordner kopieren.

Mit `--self-contained true` ist die .NET-Runtime enthalten. Für ein kleineres, frameworkabhängiges Paket stattdessen `--self-contained false` verwenden. Auf dem Zielrechner muss dann die passende .NET-9-Runtime installiert sein.

Für eine einzelne Windows-Programmdatei:

```powershell
dotnet publish .\Kontrollzentrum\Kontrollzentrum.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true
```

## Ubuntu / Linux

Für die meisten 64-Bit-Ubuntu-PCs mit Intel- oder AMD-Prozessor:

```powershell
dotnet publish .\Kontrollzentrum\Kontrollzentrum.csproj -c Release -r linux-x64 --self-contained false
```

Der Befehl kann auch unter Windows ausgeführt werden. Er erzeugt Linux-Dateien, die Windows-Dateien sind nicht ausführbar. Die Ausgabe liegt unter:

```text
Kontrollzentrum\bin\Release\net9.0\linux-x64\publish\
```

Den gesamten `publish`-Ordner auf Ubuntu kopieren und dort im Terminal in den Ordner wechseln:

```bash
chmod +x Kontrollzentrum
./Kontrollzentrum
```

Bei `--self-contained false` muss auf Ubuntu die .NET-9-Runtime installiert sein. Alternativ kann die DLL mit `dotnet Kontrollzentrum.dll` gestartet werden.

### Einzelne Programmdatei

Mit `PublishSingleFile` werden die verwalteten Abhängigkeiten in eine ausführbare Datei gebündelt. Die `.pdb`-Datei enthält Debug-Informationen und ist zum Starten nicht erforderlich.

Frameworkabhängige Einzeldatei (benötigt .NET 9 auf Ubuntu):

```powershell
dotnet publish .\Kontrollzentrum\Kontrollzentrum.csproj -c Release -r linux-x64 --self-contained false -p:PublishSingleFile=true
```

Eigenständige Einzeldatei (größer, benötigt keine installierte .NET-Runtime):

```powershell
dotnet publish .\Kontrollzentrum\Kontrollzentrum.csproj -c Release -r linux-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true
```

Die ausführbare Datei heißt unter Linux `Kontrollzentrum` (ohne `.exe`). Zum Ausführen auf Ubuntu weiterhin `chmod +x Kontrollzentrum` und `./Kontrollzentrum` verwenden. Auch eine Einzeldatei benötigt die nativen Ubuntu-Bibliotheken für die grafische Oberfläche. Falls diese fehlen:

```bash
sudo apt update
sudo apt install -y libx11-6 libice6 libsm6 libfontconfig1
```

`linux-x64` passt zu den meisten Intel-/AMD-Rechnern. Für ARM64-Geräte stattdessen `linux-arm64` verwenden. Entsprechend gibt es für Windows beispielsweise `win-arm64`.
