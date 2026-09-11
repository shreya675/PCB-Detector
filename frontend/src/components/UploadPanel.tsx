import { useEffect, useState } from "react";
import { Icon } from "./Icon";

function FileField({ label, hint, file, onFile, required }: { label: string; hint: string; file: File | null; onFile: (file: File | null) => void; required?: boolean }) {
  const [preview, setPreview] = useState<string | null>(null);
  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url);
  }, [file]);
  return <label className={file ? "dropzone has-file" : "dropzone"}>
    <input type="file" accept="image/png,image/jpeg,image/bmp,image/tiff" required={required} onChange={(event) => onFile(event.target.files?.[0] || null)}/>
    {preview ? <img src={preview} alt={`${label} preview`}/> : <div className="drop-icon"><Icon name="upload"/></div>}
    <strong>{file?.name || label}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : hint}</span>
  </label>;
}

export function UploadPanel({ busy, error, onSubmit }: { busy: boolean; error: string | null; onSubmit: (test: File, reference?: File) => Promise<void> }) {
  const [test, setTest] = useState<File | null>(null);
  const [reference, setReference] = useState<File | null>(null);
  return <form className="panel upload-panel" onSubmit={(event) => { event.preventDefault(); if (test) void onSubmit(test, reference || undefined); }}>
    <div className="panel-heading"><div><span className="eyebrow">NEW INSPECTION</span><h2>Upload PCB images</h2><p>Add a test image and, optionally, a reference board for alignment and comparison.</p></div></div>
    <div className="upload-grid"><FileField label="Test PCB image" hint="Required · PNG, JPEG, BMP or TIFF" file={test} onFile={setTest} required/><FileField label="Reference PCB image" hint="Optional · enables component and trace comparison" file={reference} onFile={setReference}/></div>
    {error && <div className="error-banner" role="alert">{error}</div>}
    <div className="form-footer"><span>Maximum upload: 20 MB per image</span><button className="primary-button" disabled={!test || busy}>{busy ? <><span className="spinner"/>Inspecting…</> : "Run inspection"}</button></div>
  </form>;
}
