# -*- coding: utf-8 -*-
import Rhino
import System.Drawing
import math

def pcb_trace_tool_orthogonal_guides():
    doc = Rhino.RhinoDoc.ActiveDoc
    
    # Save the user's original object snap settings to follow best practices
    saved_osnap_modes = Rhino.ApplicationSettings.ModelAidSettings.OsnapModes
    saved_osnap_on = Rhino.ApplicationSettings.ModelAidSettings.Osnap
    
    try:
        # Automatically enable standard snaps so user can interact with layout
        Rhino.ApplicationSettings.ModelAidSettings.Osnap = True
        Rhino.ApplicationSettings.ModelAidSettings.OsnapModes |= Rhino.ApplicationSettings.OsnapModes.Point

        # Helper function to gather all circle centers in the document at the start
        def get_all_circle_centers():
            settings = Rhino.DocObjects.ObjectEnumeratorSettings()
            settings.ObjectTypeFilter = Rhino.DocObjects.ObjectType.Curve
            curves = doc.Objects.GetObjectList(settings)
            
            centers = []
            for obj in curves:
                geom = obj.Geometry
                if isinstance(geom, Rhino.Geometry.Curve):
                    is_circle, circle = geom.TryGetCircle()
                    if is_circle:
                        centers.append(circle.Center)
            return centers

        circle_centers = get_all_circle_centers()
        
        # REMOVED DIAGONALS: Only Horizontal (0) and Vertical (90) guide lines remain
        guide_angles = [0.0, 90.0]

        # Shared guide rendering logic
        def draw_translucent_guides(display):
            guide_color = System.Drawing.Color.FromArgb(45, 0, 255, 255) # Translucent Cyan
            for center in circle_centers:
                for angle_deg in guide_angles:
                    rad = math.radians(angle_deg)
                    dx = 10000.0 * math.cos(rad)
                    dy = 10000.0 * math.sin(rad)
                    
                    p1 = Rhino.Geometry.Point3d(center.X - dx, center.Y - dy, center.Z)
                    p2 = Rhino.Geometry.Point3d(center.X + dx, center.Y + dy, center.Z)
                    display.DrawLine(p1, p2, guide_color, 1)

        # 1. First Point Selection
        gp1 = Rhino.Input.Custom.GetPoint()
        gp1.SetCommandPrompt("Click to start tracing PCB")
        gp1.PermitObjectSnap(True)
        
        def OnDynamicDraw1(sender, e):
            draw_translucent_guides(e.Display)
            
        gp1.DynamicDraw += OnDynamicDraw1
        if gp1.Get() != Rhino.Input.GetResult.Point:
            return

        points = [gp1.Point()]
        
        # 2. Subsequent Points Loop
        while True:
            gp2 = Rhino.Input.Custom.GetPoint()
            gp2.SetCommandPrompt("Press next point (Enter/ESC to stop)")
            gp2.PermitObjectSnap(True)
            
            # --- PCB HYBRID SNAP & ANGLE MATH ---
            def calculate_smart_point(mouse_pt, last_pt, snap_radius=2.0):
                best_guide_pt = None
                min_dist = snap_radius
                
                # Check closeness only to horizontal and vertical lines crossing circle centers
                for center in circle_centers:
                    for angle_deg in guide_angles:
                        rad = math.radians(angle_deg)
                        direction = Rhino.Geometry.Vector3d(math.cos(rad), math.sin(rad), 0)
                        infinite_line = Rhino.Geometry.Line(center, direction)
                        
                        # Project mouse onto the infinite guide line (False = treated as infinite)
                        proj_pt = infinite_line.ClosestPoint(mouse_pt, False)
                        dist = mouse_pt.DistanceTo(proj_pt)
                        
                        if dist < min_dist:
                            min_dist = dist
                            best_guide_pt = proj_pt
                            
                # Priority 1: If mouse tracks near an orthogonal circle axis, snap directly to it
                if best_guide_pt:
                    return best_guide_pt
                
                # Priority 2: In free space, enforce 45/90 degree locking relative to the last segment
                dx = mouse_pt.X - last_pt.X
                dy = mouse_pt.Y - last_pt.Y
                angle = math.atan2(dy, dx)
                angle_deg = math.degrees(angle)
                snapped_angle_deg = round(angle_deg / 45.0) * 45.0
                snapped_rad = math.radians(snapped_angle_deg)
                
                distance = math.sqrt(dx*dx + dy*dy)
                return Rhino.Geometry.Point3d(
                    last_pt.X + distance * math.cos(snapped_rad),
                    last_pt.Y + distance * math.sin(snapped_rad),
                    last_pt.Z
                )

            def OnDynamicDraw2(sender, e):
                draw_translucent_guides(e.Display)
                
                # Draw already placed permanent segments
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        e.Display.DrawLine(points[i], points[i+1], System.Drawing.Color.DarkGray, 2)
                
                current_mouse_pt = e.CurrentPoint
                last_pt = points[-1]
                
                # Calculate final snapped preview point
                snapped_pt = calculate_smart_point(current_mouse_pt, last_pt)
                
                # Draw the dynamic preview trace line
                e.Display.DrawLine(last_pt, snapped_pt, System.Drawing.Color.Red, 3)

            gp2.DynamicDraw += OnDynamicDraw2
            res = gp2.Get()
            
            if res == Rhino.Input.GetResult.Point:
                click_pt = gp2.Point()
                last_pt = points[-1]
                
                # Bake the same calculated logic into the permanent vertex array
                final_pt = calculate_smart_point(click_pt, last_pt)
                
                points.append(final_pt)
                doc.Views.Redraw()
            else:
                break

        # 3. Final Step: Bake exactly ONE clean polyline into the document
        if len(points) > 1:
            polyline = Rhino.Geometry.Polyline(points)
            doc.Objects.AddPolyline(polyline)
            doc.Views.Redraw()

    finally:
        # Safely revert the user's original object snaps on finish or ESC
        Rhino.ApplicationSettings.ModelAidSettings.OsnapModes = saved_osnap_modes
        Rhino.ApplicationSettings.ModelAidSettings.Osnap = saved_osnap_on
        doc.Views.Redraw()

if __name__ == "__main__":
    pcb_trace_tool_orthogonal_guides()
