import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

target_file = r"C:\Users\safak\Desktop\Logic Design Studio\src\components\LogisimSimulator.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Imports
import_target = "import { IC_DATASHEETS } from '../utils/icDatasheets';"
import_replacement = """import { IC_DATASHEETS } from '../utils/icDatasheets';
import { StandaloneKMapSolver } from './StandaloneKMapSolver';
import { StandaloneNumberConverter } from './StandaloneNumberConverter';
import {
  Calculator,
  FolderOpen,
  FilePlus,
  Save,
  Info,
  Zap,
} from 'lucide-react';"""

assert import_target in text, "Could not find import_target"
text = text.replace(import_target, import_replacement, 1)
print("1. Imports injected.")

# 2. LogicCircuitSimulatorProps
sig_target = "export const LogicCircuitSimulator: React.FC = () => {"
sig_replacement = """export interface LogicCircuitSimulatorProps {
  desktopMode?: boolean;
}

export const LogicCircuitSimulator: React.FC<LogicCircuitSimulatorProps> = ({ desktopMode = false }) => {"""

if sig_target in text:
    text = text.replace(sig_target, sig_replacement, 1)
elif 'export const LogicCircuitSimulator: React.FC<LogicCircuitSimulatorProps>' in text:
    text = text.replace('({ desktopMode: _desktopMode = false })', '({ desktopMode = false })')
    text = text.replace('desktopMode: _desktopMode', 'desktopMode')
print("2. LogicCircuitSimulatorProps injected.")

# 3. Desktop state & drop handlers
state_anchor = "  const toggleCadTheme = () => {"
desktop_state_code = """  // Desktop EDA CAD Mode State & Modals
  const [activeDesktopMenu, setActiveDesktopMenu] = useState<string | null>(null);
  const [showKMapModal, setShowKMapModal] = useState<boolean>(false);
  const [showNumberConverterModal, setShowNumberConverterModal] = useState<boolean>(false);
  const [showAboutModal, setShowAboutModal] = useState<boolean>(false);
  const [showPresetsModal, setShowPresetsModal] = useState<boolean>(false);
  const [presetModalSearch, setPresetModalSearch] = useState<string>('');
  const [presetFilterCat, setPresetFilterCat] = useState<string>('all');
  const [showLeftToolbox, setShowLeftToolbox] = useState<boolean>(true);
  const [desktopToolboxSearch, setDesktopToolboxSearch] = useState<string>('');
  const [toolboxCategoryOpen, setToolboxCategoryOpen] = useState<Record<string, boolean>>({
    presets: true,
    wiring: true,
    gates: true,
    plexers: false,
    arithmetic: false,
    memory: false,
    displays: true,
    audio: false,
    subcircuits: true,
  });

  const toggleToolboxCategory = (catId: string) => {
    setToolboxCategoryOpen((prev) => ({ ...prev, [catId]: !prev[catId] }));
  };

  const handleAddComponentAt = (type: ComponentType, posX: number, posY: number) => {
    recordHistory();
    const newComp = updatePinPositions(createComponentInstance(type, posX, posY));
    setComponents((prev) => {
      const updated = [...prev, newComp];
      const sim = simulateCircuit(updated, wires);
      setWires(sim.wires);
      return sim.components;
    });
    setSelectedCompId(newComp.id);
    setSelectedWireId(null);
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const compType = e.dataTransfer.getData('application/logic-component') as ComponentType;
    if (!compType) return;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    const canvasX = Math.round(((clientX - panOffset.x) / zoom) / 20) * 20;
    const canvasY = Math.round(((clientY - panOffset.y) / zoom) / 20) * 20;
    handleAddComponentAt(compType, canvasX, canvasY);
  };

"""

assert state_anchor in text, "Could not find state_anchor"
text = text.replace(state_anchor, desktop_state_code + state_anchor, 1)
print("3. Desktop state and drop handlers injected.")

