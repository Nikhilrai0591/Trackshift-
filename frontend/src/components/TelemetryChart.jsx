import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler,
} from 'chart.js';
import { baseChartOptions } from '../lib/chartOptions';

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler);

export default function TelemetryChart({ labels = [], datasets = [], showLegend = false }) {
  const data = {
    labels,
    datasets: datasets.map(d => ({
      label: d.label,
      data: d.data,
      borderColor: d.color,
      backgroundColor: d.fill ? d.color + '22' : 'transparent',
      fill: !!d.fill,
      borderWidth: 2,
      tension: 0.3,
    })),
  };
  return (
    <div className="chart-holder">
      <Line data={data} options={baseChartOptions(showLegend)} />
    </div>
  );
}
