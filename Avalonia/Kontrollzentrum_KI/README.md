# RoboCup Control & Monitoring Dashboard

Desktop dashboard for RoboCup SN/SSL systems. The application uses Avalonia UI on .NET 9 and follows MVVM.

## Implemented foundation

- Permanent navigation sidebar and Overview selected at startup.
- Overview status cards, system component view, and live mock activity.
- Separate grSim and SSN application areas.
- Scalable field view with moving mock robots.
- Robot overview cards with live position and orientation data.
- Central live message monitor.
- Sensors, Control, Data Analysis, Logs, and Settings areas.
- Mock communication adapters with bounded in-memory message history.
- MVVM models and an `ICommunicationAdapter` abstraction.

## Communication boundaries

No grSim or SSN wire protocol is assumed. `MockCommunicationAdapter` only generates test data and is isolated from real-adapter code.

The following specifications are still required before real communication is enabled:

- grSim transport and packet format
- SSN transport and packet format
- Sensor message schemas
- Robot command protocol and safety interlocks

## External dependencies

- Avalonia UI: cross-platform desktop UI framework.
- Avalonia Desktop: Linux and desktop platform integration.
- Avalonia Fluent2: application theme.
- Avalonia Inter Font: default UI typography.
- CommunityToolkit.Mvvm: observable properties and MVVM commands.

## Run

```bash
dotnet restore
dotnet run --project Kontrollzentrum.csproj
```
