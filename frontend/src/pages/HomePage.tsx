import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useAuthStore } from '../store/authStore';
import documentService from '../services/documentService';
import type { DocumentStats } from '../types/document';

/**
 * Home Page Component
 * 
 * Modern dashboard with hero section, features, and upload area
 */
const HomePage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string[]>([]);

  // Fetch document stats on mount
  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await documentService.getDocumentStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    // Validate file types and sizes
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'image/png',
      'image/jpeg',
      'image/jpg'
    ];

    const invalidFiles = acceptedFiles.filter(file => !allowedTypes.includes(file.type));
    const oversizedFiles = acceptedFiles.filter(file => file.size > 10 * 1024 * 1024);

    if (invalidFiles.length > 0) {
      setUploadError(`Invalid file type(s): ${invalidFiles.map(f => f.name).join(', ')}`);
      return;
    }

    if (oversizedFiles.length > 0) {
      setUploadError(`File(s) too large (max 10MB): ${oversizedFiles.map(f => f.name).join(', ')}`);
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess([]);
    setUploadProgress({});

    const successfulUploads: string[] = [];
    const failedUploads: string[] = [];

    // Upload files sequentially
    for (const file of acceptedFiles) {
      try {
        const response = await documentService.uploadDocument(file, (percentage) => {
          setUploadProgress(prev => ({ ...prev, [file.name]: percentage }));
        });

        successfulUploads.push(file.name);
        setUploadSuccess(prev => [...prev, file.name]);
      } catch (error: any) {
        failedUploads.push(file.name);
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }

    // Refresh stats
    await fetchStats();

    // Show error if any uploads failed
    if (failedUploads.length > 0) {
      setUploadError(`Failed to upload: ${failedUploads.join(', ')}`);
    }

    // Clear messages after 5 seconds
    setTimeout(() => {
      setUploadSuccess([]);
      setUploadProgress({});
      setUploadError(null);
    }, 5000);

    setIsUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    multiple: true,
    disabled: isUploading,
  });

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 p-12 text-white shadow-2xl">
        {/* Animated Background Blobs */}
        <div className="absolute top-0 -right-4 w-64 h-64 bg-white/10 rounded-full mix-blend-overlay filter blur-3xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-8 -left-4 w-64 h-64 bg-white/10 rounded-full mix-blend-overlay filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
        
        <div className="relative z-10">
          <h1 className="text-5xl font-bold mb-4 animate-fade-in">
            Welcome back, {user?.full_name || user?.username}! 👋
          </h1>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl">
            Transform your documents into insights with AI-powered analysis. Upload, analyze, and chat with your documents like never before.
          </p>
          
          <div className="flex gap-4">
            <button 
              {...getRootProps()}
              disabled={isUploading}
              className="bg-white text-blue-600 px-6 py-3 rounded-xl font-semibold hover:bg-blue-50 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <input {...getInputProps()} />
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {isUploading ? 'Uploading...' : 'Upload Documents'}
              </span>
            </button>
            <button 
              onClick={() => navigate('/documents')}
              className="bg-white/10 backdrop-blur-sm border-2 border-white/20 text-white px-6 py-3 rounded-xl font-semibold hover:bg-white/20 transition-all duration-200"
            >
              View Gallery
            </button>
          </div>

          {/* Upload Feedback */}
          {uploadError && (
            <div className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-white">
              <p className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {uploadError}
              </p>
            </div>
          )}
          {uploadSuccess.length > 0 && (
            <div className="mt-4 p-4 bg-green-500/20 border border-green-500/50 rounded-lg text-white">
              <p className="flex items-center gap-2 font-semibold mb-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Successfully uploaded {uploadSuccess.length} file(s)
              </p>
              <ul className="ml-7 text-sm space-y-1">
                {uploadSuccess.map((filename, idx) => (
                  <li key={idx}>✓ {filename}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-2xl border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {stats?.total_documents ?? 0}
          </div>
          <div className="text-sm text-gray-600">Documents</div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-2xl border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {stats?.by_status.completed ?? 0}
          </div>
          <div className="text-sm text-gray-600">Analyzed</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-2xl border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">0</div>
          <div className="text-sm text-gray-600">Queries</div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-2xl border border-orange-200">
          <div className="flex items-center justify-between mb-2">
            <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {stats?.total_size_mb.toFixed(2) ?? '0.00'} MB
          </div>
          <div className="text-sm text-gray-600">Storage</div>
        </div>
      </div>

      {/* Features Section */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Powerful Features
          </span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="group bg-white p-8 rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-blue-200 hover:-translate-y-1">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Smart Upload</h3>
            <p className="text-gray-600 leading-relaxed">
              Upload documents in various formats (PDF, Word, Excel) with drag-and-drop support and automatic processing.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="group bg-white p-8 rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-purple-200 hover:-translate-y-1">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">AI Analysis</h3>
            <p className="text-gray-600 leading-relaxed">
              Powered by advanced AI to extract insights, summarize content, and identify key information automatically.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="group bg-white p-8 rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-green-200 hover:-translate-y-1">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Interactive Chat</h3>
            <p className="text-gray-600 leading-relaxed">
              Ask questions about your documents and get instant, accurate answers using natural language queries.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Upload Section */}
      <div 
        {...getRootProps()}
        className={`bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-8 border-2 border-dashed transition-colors duration-300 ${
          isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-400'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <input {...getInputProps()} />
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white mx-auto mb-4 shadow-lg">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            {isDragActive ? 'Drop your files here!' : 'Ready to get started?'}
          </h3>
          <p className="text-gray-600 mb-6">
            {isUploading 
              ? `Uploading ${Object.keys(uploadProgress).length} file(s)...` 
              : 'Drag and drop your documents here or click to browse'}
          </p>
          {isUploading && Object.keys(uploadProgress).length > 0 && (
            <div className="w-full max-w-md mx-auto mb-4 space-y-2">
              {Object.entries(uploadProgress).map(([filename, progress]) => (
                <div key={filename} className="text-sm">
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-700 truncate max-w-xs">{filename}</span>
                    <span className="text-gray-600">{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {!isUploading && (
            <button 
              type="button"
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Choose Files
            </button>
          )}
          <p className="text-sm text-gray-500 mt-4">
            Supports PDF, DOCX, XLSX, TXT, PNG, JPG (Max 10MB)
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

