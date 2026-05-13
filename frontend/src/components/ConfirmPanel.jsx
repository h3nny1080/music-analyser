export default function ConfirmPanel({ candidates, metadata, onConfirm, onBack }) {
    return (
        <div className="panel confirm-panel">
            <h2>Is this the right track?</h2>
            <p className="subtitle">
                We found <strong>{metadata?.title}</strong>
                {metadata?.artist ? ` by ${metadata.artist}` : ""} on YouTube.
                Please confirm before we analyse.
            </p>

            <div className="candidate-list">
                {candidates.map((c, i) => (
                    <div key={c.url} className="candidate-card">

                        <img src={c.thumbnail_url} alt={c.title} />

                        <a className="candidate-info" href={c.url}
                           target="_blank"
                           rel="noreferrer"
                           className="preview-link">
                            <p className="candidate-title">{c.title}</p>
                            <p className="candidate-meta">
                                {c.channel} · {Math.floor(c.duration_seconds / 60)}:
                                {String(c.duration_seconds % 60).padStart(2, "0")}
                            </p>
                            Preview on YouTube ↗
                        </a>
                        <button className={i === 0 ? "btn-primary" : "btn-secondary"} onClick={() => onConfirm(c.url)}>
                            {i === 0 ? "Use this" : "Use instead"}
                        </button>
                    </div>
                ))}
            </div>
            <button className="btn-ghost" onClick={onBack}>
                ← Try a different link
            </button>
        </div>
);
}