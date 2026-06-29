import { TAG_COLORS, DEFAULT_TAG } from "../constants/theme";

export default function Tag({ label }) {
  const { bg, color } = TAG_COLORS[label] ?? DEFAULT_TAG;

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 99,
        fontSize: 11,
        fontWeight: 600,
        background: bg,
        color,
        marginRight: 4,
        marginBottom: 4,
      }}
    >
      {label}
    </span>
  );
}
