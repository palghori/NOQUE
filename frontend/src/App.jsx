import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { VscHome, VscArchive, VscSettingsGear, VscGithubAlt } from "react-icons/vsc";
import Dock from "./components/Dock";
import UploadPage from "./pages/UploadPage";
import ResultsPage from "./pages/ResultsPage";
import "./index.css";

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();

  const dockItems = [
    { icon: <VscHome size={18} />, label: "Home", onClick: () => navigate("/") },
    { icon: <VscArchive size={18} />, label: "Upload ZIP", onClick: () => navigate("/") },
    { icon: <VscGithubAlt size={18} />, label: "GitHub", onClick: () => window.open("https://github.com/palghori/NOQUE", "_blank") },
    { icon: <VscSettingsGear size={18} />, label: "About NOQUE", onClick: () => alert("NOQUE v1.0 — AI-Powered Legacy Code Modernizer") },
  ];

  return (
      <div className="min-h-screen">
        {/* Navigation Header */}
        <header
          style={{
            background: "var(--color-bg-secondary)",
            borderBottom: "1px solid var(--color-border)",
            padding: "16px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 50,
            backdropFilter: "blur(12px)",
          }}
        >
          <a
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              textDecoration: "none",
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: "linear-gradient(135deg, var(--color-accent), #8b5cf6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.2rem",
              }}
            >
              ⚡
            </div>
            <span
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--color-text-primary)",
                letterSpacing: "-0.02em",
              }}
            >
              NO<span style={{ color: "var(--color-accent-light)" }}>QUE</span>
            </span>
          </a>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <span className="badge badge-info">Python</span>
            <span className="badge badge-warning">JavaScript</span>
          </div>
        </header>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/results/:jobId" element={<ResultsPage />} />
        </Routes>

        {/* macOS-style Dock */}
        <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 100 }}>
          <Dock
            items={dockItems}
            panelHeight={68}
            baseItemSize={50}
            magnification={70}
          />
        </div>
      </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
