import React, { useState } from 'react';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';
import './App.css'; 

function App() {
    const [isDbConnected, setIsDbConnected] = useState(false);
    const [queryResults, setQueryResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleDbConnection = (schema) => {
        setIsDbConnected(true);
    };
    
    const handleQuerySubmit = async (query) => {
        setIsLoading(true);
        setError('');
        setQueryResults(null);

        try {
            const response = await fetch('http://localhost:8000/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'An error occurred while querying.');
            }
            setQueryResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <div className="App">
            <header className="App-header">
                <h1>AI-Powered NLP Query Engine</h1>
                <p>Dynamically query any SQL database and document set with natural language.</p>
            </header>
            <main>
                {!isDbConnected ? (
                    <DatabaseConnector onConnect={handleDbConnection} />
                ) : (
                    <>
                        <DocumentUploader />
                        <QueryPanel onQuerySubmit={handleQuerySubmit} isLoading={isLoading} />
                        {error && <div className="error-message card">{error}</div>}
                        {isLoading && <div className="loading-spinner card">Loading results...</div>}
                        {queryResults && <ResultsView data={queryResults} />}
                    </>
                )}
            </main>
        </div>
    );
}

export default App;
