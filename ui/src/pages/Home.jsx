import React from "react";

import UploadPanel from "../components/UploadPanel";

export default function Home({ onProcessingStart }) {
  return (
    <main className="container py-5">
      <div className="text-center mb-5">
        <h1 className="display-5 fw-bold">
          UNTANGLE
        </h1>

        <p className="lead text-muted">
          Customer P&ID in. Simplified process sketch out.
          Powered by AI.
        </p>
      </div>

      <div className="row justify-content-center">
        <div className="col-lg-8">
          <UploadPanel
            onProcessingStart={onProcessingStart}
          />
        </div>
      </div>
    </main>
  );
}