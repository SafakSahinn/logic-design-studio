import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\safak\Desktop\Logic Design Studio\src\utils\circuitEngine.ts', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('export const CIRCUIT_PRESETS: CircuitPreset[] = [')
import re
block = text[idx:idx+45000]
presets = re.findall(r"id:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*description:\s*['\"]([^'\"]+)['\"],\s*category:\s*['\"]([^'\"]+)['\"]", block)
for p in presets:
    print(f"[{p[3]}] {p[1]} (id: {p[0]})")
print(f"Total presets: {len(presets)}")
