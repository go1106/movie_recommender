// src/telemetry.js
import { apiPost } from "./api";

export function logImpression(userId, movieId, context) {
  return apiPost("/api/events/", { userId, action: "impression", movieId, context });
}
export function logClick(userId, movieId, context) {
  return apiPost("/api/events/", { userId, action: "click", movieId, context });
}
