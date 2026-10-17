import { FileText, Loader2, X } from "lucide-react";
import "./DocumentPanel.css";

export default function DocumentPanel({
  documents,
  uploading,
  onRemove,
  disabled,
}) {
  if (documents.length === 0 && !uploading) return null;

  return (
    <div className="docs" aria-label="Attached PDFs">
      <span className="docs-label eyebrow">Attached</span>

      <ul className="docs-list">
        {documents.map((d) => (
          <li key={d.id} className="doc-chip">
            <FileText size={14} className="doc-icon" />
            <span className="doc-name mono" title={d.filename}>
              {d.filename}
            </span>
            <button
              className="doc-remove"
              onClick={() => onRemove(d)}
              disabled={disabled || uploading}
              aria-label={`Remove ${d.filename}`}
              title="Remove"
            >
              <X size={13} />
            </button>
          </li>
        ))}

        {uploading && (
          <li className="doc-chip is-uploading" aria-live="polite">
            <Loader2 size={14} className="spin" />
            <span className="doc-name mono">Reading your PDF…</span>
          </li>
        )}
      </ul>
    </div>
  );
}