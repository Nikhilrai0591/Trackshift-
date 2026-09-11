export const baseChartOptions = (showLegend = false) => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 200 },
  plugins: {
    legend: { display: showLegend, labels: { color: '#8b8e96', boxWidth: 10, font: { size: 10 } } },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: { ticks: { color: '#5c5f68', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
    y: { ticks: { color: '#5c5f68', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.06)' } },
  },
  elements: { point: { radius: 0 } },
});
