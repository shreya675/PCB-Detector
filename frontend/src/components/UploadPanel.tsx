import { useEffect, useState } from "react";
import { Icon } from "./Icon";

interface FileFieldProps {
  label: string;
  hint: string;
  file: File | null;
  required?: boolean;
  onFile: (file: File | null) => void;
}

function FileField({ label, hint, file, required, onFile }: FileFieldProps) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <label className={file ? "dropzone has-file" : "dropzone"}>
      <input
        type="file"
        accept="image/png,image/jpeg,image/bmp,image/tiff"
        required={required}
        onChange={(event) => onFile(event.target.files?.[0] || null)}
      />
      {preview ? (
        <img src={preview} alt={`${label} preview`} />
      ) : (
        <div className="drop-icon"><Icon name="upload" /></div>
      )}
      <strong>{file?.name || label}</strong>
      <span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · click to change` : hint}</span>
      {file && (
        <button
          type="button"
          className="text-button clear-file"
          onClick={(event) => { event.preventDefault(); onFile(null); }}
        >
          Remove
        </button>
      )}
    </label>
  );
}

interface UploadPanelProps {
  busy: boolean;
  error: string | null;
  modelAvailable: boolean;
  onSubmit: (test: File, reference?: File) => Promise<void>;
}

export function UploadPanel({ busy, error, modelAvailable, onSubmit }: UploadPanelProps) {
  const [test, setTest] = useState<File | null>(null);
  const [reference, setReference] = useState<File | null>(null);

  return (
    <form
      className="panel upload-panel"
      onSubmit={(event) => {
        event.preventDefault();
        if (test) void onSubmit(test, reference || undefined);
      }}
    >
      <div className="panel-heading">
        <div>
          <div className="eyebrow">BOARD IMAGES</div>
          <h2>What are we inspecting?</h2>
          <p>Select the board to inspect. A reference image is optional.</p>
        </div>
      </div>

      {!modelAvailable && (
        <div className="info-banner" role="status" style={{ marginBottom: 16 }}>
          The detection model is unavailable. Load a model on the server before running an inspection.
        </div>
      )}

      <div className="upload-grid">
        <FileField label="Choose board image" hint="Required · PNG, JPEG, BMP or TIFF" file={test} onFile={setTest} required />
        <FileField label="Add a reference board" hint="Optional · for alignment and comparison" file={reference} onFile={setReference} />
      </div>

      {error && <div className="error-banner" role="alert" style={{ marginTop: 16 }}>{error}</div>}

      <div className="form-footer">
        <span>Maximum upload: 20 MB per image</span>
        <button className="primary-button" disabled={!test || busy}>
          {busy ? <><span className="spinner" />Inspecting…</> : "Run inspection"}
        </button>
      </div>
    </form>
  );
}
