import React, { useState } from 'react';
import API_BASE_URL from '../config';

const DatabaseConnector = ({ onConnect, onBack }) => {
    const [connectionString, setConnectionString] = useState('');
    const [status, setStatus] = useState({ message: 'Not connected.', color: 'gray' });
    const [schema, setSchema] = useState(null);
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnect = async () => {
        if (!connectionString.trim()) {
            setStatus({ message: 'Please enter a connection string.', color: 'red' });
            return;
        }

        setIsConnecting(true);
        setStatus({ message: 'Connecting and analyzing schema...', color: 'orange' });
        setSchema(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/datasource/postgres`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connection_string: connectionString }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to connect to the database.');
            }

            setStatus({ message: 'Connected! Ready to query.', color: 'green' });
            setSchema(data.schema);
            onConnect(data);
        } catch (error) {
            setStatus({ message: `Error: ${error.message}`, color: 'red' });
        } finally {
            setIsConnecting(false);
        }
    };

    return (
        <div className="card">
            <button className="back-link" onClick={onBack}>&larr; Choose a different data source</button>
            <h2>🗄 Connect to PostgreSQL</h2>
            <p>Enter your PostgreSQL connection string to begin.</p>
            <div className="connector-input">
                <input
                    type="text"
                    value={connectionString}
                    onChange={(e) => setConnectionString(e.target.value)}
                    placeholder="postgresql://user:pass@host:port/dbname"
                    disabled={isConnecting}
                />
                <button onClick={handleConnect} disabled={isConnecting}>
                    {isConnecting ? 'Connecting...' : 'Connect & Analyze'}
                </button>
            </div>
            {status.message && <p style={{ color: status.color, marginTop: '10px' }}>Status: {status.message}</p>}

            {schema && (
                <div className="schema-view">
                    <h4>Discovered Schema:</h4>
                    <pre>{JSON.stringify(schema, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default DatabaseConnector;
