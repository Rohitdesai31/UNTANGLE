import React from "react";

import PidViewer from "../components/PidViewer";

export default function PidAnalysis({
  jobId,
  onViewResults,
}) {
  return (
    <main className="container py-5">

      <div className="mb-4">
        <div className="small text-primary fw-semibold mb-2">
          STEP 3 OF 4
        </div>

        <h1 className="fw-bold">
          Original P&ID
        </h1>

        <p className="text-muted">
          Review the original customer P&ID before viewing
          the simplified process sketch.
        </p>
      </div>

      <PidViewer jobId={jobId} />

      <div className="d-flex justify-content-end mt-4">
        <button
          className="btn btn-primary"
          onClick={onViewResults}
        >
          View Results →
        </button>
      </div>

    </main>
  );
}