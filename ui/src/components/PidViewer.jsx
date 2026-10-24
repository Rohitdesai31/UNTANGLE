import React, { useEffect, useMemo, useState } from "react";

import {
  getAnalysis,
  getAnalysisPage,
  getAnalysisPageImageUrl,
} from "../services/api";


function getItemPage(item) {
  if (item?.page !== undefined && item?.page !== null) {
    return Number(item.page);
  }

  if (
    item?.page_number !== undefined &&
    item?.page_number !== null
  ) {
    return Number(item.page_number);
  }

  return null;
}


function belongsToPage(item, pageNumber) {
  const itemPage = getItemPage(item);

  if (itemPage === null || Number.isNaN(itemPage)) {
    return true;
  }

  return (
    itemPage === pageNumber ||
    itemPage === pageNumber - 1
  );
}


function getBbox(item) {
  const bbox = item?.bbox;

  if (!Array.isArray(bbox) || bbox.length < 4) {
    return null;
  }

  const values = bbox.slice(0, 4).map(Number);

  if (values.some((value) => Number.isNaN(value))) {
    return null;
  }

  return values;
}


function getLinePoints(item) {
  if (!Array.isArray(item?.points)) {
    return [];
  }

  return item.points
    .filter(
      (point) =>
        Array.isArray(point) &&
        point.length >= 2
    )
    .map((point) => [
      Number(point[0]),
      Number(point[1]),
    ])
    .filter(
      (point) =>
        !Number.isNaN(point[0]) &&
        !Number.isNaN(point[1])
    );
}


