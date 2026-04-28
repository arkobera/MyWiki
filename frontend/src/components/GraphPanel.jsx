export default function GraphPanel() {
  return (
    <section className="flex h-full min-h-[420px] flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(2,6,23,0.96))] shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
      <div className="border-b border-white/8 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-violet-300/75">
          Graph
        </p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
          Knowledge graph
        </h2>
      </div>

      <div className="flex flex-1 items-center justify-center px-6 py-8 text-center text-xl font-medium text-slate-400">
        Coming soon
      </div>
    </section>
  );
}
