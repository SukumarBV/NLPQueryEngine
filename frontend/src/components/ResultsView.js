import React from 'react';

const toCsv = (rows) => {
    if (!rows || rows.length === 0) return '';
    const headers = Object.keys(rows[0]);
    const escapeCell = (value) => {
        const str = value === null || value === undefined ? '' : String(value);
        if (/[",\n]/.test(str)) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    };
    const lines = [headers.join(',')];
    rows.forEach((row) => {
        lines.push(headers.map((h) => escapeCell(row[h])).join(','));
    });
    return lines.join('\n');
};

const downloadCsv = (rows, filename) => {
    const csv = toCsv(rows);
    if (!csv) return;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

const DatabaseTable = ({ rows }) => {
    if (!rows || rows.length === 0) return <p>No database rows matched this query.</p>;
    return (
        <table>
            <thead>
                <tr>{Object.keys(rows[0]).map((key) => <th key={key}>{key}</th>)}</tr>
            </thead>
            <tbody>
                {rows.map((row, index) => (
                    <tr key={index}>
                        {Object.values(row).map((value, i) => <td key={i}>{String(value)}</td>)}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

const DocumentResults = ({ items }) => {
    if (!items || items.length === 0) return <p>No matching document passages found.</p>;
    return (
        <>
            {items.map((item, index) => (
                <div key={index} className="result-card">
                    <p>{item.content}</p>
                    <small>
                        Source: {item.source}
                        {typeof item.similarity === 'number' && ` (Similarity: ${item.similarity.toFixed(2)})`}
                    </small>
                </div>
            ))}
        </>
    );
};

const ResultsView = ({ data }) => {
    if (!data) return <div className="card">Enter a query to see results.</div>;
    if (data.error) return <div className="card error-message"><strong>Error:</strong> {data.error}</div>;

    const { results, query_type, performance_metrics, generated_sql } = data;

    const isHybrid = query_type === 'HYBRID';
    const databaseRows = isHybrid ? results?.database : (query_type === 'SQL' ? results : null);
    const documentRows = isHybrid ? results?.documents : (query_type === 'DOCUMENT' ? results : null);

    const hasAnyResults =
        (Array.isArray(databaseRows) && databaseRows.length > 0) ||
        (Array.isArray(documentRows) && documentRows.length > 0);

    const handleExport = () => {
        if (Array.isArray(databaseRows) && databaseRows.length > 0) {
            downloadCsv(databaseRows, 'database-results.csv');
        }
        if (Array.isArray(documentRows) && documentRows.length > 0) {
            downloadCsv(documentRows, 'document-results.csv');
        }
    };

    return (
        <div className="card results-container">
            <div className="metrics">
                <span>Time: {performance_metrics?.response_time_seconds}s</span>
                <span>Cache: {performance_metrics?.cache_hit ? 'Hit' : 'Miss'}</span>
            </div>

            {!hasAnyResults && <p>No results found for your query.</p>}

            {(query_type === 'DOCUMENT' || isHybrid) && (
                <div className="document-results">
                    <h4>Document Results</h4>
                    <DocumentResults items={documentRows} />
                </div>
            )}

            {(query_type === 'SQL' || isHybrid) && (
                <div className="sql-results">
                    <h4>Database Results</h4>
                    <DatabaseTable rows={databaseRows} />
                </div>
            )}

            {generated_sql && (
                <div className="generated-sql">
                    <h4>Generated SQL:</h4>
                    <pre><code>{generated_sql}</code></pre>
                </div>
            )}

            {hasAnyResults && <button onClick={handleExport}>Export as CSV</button>}
        </div>
    );
};

export default ResultsView;
