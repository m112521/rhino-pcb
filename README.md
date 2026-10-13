# rhino-pcb
PCB Making tools for Rhino3D


How to create tracing tool:

1. Run in Rhino command: **EditPythonScript**.
2. Copy and paste code from **scripts/pcb_trace_tool2.py**.
3. Save as pcb_trace_tool2.py (copy path to this folder for step 6).
4. Mouse-Right-Click on an empty space Standard's tab -> **New Button**
5. Add button Image and text.
6. Add to **Command**:

```bash
_-RunPythonScript "C:\Path\to\folder\pcb_trace_tool2.py"
```
7. Enjoy:

<img width="1051" height="722" alt="rhino-trace" src="https://github.com/user-attachments/assets/fa8c4791-2f58-49d4-8af1-fe88229859f7" />

