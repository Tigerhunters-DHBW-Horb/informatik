using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Kontrollzentrum.ViewModels;
using System;
using Avalonia.Threading;

namespace Kontrollzentrum;

public class FieldRender : Control
{

    private readonly DispatcherTimer _timer;

    public FieldRender()
    {
        _timer = new DispatcherTimer
        {
            Interval = TimeSpan.FromMilliseconds(1000.0/60.0)
        };

        _timer.Tick += (_, _) => InvalidateVisual();

        AttachedToVisualTree += (_, _) => _timer.Start();
        DetachedFromVisualTree += (_, _) => _timer.Stop();
    }
    public override void Render(DrawingContext context)
    {
        base.Render(context);

        // Gesamten Bereich dunkel zeichnen
        context.DrawRectangle(
            Brushes.Green,
            null,
            new Rect(0, 0, Bounds.Width, Bounds.Height));

        // Größtes Spielfeld mit Seitenverhältnis 9:6 berechnen
        double scale = Math.Min(Bounds.Width / 9000.0, Bounds.Height / 6000.0);

        double fieldWidth = 9000 * scale;
        double fieldHeight = 6000 * scale;

        // Spielfeld im Control zentrieren
        double left = (Bounds.Width - fieldWidth) / 2;
        double top = (Bounds.Height - fieldHeight) / 2;

        var field = new Rect(left, top, fieldWidth, fieldHeight);

        // Grünes Spielfeld
        context.DrawRectangle(Brushes.Green, null, field);

        DrawFieldLines(context, field, scale);

        if (DataContext is not ÜbersichtViewModel viewModel)
            return;

        foreach (var robot in viewModel.Positions)
        {
            // Gleiche Orientierung wie bisher: positives X und Y
            // zeigen auf dem Bildschirm nach links bzw. nach oben.
            double x = field.Center.X - robot.X * scale;
            double y = field.Center.Y - robot.Y * scale;

            context.DrawEllipse(
                robot.TeamColor,
                null,
                new Point(x, y),
                8,
                8);
        }
    }

    private void DrawFieldLines(DrawingContext context, Rect field, double scale)
    {
        var line = new Pen(Brushes.White, 2);

        double left = field.Left;
        double top = field.Top;
        double right = field.Right;
        double bottom = field.Bottom;

        // Außenlinien
        context.DrawRectangle(null, line, field);

        // Mittellinie
        context.DrawLine(
            line,
            new Point(field.Center.X, top),
            new Point(field.Center.X, bottom));

        // Mittelkreis: Radius 500 mm
        context.DrawEllipse(
            null,
            line,
            field.Center,
            500 * scale,
            500 * scale);

        // Strafräume: 1000 mm tief und 2000 mm breit
        double penaltyDepth = 1000 * scale;
        double penaltyTop = field.Center.Y - 1000 * scale;
        double penaltyBottom = field.Center.Y + 1000 * scale;

        // Linker Strafraum
        context.DrawLine(line,
            new Point(left, penaltyTop),
            new Point(left + penaltyDepth, penaltyTop));
        context.DrawLine(line,
            new Point(left + penaltyDepth, penaltyTop),
            new Point(left + penaltyDepth, penaltyBottom));
        context.DrawLine(line,
            new Point(left + penaltyDepth, penaltyBottom),
            new Point(left, penaltyBottom));

        // Rechter Strafraum
        context.DrawLine(line,
            new Point(right, penaltyTop),
            new Point(right - penaltyDepth, penaltyTop));
        context.DrawLine(line,
            new Point(right - penaltyDepth, penaltyTop),
            new Point(right - penaltyDepth, penaltyBottom));
        context.DrawLine(line,
            new Point(right - penaltyDepth, penaltyBottom),
            new Point(right, penaltyBottom));
    }
}