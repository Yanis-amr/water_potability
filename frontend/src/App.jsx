import { useState } from "react";
import Header from "./components/Header";
import PredictForm from "./components/PredictForm";
import ResultPanel from "./components/ResultPanel";
import ShapChart from "./components/ShapChart";
import AIReport from "./components/AIReport";
import BatchUpload from "./components/BatchUpload";
import { DEFAULT_SAMPLE } from "./lib/features";
import { predictSample } from "./lib/api";

export default function App() {
  const [tab, setTab] = useState("single");
  const [sample, setSample] = useState(DEFAULT_SAMPLE);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await predictSample(sample);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Erreur lors de l'analyse de l'échantillon.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header tab={tab} setTab={setTab} />

      <main className="max-w-6xl mx-auto px-6 py-10">
        {tab === "single" ? (
          <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-6">
            <PredictForm
              sample={sample}
              setSample={setSample}
              onSubmit={handleSubmit}
              loading={loading}
            />

            <div className="space-y-6">
              {error && (
                <div className="panel p-6 border-coral">
                  <p className="font-mono text-sm text-coral">{error}</p>
                </div>
              )}

              {!result && !error && (
                <div className="panel p-10 flex flex-col items-center justify-center text-center gap-3 h-full">
                  <p className="label-eyebrow">En attente</p>
                  <p className="font-mono text-sm text-slate max-w-xs">
                    Renseignez les 9 paramètres puis lancez l&apos;analyse pour obtenir
                    la prédiction, l&apos;explicabilité SHAP et le rapport IA.
                  </p>
                </div>
              )}

              {result && <ResultPanel result={result} />}
              {result && <ShapChart values={result.shap_values} />}
              {result && <AIReport text={result.ai_report} />}
            </div>
          </div>
        ) : (
          <BatchUpload />
        )}
      </main>

      <footer className="max-w-6xl mx-auto px-6 py-8 border-t border-line mt-10">
        <p className="font-mono text-[11px] text-slate">
          Water Potability AI — pipeline scikit-learn (SVM RBF), explicabilité SHAP,
          rapport généré par IA. Aide à la décision, ne remplace pas une analyse
          certifiée en laboratoire.
        </p>
      </footer>
    </div>
  );
}