# 4. Adaptive Desktop render methods (Light / Dark theming)
desktop_render_methods = '''  // DESKTOP EDA: Toolbox Groups for Left Explorer Panel
  const DESKTOP_TOOLBOX_GROUPS = useMemo(() => [
    {
      id: 'wiring',
      title: 'Kablolama & Giriş / Çıkış',
      icon: '🔌',
      types: ['switch', 'pushbutton', 'dipSwitch4', 'clock', 'vcc', 'gnd', 'probe', 'busSplitter', 'constantHigh', 'constantLow'] as ComponentType[],
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
      types: ['mux2to1', 'mux4to1', 'mux8to1', 'demux1to2', 'demux1to4', 'decoder2to4', 'decoder3to8', 'priorityEncoder4to2'] as ComponentType[],
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
      types: ['srLatch', 'dFlipFlop', 'jkFlipFlop', 'tFlipFlop', 'register4bit', 'counter4bit', 'shiftRegister4bit', 'ram16x4'] as ComponentType[],
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
          <span className={`tracking-wide font-extrabold ${isDark ? 'text-blue-400' : 'text-blue-700'}`}>LogicDesign</span>
          <span className={`text-[10px] font-mono px-1 rounded ${isDark ? 'bg-blue-950 text-blue-300' : 'bg-blue-100 text-blue-800'}`}>CAD</span>
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
              <div className={`absolute top-full left-0 mt-0.5 w-64 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
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
                  <span className="flex items-center gap-2"><FilePlus className="w-3.5 h-3.5 text-blue-500" /> Yeni Proje</span>
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
                  <span className="flex items-center gap-2"><FolderOpen className="w-3.5 h-3.5 text-amber-500" /> Proje Aç...</span>
                  <span className="text-[10px] text-slate-400">Ctrl+O</span>
                </button>
                <button
                  onClick={() => {
                    handleExportJSON();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Save className="w-3.5 h-3.5 text-emerald-500" /> Projeyi Kaydet</span>
                  <span className="text-[10px] text-slate-400">Ctrl+S</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <button
                  onClick={() => {
                    setShowPresetsModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 text-amber-500 fill-amber-500" /> Hazır Devre Şablonları...</span>
                  <span className="text-[10px] text-amber-500 font-bold px-1.5 py-0.2 bg-amber-500/10 rounded-full">{CIRCUIT_PRESETS.length}</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
                <button
                  onClick={() => {
                    handleExportCirc();
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <span className="flex items-center gap-2"><Download className="w-3.5 h-3.5 text-indigo-500" /> Logisim Dışa Aktar</span>
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
                  <span className="flex items-center gap-2"><ImageIcon className="w-3.5 h-3.5 text-pink-500" /> Resim Olarak Kaydet</span>
                  <span className="text-[10px] text-slate-400 font-mono">.png</span>
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
                  <span className="flex items-center gap-2"><FileCode className="w-3.5 h-3.5 text-purple-500" /> Vektör Kaydet</span>
                  <span className="text-[10px] text-slate-400 font-mono">.svg</span>
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
              <div className={`absolute top-full left-0 mt-0.5 w-52 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
              }`}>
                <button
                  onClick={() => {
                    handleUndo();
                    setActiveDesktopMenu(null);
                  }}
                  disabled={historyStack.length === 0}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between disabled:opacity-30 cursor-pointer transition-colors ${
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
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between disabled:opacity-30 cursor-pointer transition-colors ${
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
                  className="w-full text-left px-3 py-1.5 hover:bg-red-500 hover:text-white text-red-500 flex items-center justify-between cursor-pointer transition-colors"
                >
                  <span className="flex items-center gap-2"><Trash2 className="w-3.5 h-3.5" /> Seçilenleri Sil</span>
                  <span className="text-[10px]">Del</span>
                </button>
                <button
                  onClick={() => {
                    handleClearCanvas();
                    setActiveDesktopMenu(null);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-red-500 hover:text-white text-red-500 flex items-center justify-between cursor-pointer transition-colors"
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
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
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
                      clockHz === hz ? 'text-blue-600 font-bold bg-blue-50/50' : isDark ? 'hover:bg-slate-800 text-slate-300' : 'hover:bg-slate-100 text-slate-700'
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
              <div className={`absolute top-full left-0 mt-0.5 w-64 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
              }`}>
                <button
                  onClick={() => {
                    setShowPresetsModal(true);
                    setActiveDesktopMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2.5 cursor-pointer transition-colors ${
                    isDark ? 'hover:bg-blue-600 hover:text-white' : 'hover:bg-blue-50 hover:text-blue-700'
                  }`}
                >
                  <Zap className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                  <span>Hazır Devre Şablonları ({CIRCUIT_PRESETS.length})</span>
                </button>
                <div className={`h-[1px] my-1 ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`} />
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
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
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
              <div className={`absolute top-full left-0 mt-0.5 w-56 rounded-xl shadow-2xl py-1 text-xs border z-50 ${
                isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-200 text-slate-800'
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
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
            }`}
            title="Yeni Devre (Ctrl+N)"
          >
            <FilePlus className="w-4 h-4 text-blue-500" />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
            }`}
            title="Devre Aç (Ctrl+O)"
          >
            <FolderOpen className="w-4 h-4 text-amber-500" />
          </button>
          <button
            onClick={() => handleExportJSON()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
            }`}
            title="JSON Kaydet (Ctrl+S)"
          >
            <Save className="w-4 h-4 text-emerald-500" />
          </button>

          {/* Circuit Presets Ribbon Button */}
          <button
            onClick={() => setShowPresetsModal(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer border ${
              isDark
                ? 'bg-amber-950/60 hover:bg-amber-900/80 border-amber-700/60 text-amber-300'
                : 'bg-amber-50 hover:bg-amber-100 border-amber-300 text-amber-800 shadow-2xs'
            }`}
            title="Hazır Örnek Devreler Kütüphanesi (24 Devre)"
          >
            <Zap className="w-3.5 h-3.5 fill-amber-500 text-amber-500" />
            <span>Hazır Devreler</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
              isDark ? 'bg-amber-500/30 text-amber-200' : 'bg-amber-200/80 text-amber-900 font-bold'
            }`}>
              {CIRCUIT_PRESETS.length}
            </span>
          </button>
        </div>

        <div className={`w-[1px] h-5 mx-1 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />

        {/* Undo / Redo */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleUndo()}
            disabled={historyStack.length === 0}
            className={`p-1.5 rounded-lg transition-colors disabled:opacity-30 cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
            }`}
            title="Geri Al (Ctrl+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleRedo()}
            disabled={redoStack.length === 0}
            className={`p-1.5 rounded-lg transition-colors disabled:opacity-30 cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
            }`}
            title="İleri Al (Ctrl+Y)"
          >
            <Redo2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDeleteSelected()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-red-900/50 text-slate-300 hover:text-red-300' : 'hover:bg-red-50 text-slate-700 hover:text-red-600'
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
            className={`px-3 py-1 rounded-lg font-bold flex items-center gap-1.5 text-xs transition-colors cursor-pointer shadow-xs ${
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
            className={`px-2 py-1 rounded-lg text-xs font-mono font-bold cursor-pointer outline-none border transition-colors ${
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
          <div
            className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold border border-blue-500/40 bg-blue-500/10 text-blue-500 select-none flex items-center gap-1.5"
            title="90° Standart Logisim CAD Hatları"
          >
            <Activity className="w-3 h-3 text-blue-500" />
            <span>90° Dik Tel</span>
          </div>

          <button
            onClick={() => handleResetView()}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDark ? 'hover:bg-slate-800 text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-700 hover:text-slate-900'
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
          <div className="flex items-center justify-between font-bold uppercase tracking-wider text-[11px]">
            <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>Bileşen Kütüphanesi</span>
            <span className={`font-mono px-1.5 py-0.2 rounded text-[9px] ${isDark ? 'bg-blue-950 text-blue-400' : 'bg-blue-100 text-blue-700'}`}>
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
          {/* Circuit Presets (Hazır Devreler) Collapsible Section */}
          <div
            className={`rounded-xl overflow-hidden border transition-colors ${
              isDark
                ? 'border-amber-900/60 bg-amber-950/20'
                : 'border-amber-200/90 bg-amber-50/40 shadow-2xs'
            }`}
          >
            <button
              onClick={() => toggleToolboxCategory('presets')}
              className={`w-full px-2.5 py-1.5 flex items-center justify-between cursor-pointer transition-colors ${
                isDark
                  ? 'hover:bg-amber-900/40 text-amber-300 font-semibold'
                  : 'hover:bg-amber-100/70 text-amber-900 font-bold'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm">⚡</span>
                <span className="text-xs">Hazır Örnek Devreler</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`text-[9.5px] font-mono px-1.5 py-0.2 rounded-full font-bold ${
                  isDark ? 'bg-amber-900/60 text-amber-300' : 'bg-amber-200 text-amber-900'
                }`}>
                  {CIRCUIT_PRESETS.length}
                </span>
                {toolboxCategoryOpen['presets'] ? (
                  <ChevronUp className="w-3.5 h-3.5 text-amber-500" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-amber-500" />
                )}
              </div>
            </button>

            {toolboxCategoryOpen['presets'] && (
              <div className={`p-1 space-y-1 border-t ${
                isDark ? 'border-amber-900/40 bg-slate-950/40' : 'border-amber-100 bg-white'
              }`}>
                {/* Button to open full modal */}
                <button
                  onClick={() => setShowPresetsModal(true)}
                  className={`w-full py-1 px-2 rounded-lg text-center font-bold text-[11px] transition-colors border flex items-center justify-center gap-1.5 cursor-pointer ${
                    isDark
                      ? 'bg-amber-600/20 hover:bg-amber-600/30 border-amber-700/60 text-amber-300'
                      : 'bg-amber-100 hover:bg-amber-200 border-amber-300 text-amber-900'
                  }`}
                >
                  <Zap className="w-3 h-3 fill-amber-500 text-amber-500" />
                  <span>Tüm Şablonları Aç...</span>
                </button>

                {/* Quick presets list */}
                <div className="space-y-0.5 max-h-48 overflow-y-auto pr-0.5">
                  {CIRCUIT_PRESETS.map((preset) => (
                    <div
                      key={preset.id}
                      onClick={() => handleLoadPreset(preset.id)}
                      className={`px-2 py-1 rounded-lg border transition-all cursor-pointer flex items-center justify-between text-xs ${
                        isDark
                          ? 'border-transparent hover:bg-amber-600/20 hover:text-amber-200 text-slate-300'
                          : 'border-transparent hover:bg-amber-50 hover:text-amber-900 text-slate-700'
                      }`}
                      title={preset.description}
                    >
                      <span className="truncate font-medium">{preset.name}</span>
                      <span className={`text-[9px] font-mono shrink-0 px-1 rounded ${
                        isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {preset.components.length}e
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

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
                          className={`px-2 py-1 rounded-lg border transition-all cursor-pointer flex items-center justify-between group text-xs ${
                            isDark
                              ? 'border-transparent hover:bg-blue-600/20 hover:text-blue-300 hover:border-blue-500/30 text-slate-300'
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
                                : 'bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-700'
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
                      className={`px-2 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center justify-between text-xs ${
                        isDark ? 'hover:bg-purple-600/30 text-slate-300 hover:text-purple-200' : 'hover:bg-purple-100 text-purple-900'
                      }`}
                      title={sub.description}
                    >
                      <span className="font-medium truncate">{sub.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 bg-purple-600 text-white rounded font-bold">
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

  // Render Desktop Bottom Status Bar - Jitter Free Absolute Center and Tabular-Nums
  const renderDesktopStatusBar = () => {
    const isDark = cadTheme === 'dark';

    return (
      <div className={`h-7 border-t flex items-center justify-between px-3 text-[11px] font-mono select-none transition-colors relative ${
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

        {/* Center tip: completely decoupled and fixed in absolute center to prevent any jitter */}
        <div className="hidden xl:block absolute left-1/2 -translate-x-1/2 pointer-events-none text-center text-slate-400 text-[10px] whitespace-nowrap">
          Boşluk: Oynat/Durdur · Del: Sil · Ctrl+Z: Geri Al · Sürükle-Bırak: Eleman Ekle
        </div>

        {/* Right items: fixed width tabular-nums to prevent layout shift */}
        <div className="flex items-center gap-3">
          <div className="w-28 text-right tabular-nums whitespace-nowrap">
            <span>X: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(mousePos.x)}</strong> Y: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(mousePos.y)}</strong></span>
          </div>
          <div className={`w-[1px] h-3.5 ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`} />
          <div className="w-16 text-right tabular-nums whitespace-nowrap">
            <span>Yakınlaştırma: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{Math.round(zoom * 100)}%</strong></span>
          </div>
        </div>
      </div>
    );
  };

  // Render Extra Desktop Modals (K-Map, Number Converter, Presets, About)
  const renderDesktopExtraModals = () => {
    const isDark = cadTheme === 'dark';

    return (
      <>
        {/* Hazır Devreler (Circuit Presets) Gallery Modal */}
        {showPresetsModal && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className={`rounded-3xl max-w-5xl w-full shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border animate-in fade-in zoom-in-95 duration-150 ${
              isDark ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-900'
            }`}>
              {/* Modal Header */}
              <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-amber-500/15 text-amber-500 rounded-2xl border border-amber-500/20">
                    <Zap className="w-5 h-5 fill-amber-500" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base flex items-center gap-2">
                      <span>Hazır Devre Şablonları & Örnek Kütüphanesi</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-bold ${
                        isDark ? 'bg-amber-500/20 text-amber-300' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {CIRCUIT_PRESETS.length} Devre
                      </span>
                    </h3>
                    <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Kombinasyonel mantık, bellek elemanları, işlemci mimarisi ve retro ses/grafik donanımları
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowPresetsModal(false)}
                  className={`p-2 rounded-xl cursor-pointer transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400 hover:text-white' : 'hover:bg-slate-200 text-slate-500 hover:text-slate-900'}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Search & Category Filter Bar */}
              <div className={`p-4 border-b space-y-3 ${isDark ? 'bg-slate-950/30 border-slate-800' : 'bg-slate-50/50 border-slate-200'}`}>
                <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
                  {/* Category Pills */}
                  <div className="flex flex-wrap gap-1.5 w-full sm:w-auto">
                    {[
                      { id: 'all', label: 'Tümü', icon: '🌟' },
                      { id: 'arithmetic', label: 'Aritmetik', icon: '🧮' },
                      { id: 'sequential', label: 'Ardışıl / Bellek', icon: '⚙️' },
                      { id: 'basic', label: 'Temel Kapılar', icon: '🔌' },
                      { id: 'bus', label: 'Veri Yolu / MUX', icon: '🚌' },
                      { id: 'music_graphics', label: 'Retro Medya / GPU', icon: '🎮' },
                    ].map((cat) => {
                      const isActive = presetFilterCat === cat.id;
                      const count = cat.id === 'all'
                        ? CIRCUIT_PRESETS.length
                        : CIRCUIT_PRESETS.filter((p) => (p.category || 'basic') === cat.id).length;
                      return (
                        <button
                          key={cat.id}
                          onClick={() => setPresetFilterCat(cat.id)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                            isActive
                              ? 'bg-blue-600 text-white shadow-sm'
                              : isDark
                              ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                              : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
                          }`}
                        >
                          <span>{cat.icon}</span>
                          <span>{cat.label}</span>
                          <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                            isActive ? 'bg-white/20 text-white' : isDark ? 'bg-slate-900 text-slate-400' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {count}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Search Input */}
                  <div className="relative w-full sm:w-64 shrink-0">
                    <Search className={`w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
                    <input
                      type="text"
                      placeholder="Devre şablonu ara..."
                      value={presetModalSearch}
                      onChange={(e) => setPresetModalSearch(e.target.value)}
                      className={`w-full pl-9 pr-3 py-1.5 rounded-xl text-xs outline-none transition-colors border ${
                        isDark
                          ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500'
                          : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:border-blue-500'
                      }`}
                    />
                  </div>
                </div>
              </div>

              {/* Presets Grid */}
              <div className="p-6 overflow-y-auto flex-1 max-h-[60vh]">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {CIRCUIT_PRESETS.filter((preset) => {
                    const cat = preset.category || 'basic';
                    if (presetFilterCat !== 'all' && cat !== presetFilterCat) {
                      return false;
                    }
                    if (presetModalSearch.trim()) {
                      const q = presetModalSearch.trim().toLowerCase();
                      return (
                        preset.name.toLowerCase().includes(q) ||
                        preset.description.toLowerCase().includes(q) ||
                        cat.toLowerCase().includes(q)
                      );
                    }
                    return true;
                  }).map((preset) => {
                    const isSelected = selectedPresetId === preset.id;
                    return (
                      <div
                        key={preset.id}
                        className={`rounded-2xl p-4 border flex flex-col justify-between transition-all group ${
                          isSelected
                            ? isDark
                              ? 'border-blue-500 bg-blue-950/20 ring-1 ring-blue-500'
                              : 'border-blue-500 bg-blue-50/50 ring-1 ring-blue-500'
                            : isDark
                            ? 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-800/40'
                            : 'border-slate-200 bg-white hover:border-blue-300 hover:shadow-md'
                        }`}
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md uppercase font-bold tracking-wider ${
                              preset.category === 'arithmetic'
                                ? 'bg-blue-500/15 text-blue-500'
                                : preset.category === 'sequential'
                                ? 'bg-purple-500/15 text-purple-500'
                                : preset.category === 'music_graphics'
                                ? 'bg-pink-500/15 text-pink-500'
                                : preset.category === 'bus'
                                ? 'bg-indigo-500/15 text-indigo-500'
                                : 'bg-emerald-500/15 text-emerald-500'
                            }`}>
                              {preset.category}
                            </span>
                            <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
                              <span>{preset.components.length} eleman</span>
                              <span>·</span>
                              <span>{preset.wires.length} tel</span>
                            </div>
                          </div>

                          <h4 className="font-bold text-sm leading-snug group-hover:text-blue-500 transition-colors">
                            {preset.name}
                          </h4>

                          <p className={`text-xs leading-relaxed line-clamp-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                            {preset.description}
                          </p>
                        </div>

                        <div className="pt-4 mt-2 border-t border-dashed border-slate-200 dark:border-slate-800 flex items-center justify-between">
                          <span className="text-[11px] text-slate-400 font-mono">
                            ID: {preset.id}
                          </span>
                          <button
                            onClick={() => {
                              handleLoadPreset(preset.id);
                              setShowPresetsModal(false);
                            }}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer hover:scale-105 active:scale-95"
                          >
                            <Zap className="w-3.5 h-3.5 fill-current" />
                            <span>Tuvale Yükle</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Modal Footer */}
              <div className={`p-4 border-t flex items-center justify-between ${isDark ? 'bg-slate-950/60 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Bir şablon yüklendiğinde mevcut çalışma geçmişe kaydedilir (Ctrl+Z ile geri alınabilir).
                </span>
                <button
                  onClick={() => setShowPresetsModal(false)}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer transition-colors ${
                    isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-200 hover:bg-slate-300 text-slate-700'
                  }`}
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        )}

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
                    <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>İkili (Bin), Onlu (Dec), Onaltılı (Hex) ve Sekizli (Oct) Taban Dönüşümü</p>
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
                  <div className="p-2.5 bg-blue-600/15 text-blue-600 rounded-2xl border border-blue-600/20">
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
                  LogicDesign Studio; mantık kapıları, aritmetik birimler, çoklayıcılar, flip-floplar, bellek elemanları, K-Map çözücü, sayı taban dönüştürücü ve ses sentezleyicisi barındıran tam teşekküllü masaüstü EDA CAD ortamıdır.
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
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold cursor-pointer transition-colors shadow-xs"
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

# 5. Insert desktop render methods before main return
return_open_str = '  return (\n    <div className="space-y-6 max-w-7xl mx-auto">'
assert return_open_str in text, "Could not find return_open_str"
text = text.replace(return_open_str, desktop_render_methods + "\n" + return_open_str, 1)
print("4. Desktop render methods injected.")

# Part A: Main Return opening with dynamic cadTheme
part_a_target = '''    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Educational Header - Clean, Spacious & Responsive */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">'''

