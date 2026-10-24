import os
import sys

# Configure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

target_file = r"C:\Users\safak\Desktop\Logic Design Studio\src\components\LogisimSimulator.tsx"

with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add StandaloneKMapSolver and StandaloneNumberConverter and extra Lucide icons
import_target = "import { IC_DATASHEETS } from '../utils/icDatasheets';"
import_replacement = """import { IC_DATASHEETS } from '../utils/icDatasheets';
import { StandaloneKMapSolver } from './StandaloneKMapSolver';
import { StandaloneNumberConverter } from './StandaloneNumberConverter';
import {
  Calculator,
  FolderOpen,
  FilePlus,
  Save,
  HelpCircle,
  Info,
  Folder,
  FolderClosed,
} from 'lucide-react';"""

if import_target in code and "StandaloneKMapSolver" not in code:
    code = code.replace(import_target, import_replacement, 1)
    print("1. Injected component and icon imports.")
else:
    print("1. Imports already present or target not found.")

# 2. Update LogicCircuitSimulator signature and interface
decl_target = "export const LogicCircuitSimulator: React.FC = () => {"
decl_replacement = """export interface LogicCircuitSimulatorProps {
  desktopMode?: boolean;
}

export const LogicCircuitSimulator: React.FC<LogicCircuitSimulatorProps> = ({ desktopMode = false }) => {"""

if decl_target in code:
    code = code.replace(decl_target, decl_replacement, 1)
    print("2. Injected LogicCircuitSimulatorProps interface.")
else:
    print("2. Function signature already updated or not found.")

# 3. Inject Desktop State & Helpers inside LogicCircuitSimulator
state_anchor = "  const toggleCadTheme = () => {"
desktop_state_code = """  // Desktop EDA CAD Mode State & Modals
  const [activeDesktopMenu, setActiveDesktopMenu] = useState<string | null>(null);
  const [showKMapModal, setShowKMapModal] = useState<boolean>(false);
  const [showNumberConverterModal, setShowNumberConverterModal] = useState<boolean>(false);
  const [showAboutModal, setShowAboutModal] = useState<boolean>(false);
  const [showLeftToolbox, setShowLeftToolbox] = useState<boolean>(true);
  const [desktopToolboxSearch, setDesktopToolboxSearch] = useState<string>('');
  const [toolboxCategoryOpen, setToolboxCategoryOpen] = useState<Record<string, boolean>>({
    wiring: true,
    gates: true,
    plexers: false,
    arithmetic: false,
    memory: false,
    displays: true,
    audio: false,
    subcircuits: true,
  });
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

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

if state_anchor in code and "activeDesktopMenu" not in code:
    code = code.replace(state_anchor, desktop_state_code + state_anchor, 1)
    print("3. Injected desktop states and drop handlers.")
else:
    print("3. Desktop state already present or anchor not found.")

# Save intermediate
with open(target_file, "w", encoding="utf-8") as f:
    f.write(code)

print("Phase 1 complete.")
