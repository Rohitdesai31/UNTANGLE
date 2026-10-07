import React, { useCallback, useEffect, useState } from "react";

import {
  getJobResults,
  getSketchUrl,
} from "../services/api";

import SketchViewer from "../components/SketchViewer";
import PidViewer from "../components/PidViewer";
import TagTable from "../components/TagTable";
import AuditReport from "../components/AuditReport";

export default function Results({
  jobId,
  onProcessAnother,
}) {
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
const [selectedOriginalId, setSelectedOriginalId] =
  useState(null);

  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true);
        setError("");

        const response = await getJobResults(jobId);

        setResults(response.results);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load UNTANGLE results."
        );
      } finally {
        setLoading(false);
      }
    }

    if (jobId) {
      loadResults();
    }
  }, [jobId]);

    const handleSelectOriginal = useCallback((originalId) => {
    setSelectedOriginalId(originalId);
  }, []);

  if (loading) {
    return (
      <main className="container py-5">
        <div className="text-center py-5">
          <div
            className="spinner-border text-primary"
            style={{ width: "3rem", height: "3rem" }}
            role="status"
          />

          <h4 className="mt-4 fw-bold">
            Preparing UNTANGLE results
          </h4>

          <p className="text-muted">
            Loading the simplified process sketch and validation report.
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="container py-5">
        <div className="alert alert-danger shadow-sm">
          <h5 className="fw-bold">
            Unable to load results
          </h5>

          <p className="mb-0">
            {error}
          </p>
        </div>
      </main>
    );
  }

  if (!results) {
    return null;
  }

  const audit = results.audit || {};

  const coverage = Number(audit.io_coverage || 0);

  const sketchUrl = getSketchUrl(jobId);

  return (
    <main className="container py-5">

      {/* HEADER */}

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4">

        <div>
          <div className="small text-primary fw-semibold mb-1">
            UNTANGLE • ANALYSIS COMPLETE
          </div>

          <h1 className="fw-bold mb-1">
            Processing Results
          </h1>

          <p className="text-muted mb-0">
            Customer P&ID → Simplified Process Sketch
          </p>
        </div>

        <div className="mt-3 mt-md-0">
          <span className="badge text-bg-success fs-6 px-3 py-2">
            ✓ Processing Complete
          </span>
        </div>

      </div>


      {/* JOB INFORMATION */}

      <div className="card shadow-sm mb-4">
        <div className="card-body">

          <div className="row g-3">

            <div className="col-md-6">
              <div className="text-muted small">
                Job ID
              </div>

              <div className="fw-semibold text-break">
                {jobId}
              </div>
            </div>

            <div className="col-md-3">
              <div className="text-muted small">
                Validation
              </div>

              <div className="fw-bold text-success">
                {audit.status || "PASS"}
              </div>
            </div>

            <div className="col-md-3">
              <div className="text-muted small">
                IO Coverage
              </div>

              <div className="fw-bold">
                {coverage.toFixed(2)}%
              </div>
            </div>

          </div>

        </div>
      </div>


      {/* MAIN VISUALIZATION */}

<div
  style={{
    display: "flex",
    gap: "24px",
    alignItems: "flex-start",
    margin: 0,
    padding: 0,
  }}
>
  <div
    style={{
      flex: 1,
      margin: 0,
      padding: 0,
    }}
  >
    <PidViewer
      jobId={jobId}
      selectedOriginalId={selectedOriginalId}
    />
  </div>

  <div
    style={{
      flex: 1,
      margin: 0,
      padding: 0,
    }}
  >
    <SketchViewer
      sketchUrl={sketchUrl}
      mapping={results.mapping || []}
      onSelectOriginal={handleSelectOriginal}
    />
  </div>
</div>


      {/* KPI CARDS */}

      <div className="row g-3 mb-4">

        <div className="col-6 col-lg-3">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small">
                IO Tags
              </div>

              <div className="fs-3 fw-bold">
                {audit.io_total || 0}
              </div>
            </div>
          </div>
        </div>


        <div className="col-6 col-lg-3">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small">
                Tags Found
              </div>

              <div className="fs-3 fw-bold text-success">
                {audit.io_found || 0}
              </div>
            </div>
          </div>
        </div>


        <div className="col-6 col-lg-3">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small">
                Tags Missing
              </div>

              <div className="fs-3 fw-bold text-danger">
                {audit.io_missing || 0}
              </div>
            </div>
          </div>
        </div>


        <div className="col-6 col-lg-3">
          <div className="card shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small">
                Equipment
              </div>

              <div className="fs-3 fw-bold">
                {audit.equipment_found || 0}
                <span className="fs-6 text-muted">
                  {" "}
                  / {audit.equipment_total || 0}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>


      {/* COVERAGE */}

      <div className="card shadow-sm mb-4">

        <div className="card-header fw-semibold">
          IO Tag Coverage
        </div>

        <div className="card-body">

          <div className="d-flex justify-content-between mb-2">

            <span className="text-muted">
              IO tags successfully identified
            </span>

            <strong>
              {coverage.toFixed(2)}%
            </strong>

          </div>

          <div
            className="progress"
            style={{ height: "12px" }}
          >

            <div
              className="progress-bar"
              role="progressbar"
              style={{
                width: `${Math.min(coverage, 100)}%`,
              }}
            />

          </div>

        </div>

      </div>


      {/* TAG REPORT */}

      <TagTable
        audit={audit}
      />


      {/* VALIDATION */}

      <AuditReport
        audit={audit}
      />


      {/* GRAPH SUMMARY */}

      <div className="card shadow-sm mt-4">

        <div className="card-header fw-semibold">
          Process Graph Summary
        </div>

        <div className="card-body">

          <div className="row g-3">

            <div className="col-md-3">

              <div className="border rounded p-3 h-100">

                <div className="text-muted small">
                  Original Nodes
                </div>

                <div className="fs-4 fw-bold">
                  {results.graph?.nodes?.length || 0}
                </div>

              </div>

            </div>


            <div className="col-md-3">

              <div className="border rounded p-3 h-100">

                <div className="text-muted small">
                  Original Connections
                </div>

                <div className="fs-4 fw-bold">
                  {results.graph?.edges?.length || 0}
                </div>

              </div>

            </div>


            <div className="col-md-3">

              <div className="border rounded p-3 h-100">

                <div className="text-muted small">
                  Simplified Nodes
                </div>

                <div className="fs-4 fw-bold">
                  {results.graph_simple?.nodes?.length || 0}
                </div>

              </div>

            </div>


            <div className="col-md-3">

              <div className="border rounded p-3 h-100">

                <div className="text-muted small">
                  Traceability Mappings
                </div>

                <div className="fs-4 fw-bold">
                  {results.mapping?.length || 0}
                </div>

              </div>

            </div>

          </div>

        </div>

      </div>


      {/* FINAL ACTION */}

      <div className="d-flex justify-content-between align-items-center mt-5">

        <div>
          <div className="fw-semibold">
            UNTANGLE analysis completed successfully.
          </div>

          <div className="text-muted small">
            Review the validation report before using the simplified sketch.
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={onProcessAnother}
        >
          Process Another P&ID
        </button>

      </div>

    </main>
  );
}