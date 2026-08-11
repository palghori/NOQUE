import { useState } from "react";
import Editor from "@monaco-editor/react";
import { FileCode, CheckCircle, XCircle, RotateCw } from "lucide-react";

export default function TestsTab({ tests }) {
  const [selectedFile, setSelectedFile] = useState(tests.length > 0 ? 0 : -1);

  if (tests.length === 0) {
    return (
      <div className="animate-fade-in-up" style={{ textAlign: "center", padding: 64, color: "var(--color-text-muted)" }}>
        No tests were generated.
      </div>
    );
  }

  const currentTest = tests[selectedFile];

  return (
    <div className="animate-fade-in-up">
      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Generated Unit Tests</h2>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>
        AI-generated tests targeting &gt;60% line coverage. Tests were validated by running pytest / jest.
      </p>

      <div style={{ display: "flex", gap: 20, height: "calc(100vh - 240px)" }}>
        {/* File List Sidebar */}
        <div
          style={{
            width: 260,
            background: "var(--color-bg-secondary)",
            borderRadius: 12,
            border: "1px solid var(--color-border)",
            overflow: "auto",
            flexShrink: 0,
          }}
        >
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--color-border)" }}>
            <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Files ({tests.length})
            </p>
          </div>
          {tests.map((test, i) => (
            <button
              key={i}
              onClick={() => setSelectedFile(i)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "12px 16px",
                border: "none",
                cursor: "pointer",
                background: selectedFile === i ? "rgba(108,92,231,0.12)" : "transparent",
                color: selectedFile === i ? "var(--color-accent-light)" : "var(--color-text-secondary)",
                fontSize: "0.85rem",
                textAlign: "left",
                borderBottom: "1px solid var(--color-border)",
                transition: "all 0.2s ease",
              }}
            >
              <FileCode size={14} />
              <span style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "0.8rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {test.file_path}
              </span>
              {/* Coverage Badge */}
              <span
                className={`badge ${test.coverage_pct >= 60 ? "badge-success" : "badge-danger"}`}
                style={{ fontSize: "0.7rem", padding: "2px 6px" }}
              >
                {test.coverage_pct != null ? `${test.coverage_pct}%` : "—"}
              </span>
            </button>
          ))}
        </div>

        {/* Code Editor Panel */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Metadata Bar */}
          <div
            className="glass-card"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              padding: "12px 20px",
              borderRadius: 12,
            }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: "0.9rem" }}>
              {currentTest.file_path}
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 12, alignItems: "center" }}>
              {currentTest.retry_count > 0 && (
                <span className="badge badge-info" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <RotateCw size={12} /> {currentTest.retry_count} retries
                </span>
              )}
              <span className={`badge ${currentTest.coverage_pct >= 60 ? "badge-success" : "badge-danger"}`}>
                Coverage: {currentTest.coverage_pct != null ? `${currentTest.coverage_pct}%` : "N/A"}
              </span>
              <span className={`badge ${currentTest.passed ? "badge-success" : "badge-warning"}`} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                {currentTest.passed ? <CheckCircle size={12} /> : <XCircle size={12} />}
                {currentTest.passed ? "Passed" : "Issues"}
              </span>
            </div>
          </div>

          {/* Monaco Editor */}
          <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", border: "1px solid var(--color-border)" }}>
            <Editor
              height="100%"
              language={currentTest.file_path.endsWith(".js") ? "javascript" : "python"}
              value={currentTest.test_code}
              theme="vs-dark"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: "var(--font-mono)",
                scrollBeyondLastLine: false,
                padding: { top: 16, bottom: 16 },
                lineNumbers: "on",
                renderLineHighlight: "none",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
