import { useEffect, useRef, useState } from "react";
import { ArrowUp, Loader2, Paperclip } from "lucide-react";
import "./MessageInput.css";

export default function MessageInput({
  models,
  model,
  onModelChange,
  onSend,
  sending,
  onAttach,
  uploading,
}) {
  const [text, setText] = useState("");
  const textRef = useRef(null);
  const fileRef = useRef(null);

  // grow with the content, up to the CSS max-height
  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  const canSend = text.trim().length > 0 && !sending && Boolean(model);

  const submit = () => {
    if (!canSend) return;
    onSend(text);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // lets you pick the same file again later
    if (file) onAttach?.(file);
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          ref={textRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask something…"
          aria-label="Message"
        />

        <div className="composer-bar">
          <div className="composer-left">
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              hidden
              onChange={handleFile}
            />
            <button
              className="icon-btn"
              onClick={() => fileRef.current?.click()}
              disabled={uploading || sending}
              aria-label="Attach a PDF"
              title="Attach a PDF"
            >
              {uploading ? (
                <Loader2 size={18} className="spin" />
              ) : (
                <Paperclip size={18} />
              )}
            </button>

            <select
              className="model-select mono"
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              disabled={sending}
              aria-label="Model"
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <button
            className="send-btn"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send message"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>

      <p className="composer-hint mono">
        Enter to send · Shift+Enter for a new line
      </p>
    </div>
  );
}