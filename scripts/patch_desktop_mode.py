import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_file = r"C:\Users\safak\Desktop\Logic Design Studio\src\components\LogisimSimulator.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    text = f.read()

# Let's define DESKTOP_TOOLBOX_GROUPS and render methods
desktop_render_methods = '''
  // DESKTOP EDA: Toolbox Groups for Left Explorer Panel
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
  const renderDesktopMenuBar = () => (
    <div className="h-7 bg-[#0f172a] border-b border-slate-800 flex items-center px-2 text-xs font-medium text-slate-300 select-none relative z-40">
      <div className="flex items-center gap-1.5 mr-4 font-bold text-blue-400">
        <Cpu className="w-3.5 h-3.5 text-blue-400" />
        <span className="tracking-wide">LogicDesign Studio</span>
      </div>

      {/* Menus */}
      <div className="flex items-center gap-1">
        {/* Dosya (File) Menu */}
        <div className="relative">
          <button
            onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'file' ? null : 'file')}
            className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              activeDesktopMenu === 'file' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Dosya
          </button>
          {activeDesktopMenu === 'file' && (
            <div className="absolute top-full left-0 mt-0.5 w-60 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  handleClearCanvas();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><FilePlus className="w-3.5 h-3.5" /> Yeni Devre</span>
                <span className="text-[10px] text-slate-400">Ctrl+N</span>
              </button>
              <button
                onClick={() => {
                  fileInputRef.current?.click();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><FolderOpen className="w-3.5 h-3.5" /> Devre Aç... (.json / .circ)</span>
                <span className="text-[10px] text-slate-400">Ctrl+O</span>
              </button>
              <div className="h-[1px] bg-slate-800 my-1" />
              <button
                onClick={() => {
                  handleExportJSON();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><Save className="w-3.5 h-3.5" /> JSON Kaydet</span>
                <span className="text-[10px] text-slate-400">Ctrl+S</span>
              </button>
              <button
                onClick={() => {
                  handleExportCirc();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><Download className="w-3.5 h-3.5" /> Logisim .circ Dışa Aktar</span>
                <span className="text-[10px] text-slate-400">Logisim</span>
              </button>
              <button
                onClick={() => {
                  handleExportPNG();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><ImageIcon className="w-3.5 h-3.5" /> PNG Şematik Çıkar</span>
              </button>
              <button
                onClick={() => {
                  handleExportSVG();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><FileCode className="w-3.5 h-3.5" /> SVG Vektör Çıkar</span>
              </button>
            </div>
          )}
        </div>

        {/* Düzen (Edit) Menu */}
        <div className="relative">
          <button
            onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'edit' ? null : 'edit')}
            className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              activeDesktopMenu === 'edit' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Düzen
          </button>
          {activeDesktopMenu === 'edit' && (
            <div className="absolute top-full left-0 mt-0.5 w-52 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  undo();
                  setActiveDesktopMenu(null);
                }}
                disabled={!canUndo}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between disabled:opacity-40 cursor-pointer"
              >
                <span className="flex items-center gap-2"><Undo2 className="w-3.5 h-3.5" /> Geri Al</span>
                <span className="text-[10px] text-slate-400">Ctrl+Z</span>
              </button>
              <button
                onClick={() => {
                  redo();
                  setActiveDesktopMenu(null);
                }}
                disabled={!canRedo}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between disabled:opacity-40 cursor-pointer"
              >
                <span className="flex items-center gap-2"><Redo2 className="w-3.5 h-3.5" /> İleri Al</span>
                <span className="text-[10px] text-slate-400">Ctrl+Y</span>
              </button>
              <div className="h-[1px] bg-slate-800 my-1" />
              <button
                onClick={() => {
                  handleDeleteSelected();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-red-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><Trash2 className="w-3.5 h-3.5" /> Seçilenleri Sil</span>
                <span className="text-[10px] text-slate-400">Del</span>
              </button>
              <button
                onClick={() => {
                  handleClearCanvas();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-red-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><Trash2 className="w-3.5 h-3.5" /> Tuvali Temizle</span>
              </button>
            </div>
          )}
        </div>

        {/* Simülasyon (Simulation) Menu */}
        <div className="relative">
          <button
            onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'sim' ? null : 'sim')}
            className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              activeDesktopMenu === 'sim' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Simülasyon
          </button>
          {activeDesktopMenu === 'sim' && (
            <div className="absolute top-full left-0 mt-0.5 w-56 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  setIsRunning(!isRunning);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2">
                  {isRunning ? <Pause className="w-3.5 h-3.5 text-amber-400" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                  {isRunning ? 'Durdur' : 'Çalıştır'}
                </span>
                <span className="text-[10px] text-slate-400">Boşluk</span>
              </button>
              <button
                onClick={() => {
                  handleSingleStep();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span className="flex items-center gap-2"><StepForward className="w-3.5 h-3.5" /> Tek Adım İlerle</span>
                <span className="text-[10px] text-slate-400">F10</span>
              </button>
              <div className="h-[1px] bg-slate-800 my-1" />
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase">Saat Frekansı</div>
              {[1, 2, 4, 8, 16, 32].map((hz) => (
                <button
                  key={hz}
                  onClick={() => {
                    setClockHz(hz);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer ${
                    clockHz === hz ? 'text-blue-400 font-bold' : ''
                  }`}
                >
                  <span>{hz} Hz</span>
                  {clockHz === hz && <Check className="w-3 h-3 text-blue-400" />}
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
              activeDesktopMenu === 'tools' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Araçlar
          </button>
          {activeDesktopMenu === 'tools' && (
            <div className="absolute top-full left-0 mt-0.5 w-64 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  setShowKMapModal(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Calculator className="w-3.5 h-3.5 text-blue-400" />
                <span>Karnaugh Haritası (K-Map Solver)</span>
              </button>
              <button
                onClick={() => {
                  setShowNumberConverterModal(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Binary className="w-3.5 h-3.5 text-emerald-400" />
                <span>Sayı Sistemleri & Taban Dönüştürücü</span>
              </button>
              <button
                onClick={() => {
                  setShowTruthTable(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Table className="w-3.5 h-3.5 text-indigo-400" />
                <span>Doğruluk Tablosu & Analiz</span>
              </button>
              <button
                onClick={() => {
                  setShowWaveform((p) => !p);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                <span>Mantık Analizörü & Osiloskop</span>
              </button>
              <button
                onClick={() => {
                  setShowSynthesizer(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Boole Fonksiyonundan Devre Sentezle</span>
              </button>
              <button
                onClick={() => {
                  setShowSubcircuitModal(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Package className="w-3.5 h-3.5 text-purple-400" />
                <span>Özel Entegre (IC) Paketleyici</span>
              </button>
              <button
                onClick={() => {
                  setShowStatsModal(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
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
              activeDesktopMenu === 'view' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Görünüm
          </button>
          {activeDesktopMenu === 'view' && (
            <div className="absolute top-full left-0 mt-0.5 w-56 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  setShowLeftToolbox(!showLeftToolbox);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span>Sol Bileşen Paleti</span>
                {showLeftToolbox && <Check className="w-3 h-3 text-blue-400" />}
              </button>
              <button
                onClick={() => {
                  setWireStyle((prev) => (prev === 'orthogonal' ? 'bezier' : 'orthogonal'));
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span>90° Dik Kablo Modu</span>
                {wireStyle === 'orthogonal' && <Check className="w-3 h-3 text-blue-400" />}
              </button>
              <button
                onClick={() => {
                  setGridMode((m) => (m === 'dots' ? 'lines' : m === 'lines' ? 'clean' : 'dots'));
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span>Izgara Kılavuzları</span>
                <span className="text-[10px] text-slate-400">{gridMode}</span>
              </button>
              <div className="h-[1px] bg-slate-800 my-1" />
              <button
                onClick={() => {
                  handleResetView();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span>Görünümü Sıfırla (%100)</span>
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  toggleCadTheme();
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center justify-between cursor-pointer"
              >
                <span>CAD Teması ({cadTheme === 'dark' ? 'Karanlık' : 'Aydınlık'})</span>
                {cadTheme === 'dark' ? <Moon className="w-3.5 h-3.5" /> : <Sun className="w-3.5 h-3.5" />}
              </button>
            </div>
          )}
        </div>

        {/* Yardım (Help) Menu */}
        <div className="relative">
          <button
            onClick={() => setActiveDesktopMenu(activeDesktopMenu === 'help' ? null : 'help')}
            className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
              activeDesktopMenu === 'help' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-200'
            }`}
          >
            Yardım
          </button>
          {activeDesktopMenu === 'help' && (
            <div className="absolute top-full left-0 mt-0.5 w-56 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 text-xs text-slate-200 z-50">
              <button
                onClick={() => {
                  setShowAboutModal(true);
                  setActiveDesktopMenu(null);
                }}
                className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white flex items-center gap-2 cursor-pointer"
              >
                <Info className="w-3.5 h-3.5 text-blue-400" />
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

  // Render Desktop Ribbon Quick Toolbar
  const renderDesktopRibbon = () => (
    <div className="h-10 bg-[#0B0F19] border-b border-slate-800 flex items-center px-3 gap-2 overflow-x-auto text-xs select-none">
      {/* File quick actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => handleClearCanvas()}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors cursor-pointer"
          title="Yeni Devre (Ctrl+N)"
        >
          <FilePlus className="w-4 h-4" />
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors cursor-pointer"
          title="Devre Aç (Ctrl+O)"
        >
          <FolderOpen className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleExportJSON()}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors cursor-pointer"
          title="JSON Kaydet (Ctrl+S)"
        >
          <Save className="w-4 h-4" />
        </button>
      </div>

      <div className="w-[1px] h-5 bg-slate-800 mx-1" />

      {/* Undo / Redo */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => undo()}
          disabled={!canUndo}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors disabled:opacity-30 cursor-pointer"
          title="Geri Al (Ctrl+Z)"
        >
          <Undo2 className="w-4 h-4" />
        </button>
        <button
          onClick={() => redo()}
          disabled={!canRedo}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors disabled:opacity-30 cursor-pointer"
          title="İleri Al (Ctrl+Y)"
        >
          <Redo2 className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleDeleteSelected()}
          className="p-1.5 hover:bg-red-900/50 text-slate-300 hover:text-red-300 rounded-lg transition-colors cursor-pointer"
          title="Seçilenleri Sil (Del)"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="w-[1px] h-5 bg-slate-800 mx-1" />

      {/* Simulation Controls */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => setIsRunning(!isRunning)}
          className={`px-3 py-1 rounded-lg font-bold flex items-center gap-1.5 text-xs transition-all cursor-pointer shadow-xs ${
            isRunning
              ? 'bg-amber-600 hover:bg-amber-500 text-white'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white'
          }`}
        >
          {isRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isRunning ? 'Durdur' : 'Çalıştır'}</span>
        </button>
        <button
          onClick={() => handleSingleStep()}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer"
          title="Tek Adım İlerle"
        >
          <StepForward className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Adım</span>
        </button>

        {/* Clock speed dropdown */}
        <select
          value={clockHz}
          onChange={(e) => setClockHz(Number(e.target.value))}
          className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-200 rounded-lg text-xs font-mono font-bold cursor-pointer outline-none"
        >
          {[0.5, 1, 2, 4, 8, 16, 32].map((hz) => (
            <option key={hz} value={hz}>{hz} Hz</option>
          ))}
        </select>
      </div>

      <div className="w-[1px] h-5 bg-slate-800 mx-1" />

      {/* Primary CAD Tool Modals */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => setShowKMapModal(true)}
          className="px-2.5 py-1 bg-blue-950/70 hover:bg-blue-900 border border-blue-800 text-blue-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Karnaugh Haritası (K-Map Solver)"
        >
          <Calculator className="w-3.5 h-3.5 text-blue-400" />
          <span>K-Map</span>
        </button>

        <button
          onClick={() => setShowNumberConverterModal(true)}
          className="px-2.5 py-1 bg-emerald-950/70 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Sayı Sistemleri Taban Dönüştürücü"
        >
          <Binary className="w-3.5 h-3.5 text-emerald-400" />
          <span>Sayı Dönüşümü</span>
        </button>

        <button
          onClick={() => setShowTruthTable(true)}
          className="px-2.5 py-1 bg-indigo-950/70 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Doğruluk Tablosu"
        >
          <Table className="w-3.5 h-3.5 text-indigo-400" />
          <span>Doğruluk Tablosu</span>
        </button>

        <button
          onClick={() => setShowWaveform((p) => !p)}
          className={`px-2.5 py-1 border rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
            showWaveform
              ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
          }`}
          title="Osiloskop & Zamanlama Analizörü"
        >
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>Osiloskop</span>
        </button>

        <button
          onClick={() => setShowSynthesizer(true)}
          className="px-2.5 py-1 bg-amber-950/70 hover:bg-amber-900 border border-amber-800 text-amber-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Boole Devre Sentezleyici"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Sentez</span>
        </button>

        <button
          onClick={() => setShowSubcircuitModal(true)}
          className="px-2.5 py-1 bg-purple-950/70 hover:bg-purple-900 border border-purple-800 text-purple-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Alt Devre (IC) Paketleyici"
        >
          <Package className="w-3.5 h-3.5 text-purple-400" />
          <span>IC Paketle</span>
        </button>

        <button
          onClick={() => setShowStatsModal(true)}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer"
          title="BOM İstatistikleri"
        >
          <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
        </button>
      </div>

      <div className="w-[1px] h-5 bg-slate-800 mx-1 ml-auto" />

      {/* View & Canvas Toggles */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => setWireStyle((p) => (p === 'orthogonal' ? 'bezier' : 'orthogonal'))}
          className={`px-2 py-1 rounded-lg text-xs font-mono font-bold transition-colors cursor-pointer ${
            wireStyle === 'orthogonal' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'
          }`}
          title="Kablo Yönlendirme: 90° Manhattan vs Eğri"
        >
          {wireStyle === 'orthogonal' ? '90° Dik Tel' : 'Eğri Tel'}
        </button>

        <button
          onClick={() => handleResetView()}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors cursor-pointer"
          title="Görünümü Sıfırla (%100)"
        >
          <Maximize2 className="w-4 h-4" />
        </button>

        <button
          onClick={() => toggleCadTheme()}
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg transition-colors cursor-pointer"
          title="Aydınlık / Karanlık Tema"
        >
          {cadTheme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
        </button>
      </div>
    </div>
  );

  // Render Desktop Left Component Toolbox (Logisim Explorer Panel)
  const renderDesktopLeftToolbox = () => {
    const q = desktopToolboxSearch.trim().toLowerCase();

    return (
      <div className="w-64 h-full bg-[#0B0F19] border-r border-slate-800 flex flex-col shrink-0 select-none overflow-hidden text-xs">
        {/* Header & Search */}
        <div className="p-2.5 border-b border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[10px]">
            <span>Bileşen Kütüphanesi</span>
            <span className="text-blue-400 font-mono">EDA CAD</span>
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Eleman ara (örn. AND, MUX, RAM)..."
              value={desktopToolboxSearch}
              onChange={(e) => setDesktopToolboxSearch(e.target.value)}
              className="w-full pl-8 pr-2.5 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        {/* Scrollable Categories List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
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
              <div key={group.id} className="border border-slate-800/80 rounded-xl bg-slate-900/50 overflow-hidden">
                <button
                  onClick={() => toggleToolboxCategory(group.id)}
                  className="w-full px-2.5 py-1.5 flex items-center justify-between hover:bg-slate-800/70 transition-colors cursor-pointer text-slate-300 font-semibold"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{group.icon}</span>
                    <span>{group.title}</span>
                  </div>
                  {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-slate-500" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />}
                </button>

                {isOpen && (
                  <div className="p-1 space-y-0.5 border-t border-slate-800/60 bg-slate-950/40">
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
                          className="px-2 py-1.5 rounded-lg hover:bg-blue-600/20 hover:text-blue-300 hover:border-blue-500/40 border border-transparent transition-all cursor-pointer flex items-center justify-between group active:scale-98"
                          title="Tıkla veya Tuvale Sürükle-Bırak"
                        >
                          <div className="flex items-center gap-2 truncate">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500/80 group-hover:scale-125 transition-transform shrink-0" />
                            <span className="text-slate-300 font-medium group-hover:text-white truncate">
                              {meta.label}
                            </span>
                          </div>
                          {meta.badge && (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 group-hover:bg-blue-900/80 group-hover:text-blue-200 shrink-0">
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
            <div className="border border-purple-900/50 rounded-xl bg-purple-950/20 overflow-hidden">
              <button
                onClick={() => toggleToolboxCategory('subcircuits')}
                className="w-full px-2.5 py-1.5 flex items-center justify-between hover:bg-purple-900/30 transition-colors cursor-pointer text-purple-300 font-semibold"
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
                <div className="p-1 space-y-0.5 border-t border-purple-900/40 bg-slate-950/40">
                  {customSubcircuits.map((sub) => (
                    <div
                      key={sub.id}
                      onClick={() => handleAddSubcircuit(sub)}
                      className="px-2 py-1.5 rounded-lg hover:bg-purple-600/30 text-slate-300 hover:text-purple-200 transition-colors cursor-pointer flex items-center justify-between"
                      title={sub.description}
                    >
                      <span className="font-medium truncate">{sub.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 bg-purple-900/80 text-purple-300 rounded shrink-0">
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
  const renderDesktopStatusBar = () => (
    <div className="h-7 bg-[#0B0F19] border-t border-slate-800 flex items-center justify-between px-3 text-[11px] font-mono text-slate-400 select-none">
      {/* Left items */}
      <div className="flex items-center gap-3">
        {/* Running status badge */}
        <div className="flex items-center gap-1.5 font-bold">
          <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span className={isRunning ? 'text-emerald-400' : 'text-amber-400'}>
            {isRunning ? 'ÇALIŞIYOR' : 'DURAKLATILDI'}
          </span>
        </div>

        <div className="w-[1px] h-3.5 bg-slate-800" />

        {/* Speed */}
        <span>Saat: <strong className="text-slate-200">{clockHz} Hz</strong></span>

        <div className="w-[1px] h-3.5 bg-slate-800" />

        {/* Active Sheet */}
        <span>Sayfa: <strong className="text-slate-200">{sheets.find((s) => s.id === activeSheetId)?.name || 'Sayfa 1'}</strong></span>

        <div className="w-[1px] h-3.5 bg-slate-800" />

        {/* Component & Wire counts */}
        <span>Bileşen: <strong className="text-slate-200">{components.length}</strong></span>
        <span>Bağlantı: <strong className="text-slate-200">{wires.length}</strong></span>
        <span>Adım: <strong className="text-slate-200">{stepCount}</strong></span>
      </div>

      {/* Center tip */}
      <div className="hidden lg:block text-slate-500 text-[10px]">
        Boşluk: Oynat/Durdur · Del: Sil · Ctrl+Z: Geri Al · Sürükle-Bırak: Eleman Ekle
      </div>

      {/* Right items */}
      <div className="flex items-center gap-3">
        <span>X: <strong className="text-slate-200">{Math.round(mousePos.x)}</strong> Y: <strong className="text-slate-200">{Math.round(mousePos.y)}</strong></span>
        <div className="w-[1px] h-3.5 bg-slate-800" />
        <span>Yakınlaştırma: <strong className="text-slate-200">{Math.round(zoom * 100)}%</strong></span>
      </div>
    </div>
  );

  // Render Extra Desktop Modals (K-Map, Number Converter, About)
  const renderDesktopExtraModals = () => (
    <>
      {/* K-Map Modal */}
      {showKMapModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 text-white rounded-3xl max-w-4xl w-full shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30">
                  <Calculator className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Karnaugh Haritası (K-Map) Çözücü</h3>
                  <p className="text-xs text-slate-400">2, 3 ve 4 Değişkenli Karnaugh Haritaları ile Minimum SOP / POS Çözümleri</p>
                </div>
              </div>
              <button
                onClick={() => setShowKMapModal(false)}
                className="p-2 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-white cursor-pointer"
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
        <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 text-white rounded-3xl max-w-4xl w-full shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
                  <Binary className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Sayı Sistemleri & Taban Dönüştürücü</h3>
                  <p className="text-xs text-slate-400">İkili (Bin), Onlu (Dec), Onaltılı (Hex), Sekizli (Oct) ve 2'ye Tümleyen</p>
                </div>
              </div>
              <button
                onClick={() => setShowNumberConverterModal(false)}
                className="p-2 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-white cursor-pointer"
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
        <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 text-white rounded-3xl max-w-lg w-full shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-2xl border border-blue-500/30">
                  <Cpu className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-white">LogicDesign Studio</h3>
                  <p className="text-xs text-blue-400 font-mono">v1.0.0 — Profesyonel Mantık CAD Simülatörü</p>
                </div>
              </div>
              <button
                onClick={() => setShowAboutModal(false)}
                className="p-2 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4 text-xs text-slate-300 leading-relaxed">
              <p>
                LogicDesign Studio; mantık kapıları, aritmetik birimler, çoklayıcılar, flip-floplar ve mikroişlemci mimarilerini görsel ve etkileşimli olarak tasarlayıp simüle edebileceğiniz tam teşekküllü bir masaüstü EDA (Elektronik Tasarım Otomasyonu) platformudur.
              </p>
              <div className="grid grid-cols-2 gap-2.5 p-3 bg-slate-950/80 rounded-2xl border border-slate-800 font-mono text-[11px]">
                <div>⚡ Simülasyon: 64Hz & Turbo</div>
                <div>📊 K-Map Çözücü: 2-4 Değişken</div>
                <div>🔢 Sayı Dönüşümü: 4 Taban</div>
                <div>🎵 Chiptune: 8-Bit Ses</div>
                <div>📈 Osiloskop: Zamanlama Analizi</div>
                <div>🧩 Alt Devre: IC Paketleme</div>
              </div>
            </div>
            <div className="p-4 bg-slate-950/60 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setShowAboutModal(false)}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
'''

# Check if desktop_render_methods is already in text
if "renderDesktopMenuBar" not in text:
    # Insert right before return (
    return_marker = "  return (\n    <div className=\"space-y-6 max-w-7xl mx-auto\">"
    if return_marker in text:
        text = text.replace(return_marker, desktop_render_methods + "\n" + return_marker, 1)
        print("Inserted desktop render methods.")
    else:
        print("Return marker not found!")
else:
    print("Desktop render methods already present.")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(text)

print("Patch methods step done.")