part_a_repl = '''    <div className={desktopMode ? `w-screen h-screen overflow-hidden flex flex-col select-none transition-colors ${cadTheme === 'dark' ? 'bg-[#090D16] text-slate-100' : 'bg-slate-50 text-slate-900'}` : "space-y-6 max-w-7xl mx-auto"}>
      {desktopMode ? (
        <>
          {renderDesktopMenuBar()}
          {renderDesktopRibbon()}
        </>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6">'''

# Part B: Educational header end & Stage Card opening
part_b_target = '''            </div>
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

part_b_repl = '''            </div>
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

# Apply Part A and Part B
assert part_a_target in text, "Could not find part_a_target"
text = text.replace(part_a_target, part_a_repl, 1)
print("5. Applied Part A")

assert part_b_target in text, "Could not find part_b_target"
text = text.replace(part_b_target, part_b_repl, 1)
print("5. Applied Part B")

# Part C: Wrap web palette end right before Multi-Sheet Project Workspace Tabs Header
marker_sheet = "{/* Multi-Sheet Project Workspace Tabs Header */}"
idx_sheet = text.find(marker_sheet)
assert idx_sheet != -1, "Could not find marker_sheet"
text = text[:idx_sheet] + "</>\n          )}\n\n        " + text[idx_sheet:]
print("5. Applied Part C")

