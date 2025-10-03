import React from 'react';

// Corresponds to the <ResultsView> component requirement
const ResultsView = ({ data }) => {
    // Initial state before any query is made
    if (!data) {
        return <div className="card">Enter a query to see results.</div>;
    }

    // NEW: Handle and display errors from the backend
    if (data.error) {
        return <div className="card error-message"><strong>Error:</strong> {data.error}</div>;
    }
    
    // Destructure data only after we know there's no error
    const { results, query_type, performance_metrics, generated_sql } = data;

    // Handle case with no results
    if (!results || results.length === 0) {
        return <div className="card">No results found for your query.</div>;
    }

    return (
        <div className="card results-container">
            {/* NEW: Use optional chaining (?.) to safely access nested properties.
              This prevents a crash if performance_metrics is missing.
            */}
            <div className="metrics">
                <span>Time: {performance_metrics?.response_time_seconds}s</span>
                <span>Cache: {performance_metrics?.cache_hit ? 'Hit' : 'Miss'}</span>
            </div>

            {query_type === 'SQL' && (
                <div className="sql-results">
                    <h4>Database Results</h4>
                    {/* This will now render a proper table */}
                    <table>
                        <thead>
                            <tr>
                                {results.length > 0 && Object.keys(results[0]).map(key => <th key={key}>{key}</th>)}
                            </tr>
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