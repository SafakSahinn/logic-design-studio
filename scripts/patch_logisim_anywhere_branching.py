import re
import sys

def patch_file(file_path):
    print(f"Applying Logisim anywhere-branching & removing curved wires on {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove the curved wire button from top control bar
    old_btn = """          <button
            onClick={() => setWireStyle(wireStyle === 'orthogonal' ? 'bezier' : 'orthogonal')}
            className={`h-8 px-2.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              wireStyle === 'orthogonal'
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-slate-100 border-slate-200 text-slate-700'
            }`}
            title="Kablo Yönlendirme Stili (90° Manhattan vs Eğik)"
          >
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>{wireStyle === 'orthogonal' ? 'Dik Açılı Hat' : 'Eğik Hat'}</span>
          </button>"""

    new_btn = """          {/* 90° Strict Logisim Orthogonal CAD Wire Mode (Curved mode permanently removed) */}
          <div
            className="h-8 px-2.5 rounded-lg border border-blue-200 bg-blue-50/80 text-blue-700 text-xs font-semibold flex items-center gap-1.5 select-none"
            title="Logisim 90° Manhattan Standart Hat Modu"
          >
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>90° Logisim Hatları</span>
          </div>"""

    if old_btn in content:
        content = content.replace(old_btn, new_btn)
        print("1. Removed curved wire toggle button from web toolbar")

    # 2. Add wireDragStartRef for instant drag-to-branch anywhere on wire
    ref_anchor = "  const draggingWireJointRef = useRef<{"
    new_ref = """  // Wire drag-to-branch state (pull branch from anywhere on wire like Logisim)
  const wireDragStartRef = useRef<{
    wireId: string;
    fromCompId: string;
    fromPinId: string;
    tap: { x: number; y: number };
    startClientX: number;
    startClientY: number;
    didDrag: boolean;
  } | null>(null);
"""
    if "wireDragStartRef" not in content:
        content = content.replace(ref_anchor, new_ref + "\n" + ref_anchor)
        print("2. Added wireDragStartRef for drag-to-branch anywhere on wire")

    # 3. In handleCanvasMouseMove: check if user started dragging from anywhere on a wire:
    old_mouse_move_head = """    const coords = getCanvasCoords(e);
    setMousePos(coords);"""

    new_mouse_move_head = """    const coords = getCanvasCoords(e);
    setMousePos(coords);

    // Instant Logisim-style pull branch wire from anywhere on wire
    if (wireDragStartRef.current && !wiringFrom && !draggingCompId && !draggingWireJointRef.current) {
      const dx = Math.abs(e.clientX - wireDragStartRef.current.startClientX);
      const dy = Math.abs(e.clientY - wireDragStartRef.current.startClientY);
      if (dx > 4 || dy > 4) {
        wireDragStartRef.current.didDrag = true;
        const wInfo = wireDragStartRef.current;
        setWiringFrom({
          compId: wInfo.fromCompId,
          pinId: wInfo.fromPinId,
          pinType: 'output',
          x: wInfo.tap.x,
          y: wInfo.tap.y,
          branchPoint: wInfo.tap,
          sourceWireId: wInfo.wireId,
        });
        wireDragStartRef.current = null;
        return;
      }
    }"""

    assert old_mouse_move_head in content, "Could not find old_mouse_move_head"
    content = content.replace(old_mouse_move_head, new_mouse_move_head)
    print("3. Injected instant drag-to-branch check into handleCanvasMouseMove")

    # 4. In handleCanvasMouseUp: clean up wireDragStartRef
    old_mouse_up = "  const handleCanvasMouseUp = (e: React.MouseEvent) => {"
    new_mouse_up = """  const handleCanvasMouseUp = (e: React.MouseEvent) => {
    wireDragStartRef.current = null;"""
    content = content.replace(old_mouse_up, new_mouse_up)
    print("4. Updated handleCanvasMouseUp to clear wireDragStartRef")

    # 5. Update wire hitbox and hover indicator in wires.map:
    # Allow pulling branch from anywhere on wire, and gliding tap dot on hover!
    old_hover_button = """                  {/* Unselected Wire Hover: Clean Single T-Junction Branch Button */}
                  {!isSelected && hoveredWireId === wire.id && !wiringFrom && !draggingWireJoint && (
                    <g
                      transform={`translate(${midX}, ${midY})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: midX, y: midY }, effectiveMidX);
                        setWiringFrom({
                          compId: wire.fromCompId,
                          pinId: wire.fromPinId,
                          pinType: 'output',
                          x: tap.x,
                          y: tap.y,
                          branchPoint: tap,
                        });
                        setSelectedWireIds([]);
                      }}
                      className="cursor-pointer"
                    >
                      <circle
                        cx={0}
                        cy={0}
                        r={11}
                        fill="#2563eb"
                        stroke="#ffffff"
                        strokeWidth={1.5}
                        filter="drop-shadow(0 2px 4px rgba(0,0,0,0.25))"
                      />
                      <path
                        d="M -4,0 L 4,0 M 0,-4 L 0,4"
                        stroke="#ffffff"
                        strokeWidth={2}
                        strokeLinecap="round"
                      />
                      <title>Kablo Ortasından T-Kavşak Çıkar (Branch Wire)</title>
                    </g>
                  )}"""

    new_hover_button = """                  {/* Logisim-Style Dynamic Anywhere-Branching Indicator: Follows mouse cursor along wire */}
                  {!isSelected && hoveredWireId === wire.id && !wiringFrom && !draggingWireJoint && (() => {
                    const tap = getClosestPointOnOrthogonalWire(startPt, endPt, mousePos, effectiveMidX);
                    return (
                      <g
                        transform={`translate(${tap.x}, ${tap.y})`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setWiringFrom({
                            compId: wire.fromCompId,
                            pinId: wire.fromPinId,
                            pinType: 'output',
                            x: tap.x,
                            y: tap.y,
                            branchPoint: tap,
                            sourceWireId: wire.id,
                          });
                          setSelectedWireIds([]);
                        }}
                        className="cursor-pointer group/tapGlide"
                      >
                        <circle
                          cx={0}
                          cy={0}
                          r={10.5}
                          fill="#2563eb"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          filter="drop-shadow(0 2px 5px rgba(0,0,0,0.3))"
                        />
                        <path
                          d="M -3.5,0 L 3.5,0 M 0,-3.5 L 0,3.5"
                          stroke="#ffffff"
                          strokeWidth={2}
                          strokeLinecap="round"
                        />
                        <title>Bu Noktadan Kablo Çek (T-Kavşak / Sürükle veya Tıkla)</title>
                      </g>
                    );
                  })()}"""

    assert old_hover_button in content, "Could not find old_hover_button"
    content = content.replace(old_hover_button, new_hover_button)
    print("5. Upgraded hover branch button to follow mouse anywhere along wire (Logisim style)")

    # 6. Update wire hitbox onMouseDown to record drag start from anywhere
    old_hitbox = """                  {/* Thick transparent hover hitbox */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke="transparent"
                    strokeWidth={18}
                  />"""

    new_hitbox = """                  {/* Thick transparent hover hitbox (supports clicking or dragging from anywhere to branch) */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke="transparent"
                    strokeWidth={18}
                    onMouseDown={(e) => {
                      if (e.button === 0 && !wiringFrom) {
                        const tap = getClosestPointOnOrthogonalWire(startPt, endPt, mousePos, effectiveMidX);
                        wireDragStartRef.current = {
                          wireId: wire.id,
                          fromCompId: wire.fromCompId,
                          fromPinId: wire.fromPinId,
                          tap,
                          startClientX: e.clientX,
                          startClientY: e.clientY,
                          didDrag: false,
                        };
                      }
                    }}
                  />"""

    assert old_hitbox in content, "Could not find old_hitbox"
    content = content.replace(old_hitbox, new_hitbox)
    print("6. Enabled onMouseDown on wire hitbox to pull branch wire from anywhere by dragging")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
