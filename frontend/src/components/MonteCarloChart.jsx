import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, BarElement, LinearScale, CategoryScale, Tooltip, Legend } from 'chart.js';
import { baseChartOptions } from '../lib/chartOptions';

ChartJS.register(BarElement, LinearScale, CategoryScale, Tooltip, Legend);

export default function MonteCarloChart({ summary = [] }) {
  const data = {
    labels: summary.map(s => s.strategy),
    datasets: [
      { label: 'Expected Position', data: summary.map(s => s.expectedPosition), backgroundColor: '#e8101f' },
      { label: 'Success Probability %', data: summary.map(s => s.successProbability), backgroundColor: '#2be3ff' },
    ],
  };
  return (
    <div style={{ height: 320 }}>
      <Bar data={data} options={baseChartOptions(true)} />
    </div>
  );
}
