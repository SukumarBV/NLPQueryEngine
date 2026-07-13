import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import API_BASE_URL from '../config';

const ACCEPTED_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
    'text/csv': ['.csv'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
};

const STRUCTURED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];
const DOC_ONLY_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
};

const isStructured = (filename) =>
    STRUCTURED_EXTENSIONS.some((ext) => filename.toLowerCase().endsWith(ext));

const DocumentUploader = ({ onBack, onReady, allowStructured = true, title = '📁 Upload Files' }) => {
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const [processingStatus, setProcessingStatus] = useState('');
    const [isUploading, setIsUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        const usable = allowStructured
            ? acceptedFiles
            : acceptedFiles.filter((f) => !isStructured(f.name));
        setFiles((prevFiles) => [...prevFiles, ...usable]);
    }, [allowStructured]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: allowStructured ? ACCEPTED_TYPES : DOC_ONLY_TYPES,
    });

    const removeFile = (indexToRemove) => {
        setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
    };

    const structuredFiles = files.filter((f) => isStructured(f.name));
    const documentFiles = files.filter((f) => !isStructured(f.name));

    const handleUpload = async () => {
        if (files.length === 0) {
            setUploadStatus('Please select files to upload.');
            return;
        }

        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });

        setIsUploading(true);
        setUploadStatus('Uploading...');
        setProcessingStatus('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/upload-documents`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            if (response.ok) {
                setUploadStatus(`Upload successful! Processing ${files.length} file(s)...`);
                setFiles([]);
                pollProcessingStatus(data.job_id);
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (error) {
            setUploadStatus(`Error: ${error.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const pollProcessingStatus = (currentJobId) => {
        setProcessingStatus('Processing...');
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/ingestion-status/${currentJobId}`);
                const data = await response.json();

                if (data.status === 'Complete') {
                    setProcessingStatus('All files processed and indexed successfully.');
                    clearInterval(interval);
                    onReady && onReady();
                } else if (typeof data.status === 'string' && data.status.startsWith('Failed')) {
                    setProcessingStatus(`${data.status} (any files that did succeed are still queryable.)`);
                    clearInterval(interval);
                    onReady && onReady();
                } else {
                    setProcessingStatus(`Status: ${data.status}`);
                }
            } catch (error) {
                setProcessingStatus('Could not get processing status.');
                clearInterval(interval);
            }
        }, 3000);
    };

    return (
        <div className="card">
            {onBack && <button className="back-link" onClick={onBack}>&larr; Choose a different data source</button>}
            <h2>{title}</h2>
            {allowStructured ? (
                <p>Drag &amp; drop PDFs, Word documents, CSVs or Excel spreadsheets — no database required.</p>
            ) : (
                <p>Add supporting documents (PDF, DOCX, TXT) to search alongside your connected data.</p>
            )}
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <p>
                    Drag 'n' drop files here, or click to select files
                    {allowStructured ? ' (PDF, DOCX, TXT, CSV, XLSX)' : ' (PDF, DOCX, TXT)'}
                </p>
            </div>
            {files.length > 0 && allowStructured && (
                <div className="upload-groups">
                    <div>
                        <h5>Structured Data</h5>
                        {structuredFiles.length === 0 && <p style={{ fontSize: 13, color: '#999' }}>None selected</p>}
                        <ul>
                            {structuredFiles.map((file) => {
                                const index = files.indexOf(file);
                                return (
                                    <li key={`${file.name}-${index}`}>
                                        <span>{file.name}</span>
                                        <button type="button" onClick={() => removeFile(index)}>Remove</button>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                    <div>
                        <h5>Documents</h5>
                        {documentFiles.length === 0 && <p style={{ fontSize: 13, color: '#999' }}>None selected</p>}
                        <ul>
                            {documentFiles.map((file) => {
                                const index = files.indexOf(file);
                                return (
                                    <li key={`${file.name}-${index}`}>
                                        <span>{file.name}</span>
                                        <button type="button" onClick={() => removeFile(index)}>Remove</button>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                </div>
            )}
            {files.length > 0 && !allowStructured && (
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {files.map((file, index) => (
                        <li key={`${file.name}-${index}`} style={{ background: '#f7f9fc', border: '1px solid #e5e9f0', borderRadius: 6, padding: '8px 10px', marginBottom: 6, fontSize: 13, display: 'flex', justifyContent: 'space-between' }}>
                            <span>{file.name}</span>
                            <button type="button" onClick={() => removeFile(index)}>Remove</button>
                        </li>
                    ))}
                </ul>
            )}
            <button onClick={handleUpload} disabled={isUploading || files.length === 0} style={{ marginTop: 12 }}>
                {isUploading ? 'Uploading...' : 'Upload and Process'}
            </button>
            {uploadStatus && <p>{uploadStatus}</p>}
            {processingStatus && <p>{processingStatus}</p>}
        </div>
    );
};

export default DocumentUploader;
