import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useDropzone } from "react-dropzone";
import { Upload, Github, ArrowRight, FileArchive, Sparkles, GitBranch, TestTube, RefreshCw } from "lucide-react";
import { createJobFromZip, createJobFromGitHub } from "../api";

export default function UploadPage() {
  const navigate = useNavigate();
  const [githubUrl, setGithubUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setUploadedFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/zip": [".zip"] },
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024,
  });

  const handleSubmitZip = async () => {
    if (!uploadedFile) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await createJobFromZip(uploadedFile);
      navigate(`/results/${data.job_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create job.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitGitHub = async () => {
    if (!githubUrl.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await createJobFromGitHub(githubUrl.trim());
      navigate(`/results/${data.job_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create job.");
    } finally {
      setIsLoading(false);
    }
  };

  const features = [
    {
      icon: <Sparkles size={24} />,
      title: "AI Explanations",
      desc: "Module & function-level code understanding",
      color: "var(--color-accent-light)",
    },
    {
      icon: <GitBranch size={24} />,
      title: "Dependency Graph",
      desc: "Interactive visual dependency mapping",
      color: "var(--color-info)",
    },
    {
      icon: <TestTube size={24} />,
      title: "Unit Tests",
      desc: "Auto-generated tests with >60% coverage",
      color: "var(--color-success)",
    },
    {
      icon: <RefreshCw size={24} />,
      title: "Modernized Code",
      desc: "Refactored code with breaking change alerts",
      color: "var(--color-warning)",
    },
  ];

  return (
    <div
      style={{
        minHeight: "calc(100vh - 69px)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "48px 24px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Gradient Orbs */}
      <div
        style={{
          position: "absolute",
          top: "-200px",
          left: "-200px",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(108,92,231,0.15) 0%, transparent 70%)",
          filter: "blur(60px)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-200px",
          right: "-200px",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(0,206,201,0.1) 0%, transparent 70%)",
          filter: "blur(60px)",
          pointerEvents: "none",
        }}
      />

      {/* Hero Section */}
      <div className="animate-fade-in-up" style={{ textAlign: "center", marginBottom: 48, position: "relative", zIndex: 1 }}>
        <h1
          style={{
            fontSize: "clamp(2rem, 5vw, 3.5rem)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            marginBottom: 16,
          }}
        >
          Understand. Modernize.{" "}
          <span
            style={{
              background: "linear-gradient(135deg, var(--color-accent-light), var(--color-success))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Ship.
          </span>
        </h1>
        <p
          style={{
            fontSize: "1.15rem",
            color: "var(--color-text-secondary)",
            maxWidth: 560,
            margin: "0 auto",
            lineHeight: 1.6,
          }}
        >
          Upload your legacy codebase and let AI explain, map dependencies, generate tests, and modernize your code — all in one click.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className="animate-fade-in-up glass-card"
        style={{
          width: "100%",
          maxWidth: 620,
          padding: 32,
          position: "relative",
          zIndex: 1,
          animationDelay: "0.15s",
        }}
      >
        {/* ZIP Upload */}
        <div
          {...getRootProps()}
          style={{
            border: `2px dashed ${isDragActive ? "var(--color-accent)" : "var(--color-border)"}`,
            borderRadius: 12,
            padding: "40px 24px",
            textAlign: "center",
            cursor: "pointer",
            transition: "all 0.3s ease",
            background: isDragActive ? "rgba(108,92,231,0.08)" : "transparent",
            marginBottom: 24,
          }}
        >
          <input {...getInputProps()} />
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: "rgba(108,92,231,0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
            }}
          >
            {uploadedFile ? <FileArchive size={28} color="var(--color-success)" /> : <Upload size={28} color="var(--color-accent-light)" />}
          </div>
          {uploadedFile ? (
            <div>
              <p style={{ fontWeight: 600, color: "var(--color-success)", marginBottom: 4 }}>{uploadedFile.name}</p>
              <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
                {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB — Click to change
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontWeight: 600, marginBottom: 4 }}>
                {isDragActive ? "Drop your ZIP here..." : "Drag & drop a ZIP file here"}
              </p>
              <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted)" }}>or click to browse (max 25MB)</p>
            </div>
          )}
        </div>

        {uploadedFile && (
          <button
            className="btn-primary"
            onClick={handleSubmitZip}
            disabled={isLoading}
            style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 24 }}
          >
            {isLoading ? (
              <div className="animate-spin" style={{ width: 20, height: 20, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" }} />
            ) : (
              <>
                Analyze Codebase <ArrowRight size={18} />
              </>
            )}
          </button>
        )}

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, margin: "0 0 24px" }}>
          <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
          <span style={{ fontSize: "0.8rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.1em" }}>or</span>
          <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
        </div>

        {/* GitHub URL */}
        <div style={{ display: "flex", gap: 12 }}>
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              gap: 10,
              background: "var(--color-bg-primary)",
              border: "1px solid var(--color-border)",
              borderRadius: 12,
              padding: "0 14px",
            }}
          >
            <Github size={18} color="var(--color-text-muted)" />
            <input
              type="text"
              placeholder="https://github.com/user/repo"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmitGitHub()}
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--color-text-primary)",
                fontSize: "0.95rem",
                padding: "14px 0",
                fontFamily: "var(--font-mono)",
              }}
            />
          </div>
          <button
            className="btn-primary"
            onClick={handleSubmitGitHub}
            disabled={isLoading || !githubUrl.trim()}
            style={{ display: "flex", alignItems: "center", gap: 8, whiteSpace: "nowrap" }}
          >
            {isLoading ? (
              <div className="animate-spin" style={{ width: 20, height: 20, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%" }} />
            ) : (
              <>
                Clone & Analyze <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div
            style={{
              marginTop: 16,
              padding: "12px 16px",
              borderRadius: 10,
              background: "rgba(255,107,107,0.1)",
              border: "1px solid rgba(255,107,107,0.2)",
              color: "var(--color-danger)",
              fontSize: "0.9rem",
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Feature Cards */}
      <div
        className="animate-fade-in-up"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
          maxWidth: 960,
          width: "100%",
          marginTop: 48,
          position: "relative",
          zIndex: 1,
          animationDelay: "0.3s",
        }}
      >
        {features.map((f, i) => (
          <div
            key={i}
            className="glass-card"
            style={{ padding: "24px 20px", display: "flex", flexDirection: "column", gap: 10 }}
          >
            <div style={{ color: f.color }}>{f.icon}</div>
            <h3 style={{ fontWeight: 700, fontSize: "0.95rem" }}>{f.title}</h3>
            <p style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)", lineHeight: 1.5 }}>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
