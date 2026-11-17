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

export default function ForecastChart({ points, unit }) {
  const data = {
    labels: points.map((p) => shortDate(p.period_start)),
    datasets: [
      {
        label: `Forecast units per ${unit}`,
        data: points.map((p) => p.predicted_qty),
        borderColor: '#b45309',
        backgroundColor: 'rgba(180, 83, 9, 0.1)',
        borderWidth: 2,
        pointRadius: 3,
        tension: 0.2,
      },
    ],
  }
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true, min: 0, title: { display: true, text: `Units per ${unit}` } },
      x: { title: { display: true, text: `${unit === 'week' ? 'Week' : 'Month'} starting` } },
    },
    plugins: { legend: { position: 'bottom' } },
  }
  const first = points[0]
  const last = points[points.length - 1]
  const summary = `Forecast demand for ${points.length} ${unit}${points.length === 1 ? '' : 's'}, from ${first.period_start} to ${last.period_start}.`

  return (
    <div>
      <div className="chart-box">
        <Line
          data={data}
          options={options}
          role="img"
          aria-label={`Line chart of forecast demand per ${unit}`}
        />
      </div>
      <p className="sr-only">{summary}</p>
    </div>
  )
}
