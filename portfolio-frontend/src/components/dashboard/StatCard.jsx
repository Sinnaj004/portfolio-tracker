import { formatCurrency } from '../../utils/formatters';

export default function StatCard({ title, value, isCurrency = true, trend }) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
      <p className="text-sm text-slate-500 font-medium">{title}</p>
      <p className={`text-3xl font-bold mt-1 ${trend ? 'text-emerald-500' : 'text-slate-900'}`}>
        {isCurrency ? formatCurrency(value) : value}
      </p>
    </div>
  );
}