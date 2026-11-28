// Reptar Local Bus (Aşama 7d-2), as Logisim-evolution's std/io "ReptarLB": the FPGA end of the REPTAR board's local
// bus. It has no behaviour of its own in the simulator (evo's propagate() throws "not implemented"): the bus master
// is the board's CPU, which nothing here plays, so the outputs stay undriven. What it is for is the FPGA flow: the
// HDL export instances a LocalBus module whose bus pins are top-level ports, and the FPGA dialog maps them on the
// board's local-bus resource (only the REPTAR Spartan-6 board has one). The label is fixed to "LocalBus", evo's
// HDL entity name.
import { registerNamespace } from '../../i18n';
import type { SignalValue } from '../../types/logic';
import { partNamespace, registerPart } from '../registry';
import { drawReptarLocalBus } from './draw';
import { reptarLocalBusHdl } from './hdl';
import { PART_ID } from './id';
import en from './locales/en.json';
import tr from './locales/tr.json';
import { BODY_HEIGHT, BODY_WIDTH, INPUT_PINS, LOCAL_BUS_NAME, OUTPUT_PINS } from './model';

registerNamespace(partNamespace(PART_ID), { en, tr });

registerPart({
  id: PART_ID,
  category: 'inputs',
  group: 'wiring',
  width: BODY_WIDTH,
  height: BODY_HEIGHT,
  inputs: INPUT_PINS,
  outputs: OUTPUT_PINS,
  fixedLabel: LOCAL_BUS_NAME,
  // Outside-world signals: nothing drives them in the simulator
  simulate(comp, ctx) {
    comp.outputs.forEach((p, i) => {
      const w = p.width ?? 1;
      if (w > 1) ctx.setBitsOut(i, Array<SignalValue>(w).fill('Z'));
      else ctx.setOut(i, 'Z');
    });
  },
  draw: drawReptarLocalBus,
  hdl: reptarLocalBusHdl,
});
