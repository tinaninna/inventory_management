import { useId, useState } from "react";

export interface DonutSlice { label: string; value: number; color: string; }

export function DonutChart({ slices, total, centerLabel }: { slices: DonutSlice[]; total: number; centerLabel: string }) {
  const size = 200;
  const stroke = 26;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const [active, setActive] = useState<number | null>(null);
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
      <div className="relative shrink-0">
        <svg viewBox={`0 0 ${size} ${size}`} width="100%" height="100%" className="h-44 w-44 sm:h-48 sm:w-48" role="img" aria-label={`${centerLabel}: ${total} total`}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#eef2f0" strokeWidth={stroke} />
          {slices.map((slice, i) => {
            const fraction = total > 0 ? slice.value / total : 0;
            const dash = fraction * circumference;
            const el = (
              <circle
                key={slice.label}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={slice.color}
                strokeWidth={active === i ? stroke + 4 : stroke}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                strokeLinecap={dash > 0 && dash < circumference ? "butt" : "round"}
                onMouseEnter={() => setActive(i)}
                onMouseLeave={() => setActive(null)}
                style={{ transition: "stroke-width 120ms ease", cursor: "pointer" }}
              >
                <title>{`${slice.label}: ${slice.value} (${total > 0 ? ((slice.value / total) * 100).toFixed(1) : "0"}%)`}</title>
              </circle>
            );
            offset += dash;
            return el;
          })}
        </svg>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="text-2xl font-extrabold text-[#152621]">{total}</p>
            <p className="text-[11px] font-semibold uppercase tracking-[.08em] text-[#7c8b84]">{centerLabel}</p>
          </div>
        </div>
      </div>
      <ul className="w-full min-w-0 space-y-3">
        {slices.map((slice, i) => (
          <li
            key={slice.label}
            className={`flex items-center justify-between gap-3 rounded-lg px-2 py-1.5 transition ${active === i ? "bg-[#f7faf8]" : ""}`}
            onMouseEnter={() => setActive(i)}
            onMouseLeave={() => setActive(null)}
          >
            <span className="flex min-w-0 items-center gap-2 text-sm font-semibold text-[#374842]">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: slice.color }} aria-hidden="true" />
              {slice.label}
            </span>
            <span className="shrink-0 text-sm font-bold text-[#152621] tabular-nums">
              {slice.value} <span className="font-medium text-[#7c8b84]">({total > 0 ? ((slice.value / total) * 100).toFixed(1) : "0"}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export interface BarDatum { label: string; value: number; }

export function BarChart({ data, color = "#236451" }: { data: BarDatum[]; color?: string }) {
  const gradientId = useId();
  const [active, setActive] = useState<number | null>(null);
  const max = Math.max(1, ...data.map((d) => d.value));
  const width = 640;
  const height = 260;
  const padding = { top: 10, right: 8, bottom: 46, left: 8 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const gap = 12;
  const barW = data.length ? (chartW - gap * (data.length - 1)) / data.length : 0;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" className="h-64 w-full" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Top components by stock quantity">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="1" />
          <stop offset="100%" stopColor={color} stopOpacity="0.72" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <line key={t} x1={padding.left} x2={width - padding.right} y1={padding.top + chartH * (1 - t)} y2={padding.top + chartH * (1 - t)} stroke="#eef2f0" strokeWidth={1} />
      ))}
      {data.map((d, i) => {
        const h = max > 0 ? (d.value / max) * chartH : 0;
        const x = padding.left + i * (barW + gap);
        const y = padding.top + (chartH - h);
        const label = d.label.length > 10 ? `${d.label.slice(0, 9)}…` : d.label;
        return (
          <g key={d.label} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)} style={{ cursor: "pointer" }}>
            <title>{`${d.label}: ${d.value}`}</title>
            <rect x={x} y={y} width={Math.max(barW, 1)} height={Math.max(h, 1)} rx={4} fill={`url(#${gradientId})`} opacity={active === null || active === i ? 1 : 0.55} />
            <text x={x + barW / 2} y={y - 6} textAnchor="middle" fontSize="11" fontWeight={700} fill="#152621">{d.value}</text>
            <text x={x + barW / 2} y={height - padding.bottom + 18} textAnchor="middle" fontSize="10" fontWeight={600} fill="#657b73">{label}</text>
          </g>
        );
      })}
      {!data.length && <text x={width / 2} y={height / 2} textAnchor="middle" fontSize="13" fill="#7c8b84">No inventory data yet</text>}
    </svg>
  );
}
