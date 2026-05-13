import { useState } from "react";
import InstrumentCard  from "./InstrumentCard";
import UnclearStemCard from "./UnclearStemCard";

export default function ResultsPanel({ results, onExport }) {
    const [selections,   setSelections]   = useState({});
    const [audioFormat,  setAudioFormat]  = useState("wav");

    const updateSelection = (stemName, update) => {
        setSelections(prev => ({
            ...prev,
            [stemName]: { ...(prev[stemName] || {}), stem_name: stemName, ...update },
        }));
    };

    const handleExport = () => {
        const payload = Object.values(selections).filter(s => s.output_choice);
        if (!payload.length) return alert("Please select at least one instrument.");
        onExport(payload, audioFormat);
    };

    return (
        <div className="panel results-panel">
            <h2>Instruments detected</h2>
            <p className="subtitle">
                Select the instruments you want, then choose sheet music,
                isolated audio, or both.
            </p>

            <div className="instrument-grid">
                {results.confirmed_instruments.map(inst => (
                    <InstrumentCard
                        key={inst.stem}
                        instrument={inst}
                        selection={selections[inst.stem]}
                        onChange={update => updateSelection(inst.stem, update)}
                    />
                ))}

                {results.unclear_stems.map(stem => (
                    <UnclearStemCard
                        key={stem.stem}
                        stem={stem}
                        selection={selections[stem.stem]}
                        onChange={update => updateSelection(stem.stem, update)}
                    />
                ))}
            </div>

            <div className="export-controls">
                <label>
                    Audio format:
                    <select value={audioFormat} onChange={e => setAudioFormat(e.target.value)}>
                        <option value="wav">WAV (best quality)</option>
                        <option value="flac">FLAC (lossless, smaller)</option>
                        <option value="aiff">AIFF (Logic / GarageBand)</option>
                    </select>
                </label>
                <button className="btn-primary" onClick={handleExport}>
                    Generate outputs
                </button>
            </div>
        </div>
    );
}