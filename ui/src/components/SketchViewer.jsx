import React, { useEffect, useRef, useState } from "react";

const EMPTY_MAPPING = [];

export default function SketchViewer({
  sketchUrl,
  mapping = EMPTY_MAPPING,
  onSelectOriginal,
}) {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadSvg() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(sketchUrl);

        if (!response.ok) {
          throw new Error("Unable to load simplified sketch.");
        }

        const svgText = await response.text();

        if (!active || !containerRef.current) {
          return;
        }

        containerRef.current.innerHTML = svgText;

        const svg = containerRef.current.querySelector("svg");

        if (!svg) {
          throw new Error("Generated sketch does not contain an SVG.");
        }

        svg.style.maxWidth = "100%";
        svg.style.maxHeight = "500px";
        svg.style.width = "100%";
        svg.style.height = "auto";

        const mappedElements =
          containerRef.current.querySelectorAll(
            '[id^="SIMPLE-"]'
          );

        mappedElements.forEach((element) => {
          const simplifiedId = element.getAttribute("id");

          const mappingItem = mapping.find(
            (item) =>
              item.simplified_id === simplifiedId
          );

          if (!mappingItem) {
            return;
          }

          element.style.cursor = "pointer";

          element.addEventListener(
            "click",
            () => {
              onSelectOriginal(
                mappingItem.original_id
              );
            }
          );

          element.addEventListener(
            "mouseenter",
            () => {
              element.style.filter =
                "drop-shadow(0 0 5px rgba(13, 110, 253, 0.8))";
            }
          );

          element.addEventListener(
            "mouseleave",
            () => {
              element.style.filter = "";
            }
          );
        });
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load simplified sketch."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (sketchUrl) {
      loadSvg();
    }

    return () => {
      active = false;

      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [sketchUrl, mapping, onSelectOriginal]);

  return (
    <div className="card shadow-sm">
      <div className="card-header fw-semibold">
  Simplified Process Sketch
</div>

<div
  className="card-body"
  style={{
    minHeight: "420px",
    backgroundColor: "#f8f9fa",
    overflow: "auto",
  }}
>
        {loading && (
          <div className="text-center py-5">
            <div
              className="spinner-border text-primary"
              role="status"
            />

            <div className="small text-muted mt-2">
              Loading simplified sketch...
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-danger">
            {error}
          </div>
        )}

        {!error && (
          <div
            ref={containerRef}
            className="d-flex justify-content-center align-items-center"
            style={{
              minHeight: "400px",
            }}
          />
        )}

        {!loading && !error && mapping.length > 0 && (
          <div className="small text-muted mt-2">
            Click an equipment or instrument in the
            simplified sketch to locate it in the
            original P&ID.
          </div>
        )}

        {!loading && !error && mapping.length === 0 && (
          <div className="small text-muted mt-2">
            Traceability mapping is not available.
          </div>
        )}
      </div>
    </div>
  );
}
 
