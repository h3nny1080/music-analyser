export default function InstrumentCard({ instrument, selection, onChange }) {
    const selected = !!selection?.output_choice;

    return (
        <div className={`instrument-card ${selected ? "selected" : ""}`}>
            <div className="card-header">
                <span className="instrument-name">{instrument.label}</span>
                <span className="confidence-badge">{instrument.confidence}% match</span>
            </div>
            <p className="stem-label">Stem: {instrument.stem}</p>

            <div className="output-choices">
                {["sheet_music", "audio_isolate", "both"].map(choice => (
                    <label key={choice} className="choice-option">
                        <input
                            type="radio"
                            name={`choice-${instrument.stem}`}
                            value={choice}
                            checked={selection?.output_choice === choice}
                            onChange={() => onChange({
                                output_choice:     choice,
                                instrument_label:  instrument.label,
                            })}
                        />
                        {choice === "sheet_music"   ? "Sheet music"    : null}
                        {choice === "audio_isolate" ? "Isolated audio" : null}
                        {choice === "both"          ? "Both"           : null}
                    </label>
                ))}
            </div>
        </div>
    );
}