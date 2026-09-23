interface MetricCardProps {
  label: string;
  value: string | number;
  note: string;
  tone?: "blue" | "green" | "orange" | "red";
}

export function MetricCard({ label, value, note, tone = "blue" }: MetricCardProps) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-label">{label}</div>
      <strong>{value}</strong>
      <span>{note}</span>
    </article>
  );
}
