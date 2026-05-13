import { useState, useCallback } from "react";
import {
    submitInput, confirmYoutube,
    getResults, submitExport, pollProgress
} from "../api";

// Pipeline stages
export const STAGES = {
    IDLE:       "idle",
    SUBMITTING: "submitting",
    CONFIRMING: "confirming",   // streaming link — show YouTube candidates
    PROCESSING: "processing",   // Demucs + CLAP running
    SELECTING:  "selecting",    // show results, user picks instruments
    EXPORTING:  "exporting",    // output layer running
    DONE:       "done",
    ERROR:      "error",
};

export function usePipeline() {
    const [stage,      setStage]      = useState(STAGES.IDLE);
    const [error,      setError]      = useState(null);
    const [candidates, setCandidates] = useState([]);
    const [metadata,   setMetadata]   = useState(null);
    const [sessionId,  setSessionId]  = useState(null);
    const [results,    setResults]    = useState(null);
    const [outputs,    setOutputs]    = useState(null);
    const [progress,   setProgress]   = useState({ stage: "", percent: 0 });

    const submit = useCallback(async (urlOrFile) => {
        setStage(STAGES.SUBMITTING);
        setError(null);

        try {
            const formData = new FormData();
            if (typeof urlOrFile === "string") {
                formData.append("url", urlOrFile);
            } else {
                formData.append("file", urlOrFile);
            }

            const data = await submitInput(formData);

            if (data.status === "confirm") {
                // Streaming link — need user to confirm YouTube match
                setCandidates(data.candidates);
                setMetadata(data.metadata);
                setStage(STAGES.CONFIRMING);
            } else if (data.session_id) {
                // YouTube / file — go straight to processing
                setSessionId(data.session_id);
                setStage(STAGES.PROCESSING);
                _pollUntilReady(data.session_id);
            }
        } catch (e) {
            setError(e.response?.data?.message || e.message);
            setStage(STAGES.ERROR);
        }
    }, []);

    const confirm = useCallback(async (youtubeUrl) => {
        setStage(STAGES.PROCESSING);
        try {
            const data = await confirmYoutube(youtubeUrl);
            setSessionId(data.session_id);
            _pollUntilReady(data.session_id);
        } catch (e) {
            setError(e.response?.data?.message || e.message);
            setStage(STAGES.ERROR);
        }
    }, []);

    const _pollUntilReady = useCallback(async (sid) => {
        const interval = setInterval(async () => {
            try {
                const prog = await pollProgress(sid);
                setProgress(prog);
                if (prog.percent >= 100) {
                    clearInterval(interval);
                    const res = await getResults(sid);
                    setResults(res);
                    setStage(STAGES.SELECTING);
                }
            } catch (e) {
                clearInterval(interval);
                setError(e.message);
                setStage(STAGES.ERROR);
            }
        }, 2000);  // poll every 2 seconds
    }, []);

    const exportOutputs = useCallback(async (selections, audioFormat) => {
        setStage(STAGES.EXPORTING);
        try {
            const data = await submitExport(sessionId, selections, audioFormat);
            setOutputs(data);
            setStage(STAGES.DONE);
        } catch (e) {
            setError(e.response?.data?.message || e.message);
            setStage(STAGES.ERROR);
        }
    }, [sessionId]);

    const reset = useCallback(() => {
        setStage(STAGES.IDLE);
        setError(null);
        setCandidates([]);
        setMetadata(null);
        setSessionId(null);
        setResults(null);
        setOutputs(null);
        setProgress({ stage: "", percent: 0 });
    }, []);

    return {
        stage, error, candidates, metadata,
        results, outputs, progress,
        submit, confirm, exportOutputs, reset,
    };
}