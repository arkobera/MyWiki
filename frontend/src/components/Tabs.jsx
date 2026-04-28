export default function Tabs({ activeTab, setActiveTab }) {
  return (
    <div className="flex bg-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setActiveTab("graphify")}
        className={`flex-1 p-3 ${
          activeTab === "graphify" ? "bg-gray-700 text-white" : "text-gray-400"
        }`}
      >
        Graphify
      </button>

      <button
        onClick={() => setActiveTab("chat")}
        className={`flex-1 p-3 ${
          activeTab === "chat" ? "bg-gray-700 text-white" : "text-gray-400"
        }`}
      >
        Chat
      </button>
    </div>
  );
}