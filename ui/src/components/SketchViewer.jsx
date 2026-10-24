import React from "react";

const SketchViewer = () => {
  return (
    <div className="sketch-viewer">
      <h2>Simplified Process Sketch</h2>

      <div className="sketch-container">
        <img
          src="/sketch.svg"
          alt="Simplified P&ID Process Sketch"
          className="sketch-image"
        />
      </div>
    </div>
  );
};

export default SketchViewer;