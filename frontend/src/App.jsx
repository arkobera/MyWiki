import { useState } from "react";
import UploadBox from "./components/UploadBox";
import FileViewer from "./components/FileViewer";
import StatusBar from "./components/StatusBar";

export default function App() {
  const [content, setContent] = useState("");
  const [status, setStatus] = useState("Waiting for a document upload.");
  const [statusTone, setStatusTone] = useState("idle");

  const handleUpload = (data) => {
    setContent(
      data.preview ||
        (data.isError
          ? "The upload did not complete. Check the status bar for details."
          : `Upload complete for ${data.fileName}.`)
    );
    setStatus(data.status || "Upload finished.");
    setStatusTone(data.isError ? "error" : "success");
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#020617_0%,_#0f172a_48%,_#111827_100%)] px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl flex-col gap-4">
        <header className="rounded-[28px] border border-white/10 bg-white/[0.03] px-6 py-5 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-300/75">
            MyWiki
          </p>
          <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Source ingestion workspace
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                Upload raw material, inspect the returned preview, and keep the
                ingestion state visible while the backend pipeline comes online.
              </p>
            </div>
            <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-sm text-cyan-100">
              API target:{" "}
              <span className="font-medium">
                {import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}
              </span>
            </div>
          </div>
        </header>

        <main className="grid flex-1 gap-4 lg:grid-cols-[minmax(320px,420px)_minmax(0,1fr)]">
          <UploadBox onUpload={handleUpload} />
          <FileViewer content={content} />
        </main>

        <StatusBar status={status} tone={statusTone} />
      </div>
    </div>
  );
}
