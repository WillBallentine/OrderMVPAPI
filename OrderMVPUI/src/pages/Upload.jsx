import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

const EMPTY = { patient_first_name: "", patient_last_name: "", patient_dob: "" };

const confidenceBadge = {
  high: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-orange-100 text-orange-700",
  none: "bg-red-100 text-red-700",
};

export default function Upload() {
  const navigate = useNavigate();
  const inputRef = useRef();
  const [file, setFile] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [confidence, setConfidence] = useState(null);
  const [extracted, setExtracted] = useState(false);
  const [extractError, setExtractError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleExtract(e) {
    e.preventDefault();
    if (!file) return;
    setExtractError("");
    setSaveError("");
    setExtracted(false);
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
      navigate("/orders");
    } catch (err) {
      setSaveError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Failed to create order");
    } finally {
      setSaving(false);
    }
  }

  function handleFileChange(e) {
    setFile(e.target.files[0]);
    setExtracted(false);
    setForm(EMPTY);
    setConfidence(null);
    setExtractError("");
    setSaveError("");
  }

  const inputClass = "w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition";

  return (
    <div className="max-w-2xl flex flex-col gap-6">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
        <h2 className="text-base font-semibold text-slate-800 mb-1">Upload PDF</h2>
        <p className="text-sm text-slate-500 mb-5">
          Extract patient information from a scanned or text-based PDF document.
        </p>
        <form onSubmit={handleExtract} className="flex flex-col gap-4">
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              file ? "border-blue-400 bg-blue-50" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50"
            }`}
            onClick={() => inputRef.current.click()}
          >
            <input ref={inputRef} type="file" accept="application/pdf" className="hidden" onChange={handleFileChange} />
            <div className="flex flex-col items-center gap-2">
              <svg className={`w-8 h-8 ${file ? "text-blue-500" : "text-slate-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              {file ? (
                <p className="text-sm font-medium text-blue-700">{file.name}</p>
              ) : (
                <>
                  <p className="text-sm font-medium text-slate-600">Click to select a PDF</p>
                  <p className="text-xs text-slate-400">Max 10MB</p>
                </>
              )}
            </div>
          </div>

          {extractError && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              <p className="text-red-600 text-sm">{extractError}</p>
            </div>
          )}

          <button type="submit" disabled={!file || extracting}
            className="bg-blue-600 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {extracting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Extracting — may take a moment for scanned documents…
              </span>
            ) : "Extract Patient Info"}
          </button>
        </form>
      </div>

      {extracted && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-slate-800">Extracted Data</h2>
            {confidence && (
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${confidenceBadge[confidence] || "bg-slate-100 text-slate-600"}`}>
                {confidence} confidence
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mb-5">
            Review and edit the extracted fields, then save as an order.
          </p>
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">First Name</label>
                <input className={inputClass} placeholder="First name" value={form.patient_first_name}
                  onChange={(e) => setForm({ ...form, patient_first_name: e.target.value })} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Last Name</label>
                <input className={inputClass} placeholder="Last name" value={form.patient_last_name}
                  onChange={(e) => setForm({ ...form, patient_last_name: e.target.value })} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Date of Birth</label>
                <input className={inputClass} placeholder="e.g. 12/05/1900" value={form.patient_dob}
                  onChange={(e) => setForm({ ...form, patient_dob: e.target.value })} required />
              </div>
            </div>
            {saveError && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                <p className="text-red-600 text-sm">{saveError}</p>
              </div>
            )}
            <div className="flex gap-3 pt-1">
              <button type="submit" disabled={saving}
                className="bg-green-600 text-white rounded-lg px-5 py-2.5 text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors">
                {saving ? "Saving…" : "Save as Order"}
              </button>
              <button type="button" onClick={() => { setExtracted(false); setForm(EMPTY); setFile(null); setConfidence(null); }}
                className="border border-slate-300 text-slate-600 rounded-lg px-5 py-2.5 text-sm font-medium hover:bg-slate-50 transition-colors">
                Start Over
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
