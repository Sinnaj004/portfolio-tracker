import React from 'react';
import Chart from 'react-apexcharts';
import { formatCurrency } from '../../utils/formatters';

export default function Portfoliochart_ApexChart({ performanceData, portfolioCurrency }) {
  const series = [
    {
      name: 'Portfoliowert',
      data: performanceData.map(item => ({
        x: new Date(item.timestamp).getTime(),
        y: item.actual_value
      }))
    },
    {
      name: 'Investiert',
      data: performanceData.map(item => ({
        x: new Date(item.timestamp).getTime(),
        y: item.invested_amount
      }))
    }
  ];

  const options = {
    chart: {
      type: 'area',
      height: 350,
      toolbar: { show: false },
      zoom: { enabled: false },
      fontFamily: 'Inter, sans-serif'
    },
    colors: ['#4f46e5', '#94a3b8'], // Indigo (wie dein Button) und Slate
    dataLabels: { enabled: false },
    stroke: {
      curve: 'smooth',
      width: [3, 2],
      dashArray: [0, 6]
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.45,
        opacityTo: 0.05,
        stops: [0, 100]
      }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false, // WICHTIG: Zeigt lokale Zeit des Users
        style: { colors: '#94a3b8', fontWeight: 600 }
      },
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      labels: {
        formatter: (val) => formatCurrency(val, portfolioCurrency),
        style: { colors: '#94a3b8', fontWeight: 600 }
      }
    },
    tooltip: {
      x: { format: 'dd. MMM yyyy' },
      theme: 'light',
      y: {
        formatter: (val) => formatCurrency(val, portfolioCurrency)
      }
    },
    grid: {
      borderColor: '#f1f5f9',
      strokeDashArray: 4
    },
    legend: {
      position: 'top',
      horizontalAlign: 'right',
      fontWeight: 700
    }
  };

  return (
    <div className="w-full h-[350px]">
      <Chart options={options} series={series} type="area" height="100%" />
    </div>
  );
}