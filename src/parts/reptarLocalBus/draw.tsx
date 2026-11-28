// Reptar Local Bus body, after evo's ReptarLocalBus.paintInstance: the bounds and the ten port names written inside
// the east edge, next to their pins (drawPort ... Direction.WEST), in a font two points smaller than the default.
import type { ReactNode } from 'react';
import type { CircuitComponentInstance } from '../../types/circuit';
import type { DrawContext } from '../registry';
import { BODY_HEIGHT, BODY_WIDTH, PORT_LABELS } from './model';

export function drawReptarLocalBus(_comp: CircuitComponentInstance, ctx: DrawContext): ReactNode {
  const cls = `text-[8px] font-mono select-none ${ctx.gateTextClass}`;
  return (
    <g filter="url(#gateShadow)">
      <rect x={0} y={0} width={BODY_WIDTH} height={BODY_HEIGHT} rx={3} fill={ctx.fillColor} stroke={ctx.strokeColor} strokeWidth={ctx.strokeWidth} />
      {PORT_LABELS.map((p) => (
        <text key={p.name} x={BODY_WIDTH - 3} y={p.y} textAnchor="end" dominantBaseline="central" className={cls}>
          {p.name}
        </text>
      ))}
    </g>
  );
}
