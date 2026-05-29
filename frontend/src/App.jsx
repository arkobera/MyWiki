import { useEffect, useState } from "react";
import UploadBox from "./components/UploadBox";
import StatusBar from "./components/StatusBar";
import FileList from "./components/FileList";
import GraphPanel from "./components/GraphPanel";
import Chat from "./pages/Chat";

const FILE_STORAGE_KEY = "mywiki-uploaded-files";
const TAB_STORAGE_KEY = "mywiki-active-tab";
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window === "undefined") {
      return "graphify";
    }

    return window.localStorage.getItem(TAB_STORAGE_KEY) || "graphify";
  });

  const [content, setContent] = useState("");
  const [status, setStatus] = useState("Waiting for a document upload.");
  const [statusTone, setStatusTone] = useState("idle");
  const [embeddingStatus, setEmbeddingStatus] = useState({
    generated: false,
    failed: false,
    skipped: true,
    message: "Embeddings will be generated for PDF uploads.",
    chunks: null,
    documents: null,
    vectorDirectory: null,
  });
  const [files, setFiles] = useState(() => {
    if (typeof window === "undefined") {
      return [];
    }

    try {
      const storedFiles = window.localStorage.getItem(FILE_STORAGE_KEY);
      return storedFiles ? JSON.parse(storedFiles) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    window.localStorage.setItem(FILE_STORAGE_KEY, JSON.stringify(files));
  }, [files]);

  useEffect(() => {
    window.localStorage.setItem(TAB_STORAGE_KEY, activeTab);
  }, [activeTab]);

  useEffect(() => {
    let ignore = false;

    const loadFiles = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/files`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Could not load existing files.");
        }

        if (!ignore && Array.isArray(data.files)) {
          setFiles(data.files);
          setStatus(
            data.files.length > 0
              ? `Loaded ${data.files.length} existing file${data.files.length === 1 ? "" : "s"} from raw/.`
              : "No existing files found in raw/."
          );
          setStatusTone("idle");
        }
      } catch {
        if (!ignore) {
          setStatus("Using saved session data. Backend file list could not be loaded.");
          setStatusTone("idle");
        }
      }
    };

    loadFiles();

    return () => {
      ignore = true;
    };
  }, []);

  const handleUpload = (data) => {
    setContent(
      data.preview ||
        (data.isError
          ? "The upload did not complete. Check the status bar for details."
          : `Upload complete for ${data.filename || data.fileName}.`)
    );

    setStatus(data.status || "Upload finished.");
    setStatusTone(data.isError ? "error" : "success");
    setEmbeddingStatus(
      data.embeddingStatus || {
        generated: false,
        failed: false,
        skipped: true,
        message: "Embedding status unavailable.",
        chunks: null,
        documents: null,
        vectorDirectory: null,
      }
    );

    const uploadedName = data.filename || data.fileName;

    if (!data.isError && uploadedName) {
      setFiles((prev) =>
        prev.includes(uploadedName) ? prev : [...prev, uploadedName]
      );
    }
  };

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.14),_transparent_28%),linear-gradient(180deg,_#020617_0%,_#0f172a_52%,_#111827_100%)] px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="flex min-h-[calc(100vh-3rem)] w-full flex-col gap-4">
        <section className="flex w-full flex-1 min-h-0 flex-col overflow-hidden rounded-[32px] border border-white/10 bg-slate-950/60 shadow-[0_30px_120px_rgba(2,6,23,0.65)] backdrop-blur">
          <header className="border-b border-white/10 px-5 py-5 sm:px-6">
            <div className="rounded-[24px] border border-white/10 bg-white/[0.03] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-300/70">
                My Wiki
              </p>
              <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                    Document workspace
                  </h1>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                    Upload files on the left and keep your graph area ready for the next phase.
                  </p>
                </div>

                <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-sm text-cyan-100">
                  API:{" "}
                  <span className="font-medium">
                    {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}
                  </span>
                </div>
              </div>
            </div>
          </header>

          <div className="border-b border-white/10 px-5 py-4 sm:px-6">
            <div className="grid grid-cols-2 overflow-hidden rounded-[20px] border border-white/10 bg-slate-900/80">
              <button
                onClick={() => setActiveTab("graphify")}
                className={`px-4 py-3 text-left text-base font-medium transition ${
                  activeTab === "graphify"
                    ? "bg-white/8 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                Graphify
              </button>

              <button
                onClick={() => setActiveTab("chat")}
                className={`border-l border-white/10 px-4 py-3 text-left text-base font-medium transition ${
                  activeTab === "chat"
                    ? "bg-white/8 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                Chat
              </button>
            </div>
          </div>

          <main className="flex flex-1 min-h-0 flex-col px-5 py-5 sm:px-6 sm:py-6">
          {activeTab === "graphify" ? (
            <div className="grid min-h-0 flex-1 gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
              <div className="flex min-h-0 flex-col gap-5">
                <UploadBox onUpload={handleUpload} />
                <FileList files={files} />
              </div>

              <div className="min-h-0 w-full min-w-0 lg:min-h-0">
                <GraphPanel refreshKey={files.join("|")} />
              </div>
            </div>
          ) : (
            <Chat />
          )}
          </main>
        </section>

        <StatusBar
          status={status}
          tone={statusTone}
          embeddingStatus={embeddingStatus}
        />
      </div>
    </div>
  );
}
