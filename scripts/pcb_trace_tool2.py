import Rhino
import System.Drawing
import math

def pcb_trace_tool_clean():
    # 
    gp1 = Rhino.Input.Custom.GetPoint()
    gp1.SetCommandPrompt("Click to start tracing PCB")
    if gp1.Get() != Rhino.Input.GetResult.Point:
        return

    points = [gp1.Point()]
    
    # 
    while True:
        gp2 = Rhino.Input.Custom.GetPoint()
        gp2.SetCommandPrompt("Press next point (Enter/ESC to stop)")
        
        # 
        def OnDynamicDraw(sender, e):
            # 1. 
            if len(points) > 1:
                for i in range(len(points) - 1):
                    e.Display.DrawLine(points[i], points[i+1], System.Drawing.Color.DarkGray, 2)
            
            # 2. 
            current_mouse_pt = e.CurrentPoint
            last_pt = points[-1]
            
            dx = current_mouse_pt.X - last_pt.X
            dy = current_mouse_pt.Y - last_pt.Y
            
            # 
            angle = math.atan2(dy, dx)
            angle_deg = math.degrees(angle)
            snapped_angle_deg = round(angle_deg / 45.0) * 45.0
            snapped_rad = math.radians(snapped_angle_deg)
            
            # 
            distance = math.sqrt(dx*dx + dy*dy)
            snapped_x = last_pt.X + distance * math.cos(snapped_rad)
            snapped_y = last_pt.Y + distance * math.sin(snapped_rad)
            snapped_pt = Rhino.Geometry.Point3d(snapped_x, snapped_y, last_pt.Z)
            
            # 
            e.Display.DrawLine(last_pt, snapped_pt, System.Drawing.Color.Red, 3)

        gp2.DynamicDraw += OnDynamicDraw
        
        # 
        res = gp2.Get()
        
        if res == Rhino.Input.GetResult.Point:
            click_pt = gp2.Point()
            last_pt = points[-1]
            dx = click_pt.X - last_pt.X
            dy = click_pt.Y - last_pt.Y
            
            angle_deg = math.degrees(math.atan2(dy, dx))
            snapped_rad = math.radians(round(angle_deg / 45.0) * 45.0)
            distance = math.sqrt(dx*dx + dy*dy)
            
            final_pt = Rhino.Geometry.Point3d(
                last_pt.X + distance * math.cos(snapped_rad),
                last_pt.Y + distance * math.sin(snapped_rad),
                last_pt.Z
            )
            
            # 
            points.append(final_pt)
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
        else:
            # 
            break

    # 3. 
    if len(points) > 1:
        polyline = Rhino.Geometry.Polyline(points)
        Rhino.RhinoDoc.ActiveDoc.Objects.AddPolyline(polyline)
        Rhino.RhinoDoc.ActiveDoc.Views.Redraw()

if __name__ == "__main__":
    pcb_trace_tool_clean()
