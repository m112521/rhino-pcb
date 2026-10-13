import Rhino
import System.Drawing
import math

SNAP_PIXELS = 12.0      # snap distance on screen, in pixels
GUIDE_LENGTH = 100000.0 # length of drawn guide lines (model units)

# Directions of the 4 guide lines (0, 45, 90, 135 degrees)
GUIDE_DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a)))
              for a in (0, 45, 90, 135)]


def collect_targets(doc):
    """Points we want to line up with: circle centers, point objects,
    polyline/line vertices already in the document."""
    targets = []
    for obj in doc.Objects:
        geo = obj.Geometry
        if isinstance(geo, Rhino.Geometry.Point):
            targets.append(geo.Location)
        elif isinstance(geo, Rhino.Geometry.Curve):
            ok, circle = geo.TryGetCircle()
            if ok:
                targets.append(circle.Center)
                continue
            ok, pl = geo.TryGetPolyline()
            if ok:
                for p in pl:
                    targets.append(p)
            else:
                targets.append(geo.PointAtStart)
                targets.append(geo.PointAtEnd)
    return targets


def cross(ax, ay, bx, by):
    return ax * by - ay * bx


def snap_point(raw, last, targets, viewport):
    """Constrain `raw` to 45/90 degree rays from `last`, then snap to guide
    lines through `targets`. Returns (point, guide) where guide is
    (target_point, (gx, gy)) or None."""
    dx = raw.X - last.X
    dy = raw.Y - last.Y
    dist = math.hypot(dx, dy)
    if dist < 1e-12:
        return Rhino.Geometry.Point3d(last), None

    # 1) angle snap (same as before)
    ang = round(math.degrees(math.atan2(dy, dx)) / 45.0) * 45.0
    rad = math.radians(ang)
    ux, uy = math.cos(rad), math.sin(rad)
    p = Rhino.Geometry.Point3d(last.X + dist * ux, last.Y + dist * uy, last.Z)

    # 2) tolerance in model units (pixels -> units at this location)
    # GetWorldToScreenScale has an `out` parameter -> returns (bool, value)
    res = viewport.GetWorldToScreenScale(p)
    if isinstance(res, tuple):
        ok, scale = res
    else:
        ok, scale = True, res
    tol = SNAP_PIXELS / scale if (ok and scale > 1e-12) else 0.0

    # 3) intersect our ray with every guide line through every target
    best, best_d, best_guide = None, tol, None
    for t in targets:
        for gx, gy in GUIDE_DIRS:
            den = cross(ux, uy, gx, gy)
            if abs(den) < 1e-9:
                continue  # ray parallel to this guide
            # last + u*s = t + g*k   ->   s = cross(t-last, g) / cross(u, g)
            s = cross(t.X - last.X, t.Y - last.Y, gx, gy) / den
            if s < 1e-9:
                continue  # behind or at the start point
            q = Rhino.Geometry.Point3d(last.X + ux * s, last.Y + uy * s, last.Z)
            d = q.DistanceTo(p)
            if d < best_d:
                best, best_d, best_guide = q, d, (t, (gx, gy))
    if best is not None:
        return best, best_guide
    return p, None


def pcb_trace_tool_clean():
    doc = Rhino.RhinoDoc.ActiveDoc

    gp1 = Rhino.Input.Custom.GetPoint()
    gp1.SetCommandPrompt("Click to start tracing PCB")
    if gp1.Get() != Rhino.Input.GetResult.Point:
        return

    points = [gp1.Point()]
    static_targets = collect_targets(doc)

    while True:
        gp2 = Rhino.Input.Custom.GetPoint()
        gp2.SetCommandPrompt("Press next point (Enter/ESC to stop)")

        def OnDynamicDraw(sender, e):
            # already placed segments
            for i in range(len(points) - 1):
                e.Display.DrawLine(points[i], points[i + 1],
                                   System.Drawing.Color.DarkGray, 2)

            last_pt = points[-1]
            targets = static_targets + points[:-1]  # own earlier vertices too
            snapped, guide = snap_point(e.CurrentPoint, last_pt, targets,
                                        e.Viewport)

            # guide line through the target we are snapped to
            if guide is not None:
                t, (gx, gy) = guide
                a = Rhino.Geometry.Point3d(t.X - gx * GUIDE_LENGTH,
                                           t.Y - gy * GUIDE_LENGTH, last_pt.Z)
                b = Rhino.Geometry.Point3d(t.X + gx * GUIDE_LENGTH,
                                           t.Y + gy * GUIDE_LENGTH, last_pt.Z)
                e.Display.DrawDottedLine(a, b, System.Drawing.Color.Cyan)
                e.Display.DrawPoint(snapped,
                                    Rhino.Display.PointStyle.RoundControlPoint,
                                    7, System.Drawing.Color.Cyan)

            # current segment
            e.Display.DrawLine(last_pt, snapped, System.Drawing.Color.Red, 3)

        gp2.DynamicDraw += OnDynamicDraw

        res = gp2.Get()

        if res == Rhino.Input.GetResult.Point:
            last_pt = points[-1]
            targets = static_targets + points[:-1]
            final_pt, _ = snap_point(gp2.Point(), last_pt, targets,
                                     gp2.View().ActiveViewport)
            points.append(final_pt)
            doc.Views.Redraw()
        else:
            break

    if len(points) > 1:
        polyline = Rhino.Geometry.Polyline(points)
        doc.Objects.AddPolyline(polyline)
        doc.Views.Redraw()


if __name__ == "__main__":
    pcb_trace_tool_clean()
