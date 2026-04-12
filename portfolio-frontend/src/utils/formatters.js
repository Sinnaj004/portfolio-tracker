export const formatCurrency = (value, currency = 'EUR') => {

  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: currency.toUpperCase(), // Stellt sicher, dass es 'CHF', 'USD' etc. ist
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const calculateGrowth = (avg, current) => {
  if (!avg || avg === 0) return { value: '0.00%', isPositive: true };
  
  const percent = ((current / avg) - 1) * 100;
  return {
    value: (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%',
    isPositive: percent >= 0
  };
};