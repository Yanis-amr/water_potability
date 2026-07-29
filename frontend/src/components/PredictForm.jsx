import { FEATURES } from "../lib/features";

export default function PredictForm({ sample, setSample, onSubmit, loading }) {
  const handleChange = (key, value) => {
    setSample((prev) => ({ ...prev, [key]: value === "" ? "" : Number(value) }));
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="panel p-6"
    >
      <div className="flex items-center justify-between mb-5">
        <p className="label-eyebrow">Paramètres physico-chimiques</p>
        <p className="font-mono text-[11px] text-slate">9 variables</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {FEATURES.map((f) => (
          <label key={f.key} className="block">
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="font-mono text-[11px] text-slate">
                <span className="text-aquaDim">{f.code}</span> · {f.label}
              </span>
              {f.unit && <span className="font-mono text-[10px] text-slate">{f.unit}</span>}
            </div>
            <input
              type="number"
              step={f.step}
              required
              value={sample[f.key]}
              onChange={(e) => handleChange(f.key, e.target.value)}
              className="field-input"
            />
          </label>
        ))}
      </div>

      <button type="submit" disabled={loading} className="btn-primary w-full mt-6">
        {loading ? "Analyse en cours…" : "Analyser l'échantillon"}
      </button>
    </form>
  );
}
