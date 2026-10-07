import React, { useEffect, useState } from "react";

import {
  getJobStatus,
  getJobResults,
} from "../services/api";

export default function Processing({
  jobId,
  onComplete,
}) {
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function checkProcessing() {
      try {
        const statusResponse =
          await getJobStatus(jobId);

        if (!active) {
          return;
        }

        if (statusResponse.status === "completed") {
          await getJobResults(jobId);

          if (active) {
            onComplete(jobId);
          }

          return;
        }

        if (statusResponse.status === "failed") {
          setError(
            statusResponse.message ||
            "UNTANGLE processing failed."
          );

          return;
        }

        setTimeout(checkProcessing, 1000);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to check processing status."
          );
        }
      }
    }

    checkProcessing();

    return () => {
      active = false;
    };
  }, [jobId, onComplete]);

  return (
    <main className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-7">
          <div className="card shadow-sm">
            <div className="card-body p-5">

              <div className="text-center mb-5">
                <div
                  className="spinner-border text-primary mb-3"
                  style={{
                    width: "3rem",
                    height: "3rem",
                  }}
                  role="status"
                />

                <h2 className="fw-bold">
                  UNTANGLE is processing
                </h2>

                <p className="text-muted mb-0">
                  Please wait while the P&ID is analyzed
                  and the simplified process sketch is prepared.
                </p>
              </div>

              <div className="list-group">

                <div className="list-group-item d-flex justify-content-between align-items-center">
                  <span>
                    P&ID uploaded
                  </span>
                  <span className="badge text-bg-success">
                    ✓
                  </span>
                </div>

                <div className="list-group-item d-flex justify-content-between align-items-center">
                  <span>
                    IO List uploaded
                  </span>
                  <span className="badge text-bg-success">
                    ✓
                  </span>
                </div>

                <div className="list-group-item d-flex justify-content-between align-items-center">
                  <span>
                    P&ID analysis
                  </span>
                  <span className="badge text-bg-primary">
                    Processing
                  </span>
                </div>

                <div className="list-group-item d-flex justify-content-between align-items-center">
                  <span>
                    Topology generation
                  </span>
                  <span className="badge text-bg-primary">
                    Processing
                  </span>
                </div>

                <div className="list-group-item d-flex justify-content-between align-items-center">
                  <span>
                    Simplified sketch
                  </span>
                  <span className="badge text-bg-primary">
                    Processing
                  </span>
                </div>

              </div>

              {error && (
                <div className="alert alert-danger mt-4 mb-0">
                  {error}
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </main>
  );
}