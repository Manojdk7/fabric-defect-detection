import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

// Use 127.0.0.1 — another service (Node) may be bound to localhost:5000 on IPv6
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000/api";
const DEFAULT_CONFIDENCE = 0.35;

const emptySummary = {
  total_defects: 0,
  status: "READY",
  quality_score: null,
};

const defaultWorkflow = {
  operator_name: "",
  batch_id: "",
  fabric_type: "",
  production_line: "Line A",
  shift: "A",
};

function loadSavedUser() {
  try {
    return JSON.parse(localStorage.getItem("qis_user") || "null");
  } catch {
    return null;
  }
}

const icons = {
  activity: "M4 12h4l3-8 4 16 3-8h2",
  alert: "M12 9v4m0 4h.01M10.3 4.1 2.2 18a2 2 0 0 0 1.7 3h16.2a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  camera: "M4 8h3l2-3h6l2 3h3v11H4z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
  check: "m5 13 4 4L19 7",
  clock: "M12 6v6l4 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  download: "M12 3v12m0 0 5-5m-5 5-5-5M5 21h14",
  gauge: "M4 14a8 8 0 0 1 16 0M12 14l4-4M7 18h10",
  image: "M4 5h16v14H4z M8 13l3-3 4 5 2-2 3 4 M8 9h.01",
  refresh: "M20 6v5h-5M4 18v-5h5M18.5 9A7 7 0 0 0 6.1 6.1M5.5 15A7 7 0 0 0 17.9 17.9",
  search: "M11 19a8 8 0 1 1 5.7-2.3L21 21",
  shield: "M12 3 20 7v5c0 5-3.4 8-8 9-4.6-1-8-4-8-9V7z",
  upload: "M12 16V4m0 0-5 5m5-5 5 5M5 20h14",
  user: "M20 21a8 8 0 0 0-16 0M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z",
  zoom: "M11 19a8 8 0 1 1 5.7-2.3L21 21m-10-6V7m-4 4h8",
};

function Icon({ name }) {
  return (
    <svg aria-hidden="true" className="icon" fill="none" viewBox="0 0 24 24">
      <path d={icons[name]} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

function Sparkline({ values = [36, 48, 42, 60, 58, 72, 68], tone = "blue" }) {
  const max = Math.max(...values);
  const min = Math.min(...values);
  const spread = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1 || 1)) * 100;
      const y = 34 - ((value - min) / spread) * 28;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg className={`sparkline ${tone}`} preserveAspectRatio="none" viewBox="0 0 100 40">
      <polyline points={points} />
    </svg>
  );
}

