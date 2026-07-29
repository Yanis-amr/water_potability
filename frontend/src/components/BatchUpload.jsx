import { useRef, useState } from "react";
import { batchPredict } from "../lib/api";

export default function BatchUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setSummary(null);
    setError(null);
    setDownloadUrl(null);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const { blob, summary } = await batchPredict(file);
      setSummary(summary);
      setDownloadUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(err?.response?.data?.detail || "Erreur lors de l'analyse du lot.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-6">
      <div className="panel p-6">
        <p className="label-eyebrow mb-4">Analyse par lot — import CSV</p>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            handleFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className="border border-dashed border-line rounded-lg py-12 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-aqua transition-colors"
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2FD5C8" strokeWidth="1.5">
            <path d="M12 3v12m0-12 4 4m-4-4-4 4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="font-mono text-sm text-slate">
            {file ? file.name : "Glissez un fichier .csv ou cliquez pour sélectionner"}
          </p>
          <p className="font-mono text-[10px] text-slate">
            colonnes attendues : ph, hardness, tds, chlorine, sulfate, conductivity, organic_carbon, trihalomethanes, turbidity
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="btn-primary w-full mt-6"
        >
          {loading ? "Analyse du lot en cours…" : "Analyser le lot"}
        </button>

        {error && <p className="font-mono text-xs text-coral mt-4">{error}</p>}

        {downloadUrl && (
          <a
            href={downloadUrl}
            download="predictions_enrichies.csv"
            className="btn-ghost mt-4 flex items-center justify-center gap-2 w-full"
          >
            Télécharger le CSV enrichi
          </a>
        )}
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-4">Synthèse</p>
        {!summary && (
          <p className="font-mono text-sm text-slate">
            Le résumé statistique et le rapport IA apparaîtront ici après analyse.
          </p>
        )}
        {summary && (
          <div className="space-y-5">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="border border-line rounded-lg py-3">
                <p className="font-mono text-2xl text-paper">{summary.n_samples}</p>
                <p className="font-mono text-[10px] text-slate mt-1">échantillons</p>
              </div>
              <div className="border border-line rounded-lg py-3">
                <p className="font-mono text-2xl text-aqua">{summary.n_potable}</p>
                <p className="font-mono text-[10px] text-slate mt-1">potables</p>
              </div>
              <div className="border border-line rounded-lg py-3">
                <p className="font-mono text-2xl text-coral">{summary.n_non_potable}</p>
                <p className="font-mono text-[10px] text-slate mt-1">non potables</p>
              </div>
            </div>

            {summary.most_problematic_features?.length > 0 && (
              <div>
                <p className="font-mono text-[11px] text-slate mb-2">
                  Variables les plus problématiques
                </p>
                <div className="flex flex-wrap gap-2">
                  {summary.most_problematic_features.map((f) => (
                    <span
                      key={f}
                      className="font-mono text-[11px] px-2 py-1 border border-line rounded-full text-amber"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {summary.ai_summary && (
              <div className="border-t border-line pt-4">
                <p className="font-mono text-[11px] text-slate mb-2">Résumé IA</p>
                <p className="font-mono text-[13px] leading-relaxed text-paper/90 whitespace-pre-wrap">
                  {summary.ai_summary}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
