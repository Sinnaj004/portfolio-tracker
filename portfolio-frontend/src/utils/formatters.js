export const formatCurrency = (value) => {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(value);
};

export const calculateGrowth = (avg, current) => {
  const percent = ((current / avg) - 1) * 100;
  return {
    value: percent.toFixed(2) + '%',
    isPositive: percent >= 0
  };
};