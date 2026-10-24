import re
import sys

def patch_logisim(file_path):
    print(f"Applying Logisim-grade wiring engine to {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update CircuitWire type in src/types/circuit.ts if needed, but let's check what's in LogisimSimulator
    # Ensure CircuitWire interface or usages support sourceWireId and waypoints
    
    # 2. Add dynamic branch anchor resolver helper
    helper_code = """
  // Helper: Get strictly welded start point for any wire (resolves T-junction branches dynamically)
  const getWireStartPt = (wire: CircuitWire): { x: number; y: number } => {
    if (wire.branchPoint) {
      // Find parent wire in the same electrical net (same fromPinId)
      const parentWire = wires.find(
        (w) => w.id !== wire.id && w.fromPinId === wire.fromPinId && (!w.branchPoint || w.id === wire.sourceWireId)
      );
      if (parentWire) {
        const fromPin = findPinById(parentWire.fromPinId);
        const toPin = findPinById(parentWire.toPinId);
        if (fromPin && toPin) {
          const p1 = parentWire.branchPoint || { x: fromPin.x, y: fromPin.y };
          const p2 = { x: toPin.x, y: toPin.y };
          const defaultMidX = Math.round((p1.x + p2.x) / 2);
          const parentElbowX = parentWire.elbowX !== undefined ? parentWire.elbowX : defaultMidX;

          // If branchPoint was tapped onto or near parent's vertical segment:
          // Snap its X directly to parent's current elbowX so it is mathematically impossible to detach!
          const minY = Math.min(p1.y, p2.y) - 6;
          const maxY = Math.max(p1.y, p2.y) + 6;
          if (wire.branchPoint.y >= minY && wire.branchPoint.y <= maxY) {
            return {
              x: parentElbowX,
              y: wire.branchPoint.y,
            };
          }
          // If tapped on parent's start horizontal segment:
          return {
            x: wire.branchPoint.x,
            y: p1.y,
          };
        }
      }
      return wire.branchPoint;
    }
    const fromPin = findPinById(wire.fromPinId);
    return fromPin ? { x: fromPin.x, y: fromPin.y } : { x: 0, y: 0 };
  };
"""

    # Check where getClosestPointOnOrthogonalWire is defined and inject helper before it
    anchor = "  // Helper: Find closest orthogonal projection point on a Manhattan wire path"
    assert anchor in content, "Could not find getClosestPointOnOrthogonalWire anchor"
    if "const getWireStartPt =" not in content:
        content = content.replace(anchor, helper_code + "\n" + anchor)
        print("1. Injected getWireStartPt dynamic branch anchor resolver")

    # 3. Update wire renderer in wires.map:
    # Replace `const startPt = wire.branchPoint || { x: fromPin.x, y: fromPin.y };` with `const startPt = getWireStartPt(wire);`
    old_start_pt = "const startPt = wire.branchPoint || { x: fromPin.x, y: fromPin.y };"
    new_start_pt = "const startPt = getWireStartPt(wire);"
    assert old_start_pt in content, "Could not find old_start_pt"
    content = content.replace(old_start_pt, new_start_pt)
    print("2. Updated startPt calculation to use getWireStartPt")

    # Also update solder junction dot to use getWireStartPt:
    old_dot = """                  {/* Solder Junction Dot for Mid-Wire T-Junction */}
                  {wire.branchPoint && (
                    <g className="pointer-events-none">
                      <circle
                        cx={wire.branchPoint.x}
                        cy={wire.branchPoint.y}
                        r={wire.isBus ? 6 : 4.5}
                        fill={isHigh ? '#16a34a' : wire.isBus ? '#2563eb' : '#475569'}
                        stroke="#ffffff"
                        strokeWidth={1.5}
                      />
                    </g>
                  )}"""

    new_dot = """                  {/* Solder Junction Dot for Mid-Wire T-Junction - Strictly welded to startPt */}
                  {wire.branchPoint && (
                    <g className="pointer-events-none">
                      <circle
                        cx={startPt.x}
                        cy={startPt.y}
                        r={wire.isBus ? 6 : 4.5}
                        fill={isHigh ? '#16a34a' : wire.isBus ? '#2563eb' : '#475569'}
                        stroke="#ffffff"
                        strokeWidth={1.5}
                      />
                    </g>
                  )}"""

    assert old_dot in content, "Could not find old_dot"
    content = content.replace(old_dot, new_dot)
    print("3. Updated solder junction dot cx, cy to use welded startPt")

    # 4. In handleCanvasMouseMove:
    # When draggingWireJoint moves elbowX:
    # Update both the target wire AND all branch wires in the net
    old_joint_drag = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
    if (activeDragJoint) {
      const snappedX = snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x);
      setWires((prev) => {
        const targetWire = prev.find((w) => w.id === activeDragJoint.wireId);
        if (!targetWire) return prev;
        const p1 = targetWire.branchPoint || findPinById(targetWire.fromPinId);
        const p2 = findPinById(targetWire.toPinId);
        const oldMidX = targetWire.elbowX !== undefined ? targetWire.elbowX : (p1 && p2 ? Math.round((p1.x + p2.x) / 2) : snappedX);

        return prev.map((w) => {
          if (w.id === activeDragJoint.wireId) {
            return { ...w, elbowX: snappedX };
          }
          // Follow child branch wires tapped on this vertical segment
          if (w.branchPoint && w.fromCompId === targetWire.fromCompId && Math.abs(w.branchPoint.x - oldMidX) <= 6) {
            return {
              ...w,
              branchPoint: {
                ...w.branchPoint,
                x: snappedX,
              },
            };
          }
          return w;
        });
      });
      return;
    }"""

    new_joint_drag = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
    if (activeDragJoint) {
      const snappedX = snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x);
      setWires((prev) => {
        const targetWire = prev.find((w) => w.id === activeDragJoint.wireId);
        if (!targetWire) return prev;

        return prev.map((w) => {
          if (w.id === activeDragJoint.wireId) {
            return { ...w, elbowX: snappedX };
          }
          // ANY branch wire in the same electrical net (same fromPinId or sourceWireId) follows elbowX
          if (w.branchPoint && (w.fromPinId === targetWire.fromPinId || w.sourceWireId === targetWire.id)) {
            return {
              ...w,
              branchPoint: {
                ...w.branchPoint,
                x: snappedX,
              },
            };
          }
          return w;
        });
      });
      return;
    }"""

    assert old_joint_drag in content, "Could not find old_joint_drag"
    content = content.replace(old_joint_drag, new_joint_drag)
    print("4. Updated activeDragJoint to unconditionally weld all branch wires in the net")

    # 5. Enable Logisim-style Waypoints while drawing wire:
    # When user clicks canvas while wiringFrom is active, add waypoint!
    old_canvas_mouse_down = """    // Normal left-click on canvas background starts box selection
    if (e.button === 0 && !wiringFrom) {"""

    new_canvas_mouse_down = """    // Logisim-style interactive wiring: Clicking canvas while wiring places a corner waypoint!
    if (e.button === 0 && wiringFrom) {
      const coords = getCanvasCoords(e);
      const snapped = {
        x: snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x),
        y: snapToGrid ? Math.round(coords.y / 10) * 10 : Math.round(coords.y),
      };
      setWiringFrom((prev) => (prev ? {
        ...prev,
        waypoints: [...(prev.waypoints || []), snapped],
      } : null));
      return;
    }

    // Normal left-click on canvas background starts box selection
    if (e.button === 0 && !wiringFrom) {"""

    assert old_canvas_mouse_down in content, "Could not find old_canvas_mouse_down"
    content = content.replace(old_canvas_mouse_down, new_canvas_mouse_down)
    print("5. Added Logisim-style canvas waypoint click handler")

    # 6. Update wiringFrom state type definition to include waypoints and sourceWireId
    old_wiring_state = """  const [wiringFrom, setWiringFrom] = useState<{
    compId: string;
    pinId: string;
    pinType: 'input' | 'output';
    x: number;
    y: number;
    branchPoint?: { x: number; y: number };
  } | null>(null);"""

    new_wiring_state = """  const [wiringFrom, setWiringFrom] = useState<{
    compId: string;
    pinId: string;
    pinType: 'input' | 'output';
    x: number;
    y: number;
    branchPoint?: { x: number; y: number };
    sourceWireId?: string;
    waypoints?: { x: number; y: number }[];
  } | null>(null);"""

    assert old_wiring_state in content, "Could not find old_wiring_state"
    content = content.replace(old_wiring_state, new_wiring_state)
    print("6. Updated wiringFrom state type definition")

    # 7. Update dynamic active wire preview renderer to draw waypoints
    old_preview = """            {/* Dynamic Active Wire being drawn */}
            {wiringFrom && (
              <path
                d={
                  wireStyle === 'orthogonal'
                    ? `M ${wiringFrom.x},${wiringFrom.y} H ${Math.round((wiringFrom.x + mousePos.x) / 2)} V ${mousePos.y} H ${mousePos.x}`
                    : `M ${wiringFrom.x},${wiringFrom.y} C ${wiringFrom.x + 40},${wiringFrom.y} ${mousePos.x - 40},${mousePos.y} ${mousePos.x},${mousePos.y}`
                }
                fill="none"
                stroke="#3b82f6"
                strokeWidth={2.5}
                strokeDasharray="5,5"
                className="pointer-events-none"
              />
            )}"""

    new_preview = """            {/* Dynamic Active Wire being drawn (supports Logisim interactive waypoints) */}
            {wiringFrom && (
              <g className="pointer-events-none">
                <path
                  d={(() => {
                    const start = { x: wiringFrom.x, y: wiringFrom.y };
                    const current = mousePos;
                    if (wiringFrom.waypoints && wiringFrom.waypoints.length > 0) {
                      let d = `M ${start.x},${start.y}`;
                      for (const pt of wiringFrom.waypoints) {
                        d += ` L ${pt.x},${pt.y}`;
                      }
                      const lastPt = wiringFrom.waypoints[wiringFrom.waypoints.length - 1];
                      const midX = Math.round((lastPt.x + current.x) / 2);
                      d += ` H ${midX} V ${current.y} H ${current.x}`;
                      return d;
                    }
                    const midX = Math.round((start.x + current.x) / 2);
                    return wireStyle === 'orthogonal'
                      ? `M ${start.x},${start.y} H ${midX} V ${current.y} H ${current.x}`
                      : `M ${start.x},${start.y} C ${start.x + 40},${start.y} ${current.x - 40},${current.y} ${current.x},${current.y}`;
                  })()}
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  strokeDasharray="5,5"
                />
                {wiringFrom.waypoints?.map((pt, idx) => (
                  <circle key={idx} cx={pt.x} cy={pt.y} r={4} fill="#3b82f6" stroke="#ffffff" strokeWidth={1.5} />
                ))}
              </g>
            )}"""

    assert old_preview in content, "Could not find old_preview"
    content = content.replace(old_preview, new_preview)
    print("7. Updated active wire preview to render waypoints")

    # 8. When creating wire from wiringFrom in handlePinClick, preserve sourceWireId and waypoints:
    old_new_wire = """    const newWire: CircuitWire = {
      id: `wire_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      fromCompId,
      fromPinId,
      toCompId,
      toPinId,
      value: 0,
      branchPoint: wiringFrom.branchPoint,
      isBus: defaultWireIsBus,
      bitWidth: defaultWireIsBus ? 4 : 1,
    };"""

    new_new_wire = """    const newWire: CircuitWire = {
      id: `wire_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      fromCompId,
      fromPinId,
      toCompId,
      toPinId,
      value: 0,
      branchPoint: wiringFrom.branchPoint,
      sourceWireId: wiringFrom.sourceWireId,
      waypoints: wiringFrom.waypoints,
      isBus: defaultWireIsBus,
      bitWidth: defaultWireIsBus ? 4 : 1,
    };"""

    assert old_new_wire in content, "Could not find old_new_wire"
    content = content.replace(old_new_wire, new_new_wire)
    print("8. Updated newWire creation to preserve sourceWireId and waypoints")

    # 9. Support waypoints in wire path renderer in wires.map
    old_path_render = """              let pathD: string;
              if (wireStyle === 'orthogonal') {
                pathD = `M ${startPt.x},${startPt.y} H ${effectiveMidX} V ${endPt.y} H ${endPt.x}`;
              } else {
                const dx = Math.abs(endPt.x - startPt.x) * 0.5;
                pathD = `M ${startPt.x},${startPt.y} C ${startPt.x + dx},${startPt.y} ${endPt.x - dx},${endPt.y} ${endPt.x},${endPt.y}`;
              }"""

    new_path_render = """              let pathD: string;
              if (wire.waypoints && wire.waypoints.length > 0) {
                let d = `M ${startPt.x},${startPt.y}`;
                for (const pt of wire.waypoints) {
                  d += ` L ${pt.x},${pt.y}`;
                }
                d += ` L ${endPt.x},${endPt.y}`;
                pathD = d;
              } else if (wireStyle === 'orthogonal') {
                pathD = `M ${startPt.x},${startPt.y} H ${effectiveMidX} V ${endPt.y} H ${endPt.x}`;
              } else {
                const dx = Math.abs(endPt.x - startPt.x) * 0.5;
                pathD = `M ${startPt.x},${startPt.y} C ${startPt.x + dx},${startPt.y} ${endPt.x - dx},${endPt.y} ${endPt.x},${endPt.y}`;
              }"""

    assert old_path_render in content, "Could not find old_path_render"
    content = content.replace(old_path_render, new_path_render)
    print("9. Updated wire path rendering to support arbitrary waypoints")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_logisim(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
