import { useState } from "react";
import { ChevronDown, ChevronRight, FileCode } from "lucide-react";

export default function ExplanationTab({ explanations }) {
  // Group explanations by file_path
  const grouped = {};
  explanations.forEach((exp) => {
    if (!grouped[exp.file_path]) {
      grouped[exp.file_path] = { module_summary: null, functions: [] };
    }
    if (exp.module_summary && !exp.function_name) {
      grouped[exp.file_path].module_summary = exp.module_summary;
    }
    if (exp.function_name) {
      grouped[exp.file_path].functions.push(exp);
    }
  });

  return (
    <div className="animate-fade-in-up">
      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Code Explanations</h2>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: 32, lineHeight: 1.6 }}>
        AI-generated explanations at module and function level for every file in your codebase.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {Object.entries(grouped).map(([filePath, data]) => (
          <FileAccordion key={filePath} filePath={filePath} data={data} />
        ))}
      </div>
    </div>
  );
}

function FileAccordion({ filePath, data }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="glass-card" style={{ overflow: "hidden" }}>
      {/* File Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "16px 20px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "var(--color-text-primary)",
          fontSize: "0.95rem",
          fontWeight: 600,
          textAlign: "left",
        }}
      >
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <FileCode size={16} color="var(--color-accent-light)" />
        <span style={{ fontFamily: "var(--font-mono)" }}>{filePath}</span>
      </button>

      {isOpen && (
        <div style={{ padding: "0 20px 20px", borderTop: "1px solid var(--color-border)" }}>
          {/* Module Summary */}
          {data.module_summary && (
            <div style={{ padding: "16px 0", borderBottom: data.functions.length > 0 ? "1px solid var(--color-border)" : "none" }}>
              <p style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Module Summary</p>
              <p style={{ lineHeight: 1.7, color: "var(--color-text-secondary)" }}>{data.module_summary}</p>
            </div>
          )}

          {/* Function Details */}
          {data.functions.map((func, i) => (
            <div key={i} style={{ padding: "16px 0", borderBottom: i < data.functions.length - 1 ? "1px solid var(--color-border)" : "none" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--color-accent-light)" }}>{func.function_name}()</span>
                {func.confidence != null && (
                  <span
                    className={`badge ${func.confidence >= 0.8 ? "badge-success" : func.confidence >= 0.5 ? "badge-warning" : "badge-danger"}`}
                  >
                    {Math.round(func.confidence * 100)}% confident
                  </span>
                )}
              </div>
              <p style={{ lineHeight: 1.7, color: "var(--color-text-secondary)", marginBottom: 8 }}>{func.purpose}</p>

              {func.params && func.params.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", fontWeight: 600 }}>Params: </span>
                  {func.params.map((p, j) => (
                    <span key={j} style={{ fontSize: "0.85rem", fontFamily: "var(--font-mono)", color: "var(--color-info)", marginRight: 8 }}>
                      {p}
                    </span>
                  ))}
                </div>
              )}
              {func.returns && (
                <div>
                  <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", fontWeight: 600 }}>Returns: </span>
                  <span style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)" }}>{func.returns}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
