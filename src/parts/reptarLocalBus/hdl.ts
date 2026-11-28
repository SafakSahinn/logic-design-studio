// Reptar Local Bus HDL, after evo's ReptarLocalBusHdlGeneratorFactory (VHDL only there; Verilog here is the same
// circuit). A helper module named LocalBus (evo forces the entity name to the label) turns the bus pins around:
//   FPGA_in(0..3)   -> nCS3, nADV_ALE, RE_nOE, nWE          (from the board's CPU)
//   FPGA_in(4..12)  -> Addr_LB_o(0..8)                      (upper address bits A15..A23)
//   FPGA_out(0..1)  <- not WAIT3_i, not IRQ_i
//   Addr_Data_LB_io <-> 16 Xilinx IOBUFs (LVCMOS18, 12 mA, fast), T = Addr_Data_LB_tris_i (1 = read the pins)
// FPGA_in / FPGA_out / Addr_Data_LB_io are top-level ports of the design (evo's bubble buses), mapped on the
// board's LocalBus resource (13 inputs, 2 outputs, 16 bidirectional pins, the same order).
//
// Two mistakes of evo's text are not copied: it assigns FPGA_in(11 DOWNTO 4), 8 bits, to the 9-bit Addr_LB_o, and its
// IOBUF generic map misses the comma after IOSTANDARD; neither compiles.
import type { CircuitComponentInstance } from '../../types/circuit';
import type { HdlContext, HdlLang } from '../registry';
import { ADDR_WIDTH, DATA_WIDTH, FPGA_IN_WIDTH, FPGA_OUT_WIDTH, IN, LOCAL_BUS_NAME, OUT } from './model';
import { t } from './text';

function renderVhdl(name: string): string {
  return [
    `-- Reptar Local Bus (Logisim-evolution ReptarLB): the FPGA side of the REPTAR board's local bus.`,
    `-- Needs the Xilinx UNISIM library (IOBUF), as in evolution: Spartan-6 / ISE.`,
    'library IEEE;',
    'use IEEE.STD_LOGIC_1164.ALL;',
    'library UNISIM;',
    'use UNISIM.vcomponents.all;',
    '',
    `entity ${name} is`,
    '  port (',
    `    Addr_Data_LB_io     : inout std_logic_vector(${DATA_WIDTH - 1} downto 0);`,
    '    SP6_LB_nCS3_o       : out std_logic;',
    '    SP6_LB_nADV_ALE_o   : out std_logic;',
    '    SP6_LB_RE_nOE_o     : out std_logic;',
    '    SP6_LB_nWE_o        : out std_logic;',
    '    SP6_LB_WAIT3_i      : in std_logic;',
    '    IRQ_i               : in std_logic;',
    `    FPGA_in             : in std_logic_vector(${FPGA_IN_WIDTH - 1} downto 0);`,
    `    FPGA_out            : out std_logic_vector(${FPGA_OUT_WIDTH - 1} downto 0);`,
    `    Addr_LB_o           : out std_logic_vector(${ADDR_WIDTH - 1} downto 0);`,
    `    Addr_Data_LB_o      : out std_logic_vector(${DATA_WIDTH - 1} downto 0);`,
    `    Addr_Data_LB_i      : in std_logic_vector(${DATA_WIDTH - 1} downto 0);`,
    '    Addr_Data_LB_tris_i : in std_logic',
    '  );',
    `end entity ${name};`,
    '',
    `architecture PlatformIndependent of ${name} is`,
    'begin',
    '  FPGA_out(0) <= not SP6_LB_WAIT3_i;',
    '  FPGA_out(1) <= not IRQ_i;',
    '  SP6_LB_nCS3_o     <= FPGA_in(0);',
    '  SP6_LB_nADV_ALE_o <= FPGA_in(1);',
    '  SP6_LB_RE_nOE_o   <= FPGA_in(2);',
    '  SP6_LB_nWE_o      <= FPGA_in(3);',
    `  Addr_LB_o         <= FPGA_in(${FPGA_IN_WIDTH - 1} downto 4);`,
    '',
    "  IOBUF_Addresses_Datas : for i in 0 to Addr_Data_LB_io'length - 1 generate",
    '    IOBUF_Addresse_Data : IOBUF',
    '      generic map (',
    '        DRIVE      => 12,',
    '        IOSTANDARD => "LVCMOS18",',
    '        SLEW       => "FAST"',
    '      )',
    '      port map (',
    '        O  => Addr_Data_LB_o(i),     -- buffer output (the pin as read)',
    '        IO => Addr_Data_LB_io(i),    -- the top-level pin',
    '        I  => Addr_Data_LB_i(i),     -- buffer input (what the circuit drives)',
    '        T  => Addr_Data_LB_tris_i    -- three-state enable: 1 = input, 0 = output',
    '      );',
    '  end generate;',
    `end architecture PlatformIndependent;`,
  ].join('\n');
}

