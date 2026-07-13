import React from 'react';

const CARDS = [
    {
        mode: 'postgres',
        icon: '🗄',
        title: 'Connect PostgreSQL',
        description: 'Connect your own PostgreSQL database for AI-powered SQL querying.',
        button: 'Connect Database',
        className: 'postgres',
    },
    {
        mode: 'upload',
        icon: '📁',
        title: 'Upload Files',
        description: 'Upload PDFs, Word documents, CSVs or Excel spreadsheets.',
        button: 'Upload Files',
        className: 'upload',
        formats: ['PDF', 'DOCX', 'TXT', 'CSV', 'XLSX'],
    },
    {
        mode: 'demo',
        icon: '🚀',
        title: 'Try Demo',
        description: 'Instantly explore the app using a preloaded sample database.',
        button: 'Use Demo',
        className: 'demo',
    },
];

const DataSourceSelector = ({ onSelectMode, loadingMode }) => {
    return (
        <div className="datasource-selector">
            <h2 style={{ textAlign: 'center' }}>Choose Your Data Source</h2>
            <p className="selector-intro">
                Connect a live database, upload your own files, or jump straight into a sample dataset with no setup required.
            </p>
            <div className="datasource-grid">
                {CARDS.map((card) => (
                    <div key={card.mode} className={`datasource-card ${card.className}`}>
                        <div className="datasource-card-icon">{card.icon}</div>
                        <h3>{card.title}</h3>
                        <p>{card.description}</p>
                        {card.formats && (
                            <ul className="formats">
                                {card.formats.map((f) => (
                                    <li key={f}>{f}</li>
                                ))}
                            </ul>
                        )}
                        <button onClick={() => onSelectMode(card.mode)} disabled={!!loadingMode}>
                            {loadingMode === card.mode ? 'Loading...' : card.button}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DataSourceSelector;
