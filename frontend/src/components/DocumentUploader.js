import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const DocumentUploader = () => {
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const [jobId, setJobId] = useState(null);
    const [processingStatus, setProcessingStatus] = useState('');

    const onDrop = useCallback(acceptedFiles => {
        setFiles(prevFiles => [...prevFiles, ...acceptedFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: 'application/pdf,.docx,.txt,.csv' });

    const handleUpload = async () => {
        if (files.length === 0) {
            setUploadStatus('Please select files to upload.');
            return;
        }

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        setUploadStatus('Uploading...');
        try {
            const response = await fetch('http://localhost:8000/api/upload-documents', {
                method: 'POST',
                body: formData,
            });
            
            const data = await response.json();
            if (response.ok) {
                setUploadStatus(`Upload successful! Processing job ID: ${data.job_id}`);
                setJobId(data.job_id);
                pollProcessingStatus(data.job_id);
            } else {
                throw new Error(data.detail || 'Upload failed');
            }

        } catch (error) {
            setUploadStatus(`Error: ${error.message}`);
        }
    };

    const pollProcessingStatus = async (currentJobId) => {
        setProcessingStatus('Processing...');
        // In a real app, you might use WebSockets, but polling is sufficient per requirements.
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/ingestion-status/${currentJobId}`);
                const data = await response.json();
                if (data.status === 'Complete') { // This logic depends on backend status updates
                    setProcessingStatus('All documents processed and indexed successfully.');
                    clearInterval(interval);
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
            <h2>2. Upload Documents (Optional)</h2>
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <p>Drag 'n' drop files here, or click to select files (PDF, DOCX, TXT)</p>
            </div>
            <aside>
                <h4>Selected Files:</h4>
                <ul>{files.map(file => <li key={file.path}>{file.path} - {file.size} bytes</li>)}</ul>
            </aside>
            <button onClick={handleUpload}>Upload and Process</button>
            {uploadStatus && <p>{uploadStatus}</p>}
            {processingStatus && <p>{processingStatus}</p>}
        </div>
    );
};

export default DocumentUploader;