function renderVerilog(name: string): string {
  return [
    `// Reptar Local Bus (Logisim-evolution ReptarLB): the FPGA side of the REPTAR board's local bus.`,
    `// Uses the Xilinx IOBUF primitive (UNISIM), as evolution's VHDL does: Spartan-6 / ISE.`,
    `module ${name} (`,
    `  inout  wire [${DATA_WIDTH - 1}:0] Addr_Data_LB_io,`,
    '  output wire        SP6_LB_nCS3_o,',
    '  output wire        SP6_LB_nADV_ALE_o,',
    '  output wire        SP6_LB_RE_nOE_o,',
    '  output wire        SP6_LB_nWE_o,',
    '  input  wire        SP6_LB_WAIT3_i,',
    '  input  wire        IRQ_i,',
    `  input  wire [${FPGA_IN_WIDTH - 1}:0] FPGA_in,`,
    `  output wire [${FPGA_OUT_WIDTH - 1}:0]  FPGA_out,`,
    `  output wire [${ADDR_WIDTH - 1}:0]  Addr_LB_o,`,
    `  output wire [${DATA_WIDTH - 1}:0] Addr_Data_LB_o,`,
    `  input  wire [${DATA_WIDTH - 1}:0] Addr_Data_LB_i,`,
    '  input  wire        Addr_Data_LB_tris_i',
    ');',
    '  assign FPGA_out[0] = ~SP6_LB_WAIT3_i;',
    '  assign FPGA_out[1] = ~IRQ_i;',
    '  assign SP6_LB_nCS3_o     = FPGA_in[0];',
    '  assign SP6_LB_nADV_ALE_o = FPGA_in[1];',
    '  assign SP6_LB_RE_nOE_o   = FPGA_in[2];',
    '  assign SP6_LB_nWE_o      = FPGA_in[3];',
    `  assign Addr_LB_o         = FPGA_in[${FPGA_IN_WIDTH - 1}:4];`,
    '',
    '  genvar i;',
    '  generate',
    `    for (i = 0; i < ${DATA_WIDTH}; i = i + 1) begin : IOBUF_Addresses_Datas`,
    '      IOBUF #(',
    '        .DRIVE(12),',
    '        .IOSTANDARD("LVCMOS18"),',
    '        .SLEW("FAST")',
    '      ) IOBUF_Addresse_Data (',
    '        .O(Addr_Data_LB_o[i]),    // buffer output (the pin as read)',
    '        .IO(Addr_Data_LB_io[i]),  // the top-level pin',
    '        .I(Addr_Data_LB_i[i]),    // buffer input (what the circuit drives)',
    '        .T(Addr_Data_LB_tris_i)   // three-state enable: 1 = input, 0 = output',
    '      );',
    '    end',
    '  endgenerate',
    'endmodule',
  ].join('\n');
}

const zeros = (lang: HdlLang, width: number, zero: string): string => (width === 1 ? zero : lang === 'verilog' ? `${width}'b0` : "(others => '0')");

export function reptarLocalBusHdl(comp: CircuitComponentInstance, ctx: HdlContext): void {
  const label = comp.label || LOCAL_BUS_NAME;
  const fpgaIn = ctx.topPort(`${label}_FPGA_in`, 'in', FPGA_IN_WIDTH);
  if (fpgaIn === null) {
    // Inside an IC: its module has no FPGA pins (evo passes them up as bubbles; ours stay at the top level)
    ctx.comment(t('hdl.insideIcComment'));
    comp.outputs.forEach((p, i) => ctx.assign(i, zeros(ctx.lang, p.width ?? 1, ctx.zero)));
    ctx.warn(t('hdl.insideIc'));
    return;
  }
  const fpgaOut = ctx.topPort(`${label}_FPGA_out`, 'out', FPGA_OUT_WIDTH)!;
  const fpgaIo = ctx.topPort(`${label}_Addr_Data_LB_io`, 'inout', DATA_WIDTH)!;
  const mod = ctx.module('localBus', LOCAL_BUS_NAME, (lang, name) => (lang === 'vhdl' ? renderVhdl(name) : renderVerilog(name)));
  ctx.instance(mod, 'localbus', [
    ['Addr_Data_LB_io', fpgaIo],
    ['SP6_LB_nCS3_o', ctx.output(OUT.nCs3)],
    ['SP6_LB_nADV_ALE_o', ctx.output(OUT.nAdvAle)],
    ['SP6_LB_RE_nOE_o', ctx.output(OUT.reNoe)],
    ['SP6_LB_nWE_o', ctx.output(OUT.nWe)],
    ['SP6_LB_WAIT3_i', ctx.input(IN.wait3)],
    ['IRQ_i', ctx.input(IN.irq)],
    ['FPGA_in', fpgaIn],
    ['FPGA_out', fpgaOut],
    ['Addr_LB_o', ctx.output(OUT.addr)],
    ['Addr_Data_LB_o', ctx.output(OUT.dataOut)],
    ['Addr_Data_LB_i', ctx.input(IN.dataIn)],
    ['Addr_Data_LB_tris_i', ctx.input(IN.tris)],
  ]);
  ctx.warn(t('hdl.unisim'));
}
