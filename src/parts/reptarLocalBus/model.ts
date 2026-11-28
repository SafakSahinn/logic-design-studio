// Reptar Local Bus part: pins and geometry, after Logisim-evolution's std/io/ReptarLocalBus ("ReptarLB").
//
// The part is the FPGA side of the local bus of the REDS REPTAR board (Spartan-6 xc6slx150t): the board's CPU is the
// bus master and drives chip select, address latch, read and write strobes and the upper address bits into the FPGA;
// the circuit answers with WAIT and IRQ and shares the 16-bit multiplexed address / data lines through three-state
// buffers. Nothing in the simulator plays the CPU, so the part only matters for the FPGA flow (evo's propagate()
// throws "not implemented"); its outputs stay undriven here.
//
// evo's bounds are (-110,-10) 110 x 110 around the first port, all ten ports on the east edge 10 apart (evo port
// index: y): 0 nCS3_o, 1 nADV_ALE_o, 2 RE_nOE_o, 3 nWE_o, 4 WAIT3_i, 5 Addr_Data_LB_o (16), 6 Addr_Data_LB_i (16),
// 7 Addr_Data_LB_tris_i, 8 Addr_LB_o (9), 9 IRQ_i. With the body's top left as origin a port at evo y sits at
// (110, y + 10).
import type { PinDefinition } from '../../types/circuit';

export const BODY_WIDTH = 110;
export const BODY_HEIGHT = 110;
const PIN_X = BODY_WIDTH;
/** y of evo port n */
export const portY = (n: number): number => 10 + 10 * n;

/** evo forces the label (its HDL entity name) to this and makes it read-only */
export const LOCAL_BUS_NAME = 'LocalBus';

/** Address / data lines and upper address bits */
export const DATA_WIDTH = 16;
export const ADDR_WIDTH = 9;

/** FPGA pins of the bus (evo MAPINFO: 13 inputs, 2 outputs, 16 bidirectional) */
export const FPGA_IN_WIDTH = 13;
export const FPGA_OUT_WIDTH = 2;

/** Circuit inputs, in comp.inputs order: [pin id, evo port index, width] */
const INPUTS: [id: string, name: string, port: number, width: number][] = [
  ['wait3', 'SP6_LB_WAIT3_i', 4, 1],
  ['dataIn', 'Addr_Data_LB_i', 6, DATA_WIDTH],
  ['tris', 'Addr_Data_LB_tris_i', 7, 1],
  ['irq', 'IRQ_i', 9, 1],
];

/** Circuit outputs, in comp.outputs order */
const OUTPUTS: [id: string, name: string, port: number, width: number][] = [
  ['nCs3', 'SP6_LB_nCS3_o', 0, 1],
  ['nAdvAle', 'SP6_LB_nADV_ALE_o', 1, 1],
  ['reNoe', 'SP6_LB_RE_nOE_o', 2, 1],
  ['nWe', 'SP6_LB_nWE_o', 3, 1],
  ['dataOut', 'Addr_Data_LB_o', 5, DATA_WIDTH],
  ['addr', 'Addr_LB_o', 8, ADDR_WIDTH],
];

/** Indices into comp.inputs */
export const IN = { wait3: 0, dataIn: 1, tris: 2, irq: 3 } as const;
/** Indices into comp.outputs */
export const OUT = { nCs3: 0, nAdvAle: 1, reNoe: 2, nWe: 3, dataOut: 4, addr: 5 } as const;

const pin = (type: 'input' | 'output') => ([id, name, port, width]: (typeof INPUTS)[number]): PinDefinition => ({
  id,
  name,
  type,
  relX: PIN_X,
  relY: portY(port),
  ...(width > 1 ? { width } : {}),
});

export const INPUT_PINS: PinDefinition[] = INPUTS.map(pin('input'));
export const OUTPUT_PINS: PinDefinition[] = OUTPUTS.map(pin('output'));

/** The ten port names top to bottom with their y, as evo's paintInstance draws them */
export const PORT_LABELS: { name: string; y: number }[] = [...INPUTS, ...OUTPUTS]
  .map(([, name, port]) => ({ name, y: portY(port) }))
  .sort((a, b) => a.y - b.y);