# Part D: Interactive Canvas container styling & drag-and-drop
canvas_marker = "{/* Interactive SVG Canvas */}"
idx_canvas = text.find(canvas_marker)
assert idx_canvas != -1, "Could not find canvas_marker"

target_canvas_block = '''        {/* Interactive SVG Canvas */}
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
              draggingWireJoint
                ? 'cursor-ew-resize select-none'
                : isPanning
                ? 'cursor-grabbing'
                : isSpacePressedRef.current || canvasMode === 'pan'
                ? 'cursor-grab'
                : 'cursor-crosshair'
            }`}
            style={{ minHeight: '560px' }}'''

repl_canvas_block = '''        {/* Interactive SVG Canvas */}
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
              draggingWireJoint
                ? 'cursor-ew-resize select-none'
                : isPanning
                ? 'cursor-grabbing'
                : isSpacePressedRef.current || canvasMode === 'pan'
                ? 'cursor-grab'
                : 'cursor-crosshair'
            }`}
            style={desktopMode ? { width: '100%', height: '100%' } : { minHeight: '560px' }}'''

# Replace canvas div dynamically
idx_c = text.find('ref={canvasContainerRef}')
if idx_c != -1:
    div_start = text.rfind('<div', 0, idx_c)
    div_end = text.find('>', idx_c) + 1
    canvas_div_repl = '''<div
          ref={canvasContainerRef}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleCanvasDrop}
          className={`relative flex-1 w-full h-full min-h-0 overflow-hidden select-none transition-colors ${
            cadTheme === 'dark' ? 'bg-[#070A12]' : 'bg-slate-50/60'
          }`}
          style={desktopMode ? { width: '100%', height: '100%' } : { minHeight: '560px' }}
        >'''
    text = text[:div_start] + canvas_div_repl + text[div_end:]
    # Also update svg style
    svg_idx = text.find('<svg', div_start)
    if svg_idx != -1:
        svg_style_idx = text.find("style={{ minHeight: '560px' }}", svg_idx)
        if svg_style_idx != -1 and svg_style_idx < svg_idx + 600:
            text = text[:svg_style_idx] + "style={desktopMode ? { width: '100%', height: '100%' } : { minHeight: '560px' }}" + text[svg_style_idx + len("style={{ minHeight: '560px' }}"):]
