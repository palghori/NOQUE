import { useState } from "react";
import ReactDiffViewer from "react-diff-viewer-continued";
import { FileCode, AlertTriangle, Shield, ArrowRight } from "lucide-react";

export default function RefactorTab({ refactors }) {
  const [selectedFile, setSelectedFile] = useState(refactors.length > 0 ? 0 : -1);

  if (refactors.length === 0) {
    return (
      <div className="animate-fade-in-up" style={{ textAlign: "center", padding: 64, color: "var(--color-text-muted)" }}>
        No refactored code available.
      </div>
    );
  }

  const current = refactors[selectedFile];
  const breakingChanges = current.breaking_changes || [];

  const riskColor = {
    high: "var(--color-danger)",
    medium: "var(--color-warning)",
    low: "var(--color-success)",
  };

  return (
    <div className="animate-fade-in-up">
      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Modernized Code</h2>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>
        Side-by-side diff of original vs. modernized code with breaking change warnings.
      </p>

      {/* File Selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {refactors.map((r, i) => (
          <button
            key={i}
            onClick={() => setSelectedFile(i)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 14px",
              borderRadius: 8,
              border: selectedFile === i ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
              background: selectedFile === i ? "rgba(108,92,231,0.12)" : "var(--color-bg-card)",
              color: selectedFile === i ? "var(--color-accent-light)" : "var(--color-text-secondary)",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontFamily: "var(--font-mono)",
              transition: "all 0.2s ease",
            }}
          >
            <FileCode size={13} />
            {r.file_path}
            {(r.breaking_changes || []).length > 0 && (
              <AlertTriangle size={13} color="var(--color-warning)" />
            )}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 20 }}>
        {/* Diff Viewer */}
        <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", border: "1px solid var(--color-border)" }}>
          <ReactDiffViewer
            oldValue={current.original_code || ""}
            newValue={current.refactored_code || ""}
            splitView={true}
            leftTitle="Original Code"
            rightTitle="Modernized Code"
            useDarkTheme={true}
            styles={{
              variables: {
                dark: {
                  diffViewerBackground: "#0a0a0f",
                  addedBackground: "rgba(0,206,201,0.08)",
                  addedColor: "#e8e8f0",
                  removedBackground: "rgba(255,107,107,0.08)",
                  removedColor: "#e8e8f0",
                  wordAddedBackground: "rgba(0,206,201,0.25)",
                  wordRemovedBackground: "rgba(255,107,107,0.25)",
                  addedGutterBackground: "rgba(0,206,201,0.15)",
                  removedGutterBackground: "rgba(255,107,107,0.15)",
                  gutterBackground: "#12121a",
                  gutterBackgroundDark: "#0a0a0f",
                  codeFoldBackground: "#1a1a2e",
                  codeFoldGutterBackground: "#12121a",
                  emptyLineBackground: "#0a0a0f",
                },
              },
              contentText: {
                fontFamily: "var(--font-mono)",
                fontSize: "0.85rem",
              },
            }}
          />
        </div>

        {/* Breaking Changes Sidebar */}
        {breakingChanges.length > 0 && (
          <div
            style={{
              width: 300,
              flexShrink: 0,
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Shield size={16} color="var(--color-warning)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: 700 }}>
                Breaking Changes ({breakingChanges.length})
              </h3>
            </div>

            {breakingChanges.map((bc, i) => (
              <div
                key={i}
                className="glass-card"
                style={{ padding: 16 }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <AlertTriangle size={14} color={riskColor[bc.risk] || "var(--color-warning)"} />
                  <span
                    className={`badge ${bc.risk === "high" ? "badge-danger" : bc.risk === "medium" ? "badge-warning" : "badge-success"}`}
                  >
                    {bc.risk} risk
                  </span>
                </div>
                <p style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: 6 }}>
                  {bc.change}
                </p>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                  <ArrowRight size={12} color="var(--color-text-muted)" style={{ marginTop: 3, flexShrink: 0 }} />
                  <p style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", lineHeight: 1.5 }}>
                    {bc.migration_note}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
