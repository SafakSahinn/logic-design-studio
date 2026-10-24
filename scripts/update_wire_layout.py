import os

def update_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    s = text.find('{/* Quick T-Junction Branch Button')
    assert s != -1, f"Could not find start in {path}"
    e = text.find('{/* Floating Live Signal Tooltip on Hover', s)
    assert e != -1, f"Could not find end in {path}"

    new_block = '''{/* Unselected Wire Hover: Clean Single T-Junction Branch Button */}
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
                      {/* Midpoint Handle on vertical segment - Wide transparent hit area prevents mouse slip */}
                      <g
                        className="cursor-ew-resize group/joint"
                        onMouseDown={(e) => {
                          e.stopPropagation();
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
                          cx={effectiveMidX}
                          cy={midY}
                          r={16}
                          fill="transparent"
                        />
                        <circle
                          cx={effectiveMidX}
                          cy={midY}
                          r={6.5}
                          fill="#3b82f6"
                          stroke="#ffffff"
                          strokeWidth={2}
                          className="group-hover/joint:scale-125 transition-transform"
                          filter="drop-shadow(0 1px 3px rgba(0,0,0,0.3))"
                        />
                        <title>Segmenti Yatay Taşı / Sürükle (Çift tıkla sıfırla)</title>
                      </g>

                      {/* Elbow Corner 1 (Top / Start corner) */}
                      <g
                        className="cursor-ew-resize group/corner1"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner1' });
                        }}
                      >
                        <circle cx={effectiveMidX} cy={startPt.y} r={14} fill="transparent" />
                        <circle
                          cx={effectiveMidX}
                          cy={startPt.y}
                          r={5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          className="group-hover/corner1:scale-125 transition-transform"
                        />
                        <title>Dirsek Köşesi 1 (Sürükle)</title>
                      </g>

                      {/* Elbow Corner 2 (Bottom / End corner) */}
                      <g
                        className="cursor-ew-resize group/corner2"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          setDraggingWireJoint({ wireId: wire.id, type: 'corner2' });
                        }}
                      >
                        <circle cx={effectiveMidX} cy={endPt.y} r={14} fill="transparent" />
                        <circle
                          cx={effectiveMidX}
                          cy={endPt.y}
                          r={5}
                          fill="#60a5fa"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          className="group-hover/corner2:scale-125 transition-transform"
                        />
                        <title>Dirsek Köşesi 2 (Sürükle)</title>
                      </g>
                    </g>
                  )}

                  {/* Selected Wire: Floating Action Toolbar Pill (Positioned cleanly 28px ABOVE midpoint so it never conflicts with drag handles) */}
                  {isSelected && !wiringFrom && !draggingWireJoint && (
                    <g
                      transform={`translate(${effectiveMidX}, ${midY < 45 ? midY + 28 : midY - 28})`}
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

    text = text[:s] + new_block + text[e:]

    # Also update the SVG cursor to lock to cursor-ew-resize during draggingWireJoint
    svg_cursor_target = "isPanning\n                ? 'cursor-grabbing'\n                : isSpacePressedRef.current || canvasMode === 'pan'\n                ? 'cursor-grab'\n                : 'cursor-crosshair'"
    svg_cursor_repl = "draggingWireJoint\n                ? 'cursor-ew-resize select-none'\n                : isPanning\n                ? 'cursor-grabbing'\n                : isSpacePressedRef.current || canvasMode === 'pan'\n                ? 'cursor-grab'\n                : 'cursor-crosshair'"
    if svg_cursor_target in text:
        text = text.replace(svg_cursor_target, svg_cursor_repl)
        print("Updated SVG cursor!")
    else:
        print("Note: svg_cursor_target not matched directly, checking single line version...")
        svg_c2 = "isPanning ? 'cursor-grabbing' : isSpacePressedRef.current || canvasMode === 'pan' ? 'cursor-grab' : 'cursor-crosshair'"
        svg_c2_repl = "draggingWireJoint ? 'cursor-ew-resize select-none' : isPanning ? 'cursor-grabbing' : isSpacePressedRef.current || canvasMode === 'pan' ? 'cursor-grab' : 'cursor-crosshair'"
        if svg_c2 in text:
            text = text.replace(svg_c2, svg_c2_repl)
            print("Updated SVG cursor single-line!")

    # Also update wire g container to pointer-events-none during draggingWireJoint
    wire_g_target = 'className="cursor-pointer group"'
    wire_g_repl = 'className={draggingWireJoint ? "pointer-events-none" : "cursor-pointer group"}'
    # only replace the wire.id g container
    wire_id_str = 'key={wire.id}'
    idx_w = text.find(wire_id_str)
    if idx_w != -1:
        idx_class = text.find(wire_g_target, idx_w)
        if idx_class != -1 and idx_class - idx_w < 1800:
            text = text[:idx_class] + wire_g_repl + text[idx_class + len(wire_g_target):]
            print("Updated wire.id g container className!")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Successfully updated {path}")

update_file(r"C:\Users\safak\Desktop\Logic Deisgn Web Site\src\components\LogisimSimulator.tsx")