print("5. Applied Part D")

# Part E: Bottom Bar (Live Logic Analyzer / Truth Bar)
live_logic_marker = "{/* Live Logic Analyzer / Truth Bar */}"
idx_live = text.find(live_logic_marker)
assert idx_live != -1, "Could not find live_logic_marker"

timing_marker = "{/* Digital Timing Diagram / Oscilloscope Panel (Timing Scope) */}"
idx_timing = text.find(timing_marker)
assert idx_timing != -1, "Could not find timing_marker"

live_block_full = text[idx_live:idx_timing]
div_start = live_block_full.find("<div className={`p-5 border-t")
assert div_start != -1, "Could not find div_start in live_block_full"

last_div = live_block_full.rfind("</div>")
second_last_div = live_block_full.rfind("</div>", 0, last_div)
original_live_div = live_block_full[div_start:second_last_div + 6]

new_live_block = '''{/* Bottom Bar: Desktop Status Bar vs Web Live Analyzer */}
        {desktopMode ? (
          renderDesktopStatusBar()
        ) : (
          ''' + original_live_div + '''
        )}
        </div>
      </div>

      '''

text = text[:idx_live] + new_live_block + text[idx_timing:]
print("5. Applied Part E")

# Part F: Modals before toast
toast_marker = "{/* Floating Action Toast Notification */}"
idx_toast = text.find(toast_marker)
assert idx_toast != -1, "Could not find toast_marker"

extra_modals_code = '''{/* Desktop Extra Modals (K-Map, Number Converter, Presets, About) */}
      {desktopMode && renderDesktopExtraModals()}

      '''
text = text[:idx_toast] + extra_modals_code + text[idx_toast:]
print("5. Applied Part F")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: LogisimSimulator.tsx completely generated with full adaptive theming, jitter-free status bar, and Hazır Devreler presets!")