function KpiCard({ icon, label, value, trend, tone, values }) {
  return (
    <article className={`kpi-card ${tone}`}>
      <div className="kpi-top">
        <span className="icon-tile">
          <Icon name={icon} />
        </span>
        <span className="trend">{trend}</span>
      </div>
      <span className="kpi-label">{label}</span>
      <strong>{value}</strong>
      <Sparkline tone={tone} values={values} />
    </article>
  );
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) {
    return "--";
  }

  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function App() {
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const loadingRef = useRef(false);
  const resultViewerRef = useRef(null);

  const [authToken, setAuthToken] = useState(() => localStorage.getItem("qis_token") || "");
  const [user, setUser] = useState(loadSavedUser);
  const [loginForm, setLoginForm] = useState({ username: "admin", password: "admin123" });
  const [loginError, setLoginError] = useState("");
  const [backendStatus, setBackendStatus] = useState("unchecked");
  const [backendMessage, setBackendMessage] = useState("Backend not checked");
  const [backendVersion, setBackendVersion] = useState("1.0.0");
  const [activeSource, setActiveSource] = useState("upload");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewName, setPreviewName] = useState("");
  const [confidence, setConfidence] = useState(DEFAULT_CONFIDENCE);
  const [inspectionMode, setInspectionMode] = useState("fabric");
  const [cameraStatus, setCameraStatus] = useState("idle");
  const [autoScan, setAutoScan] = useState(false);
  const [scanInterval, setScanInterval] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [inspectionResult, setInspectionResult] = useState(null);
  const [processingTime, setProcessingTime] = useState(null);
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [sortKey, setSortKey] = useState("confidence");
  const [sortDirection, setSortDirection] = useState("desc");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragActive, setDragActive] = useState(false);
  const [workflow, setWorkflow] = useState(defaultWorkflow);
  const [captureCount, setCaptureCount] = useState(0);
  const [countdownTimer, setCountdownTimer] = useState(0);

  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  const resetResults = useCallback(() => {
    setError("");
    setInspectionResult(null);
    setProcessingTime(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setAutoScan(false);
    setCameraStatus("idle");
    setCaptureCount(0);
    setCountdownTimer(0);
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [previewUrl]);

  const checkBackend = useCallback(async () => {
    setBackendStatus("checking");
    setBackendMessage("Checking backend");

    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();

      if (!response.ok) {
        setBackendStatus("offline");
        setBackendMessage(data.error || "Backend responded with an error");
        return;
      }

      setBackendStatus("online");
      setBackendVersion(data.version || "1.0.0");
      setBackendMessage(`${data.status} - ${data.service}`);
    } catch (err) {
      setBackendStatus("offline");
      setBackendMessage(`Backend not connected: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  const loadHistory = useCallback(
    async (tokenOverride) => {
      const token = tokenOverride || authToken;
      if (!token) {
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/inspections?limit=25`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();

        if (!response.ok) {
          if (response.status === 401) {
            setAuthToken("");
            setUser(null);
            localStorage.removeItem("qis_token");
            localStorage.removeItem("qis_user");
          }
          return;
        }

        const mapped = (data.items || []).map((item) => ({
          id: item.inspection_id,
          time: new Date(item.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }),
          status: item.summary?.status || "READY",
          score: item.summary?.quality_score ?? 0,
          defects: item.summary?.total_defects ?? 0,
          critical: item.severity_breakdown?.critical ?? 0,
          medium: item.severity_breakdown?.medium ?? 0,
          minor: item.severity_breakdown?.minor ?? 0,
          duration: item.processing_time_ms,
          mode: item.metadata?.fabric_type || item.defect_type || "fabric",
        }));
        setHistory(mapped);
      } catch {
        // History is helpful, but the main inspection flow should stay usable.
      }
    },
    [authToken],
  );

  useEffect(() => {
    if (authToken) {
      loadHistory();
    }
  }, [authToken, loadHistory]);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoginError("");

    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginForm),
      });
      const data = await response.json();

      if (!response.ok) {
        setLoginError(data.error || "Login failed.");
        return;
      }

      setAuthToken(data.token);
      setUser(data.user);
      localStorage.setItem("qis_token", data.token);
      localStorage.setItem("qis_user", JSON.stringify(data.user));
      loadHistory(data.token);
    } catch (err) {
      setLoginError(`Login error: ${err.message}`);
    }
  };

  const handleLogout = async () => {
    if (authToken) {
      await fetch(`${API_BASE_URL}/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      }).catch(() => {});
    }

    setAuthToken("");
    setUser(null);
    setHistory([]);
    localStorage.removeItem("qis_token");
    localStorage.removeItem("qis_user");
  };

  const setImageSelection = useCallback(
    (file, objectUrl, name) => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setSelectedFile(file);
      setPreviewUrl(objectUrl);
      setPreviewName(name);
      resetResults();
    },
    [previewUrl, resetResults],
  );

  const handleFile = useCallback(
    (file) => {
      if (!file) {
        return;
      }

      setImageSelection(file, URL.createObjectURL(file), file.name);
    },
    [setImageSelection],
  );

  const handleFileChange = (event) => {
    handleFile(event.target.files?.[0]);
  };

  const inspectFile = useCallback(
    async (fileToInspect = selectedFile) => {
      if (!fileToInspect) {
        setError("No image selected.");
        return;
      }

      const startedAt = performance.now();
      setLoading(true);
      setError("");
      setInspectionResult(null);

      try {
        const formData = new FormData();
        formData.append("file", fileToInspect);
        formData.append("confidence", String(confidence));
        formData.append("defect_type", "fabric");
        Object.entries(workflow).forEach(([key, value]) => {
          formData.append(key, value);
        });

        const response = await fetch(`${API_BASE_URL}/inspect`, {
          method: "POST",
          headers: { Authorization: `Bearer ${authToken}` },
          body: formData,
        });

        const data = await response.json();
        const elapsed = Math.round(performance.now() - startedAt);
        setProcessingTime(elapsed);

        if (!response.ok) {
          setError(data.error || "Inspection failed.");
          return;
        }

        setInspectionResult(data);
        loadHistory();
        setHistory((current) => [
          {
            id: data.inspection_id,
            time: nowTime(),
            status: data.summary?.status || "READY",
            score: data.summary?.quality_score ?? 0,
            defects: data.summary?.total_defects ?? 0,
            critical: data.severity_breakdown?.critical ?? 0,
            medium: data.severity_breakdown?.medium ?? 0,
            minor: data.severity_breakdown?.minor ?? 0,
            duration: elapsed,
            mode: inspectionMode,
          },
          ...current,
        ].slice(0, 8));
      } catch (err) {
        setProcessingTime(Math.round(performance.now() - startedAt));
        setError(`Inspection error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    },
    [authToken, confidence, inspectionMode, loadHistory, selectedFile, workflow],
  );

  const startCamera = async () => {
    console.log("[Camera] startCamera called, cameraStatus:", cameraStatus);

    if (cameraStatus === "live") {
      console.log("[Camera] Already live, returning.");
      return;
    }

    if (!window.isSecureContext) {
      console.error("[Camera] Not a secure context! URL:", window.location.href);
      setCameraStatus("blocked");
      setError("Camera needs a secure browser context. Open the dashboard at http://localhost:3000.");
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      console.error("[Camera] getUserMedia not available.");
      setCameraStatus("blocked");
      setError("Camera access is not available in this browser.");
      return;
    }

    setError("");
    setCameraStatus("starting");
    console.log("[Camera] Requesting camera permission...");

    try {
      let stream;
      const preferredConstraints = {
        audio: false,
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };
      const fallbackConstraints = {
        audio: false,
        video: true,
      };

      try {
        stream = await navigator.mediaDevices.getUserMedia(preferredConstraints);
        console.log("[Camera] Got stream with preferred constraints.");
      } catch (preferredError) {
        console.warn("[Camera] Preferred constraints failed:", preferredError.message, "— trying fallback.");
        stream = await navigator.mediaDevices.getUserMedia(fallbackConstraints);
        console.log("[Camera] Got stream with fallback constraints.");
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        console.log("[Camera] Video playing, dimensions:", videoRef.current.videoWidth, "x", videoRef.current.videoHeight);
      } else {
        console.error("[Camera] videoRef.current is null!");
      }

      setCameraStatus("live");
      setAutoScan(true);
      setCaptureCount(0);
      setCountdownTimer(scanInterval);
      console.log("[Camera] Camera is now live.");
    } catch (err) {
      console.error("[Camera] Error:", err.name, err.message);
      setCameraStatus("blocked");
      const help =
        err.name === "NotAllowedError"
          ? "Allow camera permission in the browser address bar, then press Start Camera again."
          : err.name === "NotFoundError"
            ? "No webcam was found. Connect or enable a camera and retry."
            : "Close other apps using the camera and retry.";
      setError(`Camera error: ${err.message}. ${help}`);
    }
  };

  const captureFrame = useCallback(
    (runInspection = false) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (!video || !canvas || video.readyState < 2) {
        setError("Camera frame is not ready.");
        return;
      }

      const width = video.videoWidth || 1280;
      const height = video.videoHeight || 720;
      canvas.width = width;
      canvas.height = height;

      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            setError("Unable to capture image.");
            return;
          }

          const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
          const file = new File([blob], `camera_capture_${timestamp}.jpg`, {
            type: "image/jpeg",
          });
          const objectUrl = URL.createObjectURL(blob);

          setImageSelection(file, objectUrl, file.name);

          if (runInspection) {
            inspectFile(file);
          }
        },
        "image/jpeg",
        0.92,
      );
    },
    [inspectFile, setImageSelection],
  );

  useEffect(() => {
    if (!autoScan || cameraStatus !== "live") {
      setCountdownTimer(0);
      return;
    }

    setCountdownTimer(scanInterval);

    const countdownInterval = window.setInterval(() => {
      setCountdownTimer((prev) => {
        if (prev <= 1) {
          // Time to capture
          if (!loadingRef.current) {
            setCaptureCount((count) => count + 1);
            captureFrame(true);
          }
          return scanInterval; // Reset countdown
        }
        return prev - 1;
      });
    }, 1000);

    return () => window.clearInterval(countdownInterval);
  }, [autoScan, cameraStatus, scanInterval, captureFrame]);

  const handleSourceChange = (source) => {
    setActiveSource(source);
    resetResults();

    if (source === "upload") {
      stopCamera();
    }
  };

  const handleClear = () => {
    setSelectedFile(null);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl("");
    setPreviewName("");
    setConfidence(DEFAULT_CONFIDENCE);
    setInspectionMode("fabric");
    setAutoScan(false);
    setCaptureCount(0);
    setCountdownTimer(0);
    resetResults();

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getAnnotatedImageUrl = (result) => {
    const resultPath = result?.annotated_image_path;

    if (!resultPath) {
      return "";
    }

    const filename = resultPath.split(/[\\/]/).pop();
    return `${API_BASE_URL}/results/${encodeURIComponent(filename)}`;
  };

  const exportCsv = () => {
    const headers = ["Defect Type", "Severity", "Confidence Score", "Coordinates", "Timestamp", "Status"];
    const rows = (inspectionResult?.detections || []).map((detection) => [
      detection.type,
      detection.severity,
      `${Math.round(detection.confidence * 100)}%`,
      detection.bbox?.join(" ") || "",
      inspectionResult?.inspection_id || "",
      detection.severity === "high" ? "Reject" : "Review",
    ]);
    const csv = [headers, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `inspection_${inspectionResult?.inspection_id || "results"}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportPdf = () => {
    window.print();
  };

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setSortKey(key);
    setSortDirection("asc");
  };

  const openFullscreen = () => {
    if (resultViewerRef.current?.requestFullscreen) {
      resultViewerRef.current.requestFullscreen();
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    handleFile(event.dataTransfer.files?.[0]);
  };

  const summary = inspectionResult?.summary || emptySummary;
  const detections = useMemo(() => inspectionResult?.detections || [], [inspectionResult]);
  const severity = inspectionResult?.severity_breakdown || { critical: 0, medium: 0, minor: 0 };
  const defectBreakdown = inspectionResult?.defect_breakdown || {};
  const annotatedImageUrl = getAnnotatedImageUrl(inspectionResult);
  const appState = loading ? "processing" : error ? "error" : backendStatus === "online" ? "ready" : "offline";
  const qualityScoreText = summary.quality_score === null || summary.quality_score === undefined ? "--" : `${summary.quality_score}%`;
  const defectTotal = Math.max(1, severity.critical + severity.medium + severity.minor);
  const severityChart = {
    background: `conic-gradient(#ef4444 0 ${(severity.critical / defectTotal) * 100}%, #f59e0b ${(severity.critical / defectTotal) * 100}% ${((severity.critical + severity.medium) / defectTotal) * 100}%, #22c55e ${((severity.critical + severity.medium) / defectTotal) * 100}% 100%)`,
  };
  const historyScores = history.length ? history.map((item) => item.score).reverse() : [76, 82, 80, 88, 84, 91, 89];
  const filteredDetections = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return [...detections]
      .filter((detection) => {
        const matchesQuery = !query || `${detection.type} ${detection.severity}`.toLowerCase().includes(query);
        const matchesSeverity = severityFilter === "all" || detection.severity === severityFilter;
        return matchesQuery && matchesSeverity;
      })
      .sort((a, b) => {
        const direction = sortDirection === "asc" ? 1 : -1;
        const aValue = sortKey === "area" ? a.area_percentage : a[sortKey];
        const bValue = sortKey === "area" ? b.area_percentage : b[sortKey];

        if (typeof aValue === "number" && typeof bValue === "number") {
          return (aValue - bValue) * direction;
        }

        return String(aValue).localeCompare(String(bValue)) * direction;
      });
  }, [detections, searchTerm, severityFilter, sortDirection, sortKey]);
  const fileMeta = selectedFile
    ? [
        ["Name", previewName],
        ["Size", formatBytes(selectedFile.size)],
        ["Type", selectedFile.type || "image"],
        ["Mode", inspectionMode],
      ]
    : [
        ["Name", "--"],
        ["Size", "--"],
        ["Type", "--"],
        ["Mode", inspectionMode],
      ];
  const recommendationState =
    summary.status === "FAIL" && severity.critical > 0
      ? "fail"
      : summary.status === "FAIL"
        ? "warning"
        : summary.status === "PASS"
          ? "pass"
          : "idle";
  const recommendationCards = {
    pass: [
      ["PASS", "Product meets quality standards", "Archive inspection and continue batch release.", qualityScoreText],
    ],
    warning: [
      ["WARNING", "Requires secondary inspection", "Review highlighted areas before approving this item.", `${Math.round(confidence * 100)}%`],
    ],
    fail: [
      ["FAIL", "Critical defects detected", "Reject item or route to rework with supervisor approval.", `${Math.round(confidence * 100)}%`],
    ],
    idle: [
      ["READY", "Awaiting inspection", "Run a camera or upload inspection to generate AI guidance.", "--"],
    ],
  };

  if (!authToken) {
    return (
      <main className="app-shell login-shell">
        <section className="login-panel">
          <div className="brand-lockup">
            <div className="logo-mark">
              <Icon name="shield" />
            </div>
            <div>
              <span>QIS Manufacturing AI</span>
              <h1>Quality Inspection System</h1>
            </div>
          </div>

          <form className="login-card" onSubmit={handleLogin}>
            <div>
              <p>Secure Access</p>
              <h2>Operator Login</h2>
            </div>

            <label>
              Username
              <input
                autoComplete="username"
                onChange={(event) => setLoginForm((current) => ({ ...current, username: event.target.value }))}
                value={loginForm.username}
              />
            </label>

            <label>
              Password
              <input
                autoComplete="current-password"
                onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                type="password"
                value={loginForm.password}
              />
            </label>

            <button className="primary-btn" type="submit">
              Sign In
            </button>

            <span className={`system-state ${backendStatus === "online" ? "ready" : backendStatus}`}>
              <span />
              {backendMessage}
            </span>

            {loginError && <p className="error-banner">{loginError}</p>}
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="logo-mark">
            <Icon name="shield" />
          </div>
          <div>
            <span>QIS Manufacturing AI</span>
            <h1>Quality Inspection System</h1>
          </div>
        </div>

        <div className="nav-actions">
          <span className={`system-state ${appState}`}>
            <span />
            {appState}
          </span>
          <button className="icon-button" onClick={checkBackend} title="Refresh status" type="button">
            <Icon name="refresh" />
          </button>
          <button className="icon-button" title="Notifications" type="button">
            <Icon name="bell" />
          </button>
          <button className="profile-button" onClick={handleLogout} title="Logout" type="button">
            <Icon name="user" />
            <span>{user?.username || "QA"}</span>
          </button>
        </div>
      </header>

      <section className="kpi-grid" aria-label="Quality inspection KPIs">
        <KpiCard icon="gauge" label="Quality Score" tone="blue" trend="+4.8%" value={qualityScoreText} values={historyScores} />
        <KpiCard icon="alert" label="Total Defects" tone="red" trend={summary.total_defects ? "Review" : "Clear"} value={summary.total_defects} values={[2, 4, 3, 5, 2, 1, summary.total_defects]} />
        <KpiCard icon="activity" label="AI Confidence" tone="green" trend="+1.2%" value={`${Math.round(confidence * 100)}%`} values={[52, 58, 61, 64, 68, 72, Math.round(confidence * 100)]} />
        <KpiCard icon="clock" label="Processing Time" tone="amber" trend="Live" value={processingTime ? `${(processingTime / 1000).toFixed(2)}s` : "--"} values={[1.2, 1.1, 1.4, 1, 1.3, 1.1, processingTime ? processingTime / 1000 : 1.2]} />
      </section>

      <section className="workspace">
        <div className="workspace-panel intake-panel">
          <div className="panel-heading">
            <div>
              <p>Image Intake</p>
              <h2>Capture Source</h2>
            </div>
            <div className="source-tabs" aria-label="Image source">
              <button aria-pressed={activeSource === "upload"} className={activeSource === "upload" ? "active" : ""} onClick={() => handleSourceChange("upload")} type="button">
                Upload
              </button>
              <button aria-pressed={activeSource === "camera"} className={activeSource === "camera" ? "active" : ""} onClick={() => handleSourceChange("camera")} type="button">
                Camera
              </button>
            </div>
          </div>

          {activeSource === "upload" && (
            <>
              <label
                className={`drop-zone ${dragActive ? "dragging" : ""}`}
                htmlFor="inspection-file"
                onDragLeave={() => setDragActive(false)}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragActive(true);
                }}
                onDrop={handleDrop}
              >
                {previewUrl ? (
                  <img className="preview-image" src={previewUrl} alt="Selected inspection preview" />
                ) : (
                  <span className="drop-content">
                    <Icon name="upload" />
                    <strong>Upload inspection image</strong>
                    <small>PNG, JPG, JPEG, GIF, BMP</small>
                  </span>
                )}
              </label>
              <input id="inspection-file" ref={fileInputRef} className="hidden-input" type="file" accept="image/*" onChange={handleFileChange} />
            </>
          )}

          {activeSource === "camera" && (
            <div className="camera-stack">
              <div className={`camera-view ${cameraStatus}`}>
                <video ref={videoRef} className="camera-video" muted playsInline />
                {cameraStatus !== "live" && (
                  <div className="camera-placeholder">
                    <Icon name="camera" />
                    <strong>{cameraStatus === "starting" ? "Starting camera" : "Camera idle"}</strong>
                  </div>
                )}
              </div>
              <canvas ref={canvasRef} className="capture-canvas" aria-hidden="true" />
              <div className="button-row dense">
                {cameraStatus === "live" ? (
                  <button className="secondary-btn" onClick={stopCamera} type="button">
                    Stop
                  </button>
                ) : (
                  <button className="primary-btn" disabled={cameraStatus === "starting"} onClick={startCamera} type="button">
                    Start Camera
                  </button>
                )}
                <button className="secondary-btn" disabled={cameraStatus !== "live"} onClick={() => captureFrame(false)} type="button">
                  Capture
                </button>
                <button className="primary-btn" disabled={cameraStatus !== "live" || loading} onClick={() => captureFrame(true)} type="button">
                  Capture & Inspect
                </button>
              </div>
            </div>
          )}

          <div className="mode-row">
            <label>
              <span>Inspection Mode</span>
              <select value={inspectionMode} onChange={(event) => setInspectionMode(event.target.value)}>
                <option value="fabric">Fabric</option>
                <option value="garment">Garment</option>
                <option value="surface">Surface</option>
                <option value="custom">Custom</option>
              </select>
            </label>
            <label>
              <span>AI Confidence</span>
              <input max="1" min="0" onChange={(event) => setConfidence(Number(event.target.value))} step="0.05" type="range" value={confidence} />
            </label>
          </div>

          <div className="workflow-grid">
            <label>
              Operator
              <input
                onChange={(event) => setWorkflow((current) => ({ ...current, operator_name: event.target.value }))}
                placeholder="Operator name"
                value={workflow.operator_name}
              />
            </label>
            <label>
              Batch ID
              <input
                onChange={(event) => setWorkflow((current) => ({ ...current, batch_id: event.target.value }))}
                placeholder="Batch number"
                value={workflow.batch_id}
              />
            </label>
            <label>
              Fabric Type
              <input
                onChange={(event) => setWorkflow((current) => ({ ...current, fabric_type: event.target.value }))}
                placeholder="Cotton, denim, silk"
                value={workflow.fabric_type}
              />
            </label>
            <label>
              Line
              <input
                onChange={(event) => setWorkflow((current) => ({ ...current, production_line: event.target.value }))}
                value={workflow.production_line}
              />
            </label>
            <label>
              Shift
              <select
                onChange={(event) => setWorkflow((current) => ({ ...current, shift: event.target.value }))}
                value={workflow.shift}
              >
                <option value="A">Shift A</option>
                <option value="B">Shift B</option>
                <option value="C">Shift C</option>
              </select>
            </label>
          </div>

          {activeSource === "camera" && (
            <div className="live-controls">
              <label>
                <input 
                  checked={autoScan} 
                  disabled={cameraStatus !== "live"} 
                  onChange={(event) => {
                    setAutoScan(event.target.checked);
                    if (!event.target.checked) {
                      setCaptureCount(0);
                      setCountdownTimer(0);
                    } else {
                      setCountdownTimer(scanInterval);
                    }
                  }} 
                  type="checkbox" 
                />
                Live scan {autoScan && `(${captureCount} captures)`}
              </label>
              <label>
                Interval
                <input
                  max="15"
                  min="2"
                  onChange={(event) => setScanInterval(Math.min(15, Math.max(2, Number(event.target.value) || 2)))}
                  type="number"
                  value={scanInterval}
                />
                {autoScan && <span style={{ marginLeft: "10px", fontWeight: "bold", color: "#000000" }}>Next: {countdownTimer}s</span>}
              </label>
            </div>
          )}

          <dl className="metadata-grid">
            {fileMeta.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd title={value}>{value}</dd>
              </div>
            ))}
          </dl>

          <div className="button-row">
            <button className="primary-btn run-btn" disabled={loading || !selectedFile} onClick={() => inspectFile()} type="button">
              {loading ? "Processing" : "Run Inspection"}
            </button>
            <button className="secondary-btn" onClick={handleClear} type="button">
              Clear
            </button>
          </div>

          {error && <p className="error-banner">{error}</p>}
        </div>

        <div className="workspace-panel result-panel">
          <div className="panel-heading">
            <div>
              <p>Inspection Results</p>
              <h2>Annotated Viewer</h2>
            </div>
            <div className="viewer-tools">
              <button className="icon-button" onClick={() => setZoom((current) => Math.max(1, current - 0.2))} title="Zoom out" type="button">
                -
              </button>
              <button className="icon-button" onClick={() => setZoom((current) => Math.min(3, current + 0.2))} title="Zoom in" type="button">
                <Icon name="zoom" />
              </button>
              <button className="icon-button" onClick={() => setPan((current) => ({ ...current, y: current.y - 18 }))} title="Pan up" type="button">
                ^
              </button>
              <button className="icon-button" onClick={() => setPan((current) => ({ ...current, y: current.y + 18 }))} title="Pan down" type="button">
                v
              </button>
              <button className="secondary-btn" onClick={openFullscreen} type="button">
                Fullscreen
              </button>
            </div>
          </div>

          <div ref={resultViewerRef} className="annotated-viewer">
            {annotatedImageUrl ? (
              <img
                alt="Annotated inspection result"
                src={annotatedImageUrl}
                style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
              />
            ) : previewUrl ? (
              <img alt="Inspection source" src={previewUrl} style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }} />
            ) : (
              <div className="empty-state">
                <Icon name="image" />
                <strong>No inspection image</strong>
              </div>
            )}
            {loading && <div className="scan-overlay">AI inspection running</div>}
          </div>

          <div className="result-summary-row">
            <div>
              <span>Status</span>
              <strong className={String(summary.status || "ready").toLowerCase()}>{summary.status}</strong>
            </div>
            <div>
              <span>Inspection ID</span>
              <strong>{inspectionResult?.inspection_id || "--"}</strong>
            </div>
            <div>
              <span>Model</span>
              <strong>YOLOv8 Fabric</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="analytics-grid">
        <div className="analytics-panel">
          <div className="panel-heading compact-heading">
            <div>
              <p>Severity Overview</p>
              <h2>Defect Risk</h2>
            </div>
          </div>
          <div className="donut-layout">
            <div className="donut-chart" style={severityChart}>
              <span>{summary.total_defects}</span>
            </div>
            <div className="legend-list">
              <span><b className="critical-dot" />Critical {severity.critical}</span>
              <span><b className="warning-dot" />Medium {severity.medium}</span>
              <span><b className="success-dot" />Minor {severity.minor}</span>
            </div>
          </div>
        </div>

        <div className="analytics-panel">
          <div className="panel-heading compact-heading">
            <div>
              <p>Distribution</p>
              <h2>Defect Types</h2>
            </div>
          </div>
          <div className="bar-list">
            {Object.keys(defectBreakdown).length ? (
              Object.entries(defectBreakdown).map(([type, count]) => (
                <div key={type} className="bar-row">
                  <span>{type}</span>
                  <div><b style={{ width: `${Math.min(100, count * 18)}%` }} /></div>
                  <strong>{count}</strong>
                </div>
              ))
            ) : (
              <div className="empty-copy">No distribution data</div>
            )}
          </div>
        </div>

        <div className="analytics-panel">
          <div className="panel-heading compact-heading">
            <div>
              <p>Trend</p>
              <h2>Quality History</h2>
            </div>
          </div>
          <Sparkline tone="blue" values={historyScores} />
          <div className="batch-row">
            <span>Current {qualityScoreText}</span>
            <span>Previous {history[1]?.score ? `${history[1].score}%` : "--"}</span>
            <span>Batch A {history.length ? `${Math.round(history.reduce((sum, item) => sum + item.score, 0) / history.length)}%` : "--"}</span>
          </div>
        </div>

        <div className="analytics-panel recommendation-panel">
          <div className="panel-heading compact-heading">
            <div>
              <p>AI Recommendations</p>
              <h2>Decision Support</h2>
            </div>
          </div>
          {recommendationCards[recommendationState].map(([label, title, action, score]) => (
            <article className={`recommendation ${recommendationState}`} key={label}>
              <span>{label}</span>
              <strong>{title}</strong>
              <p>{action}</p>
              <small>Confidence {score}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="data-section">
        <div className="table-toolbar">
          <div>
            <p>Detection Table</p>
            <h2>Defect Records</h2>
          </div>
          <div className="table-actions">
            <label className="search-box">
              <Icon name="search" />
              <input onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search defects" value={searchTerm} />
            </label>
            <select onChange={(event) => setSeverityFilter(event.target.value)} value={severityFilter}>
              <option value="all">All severity</option>
              <option value="high">Critical</option>
              <option value="medium">Medium</option>
              <option value="low">Minor</option>
            </select>
            <button className="secondary-btn" disabled={!detections.length} onClick={exportCsv} type="button">
              <Icon name="download" />
              CSV
            </button>
            <button className="secondary-btn" disabled={!inspectionResult} onClick={exportPdf} type="button">
              PDF
            </button>
          </div>
        </div>

        <div className="detection-table" role="table" aria-label="Defect records">
          <div className="table-row table-head" role="row">
            <button onClick={() => toggleSort("type")} role="columnheader" type="button">Defect Type</button>
            <button onClick={() => toggleSort("severity")} role="columnheader" type="button">Severity</button>
            <button onClick={() => toggleSort("confidence")} role="columnheader" type="button">Confidence</button>
            <span role="columnheader">Coordinates</span>
            <span role="columnheader">Timestamp</span>
            <span role="columnheader">Status</span>
          </div>
          {filteredDetections.length ? (
            filteredDetections.map((detection, index) => (
              <div className="table-row" role="row" key={`${detection.type}-${index}`}>
                <span role="cell">{detection.type}</span>
                <span className={`severity-pill ${detection.severity}`} role="cell">{detection.severity}</span>
                <span role="cell">{Math.round(detection.confidence * 100)}%</span>
                <span role="cell">{detection.bbox?.join(", ") || "--"}</span>
                <span role="cell">{inspectionResult?.inspection_id || "--"}</span>
                <span role="cell">{detection.severity === "high" ? "Reject" : "Review"}</span>
              </div>
            ))
          ) : (
            <div className="table-empty">No detection records</div>
          )}
        </div>
      </section>

      <footer className="footer-grid">
        <section>
          <p>Recent Inspections</p>
          <div className="timeline">
            {(history.length ? history : [{ id: "No inspections yet", time: "--", status: "READY", score: 0 }]).map((item) => (
              <div key={item.id}>
                <span>{item.time}</span>
                <strong>{item.status}</strong>
                <small>{item.id}</small>
              </div>
            ))}
          </div>
        </section>
        <section>
          <p>System Health</p>
          <strong>{backendStatus}</strong>
          <span>{backendMessage}</span>
        </section>
        <section>
          <p>Model Version</p>
          <strong>{backendVersion}</strong>
          <span>YOLOv8 defect detector</span>
        </section>
        <section>
          <p>Detection Performance</p>
          <strong>{qualityScoreText}</strong>
          <span>{processingTime ? `${processingTime} ms latency` : "Waiting for inspection"}</span>
        </section>
      </footer>
    </main>
  );
}

export default App;
