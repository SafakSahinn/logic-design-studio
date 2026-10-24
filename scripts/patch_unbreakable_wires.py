import re
import sys

def patch_file(file_path):
    print(f"Applying unbreakable clamped branch anchor resolver to {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace getWireStartPt with the unbreakable clamped resolver
    old_get_wire_start = """  // Helper: Get strictly welded start point for any wire (resolves T-junction branches dynamically)
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
  };"""

    new_get_wire_start = """  // Helper: Get strictly welded start point for any wire (unbreakable clamped branch resolver)
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

          const minY = Math.min(p1.y, p2.y);
          const maxY = Math.max(p1.y, p2.y);
          const bp = wire.branchPoint;

          // If parent wire has a vertical span, clamp strictly to parent's vertical segment:
          if (minY !== maxY) {
            const clampedY = Math.max(minY, Math.min(maxY, bp.y));
            return {
              x: parentElbowX,
              y: clampedY,
            };
          } else {
            // Parent wire is purely horizontal at y = p1.y
            const minX = Math.min(p1.x, p2.x);
            const maxX = Math.max(p1.x, p2.x);
            const clampedX = Math.max(minX, Math.min(maxX, bp.x));
            return {
              x: clampedX,
              y: p1.y,
            };
          }
        }
      }
      return wire.branchPoint;
    }
    const fromPin = findPinById(wire.fromPinId);
    return fromPin ? { x: fromPin.x, y: fromPin.y } : { x: 0, y: 0 };
  };"""

    assert old_get_wire_start in content, "Could not find old_get_wire_start"
    content = content.replace(old_get_wire_start, new_get_wire_start)
    print("1. Replaced getWireStartPt with unbreakable clamped resolver")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
