import React, { useState } from 'react';

const DatabaseConnector = ({ onConnect }) => {
    const [connectionString, setConnectionString] = useState('postgresql://user:pass@db:5432/company_db');
    const [status, setStatus] = useState({ message: 'Not connected.', color: 'gray' });
    const [schema, setSchema] = useState(null);
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnect = async () => {
        setIsConnecting(true);
        setStatus({ message: 'Connecting and analyzing...', color: 'orange' });
        setSchema(null);

        try {
            // Step 1: Connect to the database and discover the schema
            const connectResponse = await fetch('http://localhost:8000/api/connect-database', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connection_string: connectionString }),
            });

            const connectData = await connectResponse.json();
            if (!connectResponse.ok) {
                throw new Error(connectData.detail || 'Failed to connect to the database.');
            }

            setStatus({ message: 'Database connected! Discovering schema...', color: 'blue' });
            setSchema(connectData);

            // Step 2: Initialize the query engine on the backend with the connection string
            const initResponse = await fetch('http://localhost:8000/api/initialize-engine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connection_string: connectionString }),
            });

            if (!initResponse.ok) {
                 const initErrorData = await initResponse.json();
                throw new Error(initErrorData.detail || 'Failed to initialize query engine.');
            }

            setStatus({ message: 'Connection successful! Ready to query.', color: 'green' });
            onConnect(connectData); // Notify parent component

        } catch (error) {
            setStatus({ message: `Error: ${error.message}`, color: 'red' });
        } finally {
            setIsConnecting(false);
        }
    };

    return (
        <div className="card">
            <h2>1. Connect to Database</h2>
            <p>Enter your database connection string to begin.</p>
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
            
            {/* Schema Visualization */}
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