export default function Header({ tab, setTab }) {
  return (
    <header className="border-b border-line">
      <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <svg width="28" height="28" viewBox="0 0 32 32" className="shrink-0">
            <path
              d="M16 2s10 12 10 18a10 10 0 1 1-20 0C6 14 16 2 16 2z"
              fill="#2FD5C8"
            />
          </svg>
          <div>
            <p className="font-display font-semibold text-lg leading-none">
              Water Potability <span className="text-aqua">AI</span>
            </p>
            <p className="label-eyebrow mt-1">Laboratoire d&apos;analyse — SVM RBF</p>
          </div>
        </div>

        <nav className="flex gap-1 bg-panel border border-line rounded-lg p-1">
          <button
            onClick={() => setTab("single")}
            className={`px-4 py-2 rounded-md font-mono text-xs uppercase tracking-wide transition-colors ${
              tab === "single" ? "bg-aqua text-ink" : "text-slate hover:text-paper"
            }`}
          >
            Échantillon
          </button>
          <button
            onClick={() => setTab("batch")}
            className={`px-4 py-2 rounded-md font-mono text-xs uppercase tracking-wide transition-colors ${
              tab === "batch" ? "bg-aqua text-ink" : "text-slate hover:text-paper"
            }`}
          >
            Lot (CSV)
          </button>
        </nav>
      </div>
    </header>
  );
}
