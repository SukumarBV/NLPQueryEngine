// In production (single-container Koyeb deploy) the frontend and API are
// served from the same origin, so leaving this empty makes every request
// relative (e.g. "/api/query"). For local development where the React
// dev server and FastAPI run on different ports, set REACT_APP_API_URL
// (see frontend/Dockerfile / .env) to point at the backend, e.g.
// http://localhost:8000.
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

export default API_BASE_URL;
