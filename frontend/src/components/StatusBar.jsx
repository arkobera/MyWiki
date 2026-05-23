const toneClasses = {
  idle: "border-slate-700/80 bg-slate-900/70 text-slate-300",
  success: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100",
  error: "border-rose-400/20 bg-rose-500/10 text-rose-100",
};

const embeddingToneClasses = {
  success: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100",
  failed: "border-rose-400/20 bg-rose-500/10 text-rose-100",
  skipped: "border-slate-700/80 bg-slate-900/70 text-slate-300",
};

export default function StatusBar({ status, tone = "idle", embeddingStatus }) {
  const embeddingTone = embeddingStatus?.failed
    ? "failed"
    : embeddingStatus?.generated
      ? "success"
      : "skipped";

  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <div
        className={`rounded-[22px] border px-4 py-3 text-sm shadow-[0_12px_40px_rgba(2,6,23,0.35)] ${toneClasses[tone] || toneClasses.idle}`}
      >
        <span className="font-medium">Status:</span> {status}
      </div>

      <div
        className={`rounded-[22px] border px-4 py-3 text-sm shadow-[0_12px_40px_rgba(2,6,23,0.35)] ${embeddingToneClasses[embeddingTone] || embeddingToneClasses.skipped}`}
      >
        <div>
          <span className="font-medium">Embeddings:</span> {embeddingStatus?.message}
        </div>
        {embeddingStatus?.generated ? (
          <div className="mt-1 text-xs opacity-80">
            {embeddingStatus.documents} document(s) split into {embeddingStatus.chunks} chunk(s)
            {embeddingStatus.vectorDirectory ? ` in ${embeddingStatus.vectorDirectory}` : ""}
          </div>
        ) : null}
      </div>
    </div>
  );
}
