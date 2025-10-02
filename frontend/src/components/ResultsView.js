import React from 'react';

// Corresponds to the <ResultsView> component requirement [cite: 157]
const ResultsView = ({ data }) => {
    if (!data) return <div>Enter a query to see results.</div>;

    const { results, query_type, performance_metrics } = data;

    return (
        <div className="results-container">
            <div className="metrics">
                <span>Time: {performance_metrics.response_time_seconds}s</span>
                <span>Cache: {performance_metrics.cache_hit ? 'Hit' : 'Miss'}</span>
            </div>

            {query_type === 'SQL' && (
                <div className="sql-results">
                    <h4>Database Results</h4>
                    {/* A component like AG-Grid would be used for a full table view with pagination */}
                    <pre>{JSON.stringify(results, null, 2)}</pre>
                </div>
            )}

            {query_type === 'DOCUMENT' && (
                <div className="document-results">
                    <h4>Document Results</h4>
                    {/* Map over document results and render them in cards */}
                    <div className="result-card">{results}</div>
                </div>
            )}
            
            {query_type === 'HYBRID' && (
                 <div className="hybrid-results">
                    <h4>Combined Results</h4>
                    <p>{results}</p>
                 </div>
            )}
            
            <button>Export as CSV</button> {/* Export functionality [cite: 162] */}
        </div>
    );
};

export default ResultsView;