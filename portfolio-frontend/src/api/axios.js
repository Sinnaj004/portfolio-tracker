import axios from 'axios';

const getBaseUrl = () => {
    const envUrl = import.meta.env.VITE_API_URL;
    if (envUrl && !envUrl.includes('undefined')) {
        return envUrl;
    }
    // Dynamischer NAS-Fallback
    return `http://${window.location.hostname}:8000/api/v1`;
};

// Hier wird die Funktion genau EINMAL aufgerufen
const apiClient = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        'Content-Type': 'application/json'
    }
});

export default apiClient;