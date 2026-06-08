export default function AlertIcon({ size = 20, color = "#f07c00" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-label="Alerta">
      <path d="M12 2L2 20h20L12 2z" stroke={color} strokeWidth="2" fill="none" />
      <line x1="12" y1="9" x2="12" y2="14" stroke={color} strokeWidth="2" />
      <circle cx="12" cy="17" r="1" fill={color} />
    </svg>
  );
}
