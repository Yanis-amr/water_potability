import { FEATURES } from "../lib/features";

const labelFor = (key) => FEATURES.find((f) => f.key === key)?.label || key;

export default function ShapChart({ values }) {
  if (!values?.length) return null;

  const maxAbs = Math.max(...values.map((v) => Math.abs(v.impact)), 0.001);

  return (
    <div className="panel p-6">
      <p className="label-eyebrow mb-4">Facteurs influents (SHAP)</p>
      <div className="space-y-3">
        {values.map((v) => {
          const widthPct = (Math.abs(v.impact) / maxAbs) * 100;
          const positive = v.impact >= 0;
          return (
            <div key={v.feature} className="grid grid-cols-[110px_1fr_56px] items-center gap-3">
              <span className="font-mono text-xs text-slate truncate">{labelFor(v.feature)}</span>
              <div className="relative h-2 bg-ink rounded-full overflow-hidden">
                <div
                  className="absolute top-0 h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${widthPct}%`,
                    left: positive ? "50%" : `${50 - widthPct}%`,
                    background: positive ? "#2FD5C8" : "#F2603B",
                  }}
                />
                <div className="absolute left-1/2 top-0 h-full w-px bg-line" />
              </div>
              <span
                className="font-mono text-xs text-right"
                style={{ color: positive ? "#2FD5C8" : "#F2603B" }}
              >
                {positive ? "+" : ""}
                {v.impact.toFixed(3)}
              </span>
            </div>
          );
        })}
      </div>
      <p className="font-mono text-[10px] text-slate mt-4">
        positif → pousse vers « potable » · négatif → pousse vers « non potable »
      </p>
    </div>
  );
}
