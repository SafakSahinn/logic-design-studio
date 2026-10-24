import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_file = r"C:\Users\safak\Desktop\Logic Design Studio\src\components\LogisimSimulator.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update outer container to be dynamic based on cadTheme
old_outer = '    <div className={desktopMode ? "w-screen h-screen overflow-hidden flex flex-col select-none bg-[#090D16] text-slate-100" : "space-y-6 max-w-7xl mx-auto"}>'
new_outer = '    <div className={desktopMode ? `w-screen h-screen overflow-hidden flex flex-col select-none transition-colors ${cadTheme === "dark" ? "bg-[#090D16] text-slate-100" : "bg-slate-50 text-slate-900"}` : "space-y-6 max-w-7xl mx-auto"}>'

if old_outer in text:
    text = text.replace(old_outer, new_outer, 1)
    print("1. Updated outer container to be dynamic based on cadTheme.")
else:
    print("1. Outer container already updated.")

# 2. Locate desktop render methods block
start_marker = "  // DESKTOP EDA: Toolbox Groups for Left Explorer Panel"
idx_start = text.find(start_marker)
idx_c = text.find("    <div className={desktopMode")
idx_end = text.rfind("  return (\n", 0, idx_c)

assert idx_start != -1, "Could not find start_marker"
assert idx_end != -1, "Could not find idx_end"

