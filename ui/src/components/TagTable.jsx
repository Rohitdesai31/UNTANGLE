import React from "react";


export default function TagTable({ audit }) {
  if (!audit) {
    return null;
  }

  const foundTags = audit.found_tags || [];
  const missingTags = audit.missing_tags || [];

  return (
    <div className="card shadow-sm mt-4">
      <div className="card-header fw-semibold">
        IO Tag Report
      </div>

      <div className="card-body">

        <div className="row g-3 mb-4">

          <div className="col-md-3">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Total IO
              </div>
              <div className="fs-4 fw-bold">
                {audit.io_total}
              </div>
            </div>
          </div>

          <div className="col-md-3">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Found
              </div>
              <div className="fs-4 fw-bold text-success">
                {audit.io_found}
              </div>
            </div>
          </div>

          <div className="col-md-3">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Missing
              </div>
              <div className="fs-4 fw-bold text-danger">
                {audit.io_missing}
              </div>
            </div>
          </div>

          <div className="col-md-3">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Coverage
              </div>
              <div className="fs-4 fw-bold">
                {audit.io_coverage}%
              </div>
            </div>
          </div>

        </div>


        <h6 className="fw-semibold text-success">
          Found Tags
        </h6>

        <div className="mb-4">
          {foundTags.length > 0 ? (
            foundTags.map((tag) => (
              <span
                key={tag}
                className="badge text-bg-success me-2 mb-2"
              >
                {tag}
              </span>
            ))
          ) : (
            <span className="text-muted">
              No IO tags found.
            </span>
          )}
        </div>


        <h6 className="fw-semibold text-danger">
          Missing Tags
        </h6>

        <div>
          {missingTags.length > 0 ? (
            missingTags.map((tag) => (
              <span
                key={tag}
                className="badge text-bg-danger me-2 mb-2"
              >
                {tag}
              </span>
            ))
          ) : (
            <span className="text-success">
              No missing IO tags.
            </span>
          )}
        </div>

      </div>
    </div>
  );
}