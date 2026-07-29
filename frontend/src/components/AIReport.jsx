export default function AIReport({ text }) {
  if (!text) return null;

  return (
    <div className="panel p-6 border-dashed">
      <div className="flex items-center justify-between mb-4">
        <p className="label-eyebrow">Rapport généré par IA</p>
        <span className="font-mono text-[10px] text-slate border border-line rounded px-2 py-0.5">
          aide à la décision
        </span>
      </div>
      <div className="font-mono text-[13px] leading-relaxed text-paper/90 whitespace-pre-wrap">
        {text}
      </div>
    </div>
  );
}