export default function PidViewer({
  jobId,
  selectedOriginalId,
}) {
  const [analysis, setAnalysis] = useState(null);
  const [pageInfo, setPageInfo] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  const [zoom, setZoom] = useState(1);
  const [loading, setLoading] = useState(true);
  const [pageLoading, setPageLoading] = useState(false);
  const [error, setError] = useState("");

  const [showSymbols, setShowSymbols] = useState(true);
  const [highlightedOriginalId, setHighlightedOriginalId] =
  useState(null);
  const [showOCR, setShowOCR] = useState(true);
  const [showLines, setShowLines] = useState(true);


  useEffect(() => {
    let active = true;

    async function loadAnalysis() {
      try {
        setLoading(true);
        setError("");

        const data = await getAnalysis(jobId);

        if (!active) {
          return;
        }

        setAnalysis(data);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load P&ID analysis."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAnalysis();

    return () => {
      active = false;
    };
  }, [jobId]);


  useEffect(() => {
    let active = true;

    async function loadPage() {
      try {
        setPageLoading(true);
        setError("");

        const data = await getAnalysisPage(
          jobId,
          pageNumber
        );

        if (!active) {
          return;
        }

        setPageInfo(data);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load P&ID page."
          );
        }
      } finally {
        if (active) {
          setPageLoading(false);
        }
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [jobId, pageNumber]);


  const imageUrl = useMemo(() => {
    return getAnalysisPageImageUrl(
      jobId,
      pageNumber
    );
  }, [jobId, pageNumber]);


  const symbols = useMemo(() => {
    if (!Array.isArray(analysis?.symbols)) {
      return [];
    }

    return analysis.symbols.filter((item) =>
      belongsToPage(item, pageNumber)
    );
  }, [analysis, pageNumber]);


  const ocrResults = useMemo(() => {
    if (!Array.isArray(analysis?.ocr)) {
      return [];
    }

    return analysis.ocr.filter((item) =>
      belongsToPage(item, pageNumber)
    );
  }, [analysis, pageNumber]);


  const lines = useMemo(() => {
    if (!Array.isArray(analysis?.lines)) {
      return [];
    }

    return analysis.lines.filter((item) =>
      belongsToPage(item, pageNumber)
    );
  }, [analysis, pageNumber]);


  function zoomIn() {
    setZoom((value) =>
      Math.min(value + 0.25, 3)
    );
  }


  function zoomOut() {
    setZoom((value) =>
      Math.max(value - 0.25, 0.5)
    );
  }


  function resetZoom() {
    setZoom(1);
  }


  function previousPage() {
    setPageNumber((value) =>
      Math.max(value - 1, 1)
    );

    setZoom(1);
  }


  function nextPage() {
    if (!pageInfo) {
      return;
    }

    setPageNumber((value) =>
      Math.min(
        value + 1,
        pageInfo.page_count
      )
    );

    setZoom(1);
  }

  useEffect(() => {
  setHighlightedOriginalId(selectedOriginalId || null);
}, [selectedOriginalId]);

  if (loading) {
    return (
      <div className="card shadow-sm">
        <div className="card-body text-center py-5">
          <div
            className="spinner-border text-primary mb-3"
            role="status"
          />

          <div className="fw-semibold">
            Loading P&ID analysis...
          </div>
        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div className="card shadow-sm">
        <div className="card-body">
          <div className="alert alert-danger mb-0">
            {error}
          </div>
        </div>
      </div>
    );
  }


  const symbolCount =
    Array.isArray(analysis?.symbols)
      ? analysis.symbols.length
      : 0;

  const ocrCount =
    Array.isArray(analysis?.ocr)
      ? analysis.ocr.length
      : 0;

  const lineCount =
    Array.isArray(analysis?.lines)
      ? analysis.lines.length
      : 0;


  return (
    <div className="card shadow-sm">

      <div className="card-header">

        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">

          <div>
            <div className="fw-semibold">
              Customer P&ID
            </div>

            <div className="small text-muted">
              Interactive document analysis
            </div>
          </div>

          {pageInfo && (
            <span className="badge text-bg-light border">
              Page {pageNumber} of{" "}
              {pageInfo.page_count}
            </span>
          )}

        </div>

      </div>


      <div className="card-body">

        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">

          <div className="btn-group">

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={previousPage}
              disabled={
                pageNumber <= 1 ||
                pageLoading
              }
            >
              ← Previous
            </button>

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={nextPage}
              disabled={
                !pageInfo ||
                pageNumber >= pageInfo.page_count ||
                pageLoading
              }
            >
              Next →
            </button>

          </div>


          <div className="btn-group">

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={zoomOut}
              disabled={zoom <= 0.5}
            >
              −
            </button>

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={resetZoom}
            >
              {Math.round(zoom * 100)}%
            </button>

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={zoomIn}
              disabled={zoom >= 3}
            >
              +
            </button>

          </div>

        </div>


        <div className="d-flex flex-wrap gap-2 mb-3">

          <button
            type="button"
            className={
              showSymbols
                ? "btn btn-primary btn-sm"
                : "btn btn-outline-primary btn-sm"
            }
            onClick={() =>
              setShowSymbols((value) => !value)
            }
          >
            Symbols
          </button>

          <button
            type="button"
            className={
              showOCR
                ? "btn btn-warning btn-sm"
                : "btn btn-outline-warning btn-sm"
            }
            onClick={() =>
              setShowOCR((value) => !value)
            }
          >
            OCR / Tags
          </button>

          <button
            type="button"
            className={
              showLines
                ? "btn btn-success btn-sm"
                : "btn btn-outline-success btn-sm"
            }
            onClick={() =>
              setShowLines((value) => !value)
            }
          >
            Process Lines
          </button>

        </div>


        <div
          style={{
            height: "650px",
            overflow: "auto",
            backgroundColor: "#f1f3f5",
            border: "1px solid #dee2e6",
            borderRadius: "0.375rem",
          }}
        >

          <div
            style={{
              minWidth: "fit-content",
              minHeight: "100%",
              padding: "20px",
              display: "flex",
              justifyContent: "center",
              alignItems: "flex-start",
            }}
          >

            <div
              style={{
                position: "relative",
                width: pageInfo?.width || 800,
                height: pageInfo?.height || 600,
                transform: `scale(${zoom})`,
                transformOrigin: "top center",
                transition: "transform 0.15s ease",
                backgroundColor: "white",
              }}
            >

              <img
                src={imageUrl}
                alt={`P&ID page ${pageNumber}`}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  height: "100%",
                  display: "block",
                  userSelect: "none",
                }}
              />


              {showLines &&
                lines.map((line, index) => {
                  const points =
                    getLinePoints(line);

                  if (points.length < 2) {
                    return null;
                  }

                  const pointString =
                    points
                      .map(
                        ([x, y]) =>
                          `${x},${y}`
                      )
                      .join(" ");

                  return (
                    <svg
                      key={
                        line.id ||
                        `line-${index}`
                      }
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: "100%",
                        pointerEvents: "none",
                        overflow: "visible",
                      }}
                      viewBox={`0 0 ${
                        pageInfo?.width || 800
                      } ${
                        pageInfo?.height || 600
                      }`}
                      preserveAspectRatio="none"
                    >
                      <polyline
                        points={pointString}
                        fill="none"
                        stroke="#198754"
                        strokeWidth="2"
                        vectorEffect="non-scaling-stroke"
                      />
                    </svg>
                  );
                })}


              {showSymbols &&
                symbols.map((symbol, index) => {
                  const bbox =
                    getBbox(symbol);

                  if (!bbox) {
                    return null;
                  }

                  const [
                    x1,
                    y1,
                    x2,
                    y2,
                  ] = bbox;

                  const width =
                    x2 - x1;

                  const height =
                    y2 - y1;

                    const isHighlighted =
                   highlightedOriginalId &&
                  symbol.id === highlightedOriginalId;

                  return (
                    <div
                      key={
                        symbol.id ||
                        `symbol-${index}`
                      }
                      title={
                        symbol.tag ||
                        symbol.class_name ||
                        "Detected symbol"
                      }
                      style={{
                        position: "absolute",
                        left: x1,
                        top: y1,
                        width,
                        height,
                      border: isHighlighted
  ? "4px solid #dc3545"
  : "2px solid #0d6efd",
backgroundColor: isHighlighted
  ? "rgba(220, 53, 69, 0.18)"
  : "rgba(13, 110, 253, 0.08)",
boxShadow: isHighlighted
  ? "0 0 12px rgba(220, 53, 69, 0.9)"
  : "none",
pointerEvents: "none",
boxSizing: "border-box",
zIndex: isHighlighted ? 20 : 10,
                      }}
                    >
                      <span
                        style={{
                          position: "absolute",
                          top: "-22px",
                          left: 0,
                         backgroundColor: isHighlighted
  ? "#dc3545"
  : "#0d6efd",
                          color: "white",
                          padding:
                            "2px 5px",
                          borderRadius:
                            "3px",
                          fontSize:
                            "11px",
                          whiteSpace:
                            "nowrap",
                        }}
                      >
                       {isHighlighted ? "Selected: " : ""}
{symbol.tag ||
  symbol.class_name ||
  "Symbol"}
                      </span>
                    </div>
                  );
                })}


                {showOCR &&
  ocrResults.map((item, index) => {
    const bbox = getBbox(item);

    if (!bbox) {
      return null;
    }

    const [
      x1,
      y1,
      x2,
      y2,
    ] = bbox;

    return (
      <div
        key={
          item.id ||
          `ocr-${index}`
        }
        title={
          item.text ||
          "OCR text"
        }
        style={{
          position: "absolute",
          left: x1,
          top: y1,
          width: x2 - x1,
          height: y2 - y1,
          border: "1px solid #ffc107",
          backgroundColor:
            "rgba(255, 193, 7, 0.08)",
          pointerEvents: "none",
          boxSizing: "border-box",
          zIndex: 11,
        }}
      >
        <span
          style={{
            position: "absolute",
            top: "-20px",
            left: 0,
            backgroundColor: "#ffc107",
            color: "#212529",
            padding: "2px 5px",
            borderRadius: "3px",
            fontSize: "11px",
            whiteSpace: "nowrap",
            maxWidth: "250px",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {item.text || "OCR"}
        </span>
      </div>
    );
  })}

            </div>

          </div>

        </div>


        {pageLoading && (
          <div className="small text-muted mt-2">
            Loading page...
          </div>
        )}


        <div className="row g-3 mt-3">

          <div className="col-md-4">
            <div className="border rounded p-3">
              <div className="small text-muted">
                Detected Symbols
              </div>

              <div className="fs-4 fw-bold">
                {symbolCount}
              </div>
            </div>
          </div>


          <div className="col-md-4">
            <div className="border rounded p-3">
              <div className="small text-muted">
                OCR Results
              </div>

              <div className="fs-4 fw-bold">
                {ocrCount}
              </div>
            </div>
          </div>


          <div className="col-md-4">
            <div className="border rounded p-3">
              <div className="small text-muted">
                Process Lines
              </div>

              <div className="fs-4 fw-bold">
                {lineCount}
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}