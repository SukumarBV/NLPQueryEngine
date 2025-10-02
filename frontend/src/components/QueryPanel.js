import React, { useState } from 'react';

const QueryPanel = ({ onQuerySubmit, isLoading }) => {
    const [query, setQuery] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!query.trim()) return;
        onQuerySubmit(query);
    };

    return (
        <div className="card">
            <h2>3. Ask a Question</h2>
            <p>Use natural language to query the connected database and uploaded documents.</p>
            <form onSubmit={handleSubmit} className="query-form">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., How many employees do we have?"
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Searching...' : 'Submit Query'}
                </button>
            </form>
        </div>
    );
};

export default QueryPanel;