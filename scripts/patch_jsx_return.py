import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_file = r"C:\Users\safak\Desktop\Logic Design Studio\src\components\LogisimSimulator.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    text = f.read()

# Marker 1: Outer container and Educational Header
m1_target = '    <div className="space-y-6 max-w-7xl mx-auto">\n      {/* Educational Header - Clean, Spacious & Responsive */}\n      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">'

m1_replacement = '''    <div className={desktopMode ? "w-screen h-screen overflow-hidden flex flex-col select-none bg-[#090D16] text-slate-100" : "space-y-6 max-w-7xl mx-auto"}>
      {desktopMode ? (
        <>
          {renderDesktopMenuBar()}
          {renderDesktopRibbon()}
        </>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">'''

# Marker 2: End of Educational Header, start of Main Stage Card
m2_target = '''            </div>
          )}
        </div>
      </div>

      {/* Main Simulation Stage Card */}
      <div className={`rounded-3xl border overflow-hidden flex flex-col transition-colors ${
        cadTheme === 'dark'
          ? 'bg-[#0B0F19] border-slate-800 shadow-2xl text-slate-100'
          : 'bg-white border-slate-200 shadow-xs text-slate-900'
      }`}>
        {/* Top Control Bar: Tier 1 - Simulation & Analysis Suite */}'''

m2_replacement = '''            </div>
          )}
        </div>
      </div>
      )}

      {/* Main Simulation Stage Card */}
      <div className={desktopMode ? "flex-1 w-full min-h-0 flex flex-row overflow-hidden relative" : `rounded-3xl border overflow-hidden flex flex-col transition-colors ${
        cadTheme === 'dark'
          ? 'bg-[#0B0F19] border-slate-800 shadow-2xl text-slate-100'
          : 'bg-white border-slate-200 shadow-xs text-slate-900'
      }`}>
        {desktopMode && showLeftToolbox && renderDesktopLeftToolbox()}

        <div className={desktopMode ? "flex-1 min-w-0 h-full flex flex-col overflow-hidden relative" : "flex flex-col w-full"}>
          {!desktopMode && (
            <>
              {/* Top Control Bar: Tier 1 - Simulation & Analysis Suite */}'''

# Marker 3: End of Tier 3 palette, start of Multi-sheet Project Workspace Tabs Header
m3_target = '''            {/* Scroll Right Button */}
            <button
              onClick={() => scrollPalette('right')}
              className={`shrink-0 w-6 h-8 ml-1 rounded-lg flex items-center justify-center cursor-pointer transition-colors shadow-2xs ${
                cadTheme === 'dark'
                  ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                  : 'bg-slate-200/80 hover:bg-slate-300 text-slate-700'
              }`}
              title="Sağa Kaydır"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Multi-Sheet Project Workspace Tabs Header */}'''

m3_replacement = '''            {/* Scroll Right Button */}
            <button
              onClick={() => scrollPalette('right')}
              className={`shrink-0 w-6 h-8 ml-1 rounded-lg flex items-center justify-center cursor-pointer transition-colors shadow-2xs ${
                cadTheme === 'dark'
                  ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                  : 'bg-slate-200/80 hover:bg-slate-300 text-slate-700'
              }`}
              title="Sağa Kaydır"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        </>
        )}

        {/* Multi-Sheet Project Workspace Tabs Header */}'''

# Marker 4: Interactive SVG Canvas container styling and drop handler
m4_target = '''        {/* Interactive SVG Canvas */}
        <div
          ref={canvasContainerRef}
          className={`relative w-full overflow-hidden select-none transition-colors ${
            cadTheme === 'dark' ? 'bg-[#070A12]' : 'bg-slate-50/60'
          }`}
          style={{ minHeight: '560px' }}
        >
          <svg
            ref={svgRef}
            className={`w-full h-full ${
              isPanning
                ? 'cursor-grabbing'
                : isSpacePressedRef.current || canvasMode === 'pan'
                ? 'cursor-grab'
                : 'cursor-crosshair'
            }`}
            style={{ minHeight: '560px' }}'''

m4_replacement = '''        {/* Interactive SVG Canvas */}
        <div
          ref={canvasContainerRef}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleCanvasDrop}
          className={`relative flex-1 w-full h-full min-h-0 overflow-hidden select-none transition-colors ${
            cadTheme === 'dark' ? 'bg-[#070A12]' : 'bg-slate-50/60'
          }`}
          style={desktopMode ? { width: '100%', height: '100%' } : { minHeight: '560px' }}
        >
          <svg
            ref={svgRef}
            className={`w-full h-full ${
              isPanning
                ? 'cursor-grabbing'
                : isSpacePressedRef.current || canvasMode === 'pan'
                ? 'cursor-grab'
                : 'cursor-crosshair'
            }`}
            style={desktopMode ? { width: '100%', height: '100%' } : { minHeight: '560px' }}'''

