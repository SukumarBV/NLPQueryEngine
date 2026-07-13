import React, { useState } from 'react';
import DataSourceSelector from './components/DataSourceSelector';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';
import API_BASE_URL from './config';
import './App.css';

const SOURCE_LABELS = {
    postgres: 'PostgreSQL',
    uploads: 'Uploaded Files',
    demo: 'Demo Database',
};

const DemoSchemaCard = ({ schema }) => {
    const tables = schema?.tables || [];
    return (
        <div className="card">
            <h2>🚀 Demo Database</h2>
            <p>You're exploring a preloaded sample dataset — no setup needed. Here's what's inside:</p>
            <div className="demo-schema-grid">
                {tables.map((table) => (
                    <div className="demo-schema-table" key={table.name}>
                        <h5>{table.name}</h5>
                        <ul>
                            {table.columns.map((col) => (
                                <li key={col.name}>
                                    <span>{col.name}</span>
                                    <span className="demo-schema-type">{col.type}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
};

function App() {
    const [landingMode, setLandingMode] = useState(null); // null | 'postgres' | 'upload' | 'demo'
    const [demoLoading, setDemoLoading] = useState(false);
    const [isReady, setIsReady] = useState(false);
    const [activeStatus, setActiveStatus] = useState(null);

    const [queryResults, setQueryResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const refreshStatus = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/datasource/status`);
            const data = await response.json();
            setActiveStatus(data);
        } catch {
            // Non-fatal: the UI can still function without the status banner.
        }
    };

    const handleSelectMode = async (mode) => {
        setError('');
        if (mode === 'demo') {
            setDemoLoading(true);
            try {
                const response = await fetch(`${API_BASE_URL}/api/datasource/demo`, { method: 'POST' });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Failed to load the demo dataset.');
                setActiveStatus(data);
                setLandingMode('demo');
                setIsReady(true);
            } catch (err) {
                setError(err.message);
            } finally {
                setDemoLoading(false);
            }
            return;
        }
        setLandingMode(mode);
    };

    const handlePostgresConnected = (data) => {
        setActiveStatus(data);
        setIsReady(true);
    };

    const handleUploadReady = () => {
        refreshStatus();
        setIsReady(true);
    };

    const handleChangeSource = async () => {
        try {
            await fetch(`${API_BASE_URL}/api/datasource/reset`, { method: 'POST' });
        } catch {
            // Best-effort; still reset the UI locally either way.
        }
        setLandingMode(null);
        setIsReady(false);
        setActiveStatus(null);
        setQueryResults(null);
        setError('');
    };

    const handleQuerySubmit = async (query) => {
        setIsLoading(true);
        setError('');
        setQueryResults(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/query`, {
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

    const sourceLabel = activeStatus?.label || SOURCE_LABELS[activeStatus?.mode] || 'Unknown';

    return (
        <div className="App">
            <header className="App-header">
                <h1>AI-Powered NLP Query Engine</h1>
                <p>Dynamically query any SQL database and document set with natural language.</p>
            </header>
            <main>
                {!landingMode && (
                    <DataSourceSelector onSelectMode={handleSelectMode} loadingMode={demoLoading ? 'demo' : null} />
                )}

                {landingMode === 'postgres' && !isReady && (
                    <DatabaseConnector onConnect={handlePostgresConnected} onBack={() => setLandingMode(null)} />
                )}

                {landingMode === 'upload' && !isReady && (
                    <DocumentUploader onBack={() => setLandingMode(null)} onReady={handleUploadReady} allowStructured />
                )}

                {error && <div className="error-message card">{error}</div>}

                {isReady && (
                    <>
                        <div className="source-banner">
                            <span>
                                Current datasource: <strong>{sourceLabel}</strong>
                            </span>
                            <button onClick={handleChangeSource}>Change data source</button>
                        </div>

                        {landingMode === 'upload' ? (
                            <DocumentUploader onReady={handleUploadReady} allowStructured title="📁 Upload More Files" />
                        ) : landingMode === 'demo' ? (
                            <DemoSchemaCard schema={activeStatus?.schema} />
                        ) : (
                            <DocumentUploader
                                onReady={handleUploadReady}
                                allowStructured={false}
                                title="📎 Add Supporting Documents (Optional)"
                            />
                        )}

                        <QueryPanel onQuerySubmit={handleQuerySubmit} isLoading={isLoading} />
                        {isLoading && <div className="loading-spinner card">Loading results...</div>}
                        {queryResults && <ResultsView data={queryResults} />}
                    </>
                )}
            </main>
        </div>
    );
}

export default App;
