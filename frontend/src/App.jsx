import { usePipeline, STAGES } from "./hooks/usePipeline";
import InputPanel    from "./components/InputPanel";
import ConfirmPanel  from "./components/ConfirmPanel";
import ProgressBar   from "./components/ProgressBar";
import ResultsPanel  from "./components/ResultsPanel";
import DownloadPanel from "./components/DownloadPanel";
import "./App.css";

export default function App() {
  const pipeline = usePipeline();
  const { stage, error, reset } = pipeline;

  return (
      <div className="app">
        <header>
          <h1>Music Analyser</h1>
          <p className="subtitle">Identify instruments, isolate stems, generate sheet music</p>
        </header>

        <main>
          {stage === STAGES.IDLE || stage === STAGES.SUBMITTING ? (
              <InputPanel
                  onSubmit={pipeline.submit}
                  loading={stage === STAGES.SUBMITTING}
              />
          ) : null}

          {stage === STAGES.CONFIRMING ? (
              <ConfirmPanel
                  candidates={pipeline.candidates}
                  metadata={pipeline.metadata}
                  onConfirm={pipeline.confirm}
                  onBack={reset}
              />
          ) : null}

          {stage === STAGES.PROCESSING ? (
              <ProgressBar progress={pipeline.progress} />
          ) : null}

          {stage === STAGES.SELECTING ? (
              <ResultsPanel
                  results={pipeline.results}
                  onExport={pipeline.exportOutputs}
              />
          ) : null}

          {stage === STAGES.EXPORTING ? (
              <p className="status-msg">Generating your files…</p>
          ) : null}

          {stage === STAGES.DONE ? (
              <DownloadPanel outputs={pipeline.outputs} onReset={reset} />
          ) : null}

          {stage === STAGES.ERROR ? (
              <div className="error-box">
                <p>{error}</p>
                <button onClick={reset}>Try again</button>
              </div>
          ) : null}
        </main>
      </div>
  );
}