import re
import sys

def patch_file(file_path):
    print(f"Applying Logisim 90-degree orthogonal & freeform wiring to {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update draggingWireJoint type
    old_drag_state = """  // Manhattan wire corner / segment dragging state
  const [draggingWireJoint, setDraggingWireJoint] = useState<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment';
  } | null>(null);
  const draggingWireJointRef = useRef<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment';
  } | null>(null);"""

    new_drag_state = """  // Manhattan wire corner / segment dragging state (supports waypoints)
  const [draggingWireJoint, setDraggingWireJoint] = useState<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment' | 'waypoint';
    index?: number;
  } | null>(null);
  const draggingWireJointRef = useRef<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment' | 'waypoint';
    index?: number;
  } | null>(null);"""

    assert old_drag_state in content, "Could not find old_drag_state"
    content = content.replace(old_drag_state, new_drag_state)
    print("1. Updated draggingWireJoint state type to support waypoints")

    # 2. Update handleCanvasMouseMove to drag waypoints
    old_active_drag = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
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

    new_active_drag = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
    if (activeDragJoint) {
      const snappedX = snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x);
      const snappedY = snapToGrid ? Math.round(coords.y / 10) * 10 : Math.round(coords.y);
      setWires((prev) => {
        const targetWire = prev.find((w) => w.id === activeDragJoint.wireId);
        if (!targetWire) return prev;

        return prev.map((w) => {
          if (w.id === activeDragJoint.wireId) {
            // Dragging an interactive waypoint corner:
            if (activeDragJoint.type === 'waypoint' && activeDragJoint.index !== undefined && w.waypoints) {
              const updatedWps = [...w.waypoints];
              updatedWps[activeDragJoint.index] = { x: snappedX, y: snappedY };
              return { ...w, waypoints: updatedWps };
            }
            return { ...w, elbowX: snappedX };
          }
          // ANY branch wire in the same electrical net follows elbowX
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

    assert old_active_drag in content, "Could not find old_active_drag"
    content = content.replace(old_active_drag, new_active_drag)
    print("2. Updated activeDragJoint in handleCanvasMouseMove to move waypoints")

    # 3. Update canvas click during wiringFrom to support Logisim 90-degree orthogonal corner snapping AND freeform
    old_canvas_click = """    // Logisim-style interactive wiring: Clicking canvas while wiring places a corner waypoint!
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
    }"""

    new_canvas_click = """    // Logisim-style interactive wiring: Clicking canvas while wiring places 90° orthogonal corner or freeform waypoint!
    if (e.button === 0 && wiringFrom) {
      const coords = getCanvasCoords(e);
      const snapped = {
        x: snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x),
        y: snapToGrid ? Math.round(coords.y / 10) * 10 : Math.round(coords.y),
      };

      setWiringFrom((prev) => {
        if (!prev) return null;
        const lastPt = prev.waypoints && prev.waypoints.length > 0 ? prev.waypoints[prev.waypoints.length - 1] : { x: prev.x, y: prev.y };
        
        // If Shift is pressed: Freeform direct point
        // If normal (default): Strictly 90-degree orthogonal Logisim corner (Horizontal then Vertical)
        if (e.shiftKey) {
          return {
            ...prev,
            waypoints: [...(prev.waypoints || []), snapped],
          };
        } else {
          // Logisim 90° corner
          const cornerPt = { x: snapped.x, y: lastPt.y };
          const newWps = (lastPt.x !== snapped.x && lastPt.y !== snapped.y)
            ? [...(prev.waypoints || []), cornerPt, snapped]
            : [...(prev.waypoints || []), snapped];
          return {
            ...prev,
            waypoints: newWps,
          };
        }
      });
      return;
    }"""

    assert old_canvas_click in content, "Could not find old_canvas_click"
    content = content.replace(old_canvas_click, new_canvas_click)
    print("3. Updated canvas click to place 90° Logisim orthogonal corners (or Shift for freeform)")

    # 4. Render draggable handles for waypoints on selected wire
    old_handles_block = """                  {/* Manhattan Wire Joint Corner & Segment Drag Handles (Only on Selected Wire) */}
                  {wireStyle === 'orthogonal' && isSelected && !wiringFrom && (
                    <g>
                      {/* Midpoint Handle on vertical segment - Translated group ensures rock-solid 0,0 center */}
                      <g
                        transform={`translate(${effectiveMidX}, ${midY})`}
                        className="cursor-ew-resize group/joint"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          draggingWireJointRef.current = { wireId: wire.id, type: 'segment' };
                          setDraggingWireJoint({ wireId: wire.id, type: 'segment' });
                        }}
                        onDoubleClick={(e) => {
                          e.stopPropagation();
                          setWires((prev) =>
                            prev.map((w) => (w.id === wire.id ? { ...w, elbowX: undefined, jointOffset: undefined } : w))
                          );
                        }}
                      >
                        {/* 36px wide hit target guaranteed to capture pointer events */}
                        <circle
                          cx={0}
                          cy={0}
                          r={18}
                          fill="#000000"
                          fillOpacity={0}
                          pointerEvents="all"
                        />
                        {/* Crisp visible handle dot with zero coordinate shift */}
                        <circle
                          cx={0}
                          cy={0}
                          r={7}
                          fill="#2563eb"
                          stroke="#ffffff"
                          strokeWidth={2}
                          filter="drop-shadow(0 2px 5px rgba(0,0,0,0.35))"
                          pointerEvents="none"
                        />
                        {/* Inner white dot */}
                        <circle
                          cx={0}
                          cy={0}
                          r={2.5}
                          fill="#ffffff"
                          pointerEvents="none"
                        />
                        <title>Segmenti Yatay Taşı / Sürükle (Çift tıkla sıfırla)</title>
                      </g>

                      {/* Elbow Corner 1 (Top / Start corner) */}
                      <g
                        transform={`translate(${effectiveMidX}, ${startPt.y})`}
                        className="cursor-ew-resize group/corner1"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          draggingWireJointRef.current = { wireId: wire.id, type: 'corner1' };
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner1' });
                        }}
                      >
                        <circle cx={0} cy={0} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                        <circle
                          cx={0}
                          cy={0}
                          r={5.5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          pointerEvents="none"
                        />
                        <title>Dirsek Köşesi 1 (Sürükle)</title>
                      </g>

                      {/* Elbow Corner 2 (Bottom / End corner) */}
                      <g
                        transform={`translate(${effectiveMidX}, ${endPt.y})`}
                        className="cursor-ew-resize group/corner2"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          draggingWireJointRef.current = { wireId: wire.id, type: 'corner2' };
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner2' });
                        }}
                      >
                        <circle cx={0} cy={0} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                        <circle
                          cx={0}
                          cy={0}
                          r={5.5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          pointerEvents="none"
                        />
                        <title>Dirsek Köşesi 2 (Sürükle)</title>
                      </g>
                    </g>
                  )}"""

    new_handles_block = """                  {/* Interactive Wire Drag Handles (Supports both 90° Manhattan and Waypoint Freeform) */}
                  {isSelected && !wiringFrom && (
                    <g>
                      {/* Case A: Wire with interactive waypoints */}
                      {wire.waypoints && wire.waypoints.length > 0 ? (
                        <g>
                          {wire.waypoints.map((pt, i) => (
                            <g
                              key={i}
                              transform={`translate(${pt.x}, ${pt.y})`}
                              className="cursor-move group/wp"
                              onMouseDown={(e) => {
                                e.stopPropagation();
                                e.preventDefault();
                                draggingWireJointRef.current = { wireId: wire.id, type: 'waypoint', index: i };
                                setDraggingWireJoint({ wireId: wire.id, type: 'waypoint', index: i });
                              }}
                              onDoubleClick={(e) => {
                                e.stopPropagation();
                                setWires((prev) =>
                                  prev.map((w) => {
                                    if (w.id === wire.id && w.waypoints) {
                                      const nextWps = w.waypoints.filter((_, idx) => idx !== i);
                                      return { ...w, waypoints: nextWps.length > 0 ? nextWps : undefined };
                                    }
                                    return w;
                                  })
                                );
                              }}
                            >
                              <circle cx={0} cy={0} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                              <circle
                                cx={0}
                                cy={0}
                                r={6.5}
                                fill="#2563eb"
                                stroke="#ffffff"
                                strokeWidth={2}
                                filter="drop-shadow(0 2px 5px rgba(0,0,0,0.35))"
                                pointerEvents="none"
                              />
                              <circle cx={0} cy={0} r={2} fill="#ffffff" pointerEvents="none" />
                              <title>{`Köşe Noktası ${i + 1} (Sürükle, Çift tıkla kaldır)`}</title>
                            </g>
                          ))}
                        </g>
                      ) : (
                        /* Case B: Standard 90° Manhattan Wire Handles */
                        <g>
                          {/* Midpoint Handle on vertical segment */}
                          <g
                            transform={`translate(${effectiveMidX}, ${midY})`}
                            className="cursor-ew-resize group/joint"
                            onMouseDown={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              draggingWireJointRef.current = { wireId: wire.id, type: 'segment' };
                              setDraggingWireJoint({ wireId: wire.id, type: 'segment' });
                            }}
                            onDoubleClick={(e) => {
                              e.stopPropagation();
                              setWires((prev) =>
                                prev.map((w) => (w.id === wire.id ? { ...w, elbowX: undefined, jointOffset: undefined } : w))
                              );
                            }}
                          >
                            <circle
                              cx={0}
                              cy={0}
                              r={18}
                              fill="#000000"
                              fillOpacity={0}
                              pointerEvents="all"
                            />
                            <circle
                              cx={0}
                              cy={0}
                              r={7}
                              fill="#2563eb"
                              stroke="#ffffff"
                              strokeWidth={2}
                              filter="drop-shadow(0 2px 5px rgba(0,0,0,0.35))"
                              pointerEvents="none"
                            />
                            <circle
                              cx={0}
                              cy={0}
                              r={2.5}
                              fill="#ffffff"
                              pointerEvents="none"
                            />
                            <title>Segmenti Yatay Taşı / Sürükle (Çift tıkla sıfırla)</title>
                          </g>

                          {/* Elbow Corner 1 (Top / Start corner) */}
                          <g
                            transform={`translate(${effectiveMidX}, ${startPt.y})`}
                            className="cursor-ew-resize group/corner1"
                            onMouseDown={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              draggingWireJointRef.current = { wireId: wire.id, type: 'corner1' };
                              setDraggingWireJoint({ wireId: wire.id, type: 'corner1' });
                            }}
                          >
                            <circle cx={0} cy={0} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                            <circle
                              cx={0}
                              cy={0}
                              r={5.5}
                              fill="#60a5fa"
                              stroke="#ffffff"
                              strokeWidth={1.5}
                              pointerEvents="none"
                            />
                            <title>Dirsek Köşesi 1 (Sürükle)</title>
                          </g>

                          {/* Elbow Corner 2 (Bottom / End corner) */}
                          <g
                            transform={`translate(${effectiveMidX}, ${endPt.y})`}
                            className="cursor-ew-resize group/corner2"
                            onMouseDown={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              draggingWireJointRef.current = { wireId: wire.id, type: 'corner2' };
                              setDraggingWireJoint({ wireId: wire.id, type: 'corner2' });
                            }}
                          >
                            <circle cx={0} cy={0} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                            <circle
                              cx={0}
                              cy={0}
                              r={5.5}
                              fill="#60a5fa"
                              stroke="#ffffff"
                              strokeWidth={1.5}
                              pointerEvents="none"
                            />
                            <title>Dirsek Köşesi 2 (Sürükle)</title>
                          </g>
                        </g>
                      )}
                    </g>
                  )}"""

    assert old_handles_block in content, "Could not find old_handles_block"
    content = content.replace(old_handles_block, new_handles_block)
    print("4. Rendered interactive handles for both waypoints and Manhattan segments")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
