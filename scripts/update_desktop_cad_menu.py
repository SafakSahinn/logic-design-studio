with open(r'C:\Users\safak\Desktop\Logic Design Studio\scripts\build_desktop_cad_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. In ribbon:
old_ribbon_btn = """          <button
            onClick={() => setWireStyle((p) => (p === 'orthogonal' ? 'bezier' : 'orthogonal'))}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-colors cursor-pointer border ${
              wireStyle === 'orthogonal'
                ? 'bg-blue-600 text-white border-blue-600 shadow-2xs'
                : isDark
                ? 'bg-slate-800 text-slate-300 border-slate-700'
                : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}
            title="Kablo Yönlendirme: 90° Manhattan vs Eğri"
          >
            {wireStyle === 'orthogonal' ? '90° Dik Tel' : 'Eğri Tel'}
          </button>"""

new_ribbon_btn = """          <div
            className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold border border-blue-500/40 bg-blue-500/10 text-blue-500 select-none flex items-center gap-1.5"
            title="90° Standart Logisim CAD Hatları"
          >
            <Activity className="w-3 h-3 text-blue-500" />
            <span>90° Dik Tel</span>
          </div>"""

if old_ribbon_btn in text:
    text = text.replace(old_ribbon_btn, new_ribbon_btn)
    print("Updated ribbon in build_desktop_cad_app.py")

with open(r'C:\Users\safak\Desktop\Logic Design Studio\scripts\build_desktop_cad_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved build_desktop_cad_app.py")
