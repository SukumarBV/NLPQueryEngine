// frontend/src/components/ResultsView.js (Updated)
import React from 'react';

const ResultsView = ({ data }) => {
    if (!data) return <div className="card">Enter a query to see results.</div>;
    if (data.error) return <div className="card error-message"><strong>Error:</strong> {data.error}</div>;
    
    const { results, query_type, performance_metrics, generated_sql } = data;

    if (!results || results.length === 0) {
        return <div className="card">No results found for your query.</div>;
    }

    return (
        <div className="card results-container">
            <div className="metrics">
                <span>Time: {performance_metrics?.response_time_seconds}s</span>
                <span>Cache: {performance_metrics?.cache_hit ? 'Hit' : 'Miss'}</span>
            </div>

            {/* --- NEW SECTION FOR DOCUMENT/HYBRID RESULTS --- */}
            {(query_type === 'DOCUMENT' || query_type === 'HYBRID') && (
                <div className="document-results">
                    <h4>Document Results</h4>
                    {results.map((item, index) => (
                        <div key={index} className="result-card">
                            <p>{item.content}</p>
                            <small>Source: {item.source} (Similarity: {item.similarity.toFixed(2)})</small>
                        </div>
                    ))}
                </div>
            )}

            {/* Section for SQL results */}
            {query_type === 'SQL' && (
                <div className="sql-results">
                    <h4>Database Results</h4>
                    <table>
                        <thead>
                            <tr>{Object.keys(results[0]).map(key => <th key={key}>{key}</th>)}</tr>
                        </thead>
                        <tbody>
                            {results.map((row, index) => (
                                <tr key={index}>
                                    {Object.values(row).map((value, i) => <td key={i}>{String(value)}</td>)}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            
            {generated_sql && (
                <div className="generated-sql">
                    <h4>Generated SQL:</h4>
                    <pre><code>{generated_sql}</code></pre>
                </div>
            )}
            <button>Export as CSV</button>
        </div>
    );
};

export default ResultsView;