// Small line icons (inline SVG, no extra library needed)
const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };

export const Icon = {
  home: <svg {...base}><path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" /></svg>,
  spark: <svg {...base}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="M19 3v4M17 5h4" /></svg>,
  gauge: <svg {...base}><path d="M4 16a8 8 0 1 1 16 0" /><path d="M12 16l4-5" /><circle cx="12" cy="16" r="1" /></svg>,
  light: <svg {...base}><rect x="8" y="2" width="8" height="20" rx="3" /><circle cx="12" cy="7" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="17" r="1.5" /></svg>,
  route: <svg {...base}><circle cx="6" cy="19" r="2" /><circle cx="18" cy="5" r="2" /><path d="M8 19h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7" /></svg>,
  send: <svg {...base}><path d="M5 12h14M13 6l6 6-6 6" /></svg>,
  check: <svg {...base}><path d="M5 12l5 5 9-10" /></svg>,
  siren: <svg {...base}><path d="M7 18v-6a5 5 0 0 1 10 0v6" /><path d="M5 21h14v-3H5z" /><path d="M12 3v2M4.2 6.2l1.4 1.4M19.8 6.2l-1.4 1.4" /></svg>,
  map: <svg {...base}><path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z" /><path d="M9 4v14M15 6v14" /></svg>,
  logout: <svg {...base}><path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" /><path d="M10 17l5-5-5-5M15 12H3" /></svg>,
  user: <svg {...base}><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg>,
};
