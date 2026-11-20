import { useState } from "react";

// Runs an async action and keeps its loading / error / result state
export default function useAction() {
  const [state, setState] = useState({ busy: false, error: "", data: null });
  async function run(action) {
    setState((s) => ({ ...s, busy: true, error: "" }));
    try {
      setState({ busy: false, error: "", data: await action() });
    } catch (err) {
      setState({ busy: false, error: err.message, data: null });
    }
  }
  return [state, run];
}
