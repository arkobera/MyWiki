import { useRef, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const SUPPORTED_TYPES = [
  ".pdf",
  ".txt",
  ".md",
  ".json",
  ".csv",
  ".doc",
  ".docx",
];

function formatBytes(bytes) {
  if (!bytes) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export default function UploadBox({ onUpload }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const selectFile = (nextFile) => {
    setFile(nextFile || null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;

    setIsUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        data = {};
      }

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Upload failed.");
      }

      const pipelineStatus = data.pipeline?.status || null;
      const pipelineError = data.pipeline?.error || "";
      const embeddingGenerated = pipelineStatus === "indexed";
      const indexingSummary =
        pipelineStatus === "indexed"
          ? `Embeddings generated successfully for ${data.pipeline?.chunks ?? 0} chunk${data.pipeline?.chunks === 1 ? "" : "s"}.`
          : pipelineStatus === "failed"
            ? `Embedding generation failed: ${pipelineError || "Unknown pipeline error."}`
            : "Embedding generation was not run for this file type.";

      onUpload({
        fileName: file.name,
        filename: data.filename || file.name,
        preview: data.preview,
        status: data.message || data.status || `${file.name} uploaded successfully.`,
        embeddingStatus: {
          generated: embeddingGenerated,
          failed: pipelineStatus === "failed",
          skipped: pipelineStatus === null,
          message: indexingSummary,
          chunks: data.pipeline?.chunks ?? null,
          documents: data.pipeline?.documents ?? null,
          vectorDirectory: data.pipeline?.vector_directory ?? null,
        },
        isError: pipelineStatus === "failed",
      });
    } catch (uploadError) {
      const message =
        uploadError instanceof Error
          ? uploadError.message
          : "Could not upload the selected file.";
      setError(message);
      onUpload({
        fileName: file.name,
        preview: "",
        status: `Upload failed: ${message}`,
        embeddingStatus: {
          generated: false,
          failed: true,
          skipped: false,
          message: `Embedding generation failed because the upload did not complete: ${message}`,
          chunks: null,
          documents: null,
          vectorDirectory: null,
        },
        isError: true,
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.22),_transparent_36%),linear-gradient(160deg,_rgba(15,23,42,0.96),_rgba(3,7,18,0.92))] p-5 text-white shadow-[0_24px_80px_rgba(2,6,23,0.55)]">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(130deg,transparent,rgba(148,163,184,0.08),transparent)]" />

      <div className="relative flex h-full flex-col gap-5">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/80">
            Ingestion
          </p>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-white">
              Upload box
            </h2>
            <p className="mt-2 max-w-md text-sm leading-6 text-slate-300">
              Drag a document into the drop zone or browse from your device. Uploaded files stay listed below in the documents panel.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            selectFile(event.dataTransfer.files?.[0] || null);
          }}
          className={`group flex min-h-48 w-full flex-col items-center justify-center rounded-[24px] border border-dashed px-6 py-8 text-center transition ${
            isDragging
              ? "border-cyan-300 bg-cyan-300/10 shadow-[0_0_0_1px_rgba(103,232,249,0.45)]"
              : "border-slate-600/80 bg-slate-950/40 hover:border-slate-400 hover:bg-slate-900/70"
          }`}
        >
          <div className="mb-4 rounded-full border border-white/10 bg-white/5 p-4 text-cyan-200">
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className="h-8 w-8"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 16V4" />
              <path d="m7 9 5-5 5 5" />
              <path d="M4 16.5v1A2.5 2.5 0 0 0 6.5 20h11a2.5 2.5 0 0 0 2.5-2.5v-1" />
            </svg>
          </div>

          <p className="text-lg font-medium text-white">
            {file ? file.name : "Drop file here"}
          </p>
          <p className="mt-2 text-sm text-slate-400">
            {file
              ? `${formatBytes(file.size)} selected`
              : "PDF, TXT, Markdown, JSON, CSV, DOC, DOCX"}
          </p>
          <p className="mt-4 text-sm font-medium text-cyan-300 transition group-hover:text-cyan-200">
            Browse files
          </p>
        </button>

        <input
          ref={inputRef}
          type="file"
          accept={SUPPORTED_TYPES.join(",")}
          className="hidden"
          onChange={(event) => selectFile(event.target.files?.[0] || null)}
        />

        <div className="rounded-[22px] border border-white/8 bg-black/20 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-slate-200">Selected file</p>
              <p className="mt-1 text-sm text-slate-400">
                {file ? `${file.name} • ${formatBytes(file.size)}` : "No file chosen yet"}
              </p>
            </div>

            {file ? (
              <button
                type="button"
                onClick={() => selectFile(null)}
                className="rounded-full border border-white/10 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:text-white"
              >
                Clear
              </button>
            ) : null}
          </div>

          {error ? (
            <p className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
              {error}
            </p>
          ) : (
            <p className="mt-3 text-sm text-slate-500">
              Supported: {SUPPORTED_TYPES.join(", ")}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="inline-flex items-center justify-center rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        >
          {isUploading ? "Uploading to backend..." : "Upload document"}
        </button>
      </div>
    </section>
  );
}
