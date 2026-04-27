export default function FileViewer({ content }) {
  return (
    <section className="flex min-h-[420px] flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(2,6,23,0.96))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/75">
          Preview
        </p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
          Uploaded content
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Successful uploads can render returned text or metadata here for a quick
          verification pass.
        </p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <pre className="min-h-full rounded-[22px] border border-emerald-400/10 bg-black/30 p-5 font-mono text-sm leading-7 whitespace-pre-wrap text-emerald-200">
          {content || "No file loaded yet. Upload a document to inspect the response preview."}
        </pre>
      </div>
    </section>
  );
}
