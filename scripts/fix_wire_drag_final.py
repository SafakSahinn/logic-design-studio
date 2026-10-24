import os

def patch_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Add draggingWireJointRef
    state_decl = "const [draggingWireJoint, setDraggingWireJoint] = useState<{\n    wireId: string;\n    type: 'corner1' | 'corner2' | 'segment';\n  } | null>(null);"
    state_repl = """const [draggingWireJoint, setDraggingWireJoint] = useState<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment';
  } | null>(null);
  const draggingWireJointRef = useRef<{
    wireId: string;
    type: 'corner1' | 'corner2' | 'segment';
  } | null>(null);"""

    if "const draggingWireJointRef" not in text:
        assert state_decl in text, f"Could not find state_decl in {file_path}"
        text = text.replace(state_decl, state_repl, 1)
        print(f"1. Added draggingWireJointRef to {file_path}")

    # 2. Update handleCanvasMouseMove
    old_mouse_move = """    if (draggingWireJoint) {
      const snappedX = snapToGrid ? Math.round(coords.x / 10) * 10 : Math.round(coords.x);
      setWires((prev) =>
        prev.map((w) => {
          if (w.id === draggingWireJoint.wireId) {
            return { ...w, elbowX: snappedX };
          }
          return w;
        })
      );
      return;
    }"""

    new_mouse_move = """    const activeDragJoint = draggingWireJointRef.current || draggingWireJoint;
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
    }"""

    if "const activeDragJoint = draggingWireJointRef.current" not in text:
        assert old_mouse_move in text, f"Could not find old_mouse_move in {file_path}"
        text = text.replace(old_mouse_move, new_mouse_move, 1)
        print(f"2. Updated handleCanvasMouseMove in {file_path}")

    # 3. Update handleCanvasMouseUp
    old_mouse_up = """  const handleCanvasMouseUp = (e: React.MouseEvent) => {
    if (draggingWireJoint) {
      setDraggingWireJoint(null);
      recordHistory();
      runSimulation();
    }"""

    new_mouse_up = """  const handleCanvasMouseUp = (e: React.MouseEvent) => {
    if (draggingWireJointRef.current || draggingWireJoint) {
      draggingWireJointRef.current = null;
      setDraggingWireJoint(null);
      recordHistory();
      runSimulation();
    }"""

    if "if (draggingWireJointRef.current || draggingWireJoint)" not in text:
        assert old_mouse_up in text, f"Could not find old_mouse_up in {file_path}"
        text = text.replace(old_mouse_up, new_mouse_up, 1)
        print(f"3. Updated handleCanvasMouseUp in {file_path}")

    # 4. Update handleGlobalRelease
    old_global = """  useEffect(() => {
    const handleGlobalRelease = () => {"""
    new_global = """  useEffect(() => {
    const handleGlobalRelease = () => {
      draggingWireJointRef.current = null;
      setDraggingWireJoint(null);"""

    if "draggingWireJointRef.current = null;\n      setDraggingWireJoint(null);\n      setComponents" not in text:
        assert old_global in text, f"Could not find old_global in {file_path}"
        text = text.replace(old_global, new_global, 1)
        print(f"4. Updated handleGlobalRelease in {file_path}")

    # 5. Update wire handles and floating toolbar block
    s = text.find('{/* Unselected Wire Hover:')
    if s == -1:
        s = text.find('{/* Quick T-Junction Branch Button')
    assert s != -1, f"Could not find wire handles start in {file_path}"

    e = text.find('{/* Floating Live Signal Tooltip on Hover', s)
    assert e != -1, f"Could not find wire handles end in {file_path}"

    new_wire_section = '''{/* Unselected Wire Hover: Clean Single T-Junction Branch Button */}
                  {!isSelected && hoveredWireId === wire.id && !wiringFrom && !draggingWireJoint && (
                    <g
                      transform={`translate(${midX}, ${midY})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: midX, y: midY });
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
                  )}

                  {/* Manhattan Wire Joint Corner & Segment Drag Handles (Only on Selected Wire) */}
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
                  )}

                  {/* Selected Wire: Floating Action Toolbar Pill (Positioned cleanly 34px ABOVE midpoint with 18px clear air gap) */}
                  {isSelected && !wiringFrom && !draggingWireJoint && !draggingWireJointRef.current && (
                    <g
                      transform={`translate(${effectiveMidX}, ${midY < 55 ? midY + 34 : midY - 34})`}
                      className="select-none"
                    >
                      {/* Pill container shadow and background */}
                      <rect
                        x={-38}
                        y={-14}
                        width={76}
                        height={28}
                        rx={14}
                        fill={cadTheme === 'dark' ? '#0f172a' : '#ffffff'}
                        stroke={cadTheme === 'dark' ? '#334155' : '#cbd5e1'}
                        strokeWidth={1.5}
                        filter="drop-shadow(0 4px 8px rgba(0,0,0,0.25))"
                      />

                      {/* Action 1: Delete Wire Button */}
                      <g
                        transform="translate(-22, 0)"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSelected();
                        }}
                        className="cursor-pointer group/del"
                      >
                        <circle
                          cx={0}
                          cy={0}
                          r={9.5}
                          fill="#ef4444"
                          className="group-hover/del:scale-110 transition-transform"
                        />
                        <path
                          d="M -3,-3 L 3,3 M 3,-3 L -3,3"
                          stroke="#ffffff"
                          strokeWidth={1.8}
                          strokeLinecap="round"
                        />
                        <title>Kabloyu Sil (Del / Backspace)</title>
                      </g>

                      {/* Action 2: T-Junction Branch Wire Button */}
                      <g
                        transform="translate(0, 0)"
                        onClick={(e) => {
                          e.stopPropagation();
                          const tap = getClosestPointOnOrthogonalWire(startPt, endPt, { x: effectiveMidX, y: midY });
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
                        className="cursor-pointer group/add"
                      >
                        <circle
                          cx={0}
                          cy={0}
                          r={9.5}
                          fill="#2563eb"
                          className="group-hover/add:scale-110 transition-transform"
                        />
                        <path
                          d="M -3.5,0 L 3.5,0 M 0,-3.5 L 0,3.5"
                          stroke="#ffffff"
                          strokeWidth={1.8}
                          strokeLinecap="round"
                        />
                        <title>Kablo Ortasından T-Kavşak Çıkar (Branch Wire)</title>
                      </g>

                      {/* Action 3: Toggle Bus Width Mode Button */}
                      <g
                        transform="translate(22, 0)"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleWireBus(wire.id);
                        }}
                        className="cursor-pointer group/bus"
                      >
                        <circle
                          cx={0}
                          cy={0}
                          r={9.5}
                          fill={wire.isBus ? '#6366f1' : '#64748b'}
                          className="group-hover/bus:scale-110 transition-transform"
                        />
                        <text
                          x={0}
                          y={3.5}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize={8}
                          fontWeight="bold"
                          fontFamily="monospace"
                        >
                          {wire.isBus ? '1B' : '/4'}
                        </text>
                        <title>{wire.isBus ? '1-Bit Standart Kabloya Çevir' : '4-Bit Kalın Veri Yolu (Bus) Yap'}</title>
                      </g>
                    </g>
                  )}

                  '''

    text = text[:s] + new_wire_section + text[e:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Successfully patched {file_path}")

web_file = r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx"
patch_file(web_file)
