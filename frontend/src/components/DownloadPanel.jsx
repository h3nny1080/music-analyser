const FILE_ICONS = { pdf: "🎼", wav: "🎵", flac: "🎵", aiff: "🎵" };

export default function DownloadPanel({ outputs, onReset }) {
    return (
        <div className="panel download-panel">
            <h2>Your files are ready</h2>

            <div className="file-list">
                {outputs.files.map((f, i) => (
                    <div key={i} className="file-row">
                        <a href={`http://localhost:8000${f.download_url}`}>download</a>
                        <span className="file-icon">{FILE_ICONS[f.file_type] || "📄"}</span>
                        <div className="file-info">
                            <span className="file-name">{f.instrument_label}</span>
                            <span className="file-meta">
                                {f.file_type.toUpperCase()} ·{" "}
                                                {(f.size_bytes / (1024 * 1024)).toFixed(1)} MB
                            </span>
                        </div>
                    </div>
                ))}
            </div>
            {outputs.errors?.length > 0 && (
                <div className="error-list">
                    <p className="error-heading">Some outputs could not be generated:</p>
                    {outputs.errors.map((e, i) => (
                        <p key={i} className="error-item">
                            {e.stem_name}: {e.message}
                        </p>
                    ))}
                </div>
            )}
            <button className="btn-primary" onClick={onReset}>
                Analyse another track
            </button>
        </div>
    )
;}