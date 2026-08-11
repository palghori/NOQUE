import axios from "axios";

// In production, VITE_API_URL points to the deployed backend (e.g., https://codeoracle-api.onrender.com/api)
// In development, it defaults to "/api" which is proxied by Vite to localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Create a new analysis job from a ZIP file upload.
 */
export async function createJobFromZip(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/jobs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Create a new analysis job from a GitHub URL.
 */
export async function createJobFromGitHub(githubUrl) {
  const formData = new FormData();
  formData.append("github_url", githubUrl);
  const response = await api.post("/jobs", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Poll the job status.
 */
export async function getJobStatus(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Fetch the full analysis results.
 */
export async function getJobResults(jobId) {
  const response = await api.get(`/jobs/${jobId}/results`);
  return response.data;
}

export default api;
