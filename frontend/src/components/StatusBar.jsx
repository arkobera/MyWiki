const toneClasses = {
  idle: "border-slate-700/80 bg-slate-900/70 text-slate-300",
  success: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100",
  error: "border-rose-400/20 bg-rose-500/10 text-rose-100",
};

export default function StatusBar({ status, tone = "idle" }) {
  return (
    <div
      className={`rounded-[22px] border px-4 py-3 text-sm shadow-[0_12px_40px_rgba(2,6,23,0.35)] ${toneClasses[tone] || toneClasses.idle}`}
    >
      <span className="font-medium">Status:</span> {status}
    </div>
  );
}
