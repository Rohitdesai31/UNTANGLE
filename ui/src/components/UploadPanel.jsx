import React, { useState } from "react";

import {
  createJob,
  uploadJobFiles,
  processJob,
} from "../services/api";

export default function UploadPanel({ onProcessingStart }) {
  const [pidFile, setPidFile] = useState(null);
  const [ioFile, setIoFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    if (!pidFile || !ioFile) {
      setError(
        "Please select both the P&ID PDF and IO List Excel file."
      );
      return;
    }

    try {
      setLoading(true);
      setError("");

      const job = await createJob();

      await uploadJobFiles(
        job.id,
        pidFile,
        ioFile
      );

      if (onProcessingStart) {
        onProcessingStart(job.id);
      }

      await processJob(job.id);

    } catch (err) {
      setLoading(false);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start UNTANGLE processing."
      );
    }
  }

  return (
    <div className="card shadow-sm">
      <div className="card-header fw-semibold">
        Upload P&ID and IO List
      </div>

      <div className="card-body">
        <p className="text-muted">
          Upload a customer P&ID PDF and its corresponding
          IO List Excel file to start UNTANGLE processing.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="form-label fw-semibold">
              P&ID PDF
            </label>

            <input
              type="file"
              className="form-control"
              accept=".pdf"
              disabled={loading}
              onChange={(event) => {
                setPidFile(
                  event.target.files?.[0] || null
                );
              }}
            />

            {pidFile && (
              <div className="small text-success mt-2">
                Selected: {pidFile.name}
              </div>
            )}
          </div>

          <div className="mb-4">
            <label className="form-label fw-semibold">
              IO List Excel
            </label>

            <input
              type="file"
              className="form-control"
              accept=".xlsx,.xls"
              disabled={loading}
              onChange={(event) => {
                setIoFile(
                  event.target.files?.[0] || null
                );
              }}
            />

            {ioFile && (
              <div className="small text-success mt-2">
                Selected: {ioFile.name}
              </div>
            )}
          </div>

          {error && (
            <div className="alert alert-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary w-100"
            disabled={loading}
          >
            {loading
              ? "Starting UNTANGLE..."
              : "Start UNTANGLE Processing"}
          </button>
        </form>
      </div>
    </div>
  );
}