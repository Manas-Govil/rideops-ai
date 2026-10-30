import React, { useState } from 'react';
import { Table, Download, ChevronLeft, ChevronRight } from 'lucide-react';

const formatCellValue = (key, value) => {
  if (value === null || value === undefined) {
    return <span className="null-val">NULL</span>;
  }
  if (typeof value === 'boolean') {
    return (
      <span className={`bool-badge ${value ? 'bool-true' : 'bool-false'}`}>
        {value ? 'TRUE' : 'FALSE'}
      </span>
    );
  }

  const strKey = String(key).toLowerCase();

  // Currency formatting
  if (
    strKey.includes('revenue') ||
    strKey.includes('fare') ||
    strKey.includes('amount') ||
    strKey.includes('price') ||
    strKey.includes('tip')
  ) {
    const num = Number(value);
    if (!isNaN(num)) {
      return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
  }

  // Percentage formatting
  if (strKey.includes('percentage') || strKey.includes('pct') || strKey.includes('rate')) {
    const num = Number(value);
    if (!isNaN(num)) {
      return `${num.toFixed(2)}%`;
    }
  }

  // Integer count formatting
  if (
    strKey.includes('count') ||
    strKey.includes('trips') ||
    strKey.includes('occurrences') ||
    strKey.includes('total_')
  ) {
    const num = Number(value);
    if (!isNaN(num) && Number.isInteger(num)) {
      return num.toLocaleString('en-US');
    }
  }

  // Distance / Duration formatting
  if (strKey.includes('distance')) {
    const num = Number(value);
    if (!isNaN(num)) return `${num.toFixed(2)} mi`;
  }
  if (strKey.includes('duration')) {
    const num = Number(value);
    if (!isNaN(num)) return `${num.toFixed(1)} min`;
  }

  return String(value);
};

const formatColumnHeader = (col) => {
  return col
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const ResultsTable = ({ data, title = 'Structured Analytics Data' }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  if (!data || !Array.isArray(data) || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);
  const totalPages = Math.ceil(data.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const currentRows = data.slice(startIndex, startIndex + rowsPerPage);

  const exportCSV = () => {
    const headers = columns.join(',');
    const rows = data.map((row) =>
      columns.map((col) => `"${row[col] ?? ''}"`).join(',')
    );
    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `rideops_data_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="results-table-card">
      <div className="table-card-header">
        <div className="table-title-group">
          <Table size={18} className="table-icon" />
          <h4 className="table-title">{title}</h4>
          <span className="table-badge">{data.length} records</span>
        </div>
        <button className="export-btn" onClick={exportCSV} title="Export to CSV">
          <Download size={14} />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="table-scroll-container">
        <table className="data-table">
          <thead>
            <tr>
              <th className="row-num-col">#</th>
              {columns.map((col) => (
                <th key={col}>{formatColumnHeader(col)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, rIdx) => (
              <tr key={rIdx}>
                <td className="row-num-cell">{startIndex + rIdx + 1}</td>
                {columns.map((col) => (
                  <td key={col}>{formatCellValue(col, row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <span className="pagination-info">
            Showing {startIndex + 1} - {Math.min(startIndex + rowsPerPage, data.length)} of {data.length} rows
          </span>
          <div className="pagination-controls">
            <button
              className="page-btn"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft size={16} />
            </button>
            <span className="page-number">
              Page {currentPage} of {totalPages}
            </span>
            <button
              className="page-btn"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsTable;
