import ResultGauge from "./ResultGauge";

export default function ResultPanel({ result }) {
  const isPotable = result.prediction === "Potable";

  return (
    <div className="panel p-6 relative overflow-hidden">
      <div className="flex items-center justify-between mb-2">
        <p className="label-eyebrow">Résultat de l&apos;analyse</p>
        <span
          className="font-mono text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border"
          style={{
            color: isPotable ? "#2FD5C8" : "#F2603B",
            borderColor: isPotable ? "#1B8A80" : "#F2603B",
          }}
        >
          {isPotable ? "Conforme" : "Non conforme"}
        </span>
      </div>

      <ResultGauge prediction={result.prediction} probability={result.probability} />

      <div className="text-center mt-2">
        <p className="font-display text-2xl font-semibold">
          {isPotable ? "Eau potable" : "Eau non potable"}
        </p>
        <p className="font-mono text-xs text-slate mt-1">
          Modèle : SVM RBF · seuil de décision 0.5
        </p>
      </div>

      {/* effet ripple discret derrière la jauge */}
      <div
        aria-hidden
        className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 rounded-full border animate-ripple"
        style={{ borderColor: isPotable ? "#2FD5C8" : "#F2603B" }}
      />
    </div>
  );
}
