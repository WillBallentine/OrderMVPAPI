import { useState, useEffect, useRef } from "react";
import api from "../api";

const EMPTY = { patient_first_name: "", patient_last_name: "", patient_dob: "" };

const confidenceBadge = {
  high: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-orange-100 text-orange-700",
  none: "bg-red-100 text-red-700",
};

// ─── Single upload panel ──────────────────────────────────────────────────────

function SinglePanel({ onClose, onSaved }) {
  const inputRef = useRef();
  const [file, setFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [extracted, setExtracted] = useState(false);
  const [confidence, setConfidence] = useState(null);
  const [extractError, setExtractError] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const inputClass = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white";

  async function handleExtract(e) {
    e.preventDefault();
    if (!file) return;
    setExtractError("");
    setExtracting(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const { data } = await api.post("/documents/extract", body);
      const ex = data.extracted;
      setForm({
        patient_first_name: ex.patient_first_name || "",
        patient_last_name: ex.patient_last_name || "",
        patient_dob: ex.patient_dob || "",
      });
      setConfidence(ex.extraction_confidence);
      setExtracted(true);
    } catch (err) {
      setExtractError(err.response?.data?.detail || "Extraction failed");
    } finally {
      setExtracting(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaveError("");
    setSaving(true);
    try {
      await api.post("/orders/", form);
      onSaved();
    } catch (err) {
      setSaveError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Save failed");
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* File picker */}
      {!extracted && (
        <form onSubmit={handleExtract} className="flex flex-col gap-3">
          <div
            className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
              file ? "border-blue-400 bg-blue-50" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"
            }`}
            onClick={() => inputRef.current.click()}
          >
            <input ref={inputRef} type="file" accept="application/pdf" className="hidden"
              onChange={(e) => { setFile(e.target.files[0]); setExtractError(""); }} />
            <svg className={`w-6 h-6 mx-auto mb-1.5 ${file ? "text-blue-500" : "text-slate-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            {file
              ? <p className="text-xs font-medium text-blue-700 truncate">{file.name}</p>
              : <p className="text-xs text-slate-500">Click to select a PDF</p>
            }
          </div>
          {extractError && <p className="text-xs text-red-500">{extractError}</p>}
          <button type="submit" disabled={!file || extracting}
            className="bg-blue-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {extracting
              ? <span className="flex items-center justify-center gap-1.5">
                  <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Extracting…
                </span>
              : "Extract Patient Info"
            }
          </button>
          {extracting && <p className="text-xs text-slate-400 text-center">Scanned documents may take a moment</p>}
        </form>
      )}

      {/* Extracted form */}
      {extracted && (
        <form onSubmit={handleSave} className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-slate-600">Review extracted data</p>
            {confidence && (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${confidenceBadge[confidence] || "bg-slate-100 text-slate-600"}`}>
                {confidence}
              </span>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">First Name</label>
            <input className={inputClass} value={form.patient_first_name}
              onChange={(e) => setForm({ ...form, patient_first_name: e.target.value })} required />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Last Name</label>
            <input className={inputClass} value={form.patient_last_name}
              onChange={(e) => setForm({ ...form, patient_last_name: e.target.value })} required />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Date of Birth</label>
            <input className={inputClass} value={form.patient_dob}
              onChange={(e) => setForm({ ...form, patient_dob: e.target.value })} required />
          </div>
          {saveError && <p className="text-xs text-red-500">{saveError}</p>}
          <button type="submit" disabled={saving}
            className="bg-green-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors mt-1">
            {saving ? "Saving…" : "Save as Order"}
          </button>
          <button type="button" onClick={() => { setExtracted(false); setFile(null); }}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
            ← Upload a different file
          </button>
        </form>
      )}
    </div>
  );
}

// ─── Batch upload panel ───────────────────────────────────────────────────────

function BatchPanel({ onClose, onSaved }) {
  const inputRef = useRef();
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]); // { filename, form, confidence, status: idle|extracting|done|error, error }
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState(false);

  function handleFileChange(e) {
    const added = Array.from(e.target.files);
    e.target.value = "";
    setFiles((prevFiles) => {
      const existing = new Set(prevFiles.map((f) => f.name));
      const fresh = added.filter((f) => !existing.has(f.name));
      return [...prevFiles, ...fresh].slice(0, 20);
    });
    setResults((prevResults) => {
      const existing = new Set(prevResults.map((r) => r.filename));
      const fresh = added.filter((f) => !existing.has(f.name));
      return [
        ...prevResults,
        ...fresh.map((f) => ({ filename: f.name, form: EMPTY, confidence: null, status: "idle", error: "" })),
      ].slice(0, 20);
    });
    setSaved(false);
    setSaveError("");
  }

  async function handleExtractAll() {
    if (!files.length) return;
    setExtracting(true);
    setSaveError("");

    await Promise.all(
      files.map(async (file, i) => {
        setResults((prev) => prev.map((r, idx) => idx === i ? { ...r, status: "extracting" } : r));
        try {
          const body = new FormData();
          body.append("file", file);
          const { data } = await api.post("/documents/extract", body);
          const ex = data.extracted;
          setResults((prev) => prev.map((r, idx) => idx === i ? {
            ...r,
            status: "done",
            confidence: ex.extraction_confidence,
            form: {
              patient_first_name: ex.patient_first_name || "",
              patient_last_name: ex.patient_last_name || "",
              patient_dob: ex.patient_dob || "",
            },
          } : r));
        } catch (err) {
          setResults((prev) => prev.map((r, idx) => idx === i ? {
            ...r, status: "error", error: err.response?.data?.detail || "Extraction failed",
          } : r));
        }
      })
    );

    setExtracting(false);
  }

  function updateField(i, field, value) {
    setResults((prev) => prev.map((r, idx) => idx === i ? { ...r, form: { ...r.form, [field]: value } } : r));
  }

  function removeRow(i) {
    setResults((prev) => prev.filter((_, idx) => idx !== i));
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleSaveAll() {
    const valid = results.filter((r) => r.status === "done");
    if (!valid.length) return;
    setSaving(true);
    setSaveError("");
    try {
      await api.post("/orders/batch", valid.map((r) => r.form));
      setSaved(true);
      onSaved();
    } catch (err) {
      setSaveError(err.response?.data?.detail || "Batch save failed");
      setSaving(false);
    }
  }

  const allDone = results.length > 0 && results.every((r) => r.status === "done" || r.status === "error");
  const readyCount = results.filter((r) => r.status === "done").length;
  const inputClass = "w-full border border-slate-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white";

  return (
    <div className="flex flex-col gap-4">
      {/* File picker */}
      <div className="flex flex-col gap-2">
        <input ref={inputRef} type="file" accept="application/pdf" multiple className="hidden" onChange={handleFileChange} />
        <div
          className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
            files.length ? "border-blue-400 bg-blue-50" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"
          }`}
          onClick={() => inputRef.current.click()}
        >
          <svg className={`w-6 h-6 mx-auto mb-1.5 ${files.length ? "text-blue-500" : "text-slate-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          {files.length
            ? <p className="text-xs font-medium text-blue-700">{files.length} PDF{files.length > 1 ? "s" : ""} queued</p>
            : <>
                <p className="text-xs font-medium text-slate-600">Click to select PDFs</p>
                <p className="text-xs text-slate-400 mt-0.5">Up to 20 files</p>
              </>
          }
        </div>
        {files.length > 0 && files.length < 20 && (
          <button type="button" onClick={() => inputRef.current.click()}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors text-center">
            + Add more PDFs
          </button>
        )}
      </div>

      {/* Extract button */}
      {files.length > 0 && !allDone && (
        <button onClick={handleExtractAll} disabled={extracting}
          className="bg-blue-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors">
          {extracting
            ? <span className="flex items-center justify-center gap-1.5">
                <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Extracting {results.filter(r => r.status === "done" || r.status === "error").length}/{results.length}…
              </span>
            : `Extract All (${files.length})`
          }
        </button>
      )}

      {/* Per-file results */}
      {results.length > 0 && (
        <div className="flex flex-col gap-3">
          {results.map((r, i) => (
            <div key={i} className={`rounded-xl border p-3 ${
              r.status === "error" ? "border-red-200 bg-red-50" :
              r.status === "done" ? "border-slate-200 bg-white" :
              r.status === "extracting" ? "border-blue-200 bg-blue-50" :
              "border-slate-200 bg-slate-50"
            }`}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-600 truncate max-w-[160px]">{r.filename}</p>
                <div className="flex items-center gap-2 shrink-0">
                  {r.status === "extracting" && (
                    <svg className="animate-spin w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                  )}
                  {r.status === "done" && r.confidence && (
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full capitalize ${confidenceBadge[r.confidence]}`}>
                      {r.confidence}
                    </span>
                  )}
                  {r.status === "error" && <span className="text-xs text-red-500">Failed</span>}
                  <button onClick={() => removeRow(i)} className="text-slate-300 hover:text-slate-500 transition-colors">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {r.status === "done" && (
                <div className="flex flex-col gap-1.5">
                  <input className={inputClass} placeholder="First name" value={r.form.patient_first_name}
                    onChange={(e) => updateField(i, "patient_first_name", e.target.value)} />
                  <input className={inputClass} placeholder="Last name" value={r.form.patient_last_name}
                    onChange={(e) => updateField(i, "patient_last_name", e.target.value)} />
                  <input className={inputClass} placeholder="Date of birth" value={r.form.patient_dob}
                    onChange={(e) => updateField(i, "patient_dob", e.target.value)} />
                </div>
              )}
              {r.status === "error" && <p className="text-xs text-red-500">{r.error}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Save all */}
      {allDone && readyCount > 0 && (
        <div className="flex flex-col gap-2">
          {saveError && <p className="text-xs text-red-500">{saveError}</p>}
          <button onClick={handleSaveAll} disabled={saving}
            className="bg-green-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors">
            {saving ? "Saving…" : `Save ${readyCount} Order${readyCount > 1 ? "s" : ""}`}
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Main Orders page ─────────────────────────────────────────────────────────

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(true);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState("single"); // "single" | "batch"
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  useEffect(() => { fetchOrders(); }, []);

  async function fetchOrders() {
    try {
      const { data } = await api.get("/orders/");
      setOrders(data);
    } finally {
      setLoadingOrders(false);
    }
  }

  function openUpload(mode = "single") {
    setEditing(null);
    setPanelMode(mode);
    setPanelOpen(true);
  }

  function closePanel() {
    setPanelOpen(false);
    setEditing(null);
    setEditError("");
  }

  function handleSaved() {
    closePanel();
    fetchOrders();
  }

  function startEdit(order) {
    setPanelOpen(true);
    setEditing(order.id);
    setEditForm({
      patient_first_name: order.patient_first_name,
      patient_last_name: order.patient_last_name,
      patient_dob: order.patient_dob,
    });
    setEditError("");
  }

  async function handleEditSave(e) {
    e.preventDefault();
    setEditError("");
    setEditSaving(true);
    try {
      await api.put(`/orders/${editing}`, editForm);
      closePanel();
      fetchOrders();
    } catch (err) {
      setEditError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Save failed");
    } finally {
      setEditSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this order?")) return;
    await api.delete(`/orders/${id}`);
    fetchOrders();
  }

  const inputClass = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white";

  return (
    <div className="flex gap-6 items-start">

      {/* Left panel */}
      {panelOpen && (
        <div className="w-80 shrink-0">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5">

            {/* Panel header */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-800">
                {editing ? "Edit Order" : "Upload PDF"}
              </h2>
              <button onClick={closePanel} className="text-slate-400 hover:text-slate-600 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Mode tabs — only when not editing */}
            {!editing && (
              <div className="flex rounded-lg bg-slate-100 p-1 mb-4">
                {["single", "batch"].map((mode) => (
                  <button key={mode} onClick={() => setPanelMode(mode)}
                    className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors capitalize ${
                      panelMode === mode ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
                    }`}>
                    {mode === "single" ? "Single" : "Batch"}
                  </button>
                ))}
              </div>
            )}

            {/* Content */}
            {editing ? (
              <form onSubmit={handleEditSave} className="flex flex-col gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">First Name</label>
                  <input className={inputClass} value={editForm.patient_first_name}
                    onChange={(e) => setEditForm({ ...editForm, patient_first_name: e.target.value })} required />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Last Name</label>
                  <input className={inputClass} value={editForm.patient_last_name}
                    onChange={(e) => setEditForm({ ...editForm, patient_last_name: e.target.value })} required />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Date of Birth</label>
                  <input className={inputClass} value={editForm.patient_dob}
                    onChange={(e) => setEditForm({ ...editForm, patient_dob: e.target.value })} required />
                </div>
                {editError && <p className="text-xs text-red-500">{editError}</p>}
                <button type="submit" disabled={editSaving}
                  className="bg-blue-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors mt-1">
                  {editSaving ? "Saving…" : "Save Changes"}
                </button>
              </form>
            ) : panelMode === "single" ? (
              <SinglePanel onClose={closePanel} onSaved={handleSaved} />
            ) : (
              <BatchPanel onClose={closePanel} onSaved={handleSaved} />
            )}
          </div>
        </div>
      )}

      {/* Orders table */}
      <div className="flex-1 min-w-0 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-slate-800">Orders</h1>
            <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">
              {orders.length} total
            </span>
          </div>
          {!panelOpen && (
            <div className="flex gap-2">
              <button onClick={() => openUpload("single")}
                className="flex items-center gap-1.5 border border-slate-300 text-slate-700 rounded-lg px-3 py-2 text-sm font-medium hover:bg-slate-50 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Upload PDF
              </button>
              <button onClick={() => openUpload("batch")}
                className="flex items-center gap-1.5 bg-blue-600 text-white rounded-lg px-3 py-2 text-sm font-semibold hover:bg-blue-700 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Batch Upload
              </button>
            </div>
          )}
        </div>

        {loadingOrders ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm text-slate-400">Loading orders…</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <svg className="w-10 h-10 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm font-medium text-slate-500">No orders yet</p>
            <p className="text-xs text-slate-400 mt-1">Upload a PDF to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {["ID", "First Name", "Last Name", "Date of Birth", "Created", ""].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.map((o) => (
                  <tr key={o.id} className={`hover:bg-slate-50 transition-colors ${editing === o.id ? "bg-blue-50" : ""}`}>
                    <td className="px-6 py-4 text-slate-400 font-mono text-xs">{o.id}</td>
                    <td className="px-6 py-4 text-slate-800 font-medium">{o.patient_first_name}</td>
                    <td className="px-6 py-4 text-slate-800 font-medium">{o.patient_last_name}</td>
                    <td className="px-6 py-4 text-slate-600">{o.patient_dob}</td>
                    <td className="px-6 py-4 text-slate-400 text-xs">{new Date(o.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-3 justify-end">
                        <button onClick={() => startEdit(o)}
                          className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors">Edit</button>
                        <button onClick={() => handleDelete(o.id)}
                          className="text-xs font-medium text-red-500 hover:text-red-700 transition-colors">Delete</button>
                      </div>
                    </td>
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
