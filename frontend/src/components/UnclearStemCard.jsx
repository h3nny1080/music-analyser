import { useState } from "react";

export default function UnclearStemCard({ stem, selection, onChange }) {
    const [chosen, setChosen] = useState(null);

    const pick = (label) => {
        setChosen(label);
        onChange({ instrument_label: label });
    };

    return (
        <div className={`instrument-card unclear ${chosen ? "selected" : ""}`}>
            <div className="card-header">
        <span className="instrument-name">
          {chosen || "Unknown instrument"}
        </span>
                <span className="unclear-badge">Needs confirmation</span>
            </div>
            <p className="stem-label">Stem: {stem.stem}</p>

            <p className="unclear-prompt">What is this instrument?</p>
            <div className="label-options">
                {stem.top3.map(opt => (
                    <button
                        key={opt.label}
                        className={chosen === opt.label ? "label-btn active" : "label-btn"}
                        onClick={() => pick(opt.label)}
                    >
                        {opt.label}
                        <span className="opt-confidence">{opt.confidence}%</span>
                    </button>
                ))}
            </div>

            {chosen && (
                <div className="output-choices">
                    {["sheet_music", "audio_isolate", "both"].map(choice => (
                        <label key={choice} className="choice-option">
                            <input
                                type="radio"
                                name={`choice-${stem.stem}`}
                                value={choice}
                                checked={selection?.output_choice === choice}
                                onChange={() => onChange({
                                    output_choice:    choice,
                                    instrument_label: chosen,
                                })}
                            />
                            {choice === "sheet_music"   ? "Sheet music"    : null}
                            {choice === "audio_isolate" ? "Isolated audio" : null}
                            {choice === "both"          ? "Both"           : null}
                        </label>
                    ))}
                </div>
            )}
        </div>
    );
}