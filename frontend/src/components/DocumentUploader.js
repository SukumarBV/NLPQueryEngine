import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import API_BASE_URL from '../config';

const ACCEPTED_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
};

const DocumentUploader = () => {
    const [files, setFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const [processingStatus, setProcessingStatus] = useState('');
    const [isUploading, setIsUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        setFiles((prevFiles) => [...prevFiles, ...acceptedFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: ACCEPTED_TYPES,
    });

    const removeFile = (indexToRemove) => {
        setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
    };

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
                setUploadStatus(`Upload successful! Processing job ID: ${data.job_id}`);
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
                    setProcessingStatus('All documents processed and indexed successfully.');
                    clearInterval(interval);
                } else if (typeof data.status === 'string' && data.status.startsWith('Failed')) {
                    setProcessingStatus(data.status);
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
            {files.length > 0 && (
                <aside>
                    <h4>Selected Files:</h4>
                    <ul>
                        {files.map((file, index) => (
                            <li key={`${file.name}-${index}`}>
                                {file.name} - {file.size} bytes{' '}
                                <button type="button" onClick={() => removeFile(index)}>
                                    Remove
                                </button>
                            </li>
                        ))}
                    </ul>
                </aside>
            )}
            <button onClick={handleUpload} disabled={isUploading}>
                {isUploading ? 'Uploading...' : 'Upload and Process'}
            </button>
            {uploadStatus && <p>{uploadStatus}</p>}
            {processingStatus && <p>{processingStatus}</p>}
        </div>
    );
};

export default DocumentUploader;
