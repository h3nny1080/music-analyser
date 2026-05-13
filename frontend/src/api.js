import axios from "axios";

const BASE = "http://localhost:8000/api";

export const submitInput = (formData) =>
    axios.post(`${BASE}/analyse`, formData).then(r => r.data);

export const confirmYoutube = (youtubeUrl) =>
    axios.post(`${BASE}/analyse/confirm`,
        new URLSearchParams({ youtube_url: youtubeUrl })
    ).then(r => r.data);

export const getResults = (sessionId) =>
    axios.get(`${BASE}/results/${sessionId}`).then(r => r.data);

export const submitExport = (sessionId, selections, audioFormat) =>
    axios.post(`${BASE}/export/${sessionId}`, {
        selections,
        audio_format: audioFormat,
    }).then(r => r.data);

export const pollProgress = (sessionId) =>
    axios.get(`${BASE}/progress/${sessionId}`).then(r => r.data);