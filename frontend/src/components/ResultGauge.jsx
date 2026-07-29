const RADIUS = 92;
const CX = 120;
const CY = 118;
const CIRCUMFERENCE = Math.PI * RADIUS; // half circle

export default function ResultGauge({ prediction, probability }) {
  const isPotable = prediction === "Potable";
  const pct = Math.round(probability * 100);
  const accent = isPotable ? "#2FD5C8" : "#F2603B";

  const offset = CIRCUMFERENCE - (probability * CIRCUMFERENCE);
  const needleAngle = -90 + probability * 180;

  const ticks = Array.from({ length: 11 }, (_, i) => i * 10);

  return (
    <div className="relative flex flex-col items-center">
      <svg viewBox="0 0 240 150" className="w-full max-w-[280px]">
        {/* fond de la jauge */}
        <path
          d={`M ${CX - RADIUS} ${CY} A ${RADIUS} ${RADIUS} 0 0 1 ${CX + RADIUS} ${CY}`}
          fill="none"
          stroke="#1E4A54"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* arc de progression */}
        <path
          d={`M ${CX - RADIUS} ${CY} A ${RADIUS} ${RADIUS} 0 0 1 ${CX + RADIUS} ${CY}`}
          fill="none"
          stroke={accent}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.4,0,0.2,1), stroke 0.4s" }}
        />

        {/* graduations */}
        {ticks.map((t) => {
          const angle = (-90 + t * 1.8) * (Math.PI / 180);
          const x1 = CX + (RADIUS + 8) * Math.cos(angle);
          const y1 = CY + (RADIUS + 8) * Math.sin(angle);
          const x2 = CX + (RADIUS + 14) * Math.cos(angle);
          const y2 = CY + (RADIUS + 14) * Math.sin(angle);
          return (
            <line
              key={t}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#7FA8AC"
              strokeWidth="1.5"
            />
          );
        })}

        {/* aiguille */}
        <g
          style={{
            transform: `rotate(${needleAngle}deg)`,
            transformOrigin: `${CX}px ${CY}px`,
            transition: "transform 0.9s cubic-bezier(0.4,0,0.2,1)",
          }}
        >
          <line x1={CX} y1={CY} x2={CX} y2={CY - RADIUS + 16} stroke="#EAF6F6" strokeWidth="2" />
        </g>
        <circle cx={CX} cy={CY} r="5" fill="#EAF6F6" />
      </svg>

      <div className="absolute top-[62%] flex flex-col items-center">
        <span className="font-mono text-4xl font-semibold" style={{ color: accent }}>
          {pct}%
        </span>
        <span className="label-eyebrow mt-1">probabilité potable</span>
      </div>
    </div>
  );
}
