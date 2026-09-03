/**
 * API client to connect frontend with FastAPI backend
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export async function fetchActiveAlerts() {
  const response = await fetch(`${API_BASE_URL}/alerts/`);
  return response.json();
}

export async function fetchShelters() {
  const response = await fetch(`${API_BASE_URL}/shelters/`);
  return response.json();
}

export async function requestEvacuationRoute(originCoords, preferredShelterId = null) {
  const response = await fetch(`${API_BASE_URL}/evacuation/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin_latitude: originCoords.lat,
      origin_longitude: originCoords.lng,
      preferred_shelter_id: preferredShelterId,
    }),
  });
  return response.json();
}
