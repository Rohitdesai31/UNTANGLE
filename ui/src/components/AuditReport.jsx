import React from "react";


function CheckRow({ label, value }) {
  return (
    <div className="d-flex justify-content-between align-items-center border-bottom py-2">
      <span>{label}</span>

      <span
        className={
          value
            ? "badge text-bg-success"
            : "badge text-bg-danger"
        }
      >
        {value ? "PASS" : "FAIL"}
      </span>
    </div>
  );
}


export default function AuditReport({ audit }) {
  if (!audit) {
    return null;
  }

  const checks = audit.validation_checks || {};

  return (
    <div className="card shadow-sm mt-4">
      <div className="card-header fw-semibold">
        Validation & Audit Report
      </div>

      <div className="card-body">

        <div className="d-flex justify-content-between align-items-center mb-3">
          <span className="fw-semibold">
            Overall Status
          </span>

          <span
            className={
              audit.status === "PASS"
                ? "badge text-bg-success fs-6"
                : "badge text-bg-danger fs-6"
            }
          >
            {audit.status}
          </span>
        </div>


        <CheckRow
          label="Required equipment preserved"
          value={checks.all_required_equipment_preserved}
        />

        <CheckRow
          label="Found IO tags preserved"
          value={checks.all_found_io_tags_preserved}
        />

        <CheckRow
          label="Missing IO tags reported"
          value={checks.missing_io_tags_reported}
        />

        <CheckRow
          label="Process connections preserved"
          value={checks.process_connections_preserved}
        />

        <CheckRow
          label="Flow direction preserved"
          value={checks.flow_direction_preserved}
        />

        <CheckRow
          label="Simplified graph valid"
          value={checks.simplified_graph_valid}
        />


        <div className="row g-3 mt-3">

          <div className="col-md-6">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Equipment
              </div>

              <strong>
                {audit.equipment_found} / {audit.equipment_total}
              </strong>
            </div>
          </div>

          <div className="col-md-6">
            <div className="border rounded p-3">
              <div className="text-muted small">
                Connections
              </div>

              <strong>
                {audit.connections_valid ? "Valid" : "Invalid"}
              </strong>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}