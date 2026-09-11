import { useEffect, useState } from 'react';

export default function FeatureImportance({ importance = {} }) {
  const [widths, setWidths] = useState({});
  const entries = Object.entries(importance).sort((a, b) => b[1] - a[1]);

  useEffect(() => {
    setWidths({});
    const t = setTimeout(() => {
      const w = {};
      entries.forEach(([k, v]) => { w[k] = v; });
      setWidths(w);
    }, 30);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(importance)]);

  return (
    <div>
      {entries.map(([k, v]) => (
        <div className="explain-bar-row" key={k}>
          <div className="lab"><span>{k.toUpperCase()}</span><span>{v.toFixed(1)}%</span></div>
          <div className="explain-track">
            <div className="explain-fill" style={{ width: `${widths[k] || 0}%` }}></div>
          </div>
        </div>
      ))}
    </div>
  );
}
