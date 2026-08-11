import { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { getJobStatus, getJobResults } from "../api";
import ExplanationTab from "../components/ExplanationTab";
import DependencyGraphTab from "../components/DependencyGraphTab";
import TestsTab from "../components/TestsTab";
import RefactorTab from "../components/RefactorTab";
import { Sparkles, GitBranch, TestTube, RefreshCw, Loader } from "lucide-react";

const TABS = [
  { id: "explanation", label: "Explanation", icon: <Sparkles size={16} /> },
  { id: "graph", label: "Dependency Graph", icon: <GitBranch size={16} /> },
  { id: "tests", label: "Generated Tests", icon: <TestTube size={16} /> },
  { id: "refactor", label: "Refactored Code", icon: <RefreshCw size={16} /> },
];

export default function ResultsPage() {
  const { jobId } = useParams();
  const [activeTab, setActiveTab] = useState("explanation");
  const [jobStatus, setJobStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  // Poll for job status
  useEffect(() => {
    const poll = async () => {
      try {
        const status = await getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === "complete") {
          clearInterval(pollRef.current);
          const data = await getJobResults(jobId);
          setResults(data);
        } else if (status.status === "failed") {
          clearInterval(pollRef.current);
          setError(status.error_message || "Job failed.");
        }
      } catch (err) {
        setError("Failed to fetch job status.");
        clearInterval(pollRef.current);
      }
    };

    poll(); // Immediate first call
    pollRef.current = setInterval(poll, 3000);

    return () => clearInterval(pollRef.current);
  }, [jobId]);

  // Loading state
  if (!jobStatus || (jobStatus.status !== "complete" && jobStatus.status !== "failed")) {
    return (
      <div
        style={{
          minHeight: "calc(100vh - 69px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 32,
        }}
      >
        <div className="animate-pulse-glow" style={{ width: 80, height: 80, borderRadius: 20, background: "var(--color-bg-card)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Loader size={36} color="var(--color-accent-light)" className="animate-spin" />
        </div>
        <div style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Analyzing your codebase...</h2>
          <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>
            Gemini is reading, explaining, and modernizing your code.
          </p>
          {/* Progress Bar */}
          <div style={{ width: 320, height: 6, borderRadius: 3, background: "var(--color-bg-card)", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                borderRadius: 3,
                background: "linear-gradient(90deg, var(--color-accent), var(--color-success))",
                width: `${jobStatus?.progress || 0}%`,
                transition: "width 0.5s ease",
              }}
            />
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)", marginTop: 8 }}>
            {jobStatus?.progress || 0}% complete
            {jobStatus?.total_files ? ` — ${jobStatus.total_files} files detected` : ""}
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ minHeight: "calc(100vh - 69px)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="glass-card" style={{ padding: 32, textAlign: "center", maxWidth: 480 }}>
          <div style={{ fontSize: "2.5rem", marginBottom: 16 }}>❌</div>
          <h2 style={{ fontSize: "1.3rem", fontWeight: 700, marginBottom: 8, color: "var(--color-danger)" }}>Analysis Failed</h2>
          <p style={{ color: "var(--color-text-secondary)", lineHeight: 1.6 }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "calc(100vh - 69px)" }}>
      {/* Tab Sidebar */}
      <nav
        style={{
          width: 220,
          background: "var(--color-bg-secondary)",
          borderRight: "1px solid var(--color-border)",
          padding: "24px 12px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 14px",
              borderRadius: 10,
              border: "none",
              cursor: "pointer",
              fontSize: "0.9rem",
              fontWeight: activeTab === tab.id ? 600 : 400,
              background: activeTab === tab.id ? "rgba(108,92,231,0.15)" : "transparent",
              color: activeTab === tab.id ? "var(--color-accent-light)" : "var(--color-text-secondary)",
              transition: "all 0.2s ease",
              textAlign: "left",
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}

        {/* Job Metadata */}
        <div style={{ marginTop: "auto", padding: "16px 14px", borderTop: "1px solid var(--color-border)" }}>
          <p style={{ fontSize: "0.7rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Job ID</p>
          <p style={{ fontSize: "0.75rem", color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)", wordBreak: "break-all" }}>
            {jobId}
          </p>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, padding: 32, overflow: "auto" }}>
        {results && (
          <>
            {activeTab === "explanation" && <ExplanationTab explanations={results.explanations} />}
            {activeTab === "graph" && <DependencyGraphTab graph={results.graph} />}
            {activeTab === "tests" && <TestsTab tests={results.tests} />}
            {activeTab === "refactor" && <RefactorTab refactors={results.refactors} />}
          </>
        )}
      </main>
    </div>
  );
}
