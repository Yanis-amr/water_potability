export const FEATURES = [
  { key: "ph", label: "pH", unit: "", default: 7.2, step: 0.1, code: "01" },
  { key: "hardness", label: "Dureté", unit: "mg/L", default: 180, step: 1, code: "02" },
  { key: "tds", label: "Solides dissous", unit: "ppm", default: 250, step: 1, code: "03" },
  { key: "chlorine", label: "chlorine", unit: "ppm", default: 8, step: 0.1, code: "04" },
  { key: "sulfate", label: "Sulfates", unit: "mg/L", default: 340, step: 1, code: "05" },
  { key: "conductivity", label: "Conductivité", unit: "µS/cm", default: 450, step: 1, code: "06" },
  { key: "organic_carbon", label: "Carbone organique", unit: "ppm", default: 12, step: 0.1, code: "07" },
  { key: "trihalomethanes", label: "Trihalométhanes", unit: "µg/L", default: 65, step: 1, code: "08" },
  { key: "turbidity", label: "Turbidité", unit: "NTU", default: 4, step: 0.1, code: "09" },
];

export const DEFAULT_SAMPLE = FEATURES.reduce((acc, f) => {
  acc[f.key] = f.default;
  return acc;
}, {});
