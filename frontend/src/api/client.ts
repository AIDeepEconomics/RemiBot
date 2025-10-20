import axios from "axios";

const BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000
});
