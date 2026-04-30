export const getPortfolioPerformance = async (portfolioId, days = 30) => {
  const response = await fetch(`/api/v1/portfolio/${portfolioId}/performance?days=${days}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  if (!response.ok) throw new Error('Performance-Daten konnten nicht geladen werden');
  return response.json();
};