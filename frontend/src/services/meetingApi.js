import axios from "axios";

const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000" });

export const transcribeAudio = (formData) =>
  api.post("/api/v1/transcribe", formData, { headers: { "Content-Type": "multipart/form-data" } });

export const processTranscript = (transcript) =>
  api.post("/api/v1/process", { transcript });

export const summarizeTranscript = (transcript) =>
  api.post("/api/v1/summarize", { transcript });

export const extractTasks = (transcript) =>
  api.post("/api/v1/tasks", { transcript });

export const getModels = () => api.get("/api/v1/models");
