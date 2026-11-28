import type { CircuitComponentInstance } from '../types/circuit';
import { configureIo5 } from './circuitEngine';

/**
 * Real-time clocks of older project files (Aşama 7c-1). A clock used to give only the low 32 bits of evolution's
 * 64-bit time; it now has a second output T[63:32] for the high half. The low output keeps its id and spot (its
 * wires stay), the new one goes one step below it, so no wire has to move.
 */
export function upgradeRtcPins(components: CircuitComponentInstance[]): { components: CircuitComponentInstance[]; added: number } {
  let added = 0;
  const next = components.map((c) => {
    if (c.type !== 'realTimeClock' || c.outputs.length !== 1) return c;
    added++;
    return configureIo5(c, {});
  });
  return added ? { components: next, added } : { components, added };
}
