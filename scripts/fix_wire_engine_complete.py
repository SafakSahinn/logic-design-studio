import re
import sys

def patch_file(file_path):
    print(f"Patching {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update getClosestPointOnOrthogonalWire
    old_get_closest = """  // Helper: Find closest orthogonal projection point on a Manhattan wire path
  const getClosestPointOnOrthogonalWire = (
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    click: { x: number; y: number }
  ) => {
    const midX = Math.round((p1.x + p2.x) / 2);
    const segs = [
      { type: 'H' as const, x1: p1.x, x2: midX, y: p1.y },
      { type: 'V' as const, x: midX, y1: p1.y, y2: p2.y },
      { type: 'H' as const, x1: midX, x2: p2.x, y: p2.y },
    ];
    let bestPt = { x: midX, y: p1.y };
    let bestDistSq = Infinity;
    for (const s of segs) {
      let px: number;
      let py: number;
      if (s.type === 'H') {
        const minX = Math.min(s.x1, s.x2);
        const maxX = Math.max(s.x1, s.x2);
        px = Math.max(minX, Math.min(maxX, click.x));
        py = s.y;
      } else {
        const minY = Math.min(s.y1, s.y2);
        const maxY = Math.max(s.y1, s.y2);
        px = s.x;
        py = Math.max(minY, Math.min(maxY, click.y));
      }
      const dSq = (px - click.x) ** 2 + (py - click.y) ** 2;
      if (dSq < bestDistSq) {
        bestDistSq = dSq;
        bestPt = { x: px, y: py };
      }
    }
    return {
      x: snapToGrid ? Math.round(bestPt.x / 10) * 10 : Math.round(bestPt.x),
      y: snapToGrid ? Math.round(bestPt.y / 10) * 10 : Math.round(bestPt.y),
    };
  };"""

    new_get_closest = """  // Helper: Find closest orthogonal projection point on a Manhattan wire path
  const getClosestPointOnOrthogonalWire = (
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    click: { x: number; y: number },
    elbowX?: number
  ) => {
    const midX = elbowX !== undefined ? elbowX : Math.round((p1.x + p2.x) / 2);
    const segs = [
      { type: 'H' as const, x1: p1.x, x2: midX, y: p1.y },
      { type: 'V' as const, x: midX, y1: p1.y, y2: p2.y },
      { type: 'H' as const, x1: midX, x2: p2.x, y: p2.y },
    ];
    let bestPt = { x: midX, y: p1.y };
    let bestDistSq = Infinity;
    let bestSegType: 'H' | 'V' = 'H';
    for (const s of segs) {
      let px: number;
      let py: number;
      if (s.type === 'H') {
        const minX = Math.min(s.x1, s.x2);
        const maxX = Math.max(s.x1, s.x2);
        px = Math.max(minX, Math.min(maxX, click.x));
        py = s.y;
      } else {
        const minY = Math.min(s.y1, s.y2);
        const maxY = Math.max(s.y1, s.y2);
        px = s.x;
        py = Math.max(minY, Math.min(maxY, click.y));
      }
      const dSq = (px - click.x) ** 2 + (py - click.y) ** 2;
      if (dSq < bestDistSq) {
        bestDistSq = dSq;
        bestPt = { x: px, y: py };
        bestSegType = s.type;
      }
    }
    // Snap only along the free axis; keep the wire axis strictly fixed so tap never jogs off the wire!
    return {
      x: bestSegType === 'H' ? (snapToGrid ? Math.round(bestPt.x / 10) * 10 : Math.round(bestPt.x)) : bestPt.x,
      y: bestSegType === 'V' ? (snapToGrid ? Math.round(bestPt.y / 10) * 10 : Math.round(bestPt.y)) : bestPt.y,
    };
  };"""

    assert old_get_closest in content, "Could not find old_get_closest"
    content = content.replace(old_get_closest, new_get_closest)
    print("1. Replaced getClosestPointOnOrthogonalWire")

    # 2. Update wireCrossings to respect elbowX
    old_cross_mid = """    wires.forEach((w) => {
      const p1 = w.branchPoint || findPinById(w.fromPinId);
      const p2 = findPinById(w.toPinId);
      if (!p1 || !p2) return;
      const midX = Math.round((p1.x + p2.x) / 2);
      const isHigh = w.value === 1;"""

    new_cross_mid = """    wires.forEach((w) => {
      const p1 = w.branchPoint || findPinById(w.fromPinId);
      const p2 = findPinById(w.toPinId);
      if (!p1 || !p2) return;
      const defaultMidX = Math.round((p1.x + p2.x) / 2);
      const midX = w.elbowX !== undefined ? w.elbowX : defaultMidX;
      const isHigh = w.value === 1;"""

    assert old_cross_mid in content, "Could not find old_cross_mid"
    content = content.replace(old_cross_mid, new_cross_mid)
    print("2. Updated wireCrossings to respect elbowX")

    # 3. Update handleCanvasMouseMove for wire dragging & component dragging wire sync
    old_mouse_move = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
    if (activeDragJoint) {
      const snappedX = snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x);
      setWires((prev) =>
        prev.map((w) => {
          if (w.id === activeDragJoint.wireId) {
            return { ...w, elbowX: snappedX };
          }
          return w;
        })
      );
      return;
    }

    if (draggingCompId && dragGroupOffsetsRef.current.size > 0) {
      if (dragStartSnapshotRef.current) {
        dragStartSnapshotRef.current.didMove = true;
      }
      const offsets = dragGroupOffsetsRef.current;
      setComponents((prev) =>
        prev.map((c) => {
          const off = offsets.get(c.id);
          if (off) {
            const rawX = coords.x - off.x;
            const rawY = coords.y - off.y;
            // Snap to 10px grid if enabled
            const snappedX = snapToGrid ? Math.max(10, Math.round(rawX / 10) * 10) : Math.max(10, Math.round(rawX));
            const snappedY = snapToGrid ? Math.max(10, Math.round(rawY / 10) * 10) : Math.max(10, Math.round(rawY));
            return updatePinPositions({ ...c, x: snappedX, y: snappedY });
          }
          return c;
        })
      );
      return;
    }"""

    new_mouse_move = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
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
    }

    if (draggingCompId && dragGroupOffsetsRef.current.size > 0) {
      if (dragStartSnapshotRef.current) {
        dragStartSnapshotRef.current.didMove = true;
      }
      const offsets = dragGroupOffsetsRef.current;
      const initialComps = dragStartSnapshotRef.current ? dragStartSnapshotRef.current.components : [];
      const initialWires = dragStartSnapshotRef.current ? dragStartSnapshotRef.current.wires : [];
      const initialCompMap = new Map(initialComps.map((c) => [c.id, c]));

      const movedCompDeltas = new Map<string, { dx: number; dy: number }>();
      setComponents((prev) =>
        prev.map((c) => {
          const off = offsets.get(c.id);
          if (off) {
            const rawX = coords.x - off.x;
            const rawY = coords.y - off.y;
            // Snap to 10px grid if enabled
            const snappedX = snapToGrid ? Math.max(10, Math.round(rawX / 10) * 10) : Math.max(10, Math.round(rawX));
            const snappedY = snapToGrid ? Math.max(10, Math.round(rawY / 10) * 10) : Math.max(10, Math.round(rawY));
            const c0 = initialCompMap.get(c.id);
            if (c0) {
              movedCompDeltas.set(c.id, { dx: snappedX - c0.x, dy: snappedY - c0.y });
            }
            return updatePinPositions({ ...c, x: snappedX, y: snappedY });
          }
          return c;
        })
      );

      // Synchronize all connected wires, branch points, and Manhattan elbows!
      if (initialWires.length > 0 && movedCompDeltas.size > 0) {
        setWires((prev) =>
          prev.map((w) => {
            const initialWire = initialWires.find((iw) => iw.id === w.id);
            if (!initialWire) return w;

            let updatedWire = { ...w };

            // 1. If branchPoint exists and fromCompId moved:
            if (initialWire.branchPoint && movedCompDeltas.has(w.fromCompId)) {
              const delta = movedCompDeltas.get(w.fromCompId)!;
              updatedWire.branchPoint = {
                x: initialWire.branchPoint.x + delta.dx,
                y: initialWire.branchPoint.y + delta.dy,
              };
            }

            // 2. If both fromCompId and toCompId moved together with the same delta:
            const fromDelta = movedCompDeltas.get(w.fromCompId);
            const toDelta = movedCompDeltas.get(w.toCompId);
            if (fromDelta && toDelta && fromDelta.dx === toDelta.dx) {
              if (initialWire.elbowX !== undefined) {
                updatedWire.elbowX = initialWire.elbowX + fromDelta.dx;
              }
            }

            return updatedWire;
          })
        );
      }
      return;
    }"""

    assert old_mouse_move in content, "Could not find old_mouse_move"
    content = content.replace(old_mouse_move, new_mouse_move)
    print("3. Updated handleCanvasMouseMove for wire dragging and component wire sync")

    # 4. Update calls to getClosestPointOnOrthogonalWire to pass effectiveMidX
    old_call1 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, mousePos);"
    new_call1 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, mousePos, effectiveMidX);"
    content = content.replace(old_call1, new_call1)

    old_call2 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: midX, y: midY });"
    new_call2 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: midX, y: midY }, effectiveMidX);"
    content = content.replace(old_call2, new_call2)

    old_call3 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: effectiveMidX, y: midY });"
    new_call3 = "const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: effectiveMidX, y: midY }, effectiveMidX);"
    content = content.replace(old_call3, new_call3)
    print("4. Updated getClosestPointOnOrthogonalWire calls to pass effectiveMidX")

    # 5. Fix wire handles and remove scale transforms to prevent coordinate jumping
    old_handles = """                  {/* Manhattan Wire Joint Corner & Segment Drag Handles (Only on Selected Wire) */}
                  {wireStyle === 'orthogonal' && isSelected && !wiringFrom && (
                    <g>
                      {/* Midpoint Handle on vertical segment - Wide pointerEvents="all" hit area */}
                      <g
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
                        {/* 36px wide hit target with pointerEvents="all" guaranteed to capture mousedown */}
                        <circle
                          cx={effectiveMidX}
                          cy={midY}
                          r={18}
                          fill="#000000"
                          fillOpacity={0}
                          pointerEvents="all"
                        />
                        {/* Crisp visible handle dot */}
                        <circle
                          cx={effectiveMidX}
                          cy={midY}
                          r={7}
                          fill="#2563eb"
                          stroke="#ffffff"
                          strokeWidth={2}
                          className="group-hover/joint:scale-125 transition-transform"
                          filter="drop-shadow(0 2px 5px rgba(0,0,0,0.35))"
                          pointerEvents="none"
                        />
                        {/* Inner white dot */}
                        <circle
                          cx={effectiveMidX}
                          cy={midY}
                          r={2}
                          fill="#ffffff"
                          pointerEvents="none"
                        />
                        <title>Segmenti Yatay Taşı / Sürükle (Çift tıkla sıfırla)</title>
                      </g>

                      {/* Elbow Corner 1 (Top / Start corner) */}
                      <g
                        className="cursor-ew-resize group/corner1"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          draggingWireJointRef.current = { wireId: wire.id, type: 'corner1' };
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner1' });
                        }}
                      >
                        <circle cx={effectiveMidX} cy={startPt.y} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                        <circle
                          cx={effectiveMidX}
                          cy={startPt.y}
                          r={5.5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          className="group-hover/corner1:scale-125 transition-transform"
                          pointerEvents="none"
                        />
                        <title>Dirsek Köşesi 1 (Sürükle)</title>
                      </g>

                      {/* Elbow Corner 2 (Bottom / End corner) */}
                      <g
                        className="cursor-ew-resize group/corner2"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          draggingWireJointRef.current = { wireId: wire.id, type: 'corner2' };
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner2' });
                        }}
                      >
                        <circle cx={effectiveMidX} cy={endPt.y} r={16} fill="#000000" fillOpacity={0} pointerEvents="all" />
                        <circle
                          cx={effectiveMidX}
                          cy={endPt.y}
                          r={5.5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          className="group-hover/corner2:scale-125 transition-transform"
                          pointerEvents="none"
                        />
                        <title>Dirsek Köşesi 2 (Sürükle)</title>
                      </g>
                    </g>
                  )}"""

    new_handles = """                  {/* Manhattan Wire Joint Corner & Segment Drag Handles (Only on Selected Wire) */}
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

    assert old_handles in content, "Could not find old_handles"
    content = content.replace(old_handles, new_handles)
    print("5. Fixed wire handles positioning and removed jumping CSS transforms")

    # 6. Remove jumping scale classes from toolbar buttons
    content = content.replace('className="group-hover/del:scale-110 transition-transform"', 'className="group-hover/del:opacity-80 transition-opacity"')
    content = content.replace('className="group-hover/add:scale-110 transition-transform"', 'className="group-hover/add:opacity-80 transition-opacity"')
    content = content.replace('className="group-hover/bus:scale-110 transition-transform"', 'className="group-hover/bus:opacity-80 transition-opacity"')
    print("6. Removed jumping scale transforms from toolbar buttons")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {file_path}!")

if __name__ == "__main__":
    patch_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
