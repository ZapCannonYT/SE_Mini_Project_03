import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

function shortDate(s) {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export default function TrendChart({ trend }) {
  const data = {
    labels: trend.map((t) => shortDate(t.date)),
    datasets: [
      {
        label: 'Actual sales',
        data: trend.map((t) => t.actual),
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.2,
        spanGaps: false,
      },
      {
        label: 'Forecast',
        data: trend.map((t) => t.forecast),
        borderColor: '#b45309',
        backgroundColor: 'rgba(180, 83, 9, 0.1)',
        borderWidth: 2,
        borderDash: [6, 4],
        pointRadius: 2,
        tension: 0.2,
        spanGaps: false,
      },
    ],
  }
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { beginAtZero: true, min: 0, title: { display: true, text: 'Units per day' } },
      x: { ticks: { maxTicksLimit: 10 } },
    },
    plugins: { legend: { position: 'bottom' } },
  }

  const actual = trend.filter((t) => t.actual !== null)
  const future = trend.filter((t) => t.actual === null && t.forecast !== null)
  const summary = `Daily units sold over the last ${actual.length} days, followed by a ${future.length}-day forecast.`

  return (
    <div>
      <div className="chart-box">
        <Line
          data={data}
          options={options}
          role="img"
          aria-label="Line chart of actual daily sales and forecast demand"
        />
      </div>
      <p className="sr-only">{summary}</p>
    </div>
  )
}
