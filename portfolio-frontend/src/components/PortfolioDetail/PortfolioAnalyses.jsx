import React from 'react';
import Chart from 'react-apexcharts';

export default function PortfolioAnalysis({ portfolioItems, portfolioCurrency = "€" }) {
  
  // 1. Daten-Aggregation & Score-Berechnung
  const calculateData = () => {
    const sectors = {};
    const countries = {};
    const individualAssets = [];
    let totalValue = 0;

    portfolioItems.forEach(item => {
      const price = parseFloat(item.asset?.current_price || 0);
      const qty = parseFloat(item.quantity || 0);
      const marketValue = qty * price;
      totalValue += marketValue;

      const sKey = item.asset?.sector || "Unbekannt";
      const cKey = item.asset?.country || "Unbekannt";
      sectors[sKey] = (sectors[sKey] || 0) + marketValue;
      countries[cKey] = (countries[cKey] || 0) + marketValue;

      individualAssets.push({
        name: item.asset?.symbol || item.asset?.name || "Unbekannt",
        value: marketValue
      });
    });

    const sortMap = (obj) => Object.entries(obj)
      .map(([name, value]) => ({ 
        name, 
        value, 
        percentage: totalValue > 0 ? ((value / totalValue) * 100).toFixed(2) : 0 
      }))
      .sort((a, b) => b.value - a.value);

    const sortedSectors = sortMap(sectors);
    const sortedCountries = sortMap(countries);
    const sortedAssets = individualAssets.sort((a, b) => b.value - a.value);

    // --- Diversifikations-Score (basierend auf Herfindahl-Hirschman-Index) ---
    // HHI = Summe der quadrierten Prozentanteile
    const hhi = sortedAssets.reduce((sum, a) => sum + Math.pow((a.value / totalValue) * 100, 2), 0);
    // Score-Mapping: 100 (perfekt verteilt) bis 0 (Klumpenrisiko)
    const divScore = totalValue > 0 ? Math.max(0, Math.min(100, (100 - (hhi / 100)).toFixed(0))) : 0;

    const top3Sum = sortedAssets.slice(0, 3).reduce((sum, a) => sum + a.value, 0);
    const top3Percentage = totalValue > 0 ? ((top3Sum / totalValue) * 100).toFixed(2) : 0;

    return { sortedSectors, sortedCountries, sortedAssets, totalValue, top3Percentage, divScore };
  };

  const data = calculateData();

  // 2. Dynamische Palette für unbegrenzte Assets
  const generatePalette = (count) => {
    return Array.from({ length: count }, (_, i) => {
      const hue = (225 + (i * Math.floor(360 / count))) % 360;
      return `hsl(${hue}, 65%, 55%)`;
    });
  };

  const getOptions = (labels, title, unitSingular, unitPlural) => ({
    labels: labels,
    chart: { type: 'donut', fontFamily: 'Inter, sans-serif' },
    stroke: { show: false },
    dataLabels: { enabled: false },
    plotOptions: {
      pie: {
        donut: {
          size: '75%',
          labels: {
            show: true,
            total: {
              show: true,
              label: title,
              color: '#64748b',
              formatter: () => `${labels.length} ${labels.length === 1 ? unitSingular : unitPlural}`
            }
          }
        }
      }
    },
    colors: generatePalette(labels.length),
    legend: { position: 'bottom', fontSize: '12px' },
    tooltip: { 
      y: { formatter: (val) => `${val.toFixed(2)} ${portfolioCurrency} (${((val/data.totalValue)*100).toFixed(2)}%)` } 
    }
  });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* --- WIDGET SECTION: Die wichtigsten Fakten auf einen Blick --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Top 3 Assets */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
          <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Top 3 Positionen</span>
          <div className="mt-3 space-y-2">
            {data.sortedAssets.slice(0, 3).map((a, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-sm font-bold text-slate-700">{a.name}</span>
                <span className="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">
                  {data.totalValue > 0 ? ((a.value / data.totalValue) * 100).toFixed(1) : 0}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Diversifikations-Score */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 flex flex-col justify-center text-center">
          <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Diversifikations-Score</span>
          <div className="mt-2 flex items-baseline justify-center">
             <div className="text-4xl font-black text-slate-900">{data.divScore}</div>
             <div className="text-xs font-bold text-slate-400 ml-1">/ 100</div>
          </div>
          <div className={`text-[10px] font-black uppercase mt-1 ${data.divScore > 70 ? 'text-emerald-500' : 'text-amber-500'}`}>
            {data.divScore > 70 ? 'Optimale Streuung' : 'Klumpen-Gefahr'}
          </div>
        </div>

        {/* Top 3 Anteil */}
        <div className="bg-indigo-600 rounded-3xl p-6 shadow-lg flex flex-col justify-center text-white text-center md:text-left">
          <span className="text-[10px] opacity-80 font-black uppercase tracking-widest">Kumulierter Anteil (Top 3)</span>
          <div className="mt-1">
            <div className="text-3xl font-black">{data.top3Percentage}%</div>
            <p className="text-[10px] opacity-70 font-bold uppercase mt-1">des Gesamtwerts</p>
          </div>
        </div>
      </div>

      {/* --- CHART SECTION: Visuelle Aufschlüsselung --- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-400 mb-6 text-center">Branchen-Mix</h3>
          <Chart 
            options={getOptions(data.sortedSectors.map(s => s.name), 'Branchen', 'Branche', 'Branchen')} 
            series={data.sortedSectors.map(s => s.value)} 
            type="donut" width="100%" 
          />
        </div>

        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
          <h3 className="text-sm font-black uppercase tracking-widest text-slate-400 mb-6 text-center">Geografische Regionen</h3>
          <Chart 
            options={getOptions(data.sortedCountries.map(c => c.name), 'Länder', 'Land', 'Länder')} 
            series={data.sortedCountries.map(c => c.value)} 
            type="donut" width="100%" 
          />
        </div>
      </div>
    </div>
  );
}