new_desktop_render_methods = '''  // DESKTOP EDA: Toolbox Groups for Left Explorer Panel
  const DESKTOP_TOOLBOX_GROUPS = useMemo(() => [
    {
      id: 'wiring',
      title: 'Kablolama & Giriş / Çıkış',
      icon: '🔌',
      types: ['switch', 'pushbutton', 'dipSwitch4', 'clock', 'vcc', 'gnd', 'probe', 'busSplitter', 'textLabel'] as ComponentType[],
    },
    {
      id: 'gates',
      title: 'Temel Mantık Kapıları',
      icon: '🚪',
      types: ['not', 'and', 'or', 'nand', 'nor', 'xor', 'xnor', 'triState'] as ComponentType[],
    },
    {
      id: 'plexers',
      title: 'Plexers & Seçiciler',
      icon: '🔀',
      types: ['mux2to1', 'mux4to1', 'mux8to1', 'demux1to2', 'demux1to4', 'decoder2to4', 'decoder3to8', 'priorityEncoder4to2', 'bcdTo7Seg'] as ComponentType[],
    },
    {
      id: 'arithmetic',
      title: 'Aritmetik Devreler',
      icon: '➕',
      types: ['halfAdder', 'fullAdder', 'halfSubtractor', 'fullSubtractor', 'comparator4bit', 'alu4bit'] as ComponentType[],
    },
    {
      id: 'memory',
      title: 'Bellek & Sıralı Devreler',
      icon: '💾',
      types: ['srLatch', 'dFlipFlop', 'jkFlipFlop', 'tFlipFlop', 'register4bit', 'counter4bit', 'shiftRegister4bit', 'ram16x4', 'rom16x4'] as ComponentType[],
    },
    {
      id: 'displays',
      title: 'Göstergeler & Çıkışlar',
      icon: '💡',
      types: ['led', 'sevenSeg', 'hexDisplay', 'dotMatrix8x8', 'rgbMatrix16x16', 'asciiKeyboard'] as ComponentType[],
    },
    {
      id: 'audio',
      title: 'Ses & Donanım',
      icon: '🔊',
      types: ['buzzer'] as ComponentType[],
    },
  ], []);

  // Render Desktop Menu Bar (File, Edit, Simulation, Tools, View, Help)
  const renderDesktopMenuBar = () => {
    const isDark = cadTheme === 'dark';

    return (
      <div className={`h-7 border-b flex items-center px-2 text-xs font-medium select-none relative z-40 transition-colors ${
        isDark ? 'bg-[#0B0F19] border-slate-800 text-slate-300' : 'bg-slate-100/90 border-slate-200 text-slate-700'
      }`}>
        <div className="flex items-center gap-1.5 mr-4 font-bold">
          <Cpu className={`w-3.5 h-3.5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          <span className={`tracking-wide font-extrabold ${isDark ? 'text-blue-400' : 'text-blue-700'}`}>LogicDesign Studio</span>
        </div>

        {/* Menus */}
        <div className="flex items-center gap-1">
          {/* Dosya (File) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'file' ? null : 'file')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'file'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Dosya
            </button>
            {activeDesktopMenu === 'file' && (
              <div className={`absolute top-full left-0 mt-0.5 w-60 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    handleClearCanvas();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><FilePlus className="w-3.5 h-3.5 text-blue-500" /> Yeni Devre</span>
                  <span className="text-[10px] text-slate-400">Ctrl+N</span>
                </button>
                <button
                  onClick={() => {
                    fileInputRef.current?.click();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><FolderOpen className="w-3.5 h-3.5 text-amber-500" /> Devre Aç... (.json / .circ)</span>
                  <span className="text-[10px] text-slate-400">Ctrl+O</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <button
                  onClick={() => {
                    handleExportJSON();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Save className="w-3.5 h-3.5 text-emerald-500" /> JSON Kaydet</span>
                  <span className="text-[10px] text-slate-400">Ctrl+S</span>
                </button>
                <button
                  onClick={() => {
                    handleExportCirc();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Download className="w-3.5 h-3.5 text-indigo-500" /> Logisim .circ Dışa Aktar</span>
                  <span className="text-[10px] text-slate-400 font-mono">.circ</span>
                </button>
                <button
                  onClick={() => {
                    handleExportPNG();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><ImageIcon className="w-3.5 h-3.5 text-pink-500" /> PNG Şematik Çıkar</span>
                </button>
                <button
                  onClick={() => {
                    handleExportSVG();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><FileCode className="w-3.5 h-3.5 text-purple-500" /> SVG Vektör Çıkar</span>
                </button>
              </div>
            )}
          </div>

          {/* Düzen (Edit) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'edit' ? null : 'edit')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'edit'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Düzen
            </button>
            {activeDesktopMenu === 'edit' && (
              <div className={`absolute top-full left-0 mt-0.5 w-52 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    handleUndo();
                    setActiveDesktopMenu(null);
                  }}
                  disabled={historyStack.length === 0}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between disabled:opacity-40 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Undo2 className="w-3.5 h-3.5" /> Geri Al</span>
                  <span className="text-[10px] text-slate-400">Ctrl+Z</span>
                </button>
                <button
                  onClick={() => {
                    handleRedo();
                    setActiveDesktopMenu(null);
                  }}
                  disabled={redoStack.length === 0}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between disabled:opacity-40 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Redo2 className="w-3.5 h-3.5" /> İleri Al</span>
                  <span className="text-[10px] text-slate-400">Ctrl+Y</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <button
                  onClick={() => {
                    handleDeleteSelected();
                    setActiveDesktopMenu(null);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-red-500 hover:text-white text-red-600 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <span className="flex items-center gap-2"><Trash2 className="w-3.5 h-3.5" /> Seçilenleri Sil</span>
                  <span className="text-[10px]">Del</span>
                </button>
                <button
                  onClick={() => {
                    handleClearCanvas();
                    setActiveDesktopMenu(null);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-red-500 hover:text-white text-red-600 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <span className="flex items-center gap-2"><Trash2 className="w-3.5 h-3.5" /> Tüm Tuvali Temizle</span>
                </button>
              </div>
            )}
          </div>

          {/* Simülasyon (Simulation) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'sim' ? null : 'sim')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'sim'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Simülasyon
            </button>
            {activeDesktopMenu === 'sim' && (
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    setIsRunning(!isRunning);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {isRunning ? <Pause className="w-3.5 h-3.5 text-amber-500" /> : <Play className="w-3.5 h-3.5 text-emerald-500" />}
                    {isRunning ? 'Durdur' : 'Çalıştır'}
                  </span>
                  <span className="text-[10px] text-slate-400">Boşluk</span>
                </button>
                <button
                  onClick={() => {
                    handleSingleStep();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><StepForward className="w-3.5 h-3.5 text-blue-500" /> Tek Adım İlerle</span>
                  <span className="text-[10px] text-slate-400">F10</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase">Saat Frekansı</div>
                {[0.5, 1, 2, 4, 8, 16, 32].map((hz) => (
                  <button
                    key={hz}
                    onClick={() => {
                      setClockHz(hz);
                      setActiveDesktopMenu(null);
                    }}
                    className={`w-full text-left px-3 py-1 flex items-center justify-between cursor-pointer transition-colors ${
                      clockHz === hz ? 'text-blue-600 font-bold bg-blue-50/50' : isDark ? 'hover:bg-slate-800' : 'hover:bg-slate-100'
                    }`}
                  >
                    <span>{hz} Hz</span>
                    {clockHz === hz && <Check className="w-3.5 h-3.5 text-blue-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Araçlar (Tools) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'tools' ? null : 'tools')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'tools'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Araçlar
            </button>
            {activeDesktopMenu === 'tools' && (
              <div className={`absolute top-full left-0 mt-0.5 w-64 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    setShowKMapModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Calculator className="w-3.5 h-3.5 text-blue-500" />
                  <span>Karnaugh Haritası (K-Map Solver)</span>
                </button>
                <button
                  onClick={() => {
                    setShowNumberConverterModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Binary className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Sayı Sistemleri & Taban Dönüştürücü</span>
                </button>
                <button
                  onClick={() => {
                    setShowTruthTable(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Table className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Doğruluk Tablosu & Analiz</span>
                </button>
                <button
                  onClick={() => {
                    setShowWaveform((p) => !p);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Activity className="w-3.5 h-3.5 text-cyan-500" />
                  <span>Mantık Analizörü & Osiloskop</span>
                </button>
                <button
                  onClick={() => {
                    setShowSynthesizer(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>Boole Fonksiyonundan Devre Sentezle</span>
                </button>
                <button
                  onClick={() => {
                    setShowSubcircuitModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Package className="w-3.5 h-3.5 text-purple-500" />
                  <span>Özel Entegre (IC) Paketleyici</span>
                </button>
                <button
                  onClick={() => {
                    setShowStatsModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5 text-teal-500" />
                  <span>Devre İstatistikleri & BOM Raporu</span>
                </button>
              </div>
            )}
          </div>

          {/* Görünüm (View) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'view' ? null : 'view')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'view'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Görünüm
            </button>
            {activeDesktopMenu === 'view' && (
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    setShowLeftToolbox(!showLeftToolbox);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span>Sol Bileşen Paleti</span>
                  {showLeftToolbox && <Check className="w-3.5 h-3.5 text-blue-600" />}
                </button>
                <button
                  onClick={() => {
                    setWireStyle((prev) => (prev === 'orthogonal' ? 'bezier' : 'orthogonal'));
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span>90° Dik Kablo Modu</span>
                  {wireStyle === 'orthogonal' && <Check className="w-3.5 h-3.5 text-blue-600" />}
                </button>
                <button
                  onClick={() => {
                    setGridMode((m) => (m === 'dots' ? 'lines' : m === 'lines' ? 'clean' : 'dots'));
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span>Izgara Kılavuzları</span>
                  <span className="text-[10px] text-slate-400 font-mono">{gridMode}</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <button
                  onClick={() => {
                    handleResetView();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span>Görünümü Sıfırla (%100)</span>
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    toggleCadTheme();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span>CAD Teması ({isDark ? 'Karanlık Mod' : 'Aydınlık Mod'})</span>
                  {isDark ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-600" />}
                </button>
              </div>
            )}
          </div>

          {/* Yardım (Help) Menu */}
          <div className="relative">
            <button
              onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'help' ? null : 'help')}
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                activeDesktopMenu === 'help'
                  ? 'bg-blue-600 text-white font-bold'
                  : isDark
                  ? 'hover:bg-slate-800 text-slate-200'
                  : 'hover:bg-slate-200/80 text-slate-700'
              }`}
            >
              Yardım
            </button>
            {activeDesktopMenu === 'help' && (
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs z-50 border ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800 shadow-slate-300/50'
              }`}>
                <button
                  onClick={() => {
                    setShowAboutModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Info className="w-3.5 h-3.5 text-blue-500" />
                  <span>LogicDesign Studio Hakkında</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Dismiss overlay if activeDesktopMenu is open */}
        {activeDesktopMenu && (
          <div
            onClick={() => setActiveDesktopMenu(null)}
            className="fixed inset-0 z-30"
          />
        )}
      </div>
    );
  };

  // Render Desktop Ribbon Quick Toolbar
  const renderDesktopRibbon = () => {
    const isDark = cadTheme === 'dark';

    return (
      <div className={`h-10 border-b flex items-center px-3 gap-2 overflow-x-auto text-xs select-none transition-colors ${
        isDark ? 'bg-[#0D1322] border-slate-800 text-slate-300' : 'bg-white border-slate-200 text-slate-700 shadow-2xs'
      }`}>
        {/* File quick actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleClearCanvas()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="Yeni Devre (Ctrl+N)"
          >
            <FilePlus className="w-4 h-4 text-blue-500" />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="Devre Aç (Ctrl+O)"
          >
            <FolderOpen className="w-4 h-4 text-amber-500" />
          </button>
          <button
            onClick={() => handleExportJSON()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="JSON Kaydet (Ctrl+S)"
          >
            <Save className="w-4 h-4 text-emerald-500" />
          </button>
        </div>

        <div className={`w-[1px] h-5 mx-1 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

        {/* Undo / Redo */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleUndo()}
            disabled={historyStack.length === 0}
            className={`p-1.5 rounded-lg transition-colors disabled:opacity-30 cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="Geri Al (Ctrl+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleRedo()}
            disabled={redoStack.length === 0}
            className={`p-1.5 rounded-lg transition-colors disabled:opacity-30 cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="İleri Al (Ctrl+Y)"
          >
            <Redo2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDeleteSelected()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-red-900/50 text-slate-300 hover:text-red-300' : 'hover:bg-red-50 text-slate-600 hover:text-red-600'
            }`}
            title="Seçilenleri Sil (Del)"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        <div className={`w-[1px] h-5 mx-1 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

        {/* Simulation Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`px-3 py-1 rounded-lg font-bold flex items-center gap-1.5 text-xs transition-all cursor-pointer shadow-xs ${
              isRunning
                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
            }`}
          >
            {isRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isRunning ? 'Durdur' : 'Çalıştır'}</span>
          </button>
          <button
            onClick={() => handleSingleStep()}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
            }`}
            title="Tek Adım İlerle"
          >
            <StepForward className="w-3.5 h-3.5 text-blue-500" />
            <span className="hidden sm:inline">Adım</span>
          </button>

          {/* Clock speed dropdown */}
          <select
            value={clockHz}
            onChange={(e) => setClockHz(Number(e.target.value))}
            className={`px-2 py-1 rounded-lg text-xs font-mono font-bold cursor-pointer outline-none border ${
              isDark
                ? 'bg-slate-800 border-slate-700 text-slate-200'
                : 'bg-slate-100 border-slate-200 text-slate-800'
            }`}
          >
            {[0.5, 1, 2, 4, 8, 16, 32].map((hz) => (
              <option key={hz} value={hz}>{hz} Hz</option>
            ))}
          </select>
        </div>

        <div className={`w-[1px] h-5 mx-1 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

        {/* Primary CAD Tool Modals */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setShowKMapModal(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-blue-950/70 hover:bg-blue-900 border-blue-800 text-blue-300'
                : 'bg-blue-50 hover:bg-blue-100 border-blue-200 text-blue-700'
            }`}
            title="Karnaugh Haritası (K-Map Solver)"
          >
            <Calculator className="w-3.5 h-3.5 text-blue-500" />
            <span>K-Map</span>
          </button>

          <button
            onClick={() => setShowNumberConverterModal(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-emerald-950/70 hover:bg-emerald-900 border-emerald-800 text-emerald-300'
                : 'bg-emerald-50 hover:bg-emerald-100 border-emerald-200 text-emerald-700'
            }`}
            title="Sayı Sistemleri Taban Dönüştürücü"
          >
            <Binary className="w-3.5 h-3.5 text-emerald-500" />
            <span>Sayı Dönüşümü</span>
          </button>

          <button
            onClick={() => setShowTruthTable(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-indigo-950/70 hover:bg-indigo-900 border-indigo-800 text-indigo-300'
                : 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 text-indigo-700'
            }`}
            title="Doğruluk Tablosu"
          >
            <Table className="w-3.5 h-3.5 text-indigo-500" />
            <span>Doğruluk Tablosu</span>
          </button>

          <button
            onClick={() => setShowWaveform((p) => !p)}
            className={`px-2.5 py-1 border rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              showWaveform
                ? isDark
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
                  : 'bg-cyan-100 text-cyan-800 border-cyan-300'
                : isDark
                ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
            }`}
            title="Osiloskop & Zamanlama Analizörü"
          >
            <Activity className="w-3.5 h-3.5 text-cyan-500" />
            <span>Osiloskop</span>
          </button>

          <button
            onClick={() => setShowSynthesizer(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-amber-950/70 hover:bg-amber-900 border-amber-800 text-amber-300'
                : 'bg-amber-50 hover:bg-amber-100 border-amber-200 text-amber-700'
            }`}
            title="Boole Devre Sentezleyici"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Sentez</span>
          </button>

          <button
            onClick={() => setShowSubcircuitModal(true)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-purple-950/70 hover:bg-purple-900 border-purple-800 text-purple-300'
                : 'bg-purple-50 hover:bg-purple-100 border-purple-200 text-purple-700'
            }`}
            title="Alt Devre (IC) Paketleyici"
          >
            <Package className="w-3.5 h-3.5 text-purple-500" />
            <span>IC Paketle</span>
          </button>

          <button
            onClick={() => setShowStatsModal(true)}
            className={`px-2 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer border ${
              isDark
                ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
            }`}
            title="BOM İstatistikleri"
          >
            <BarChart3 className="w-3.5 h-3.5 text-slate-500" />
          </button>
        </div>

        <div className={`w-[1px] h-5 mx-1 ml-auto ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

        {/* View & Canvas Toggles */}
        <div className="flex items-center gap-1">
          <button
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
          </button>

          <button
            onClick={() => handleResetView()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'
            }`}
            title="Görünümü Sıfırla (%100)"
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          <button
            onClick={() => toggleCadTheme()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-amber-400' : 'hover:bg-slate-100 text-indigo-600'
            }`}
            title={`Tema: ${isDark ? 'Aydınlık Moda Geç' : 'Karanlık Moda Geç'}`}
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
          </button>
        </div>
      </div>
    );
  };

  // Render Desktop Left Component Toolbox (Logisim Explorer Panel)
  const renderDesktopLeftToolbox = () => {
    const isDark = cadTheme === 'dark';
    const q = desktopToolboxSearch.trim().toLowerCase();

    return (
      <div className={`w-64 h-full border-r flex flex-col shrink-0 select-none overflow-hidden text-xs transition-colors ${
        isDark ? 'bg-[#0B0F19] border-slate-800 text-slate-200' : 'bg-slate-50 border-slate-200 text-slate-800'
      }`}>
        {/* Header & Search */}
        <div className={`p-2.5 border-b space-y-2 ${isDark ? 'border-slate-800 bg-[#0B0F19]' : 'border-slate-200 bg-white'}`}>
          <div className="flex items-center justify-between font-bold uppercase tracking-wider text-[10px]">
            <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>Bileşen Kütüphanesi</span>
            <span className={`font-mono px-1.5 py-0.2 rounded text-[9px] ${isDark ? 'bg-blue-950 text-blue-400 border border-blue-800' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
              CAD
            </span>
          </div>
          <div className="relative">
            <Search className={`w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
            <input
              type="text"
              placeholder="Eleman ara (örn. AND, MUX)..."
              value={desktopToolboxSearch}
              onChange={(e) => setDesktopToolboxSearch(e.target.value)}
              className={`w-full pl-8 pr-2.5 py-1 rounded-lg text-xs outline-none transition-colors border ${
                isDark
                  ? 'bg-slate-900 border-slate-800 text-slate-200 placeholder-slate-500 focus:border-blue-500'
                  : 'bg-slate-50 border-slate-200 text-slate-800 placeholder-slate-400 focus:bg-white focus:border-blue-500'
              }`}
            />
          </div>
        </div>

        {/* Scrollable Categories List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {/* Built-in Categories */}
          {DESKTOP_TOOLBOX_GROUPS.map((group) => {
            const isOpen = toolboxCategoryOpen[group.id] || !!q;
            const filteredTypes = group.types.filter((t) => {
              if (!q) return true;
              const meta = COMPACT_COMPONENT_NAMES[t];
              const label = meta?.label || t;
              const badge = meta?.badge || '';
              return (
                t.toLowerCase().includes(q) ||
                label.toLowerCase().includes(q) ||
                badge.toLowerCase().includes(q)
              );
            });

            if (q && filteredTypes.length === 0) return null;

            return (
              <div
                key={group.id}
                className={`rounded-xl overflow-hidden border transition-colors ${
                  isDark
                    ? 'border-slate-800/80 bg-slate-900/40'
                    : 'border-slate-200/90 bg-white shadow-2xs'
                }`}
              >
                <button
                  onClick={() => toggleToolboxCategory(group.id)}
                  className={`w-full px-2.5 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark
                      ? 'hover:bg-slate-800/70 text-slate-300 font-semibold'
                      : 'hover:bg-slate-100 text-slate-800 font-bold'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{group.icon}</span>
                    <span className="text-xs">{group.title}</span>
                  </div>
                  {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                </button>

                {isOpen && (
                  <div className={`p-1 space-y-0.5 border-t ${
                    isDark ? 'border-slate-800/60 bg-slate-950/30' : 'border-slate-100 bg-slate-50/60'
                  }`}>
                    {filteredTypes.map((type) => {
                      const meta = COMPACT_COMPONENT_NAMES[type] || { label: type };
                      return (
                        <div
                          key={type}
                          draggable
                          onDragStart={(e) => {
                            e.dataTransfer.setData('application/logic-component', type);
                          }}
                          onClick={() => handleAddComponent(type)}
                          className={`px-2 py-1 rounded-lg border transition-all cursor-pointer flex items-center justify-between group active:scale-98 ${
                            isDark
                              ? 'border-transparent hover:bg-blue-600/20 hover:text-blue-300 hover:border-blue-500/40 text-slate-300'
                              : 'border-transparent hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 text-slate-700'
                          }`}
                          title="Tıkla veya Tuvale Sürükle-Bırak"
                        >
                          <div className="flex items-center gap-2 truncate">
                            <span className={`w-1.5 h-1.5 rounded-full shrink-0 group-hover:scale-125 transition-transform ${
                              isDark ? 'bg-blue-400' : 'bg-blue-600'
                            }`} />
                            <span className="font-medium truncate group-hover:font-semibold">
                              {meta.label}
                            </span>
                          </div>
                          {meta.badge && (
                            <span className={`text-[9.5px] font-mono px-1.5 py-0.2 rounded shrink-0 transition-colors ${
                              isDark
                                ? 'bg-slate-800 text-slate-400 group-hover:bg-blue-900/80 group-hover:text-blue-200'
                                : 'bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-800 border border-slate-200/50'
                            }`}>
                              {meta.badge}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}

          {/* Custom Subcircuits (User ICs) */}
          {customSubcircuits.length > 0 && (
            <div className={`rounded-xl overflow-hidden border transition-colors ${
              isDark ? 'border-purple-900/50 bg-purple-950/20' : 'border-purple-200 bg-purple-50/50 shadow-2xs'
            }`}>
              <button
                onClick={() => toggleToolboxCategory('subcircuits')}
                className={`w-full px-2.5 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                  isDark ? 'hover:bg-purple-900/30 text-purple-300' : 'hover:bg-purple-100/60 text-purple-900 font-bold'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">🧩</span>
                  <span>Özel Entegrelerim</span>
                </div>
                {toolboxCategoryOpen['subcircuits'] ? (
                  <ChevronUp className="w-3.5 h-3.5 text-purple-400" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-purple-400" />
                )}
              </button>

              {toolboxCategoryOpen['subcircuits'] && (
                <div className={`p-1 space-y-0.5 border-t ${
                  isDark ? 'border-purple-900/40 bg-slate-950/40' : 'border-purple-100 bg-white'
                }`}>
                  {customSubcircuits.map((sub) => (
                    <div
                      key={sub.id}
                      onClick={() => handleAddSubcircuit(sub)}
                      className={`px-2 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center justify-between ${
                        isDark ? 'hover:bg-purple-600/30 text-slate-300 hover:text-purple-200' : 'hover:bg-purple-100/80 text-slate-800 hover:text-purple-900'
                      }`}
                      title={sub.description}
                    >
                      <span className="font-medium truncate">{sub.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 bg-purple-600 text-white rounded shrink-0">
                        {sub.chipCode || 'IC'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render Desktop Bottom Status Bar
  const renderDesktopStatusBar = () => {
    const isDark = cadTheme === 'dark';

    return (
      <div className={`h-7 border-t flex items-center justify-between px-3 text-[11px] font-mono select-none transition-colors ${
        isDark ? 'bg-[#0B0F19] border-slate-800 text-slate-400' : 'bg-white border-slate-200 text-slate-600 shadow-2xs'
      }`}>
        {/* Left items */}
        <div className="flex items-center gap-3">
          {/* Running status badge */}
          <div className="flex items-center gap-1.5 font-bold">
            <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            <span className={isRunning ? 'text-emerald-600' : 'text-amber-600'}>
              {isRunning ? 'ÇALIŞIYOR' : 'DURAKLATILDI'}
            </span>
          </div>

          <div className={`w-[1px] h-3.5 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

          {/* Speed */}
          <span>Saat: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{clockHz} Hz</strong></span>

          <div className={`w-[1px] h-3.5 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

          {/* Active Sheet */}
          <span>Sayfa: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{sheets.find((s) => s.id === activeSheetId)?.name || 'Sayfa 1'}</strong></span>

          <div className={`w-[1px] h-3.5 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

          {/* Component & Wire counts */}
          <span>Bileşen: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{components.length}</strong></span>
          <span>Bağlantı: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{wires.length}</strong></span>
          <span>Adım: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{stepCount}</strong></span>
        </div>

        {/* Center tip */}
        <div className="hidden lg:block text-slate-400 text-[10px]">
          Boşluk: Oynat/Durdur · Del: Sil · Ctrl+Z: Geri Al · Sürükle-Bırak: Eleman Ekle
        </div>

        {/* Right items */}
        <div className="flex items-center gap-3">
          <span>X: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(mousePos.x)}</strong> Y: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(mousePos.y)}</strong></span>
          <div className={`w-[1px] h-3.5 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />
          <span>Yakınlaştırma: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(zoom * 100)}%</strong></span>
        </div>
      </div>
    );
  };

  // Render Extra Desktop Modals (K-Map, Number Converter, About)
  const renderDesktopExtraModals = () => {
    const isDark = cadTheme === 'dark';

    return (
      <>
        {/* K-Map Modal */}
        {showKMapModal && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className={`rounded-3xl max-w-4xl w-full shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border animate-in fade-in zoom-in-95 duration-150 ${
              isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-900'
            }`}>
              <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/15 text-blue-600 rounded-xl border border-blue-500/20">
                    <Calculator className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base">Karnaugh Haritası (K-Map) Çözücü</h3>
                    <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>2, 3 ve 4 Değişkenli Karnaugh Haritaları ile Minimum SOP / POS Çözümleri</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowKMapModal(false)}
                  className={`p-2 rounded-xl cursor-pointer transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400 hover:text-white' : 'hover:bg-slate-200 text-slate-500 hover:text-slate-900'}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto flex-1">
                <StandaloneKMapSolver />
              </div>
            </div>
          </div>
        )}

        {/* Number Converter Modal */}
        {showNumberConverterModal && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className={`rounded-3xl max-w-4xl w-full shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border animate-in fade-in zoom-in-95 duration-150 ${
              isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-900'
            }`}>
              <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/15 text-emerald-600 rounded-xl border border-emerald-500/20">
                    <Binary className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base">Sayı Sistemleri & Taban Dönüştürücü</h3>
                    <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>İkili (Bin), Onlu (Dec), Onaltılı (Hex), Sekizli (Oct) ve 2'ye Tümleyen</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowNumberConverterModal(false)}
                  className={`p-2 rounded-xl cursor-pointer transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400 hover:text-white' : 'hover:bg-slate-200 text-slate-500 hover:text-slate-900'}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto flex-1">
                <StandaloneNumberConverter />
              </div>
            </div>
          </div>
        )}

        {/* About Modal */}
        {showAboutModal && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className={`rounded-3xl max-w-lg w-full shadow-2xl flex flex-col overflow-hidden border animate-in fade-in zoom-in-95 duration-150 ${
              isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-900'
            }`}>
              <div className={`p-6 border-b flex items-center justify-between ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-blue-600/15 text-blue-600 rounded-2xl border border-blue-500/25">
                    <Cpu className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">LogicDesign Studio</h3>
                    <p className="text-xs text-blue-600 font-mono">v1.0.0 — Profesyonel Mantık CAD Simülatörü</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAboutModal(false)}
                  className={`p-2 rounded-xl cursor-pointer transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400 hover:text-white' : 'hover:bg-slate-200 text-slate-500 hover:text-slate-900'}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className={`p-6 space-y-4 text-xs leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                <p>
                  LogicDesign Studio; mantık kapıları, aritmetik birimler, çoklayıcılar, flip-floplar ve mikroişlemci mimarilerini görsel ve etkileşimli olarak tasarlayıp simüle edebileceğiniz tam teşekküllü bir masaüstü EDA (Elektronik Tasarım Otomasyonu) platformudur.
                </p>
                <div className={`grid grid-cols-2 gap-2.5 p-3 rounded-2xl border font-mono text-[11px] ${
                  isDark ? 'bg-slate-950/80 border-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-700'
                }`}>
                  <div>⚡ Simülasyon: 32Hz & Turbo</div>
                  <div>📊 K-Map Çözücü: 2-4 Değişken</div>
                  <div>🔢 Sayı Dönüşümü: 4 Taban</div>
                  <div>🎵 Chiptune: 8-Bit Ses</div>
                  <div>📈 Osiloskop: Zamanlama Analizi</div>
                  <div>🧩 Alt Devre: IC Paketleme</div>
                </div>
              </div>
              <div className={`p-4 border-t flex justify-end ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <button
                  onClick={() => setShowAboutModal(false)}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs"
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  };
'''

text = text[:idx_start] + new_desktop_render_methods + "\n" + text[idx_end:]

with open(target_file, "w", encoding="utf-8") as f:
    f.write(text)

print("2. Desktop render methods completely upgraded with adaptive light/dark theming!")
