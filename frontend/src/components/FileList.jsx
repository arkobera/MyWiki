export default function FileList({ files }) {
  return (
    <section className="flex min-h-[260px] flex-1 flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.96),_rgba(2,6,23,0.94))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/75">
          Documents
        </p>
        <h3 className="mt-2 text-xl font-semibold text-white">All docs</h3>
        <p className="mt-1 text-sm text-slate-400">
          Uploaded files remain visible here during the session.
        </p>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {files.length === 0 ? (
          <div className="flex h-full min-h-[140px] items-center justify-center rounded-[22px] border border-dashed border-slate-700 bg-slate-950/40 px-4 text-center text-sm text-slate-400">
            No documents yet
          </div>
        ) : (
          <div className="space-y-3">
            {files.map((file, index) => (
              <div
                key={`${file}-${index}`}
                className="rounded-[20px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-200"
              >
                {file}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