# Marker 5: Bottom Bar and Stage Card Closing
m5_target = '''        {/* Live Logic Analyzer / Truth Bar */}
        <div className={`p-5 border-t flex flex-wrap items-center justify-between gap-4 text-xs transition-colors ${
          cadTheme === 'dark' ? 'bg-[#090D16] border-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-700'
        }`}>
          <div className="flex items-center gap-6">
            {/* Inputs live status */}
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-500 uppercase tracking-wider">Canlı Girişler:</span>
              <div className="flex items-center gap-1.5 font-mono">
                {canvasSummary.inputs.length === 0 ? (
                  <span className="text-slate-400">Giriş yok</span>
                ) : (
                  canvasSummary.inputs.map((inp) => (
                    <span
                      key={inp.id}
                      className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                        inp.state.on ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {inp.label || inp.id}: {inp.state.on ? '1' : '0'}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Outputs live status */}
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-500 uppercase tracking-wider">Canlı Çıkışlar:</span>
              <div className="flex items-center gap-1.5 font-mono">
                {canvasSummary.outputs.length === 0 ? (
                  <span className="text-slate-400">Çıkış yok</span>
                ) : (
                  canvasSummary.outputs.map((out) => {
                    const isHigh = out.inputs[0]?.value === 1;
                    return (
                      <span
                        key={out.id}
                        className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                          isHigh ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {out.label || out.id}: {isHigh ? '1' : '0'}
                      </span>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="text-slate-500 font-mono text-[11px]">
            Bileşen Sayısı: <strong>{components.length}</strong> • Kablo Sayısı: <strong>{wires.length}</strong> • Adım: <strong>{stepCount}</strong>
          </div>
        </div>
      </div>'''

m5_replacement = '''        {/* Bottom Bar: Desktop Status Bar vs Web Live Analyzer */}
        {desktopMode ? (
          renderDesktopStatusBar()
        ) : (
          <div className={`p-5 border-t flex flex-wrap items-center justify-between gap-4 text-xs transition-colors ${
            cadTheme === 'dark' ? 'bg-[#090D16] border-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-700'
          }`}>
            <div className="flex items-center gap-6">
              {/* Inputs live status */}
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-500 uppercase tracking-wider">Canlı Girişler:</span>
                <div className="flex items-center gap-1.5 font-mono">
                  {canvasSummary.inputs.length === 0 ? (
                    <span className="text-slate-400">Giriş yok</span>
                  ) : (
                    canvasSummary.inputs.map((inp) => (
                      <span
                        key={inp.id}
                        className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                          inp.state.on ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {inp.label || inp.id}: {inp.state.on ? '1' : '0'}
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Outputs live status */}
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-500 uppercase tracking-wider">Canlı Çıkışlar:</span>
                <div className="flex items-center gap-1.5 font-mono">
                  {canvasSummary.outputs.length === 0 ? (
                    <span className="text-slate-400">Çıkış yok</span>
                  ) : (
                    canvasSummary.outputs.map((out) => {
                      const isHigh = out.inputs[0]?.value === 1;
                      return (
                        <span
                          key={out.id}
                          className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                            isHigh ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {out.label || out.id}: {isHigh ? '1' : '0'}
                        </span>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            <div className="text-slate-500 font-mono text-[11px]">
              Bileşen Sayısı: <strong>{components.length}</strong> • Kablo Sayısı: <strong>{wires.length}</strong> • Adım: <strong>{stepCount}</strong>
            </div>
          </div>
        )}
        </div>
      </div>'''

# Marker 6: Extra Modals before Toast
m6_target = '''      {/* Floating Action Toast Notification */}
      {toastMessage && ('''

m6_replacement = '''      {/* Desktop Extra Modals (K-Map, Number Converter, About) */}
      {desktopMode && renderDesktopExtraModals()}

      {/* Floating Action Toast Notification */}
      {toastMessage && ('''

changes = [
    ("Marker 1 (Header)", m1_target, m1_replacement),
    ("Marker 2 (Stage Card Start)", m2_target, m2_replacement),
    ("Marker 3 (Tier 3 Palette End)", m3_target, m3_replacement),
    ("Marker 4 (Canvas Styling)", m4_target, m4_replacement),
    ("Marker 5 (Bottom Bar & Stage Card End)", m5_target, m5_replacement),
    ("Marker 6 (Modals)", m6_target, m6_replacement),
]

for label, target, repl in changes:
    if target in text:
        text = text.replace(target, repl, 1)
        print(f"Applied {label}")
    else:
        print(f"FAILED to find {label}")
        sys.exit(1)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(text)

print("All JSX patches successfully applied!")
