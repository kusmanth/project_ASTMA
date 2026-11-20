import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Icon } from "../components/Icons.jsx";
import PageHead from "../components/PageHead.jsx";
import ResultView from "../components/ResultView.jsx";

const EXAMPLES = [
  "best route from Ameerpet Junction to Paradise Circle",
  "how is the traffic right now?",
  "book emergency trip for TS09AB1234 from Ameerpet Junction to Paradise Circle, critical",
  "trip 1 is completed, the ambulance reached Paradise",
];

// Flow: user message -> Plan (orchestrator) -> user approves -> Execute (right agent)
export default function Assistant({ userId, roads, junctions, chat, setChat }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  // Scroll to the newest message
  useEffect(() => {
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "smooth" });
  }, [chat]);

  const add = (msg) => setChat((c) => [...c, msg]);
  const update = (index, changes) => setChat((c) => c.map((m, i) => (i === index ? { ...m, ...changes } : m)));

  async function send(e) {
    e?.preventDefault();
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    setBusy(true);
    add({ role: "user", text: message });
    add({ role: "bot", kind: "thinking", text: "Understanding your request..." });
    try {
      const plan = await api.plan(message, userId);
      setChat((c) => [
        ...c.slice(0, -1),
        plan.task
          ? { role: "bot", kind: "plan", plan, status: "waiting" }
          : { role: "bot", kind: "text", text: plan.message || "Sorry, I can't help with that yet." },
      ]);
    } catch (err) {
      setChat((c) => [...c.slice(0, -1), { role: "bot", kind: "error", text: err.message }]);
    } finally {
      setBusy(false);
    }
  }

  async function approve(index, plan) {
    update(index, { status: "approved" });
    setBusy(true);
    add({ role: "bot", kind: "thinking", text: "Running the agent... (booking a trip can take up to a minute)" });
    try {
      const result = await api.execute(plan, userId);
      setChat((c) => [...c.slice(0, -1), { role: "bot", kind: "result", result }]);
    } catch (err) {
      setChat((c) => [...c.slice(0, -1), { role: "bot", kind: "error", text: err.message }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Your traffic companion"
        title="AI Assistant"
        text="Ask in plain English. You see the plan first, and nothing changes until you approve it."
      >
        {chat.length > 0 && <button className="ghost" onClick={() => setChat([])} disabled={busy}>New chat</button>}
      </PageHead>

      <div className="chat">
        {chat.length === 0 && (
          <div className="empty">
            <div className="empty-icon">{Icon.spark}</div>
            <h3>What do you need?</h3>
            <p className="muted">Try one of these:</p>
            <div className="chips">
              {EXAMPLES.map((ex) => (
                <button key={ex} className="chip" onClick={() => setText(ex)}>{ex}</button>
              ))}
            </div>
          </div>
        )}

        {chat.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="msg-label">{m.role === "user" ? "You" : "ASTMA assistant"}</div>

            {m.role === "user" && <p>{m.text}</p>}
            {m.kind === "thinking" && <p className="thinking"><span className="spinner" /> {m.text}</p>}
            {m.kind === "text" && <p>{m.text}</p>}
            {m.kind === "error" && <p className="error-text">{m.text}</p>}
            {m.kind === "result" && <ResultView data={m.result} roads={roads} junctions={junctions} />}

            {m.kind === "plan" && (
              <PlanCard
                plan={m.plan}
                status={m.status}
                busy={busy}
                onApprove={() => approve(i, m.plan)}
                onCancel={() => update(i, { status: "cancelled" })}
              />
            )}
          </div>
        ))}
      </div>

      <form className="composer" onSubmit={send}>
        <label>Message your traffic assistant</label>
        <textarea
          rows={3}
          maxLength={500}
          value={text}
          placeholder="Include the vehicle number, junction names or trip id when needed."
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) send(e);
          }}
        />
        <div className="composer-foot">
          <span className="muted small">{text.length}/500 · Enter to send</span>
          <button type="submit" disabled={busy || !text.trim()}>
            {busy ? "Working..." : "Send"} {Icon.send}
          </button>
        </div>
      </form>
    </>
  );
}

function PlanCard({ plan, status, busy, onApprove, onCancel }) {
  const missing = plan.missing || [];
  return (
    <div className="plan">
      <p>Here is my plan. Please check it before I start.</p>
      <div className="plan-task">
        <span className="tag">Task</span>
        <b>{plan.task}</b>
      </div>
      {plan.reason && <p className="muted">{plan.reason}</p>}

      {plan.details && Object.keys(plan.details).length > 0 && (
        <dl className="details">
          {Object.entries(plan.details).map(([k, v]) => (
            <div key={k}>
              <dt>{k.replace(/_/g, " ")}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}

      {plan.steps?.length > 0 && (
        <ol className="steps">{plan.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
      )}

      {plan.candidates && (
        <p className="muted small">
          Knowledge match (lower is closer): {Object.entries(plan.candidates).map(([k, v]) => `${k} ${v}`).join(" · ")}
        </p>
      )}

      {missing.length > 0 ? (
        <div className="alert warn">I still need: <b>{missing.join(", ")}</b>. Please send the request again with it.</div>
      ) : status === "waiting" ? (
        <div className="actions">
          <button onClick={onApprove} disabled={busy}>{Icon.check} Approve and run</button>
          <button className="ghost" onClick={onCancel} disabled={busy}>Cancel</button>
        </div>
      ) : (
        <p className={`plan-status ${status}`}>{status === "approved" ? "✓ Approved" : "Cancelled"}</p>
      )}
    </div>
  );
}
