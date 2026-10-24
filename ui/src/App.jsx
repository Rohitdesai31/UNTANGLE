import React, { useState } from "react";

import Home from "./pages/Home";
import Processing from "./pages/Processing";
import PidAnalysis from "./pages/PidAnalysis";
import Results from "./pages/Results";

export default function App() {
  const [step, setStep] = useState("upload");
  const [jobId, setJobId] = useState(null);

  function handleProcessingStart(id) {
    setJobId(id);
    setStep("processing");
  }

  function handleProcessingComplete(id) {
    setJobId(id);
    setStep("pid");
  }

  function handleViewResults() {
    setStep("results");
  }

  function handleProcessAnother() {
    setJobId(null);
    setStep("upload");
  }

  if (step === "processing" && jobId) {
    return (
      <Processing
        jobId={jobId}
        onComplete={handleProcessingComplete}
      />
    );
  }

  if (step === "pid" && jobId) {
    return (
      <PidAnalysis
        jobId={jobId}
        onViewResults={handleViewResults}
      />
    );
  }

  if (step === "results" && jobId) {
    return (
      <Results
        jobId={jobId}
        onProcessAnother={handleProcessAnother}
      />
    );
  }

  return (
    <Home
      onProcessingStart={handleProcessingStart}
    />
  );
}