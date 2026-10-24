import re
import sys

def patch_file(file_path):
    print(f"Applying strict 90-degree Logisim orthogonal routing to {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update handlePinClick to finalize with strict 90-degree orthogonal step
    old_pin_click_wire = """    const newWire: CircuitWire = {
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

    new_pin_click_wire = """    let finalWaypoints = wiringFrom.waypoints;
    if (wiringFrom.waypoints && wiringFrom.waypoints.length > 0) {
      const lastPt = wiringFrom.waypoints[wiringFrom.waypoints.length - 1];
      const targetPin = findPinById(toPinId);
      if (targetPin && (lastPt.x !== targetPin.x || lastPt.y !== targetPin.y)) {
        const midX = Math.round((lastPt.x + targetPin.x) / 2);
        finalWaypoints = [
          ...wiringFrom.waypoints,
          { x: midX, y: lastPt.y },
          { x: midX, y: targetPin.y },
        ];
      }
    }

    const newWire: CircuitWire = {
      id: `wire_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      fromCompId,
      fromPinId,
      toCompId,
      toPinId,
      value: 0,
      branchPoint: wiringFrom.branchPoint,
      sourceWireId: wiringFrom.sourceWireId,
      waypoints: finalWaypoints,
      isBus: defaultWireIsBus,
      bitWidth: defaultWireIsBus ? 4 : 1,
    };"""

    assert old_pin_click_wire in content, "Could not find old_pin_click_wire"
    content = content.replace(old_pin_click_wire, new_pin_click_wire)
    print("1. Updated handlePinClick to close waypoints with pure 90-degree orthogonal corners")

    # 2. Update wire path renderer in wires.map
    old_path_render = """              let pathD: string;
              if (wire.waypoints && wire.waypoints.length > 0) {
                let d = `M ${startPt.x},${startPt.y}`;
                for (const pt of wire.waypoints) {
                  d += ` L ${pt.x},${pt.y}`;
                }
                d += ` L ${endPt.x},${endPt.y}`;
                pathD = d;
              } else if (wireStyle === 'orthogonal') {"""

    new_path_render = """              let pathD: string;
              if (wire.waypoints && wire.waypoints.length > 0) {
                let d = `M ${startPt.x},${startPt.y}`;
                let prev = startPt;
                for (const pt of wire.waypoints) {
                  if (prev.x === pt.x) {
                    d += ` V ${pt.y}`;
                  } else if (prev.y === pt.y) {
                    d += ` H ${pt.x}`;
                  } else {
                    d += ` H ${pt.x} V ${pt.y}`;
                  }
                  prev = pt;
                }
                // Connect from last waypoint to endPt with 90° Manhattan step (NEVER diagonal!)
                if (prev.x === endPt.x) {
                  d += ` V ${endPt.y}`;
                } else if (prev.y === endPt.y) {
                  d += ` H ${endPt.x}`;
                } else {
                  const midX = Math.round((prev.x + endPt.x) / 2);
                  d += ` H ${midX} V ${endPt.y} H ${endPt.x}`;
                }
                pathD = d;
              } else if (wireStyle === 'orthogonal') {"""

    assert old_path_render in content, "Could not find old_path_render"
    content = content.replace(old_path_render, new_path_render)
    print("2. Updated renderWirePath to strictly eliminate all diagonal lines")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
