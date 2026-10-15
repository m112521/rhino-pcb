# Rhino-PCB
PCB tracing tools for Rhino3D


How to create tracing tool:

1. Run in Rhino command: **EditPythonScript**.
2. Copy and paste code from **scripts/tracing_tool3.py**.
3. Save as pcb_trace_tool2.py (copy path to this folder for step 6).
4. Mouse-Right-Click on an empty space Standard's tab -> **New Button**
5. Add button Image and text.
6. Add to **Command**:

```bash
_-RunPythonScript "C:\Path\to\folder\tracing_tool3.py"
```
7. Enjoy:

<img width="1663" height="788" alt="tracing" src="https://github.com/user-attachments/assets/cfdeb0e7-d874-485a-bfe1-49be55d85a06" />


