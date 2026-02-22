import React, { useState, useRef } from "react";
import "./MultiStrokePredict.css";

interface BatchResult {
  age: number;
  height_cm: number;
  weight_kg: number;
  hypertension: string;
  diabetes: string;
  smoking_status: string;
  cholesterol_mg_dl: number;
  stroke_risk: string;
  probability: number | null;
}

const MultiStrokePredict: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError("");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    if (!file.name.match(/\.(xlsx|csv)$/i)) {
      setError("Please upload only Excel (.xlsx) or CSV (.csv) files.");
      return;
    }

    setError("");
    setLoading(true);
    setResults([]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/predict-batch", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.results || !Array.isArray(data.results)) {
        throw new Error("Invalid response format from server");
      }

      setResults(data.results);
    } catch (err: any) {
      setError(err.message || "Failed to process file. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadResults = () => {
    // Implement Excel download functionality
    console.log("Downloading results...", results);
    // You would typically generate and download an Excel file here
  };

  const handleClear = () => {
    setFile(null);
    setFileName("");
    setResults([]);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatProbability = (prob: number | null) => {
    if (prob === null) return "—";
    return `${(prob * 100).toFixed(1)}%`;
  };

  const getRiskColor = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "high": return "#ef4444";
      case "medium": return "#f59e0b";
      case "low": return "#10b981";
      default: return "#6b7280";
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "high": return "🔴";
      case "medium": return "🟡";
      case "low": return "🟢";
      default: return "⚪";
    }
  };

  return (
    <div className="multi-stroke-container">
      <div className="header-section">
        <h1 className="main-title">
          <span className="title-icon">🧠</span>
          Batch Stroke Risk Prediction
        </h1>
        <p className="subtitle">
          Upload patient data in Excel or CSV format to get stroke risk predictions for multiple individuals
        </p>
      </div>

      <div className="content-grid">
        {/* Left Column - Upload & Instructions */}
        <div className="left-column">
          <div className="upload-card card">
            <div className="card-header">
              <span className="card-icon">📤</span>
              <h2>Upload Patient Data</h2>
            </div>
            
            <div className="file-upload-area">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.csv"
                onChange={handleFileChange}
                className="file-input"
                id="file-input"
              />
              <label htmlFor="file-input" className="file-dropzone">
                <div className="upload-icon">📄</div>
                <p className="upload-text">
                  {fileName ? fileName : "Click to select or drag & drop"}
                </p>
                <p className="upload-hint">Supports .xlsx and .csv files</p>
              </label>
            </div>

            <div className="upload-controls">
              <button
                onClick={handleUpload}
                disabled={loading || !file}
                className={`upload-btn ${loading ? "loading" : ""}`}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Processing...
                  </>
                ) : (
                  "Generate Predictions"
                )}
              </button>
              
              {(file || results.length > 0) && (
                <button
                  onClick={handleClear}
                  className="clear-btn"
                >
                  Clear All
                </button>
              )}
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
          </div>

          <div className="instructions-card card">
            <div className="card-header">
              <span className="card-icon">📋</span>
              <h2>Required Format</h2>
            </div>
            
            <div className="table-container">
              <table className="format-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Example</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><code>age</code></td>
                    <td>Integer</td>
                    <td>45</td>
                  </tr>
                  <tr>
                    <td><code>height_cm</code></td>
                    <td>Numeric</td>
                    <td>170</td>
                  </tr>
                  <tr>
                    <td><code>weight_kg</code></td>
                    <td>Numeric</td>
                    <td>70</td>
                  </tr>
                  <tr>
                    <td><code>hypertension</code></td>
                    <td>String</td>
                    <td>Yes / No</td>
                  </tr>
                  <tr>
                    <td><code>diabetes</code></td>
                    <td>String</td>
                    <td>Yes / No</td>
                  </tr>
                  <tr>
                    <td><code>smoking_status</code></td>
                    <td>String</td>
                    <td>Non-Smoker / Formerly Smoked / Smokes</td>
                  </tr>
                  <tr>
                    <td><code>cholesterol_mg_dl</code></td>
                    <td>Numeric</td>
                    <td>220</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="instructions-footer">
              <p className="note">
                <strong>Note:</strong> Ensure all columns are present and data follows the specified format.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column - Results */}
        <div className="right-column">
          {results.length > 0 ? (
            <div className="results-card card">
              <div className="results-header">
                <div>
                  <h2>Prediction Results</h2>
                  <p className="results-count">{results.length} patients analyzed</p>
                </div>
                <button
                  onClick={handleDownloadResults}
                  className="download-btn"
                  disabled={results.length === 0}
                >
                  <span className="download-icon">⬇️</span>
                  Download Excel
                </button>
              </div>

              <div className="results-summary">
                <div className="summary-item">
                  <span className="summary-label">High Risk</span>
                  <span className="summary-value high-risk">
                    {results.filter(r => r.stroke_risk?.toLowerCase() === "high").length}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Medium Risk</span>
                  <span className="summary-value medium-risk">
                    {results.filter(r => r.stroke_risk?.toLowerCase() === "medium").length}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Low Risk</span>
                  <span className="summary-value low-risk">
                    {results.filter(r => r.stroke_risk?.toLowerCase() === "low").length}
                  </span>
                </div>
              </div>

              <div className="table-wrapper">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Age</th>
                      <th>Hypertension</th>
                      <th>Diabetes</th>
                      <th>Smoking</th>
                      <th>Cholesterol</th>
                      <th>Risk Level</th>
                      <th>Probability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result, index) => (
                      <tr key={index}>
                        <td className="age-cell">{result.age}</td>
                        <td>
                          <span className={`status-badge ${result.hypertension === "Yes" ? "badge-yes" : "badge-no"}`}>
                            {result.hypertension}
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge ${result.diabetes === "Yes" ? "badge-yes" : "badge-no"}`}>
                            {result.diabetes}
                          </span>
                        </td>
                        <td>
                          <span className="smoking-badge">
                            {result.smoking_status}
                          </span>
                        </td>
                        <td className="cholesterol-cell">{result.cholesterol_mg_dl}</td>
                        <td>
                          <span 
                            className="risk-badge"
                            style={{ backgroundColor: getRiskColor(result.stroke_risk) }}
                          >
                            {getRiskIcon(result.stroke_risk)} {result.stroke_risk}
                          </span>
                        </td>
                        <td className="probability-cell">
                          {formatProbability(result.probability)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="empty-state card">
              <div className="empty-state-icon">📊</div>
              <h3>No Results Yet</h3>
              <p>Upload a file to see stroke risk predictions for your patients.</p>
              <div className="empty-state-features">
                <div className="feature">
                  <span className="feature-icon">⚡</span>
                  <span>Batch process multiple patients</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🎯</span>
                  <span>AI-powered risk assessment</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">📈</span>
                  <span>Detailed probability scores</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MultiStrokePredict;