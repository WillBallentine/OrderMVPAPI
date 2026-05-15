import { useState, useEffect } from "react";
import api from "../api";

const statusColor = (code) => {
  if (code < 300) return "bg-green-100 text-green-700";
  if (code < 400) return "bg-blue-100 text-blue-700";
  if (code < 500) return "bg-yellow-100 text-yellow-700";
  return "bg-red-100 text-red-700";
};

export default function ActivityLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  function fetchLogs() {
    setLoading(true);
    api.get("/activity-logs/").then(({ data }) => setLogs(data)).finally(() => setLoading(false));
  }

  useEffect(() => { fetchLogs(); }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Activity Log</h1>
          <p className="text-sm text-slate-500 mt-0.5">All API requests recorded in real time</p>
        </div>
        <button onClick={fetchLogs}
          className="flex items-center gap-2 border border-slate-300 text-slate-600 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm text-slate-400">Loading…</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm text-slate-400">No activity yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {["Time", "Action", "Resource", "Method", "Status", "Duration"].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3.5 text-slate-400 text-xs whitespace-nowrap font-mono">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-3.5 text-slate-700 font-medium">{log.action}</td>
                    <td className="px-6 py-3.5 text-slate-500 text-xs">
                      {log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ""}
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="text-xs font-mono font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                        {log.method}
                      </span>
                    </td>
                    <td className="px-6 py-3.5">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusColor(log.status_code)}`}>
                        {log.status_code}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-400 text-xs">{log.duration_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
