import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { BarChart3, PieChart as PieIcon, TrendingUp } from 'lucide-react';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

const CustomTooltip = ({ active, payload, label, prefix = '', suffix = '' }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-chart-tooltip">
        <p className="tooltip-label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="tooltip-value" style={{ color: entry.color || entry.fill }}>
            {entry.name}: {prefix}
            {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
            {suffix}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const Charts = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return null;
  }

  const sample = data[0];

  // 1. Hourly Demand Chart
  if ('pickup_hour' in sample && 'total_trips' in sample) {
    const formattedData = [...data]
      .sort((a, b) => Number(a.pickup_hour) - Number(b.pickup_hour))
      .map((d) => ({
        hour: `${String(d.pickup_hour).padStart(2, '0')}:00`,
        'Total Trips': Number(d.total_trips),
        'Revenue ($)': Number(d.total_revenue || 0),
        'Airport Trips': Number(d.airport_trips || 0),
      }));

    return (
      <div className="chart-card">
        <div className="chart-header">
          <div className="chart-title-group">
            <BarChart3 size={18} className="chart-icon" />
            <h4 className="chart-title">Hourly Trip Demand Distribution (24h)</h4>
          </div>
          <span className="chart-subtitle">NYC Yellow Taxi Operations</span>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={formattedData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="Total Trips" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // 2. Zone Performance Chart (Top Zones by Revenue)
  if ('zone' in sample && ('total_revenue' in sample || 'total_trips' in sample)) {
    const isRevenue = 'total_revenue' in sample;
    const metricKey = isRevenue ? 'total_revenue' : 'total_trips';
    const labelKey = isRevenue ? 'Revenue ($)' : 'Trip Volume';

    const formattedData = [...data]
      .slice(0, 8)
      .map((d) => ({
        name: d.zone.length > 20 ? `${d.zone.substring(0, 18)}...` : d.zone,
        fullName: d.zone,
        borough: d.borough,
        [labelKey]: Number(d[metricKey]),
      }));

    return (
      <div className="chart-card">
        <div className="chart-header">
          <div className="chart-title-group">
            <TrendingUp size={18} className="chart-icon" />
            <h4 className="chart-title">
              Top Taxi Zones by {isRevenue ? 'Revenue Generation' : 'Trip Volume'}
            </h4>
          </div>
          <span className="chart-subtitle">Leading Operational Clusters</span>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={formattedData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 60, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis
                type="number"
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => (isRevenue ? `$${(v / 1000000).toFixed(1)}M` : `${(v / 1000).toFixed(0)}k`)}
              />
              <YAxis type="category" dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} width={120} />
              <Tooltip content={<CustomTooltip prefix={isRevenue ? '$' : ''} />} />
              <Bar dataKey={labelKey} radius={[0, 4, 4, 0]}>
                {formattedData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // 3. Airport vs Non-Airport Comparison Chart
  if ('airport_flag' in sample && 'total_trips' in sample) {
    const pieData = data.map((d) => ({
      name: d.airport_flag ? 'Airport Trips' : 'City / Non-Airport',
      value: Number(d.total_trips),
      revenue: Number(d.total_revenue || 0),
    }));

    return (
      <div className="chart-card">
        <div className="chart-header">
          <div className="chart-title-group">
            <PieIcon size={18} className="chart-icon" />
            <h4 className="chart-title">Airport vs. Non-Airport Mobility Share</h4>
          </div>
          <span className="chart-subtitle">JFK, LGA, EWR vs Inner-City</span>
        </div>
        <div className="chart-container chart-pie-container">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={95}
                paddingAngle={4}
                dataKey="value"
              >
                <Cell fill="#3b82f6" />
                <Cell fill="#64748b" />
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // 4. Data Quality Issues Breakdown Chart
  if ('issue_type' in sample && 'total_occurrences' in sample) {
    const formattedData = [...data].slice(0, 6).map((d) => ({
      name: d.issue_type,
      Occurrences: Number(d.total_occurrences),
      severity: d.severity,
    }));

    return (
      <div className="chart-card">
        <div className="chart-header">
          <div className="chart-title-group">
            <BarChart3 size={18} className="chart-icon text-amber" />
            <h4 className="chart-title">Data Quality Issues by Frequency</h4>
          </div>
          <span className="chart-subtitle">Anomaly Breakdown</span>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={formattedData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" stroke="#64748b" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} width={140} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="Occurrences" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  return null;
};

export default Charts;
