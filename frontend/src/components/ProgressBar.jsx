const STAGE_LABELS = {
    ingestion:      "Downloading audio…",
    separation:     "Separating stems with Demucs…",
    classification: "Identifying instruments…",
    done:           "Analysis complete",
};

export default function ProgressBar({ progress }) {
    const label = STAGE_LABELS[progress.stage] || "Processing…";
    return (
        <div className="panel progress-panel">
            <p className="progress-label">{label}</p>
            <div className="progress-track">
                <div
                    className="progress-fill"
                    style={{ width: `${progress.percent}%` }}
                />
            </div>
            <p className="progress-pct">{progress.percent}%</p>
        </div>
    );
}