import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 60000,
});

export async function predictSample(sample) {
  const { data } = await api.post("/predict", sample);
  return data;
}

export async function batchPredict(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/batch_predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });

  const summaryHeader = response.headers["x-summary"];
  const summary = summaryHeader ? JSON.parse(summaryHeader) : null;

  return { blob: response.data, summary };
}

export async function getModelInfo() {
  const { data } = await api.get("/model_info");
  return data;
}

export async function getMetrics() {
  const { data } = await api.get("/metrics");
  return data;
}

export default api;
