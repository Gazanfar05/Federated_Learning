export const hospitalConfig = {
  hospitalId: "hospital_02",
  institutionDisplayName: "Hospital 02 - Data Quality and Evaluation Unit",
  requiredFeatureColumns: [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age"
  ],
  targetColumn: "Outcome",
  expectedInputFeatureCount: 8,
  expectedTargetClasses: [0, 1],
  centralApiBaseUrl: "https://127.0.0.1:8443",
  localAgentApiBaseUrl: "",
  requestTimeoutMs: 8000,
  staleDataMs: 30000,
  storageKey: "hospital_02_frontend_settings"
};
