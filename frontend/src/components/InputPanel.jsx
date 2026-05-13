import { useState } from "react";

export default function InputPanel({ onSubmit, loading }) {
    const [url,  setUrl]  = useState("");
    const [file, setFile] = useState(null);
    const [mode, setMode] = useState("url");  // "url" | "file"

    const handleSubmit = () => {
        if (mode === "url"  && url.trim())  onSubmit(url.trim());
        if (mode === "file" && file)        onSubmit(file);
    };

    return (
        <div className="panel input-panel">
            <div className="tab-row">
                <button
                    className={mode === "url" ? "tab active" : "tab"}
                    onClick={() => setMode("url")}
                >
                    Paste a link
                </button>
                <button
                    className={mode === "file" ? "tab active" : "tab"}
                    onClick={() => setMode("file")}
                >
                    Upload a file
                </button>
            </div>

            {mode === "url" ? (
                <div className="input-row">
                    <input
                        type="text"
                        placeholder="YouTube, Spotify, SoundCloud, Apple Music…"
                        value={url}
                        onChange={e => setUrl(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleSubmit()}
                    />
                </div>
            ) : (
                <div className="input-row">
                    <input
                        type="file"
                        accept=".mp3,.wav,.flac,.aiff,.ogg,.m4a"
                        onChange={e => setFile(e.target.files[0])}
                    />
                </div>
            )}

            <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={loading || (mode === "url" ? !url.trim() : !file)}
            >
                {loading ? "Submitting…" : "Analyse"}
            </button>
        </div>
    );
}