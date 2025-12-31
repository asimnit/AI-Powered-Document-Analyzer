import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useStoreStore } from '../store/storeStore';
import storeService from '../services/storeService';
import documentService from '../services/documentService';
import type { Document, ProcessingStatus } from '../types/document';
import type { SearchResultItem } from '../types/store';
import { useWebSocket } from '../hooks/useWebSocket';

/**
 * Store View Page Component
 * 
 * Complete document management within a store with all features:
 * - Upload with validation and progress
 * - Real-time WebSocket updates
 * - Individual document actions (process, retry, download, delete)
 * - Bulk operations (process all, retry failed)
 * - Search and filter
 * - Grid layout with file type icons
 */

// Helper function to convert error details to string
const getErrorMessage = (err: any, defaultMessage: string): string => {
  const detail = err.response?.data?.detail;
  
  if (Array.isArray(detail)) {
    return detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
  }
  
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  
  return detail || defaultMessage;
};

const StoreViewPage: React.FC = () => {
  const { storeId } = useParams<{ storeId: string }>();
  const navigate = useNavigate();
  const { currentStore, fetchStoreById } = useStoreStore();
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<ProcessingStatus | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; documentId: number | null }>({ show: false, documentId: null });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [isProcessingAll, setIsProcessingAll] = useState(false);
  const [isRetryingAll, setIsRetryingAll] = useState(false);
  const [isRetryingIndexing, setIsRetryingIndexing] = useState(false);
  
  // Semantic search states
  const [semanticQuery, setSemanticQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  // WebSocket connection for real-time updates
  const handleDocumentUpdate = useCallback((update: any) => {
    console.log('Document update received:', update);
    console.log('Update status:', update.status, 'Message:', update.message);
    
    setDocuments((prevDocuments) => 
      prevDocuments.map((doc) => {
        if (doc.id === update.document_id) {
          console.log('Updating document:', doc.id, 'Old status:', doc.status, 'New status:', update.status);
          
          const updatedDoc = {
            ...doc,
            status: update.status as ProcessingStatus,
            error_message: update.message || doc.error_message
          };
          
          console.log('Updated doc:', updatedDoc);
          return updatedDoc;
        }
        return doc;
      })
    );
  }, []);

  const { isConnected } = useWebSocket(handleDocumentUpdate);

  useEffect(() => {
    if (storeId) {
      fetchStoreById(parseInt(storeId));
      loadDocuments();
    }
  }, [storeId, page, statusFilter, searchQuery]);

  const loadDocuments = async () => {
    if (!storeId) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await storeService.getStoreDocuments(
        parseInt(storeId),
        page,
        12,
        statusFilter,
        searchQuery || undefined
      );
      setDocuments(response.documents);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to load documents'));
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!storeId || acceptedFiles.length === 0) return;

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
        await documentService.uploadDocument(
          file,
          (percentage) => {
            setUploadProgress(prev => ({ ...prev, [file.name]: percentage }));
          },
          parseInt(storeId)
        );

        successfulUploads.push(file.name);
        setUploadSuccess(prev => [...prev, file.name]);
      } catch (error: any) {
        failedUploads.push(file.name);
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }

    // Refresh documents list
    await loadDocuments();

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
  }, [storeId]);

  const { getInputProps, open } = useDropzone({
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
    noClick: true,
    noKeyboard: true,
  });

  const handleProcessAll = async () => {
    if (!storeId || isProcessingAll) return;
    setError(null);
    setInfoMessage(null);
    setSuccessMessage(null);
    setIsProcessingAll(true);
    try {
      const response = await storeService.processAllDocuments(parseInt(storeId));
      console.log('Process all response:', response);
      if (response.documents_queued > 0) {
        setSuccessMessage(response.message);
        setTimeout(() => setSuccessMessage(null), 5000);
      } else {
        setInfoMessage(response.message);
        setTimeout(() => setInfoMessage(null), 5000);
      }
      await loadDocuments();
    } catch (err: any) {
      const errorMsg = getErrorMessage(err, 'Failed to start processing');
      console.error('Process all error:', errorMsg, err);
      setError(errorMsg);
    } finally {
      setIsProcessingAll(false);
    }
  };

  const handleRetryAll = async () => {
    if (!storeId || isRetryingAll) return;
    setError(null);
    setInfoMessage(null);
    setSuccessMessage(null);
    setIsRetryingAll(true);
    try {
      const response = await storeService.retryAllFailed(parseInt(storeId));
      console.log('Retry all response:', response);
      if (response.documents_queued > 0) {
        setSuccessMessage(response.message);
        setTimeout(() => setSuccessMessage(null), 5000);
      } else {
        setInfoMessage(response.message);
        setTimeout(() => setInfoMessage(null), 5000);
      }
      await loadDocuments();
    } catch (err: any) {
      const errorMsg = getErrorMessage(err, 'Failed to start retry');
      console.error('Retry all error:', errorMsg, err);
      setError(errorMsg);
    } finally {
      setIsRetryingAll(false);
    }
  };

  const handleRetryAllIndexing = async () => {
    if (!storeId || isRetryingIndexing) return;
    setError(null);
    setInfoMessage(null);
    setSuccessMessage(null);
    setIsRetryingIndexing(true);
    try {
      const response = await storeService.retryAllIndexing(parseInt(storeId));
      console.log('Retry all indexing response:', response);
      if (response.documents_queued > 0) {
        setSuccessMessage(response.message);
        setTimeout(() => setSuccessMessage(null), 5000);
      } else {
        setInfoMessage(response.message);
        setTimeout(() => setInfoMessage(null), 5000);
      }
      await loadDocuments();
    } catch (err: any) {
      const errorMsg = getErrorMessage(err, 'Failed to start indexing retry');
      console.error('Retry all indexing error:', errorMsg, err);
      setError(errorMsg);
    } finally {
      setIsRetryingIndexing(false);
    }
  };

  const handleProcess = async (id: number) => {
    try {
      await documentService.processDocument(id);
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to start processing'));
    }
  };

  const handleRetryIndexing = async (id: number) => {
    try {
      await documentService.retryIndexing(id);
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to retry indexing'));
    }
  };

  const handleDownload = async (id: number, filename: string) => {
    try {
      await documentService.downloadDocument(id, filename);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to download document'));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await documentService.deleteDocument(id);
      setDeleteConfirm({ show: false, documentId: null });
      await loadDocuments();
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to delete document'));
    }
  };

  const handleSemanticSearch = async () => {
    if (!storeId || !semanticQuery.trim()) return;
    
    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await storeService.searchInStore(parseInt(storeId), semanticQuery.trim(), 5);
      setSearchResults(response.results);
      setShowSearchResults(true);
      console.log('Search results:', response);
    } catch (err: any) {
      const errorMsg = getErrorMessage(err, 'Search failed');
      setSearchError(errorMsg);
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSemanticQuery('');
    setSearchResults([]);
    setShowSearchResults(false);
    setSearchError(null);
    setExpandedChunks(new Set());
  };

  const toggleChunkExpansion = (chunkId: number) => {
    setExpandedChunks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  };

  const getStatusColor = (status: ProcessingStatus) => {
    switch (status) {
      case 'completed':
      case 'indexed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'processing':
      case 'indexing':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed':
      case 'indexing_failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'partially_indexed':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getFileIcon = (filename: string) => {
    const lower = filename.toLowerCase();
    
    if (lower.endsWith('.pdf')) {
      return (
        <svg className="w-16 h-16 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (lower.endsWith('.docx') || lower.endsWith('.doc')) {
      return (
        <svg className="w-16 h-16 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (lower.endsWith('.xlsx') || lower.endsWith('.xls')) {
      return (
        <svg className="w-16 h-16 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg')) {
      return (
        <svg className="w-16 h-16 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
        </svg>
      );
    } else if (lower.endsWith('.txt')) {
      return (
        <svg className="w-16 h-16 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    return (
      <svg className="w-16 h-16 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  };

  if (!currentStore && !loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Store Not Found</h2>
          <button onClick={() => navigate('/stores')} className="text-blue-600 hover:underline">
            ← Back to Stores
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <input {...getInputProps()} />
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/stores')}
            className="text-blue-600 hover:text-blue-800 mb-2 flex items-center gap-1 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Stores
          </button>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {currentStore?.name || 'Loading...'}
            </span>
          </h1>
          {currentStore?.description && (
            <p className="text-gray-600 mt-1">{currentStore.description}</p>
          )}
        </div>
        
        <button
          onClick={open}
          disabled={isUploading}
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {isUploading ? 'Uploading...' : 'Upload New'}
        </button>
      </div>

      {/* Upload Feedback */}
      {uploadError && (
        <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {uploadError}
        </div>
      )}
      {uploadSuccess.length > 0 && (
        <div className="bg-green-50 border border-green-300 text-green-800 px-4 py-3 rounded-lg">
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
      {successMessage && (
        <div className="bg-green-50 border border-green-300 text-green-800 px-4 py-3 rounded-lg">
          <p className="flex items-center gap-2 font-semibold">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {successMessage}
          </p>
        </div>
      )}
      {isUploading && Object.keys(uploadProgress).length > 0 && (
        <div className="bg-blue-50 border border-blue-300 text-blue-800 px-4 py-3 rounded-lg">
          <p className="font-semibold mb-2">Uploading files...</p>
          <div className="space-y-2">
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="truncate max-w-xs">{filename}</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bulk Actions & Filters */}
      <div className="bg-white rounded-xl shadow-md p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-semibold text-gray-700">Actions & Filters</h3>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 text-xs ${isConnected ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`}></div>
              {isConnected ? 'Live updates' : 'Reconnecting...'}
            </div>
          </div>
        </div>
        
        {/* Bulk Action Buttons */}
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={handleProcessAll}
            disabled={isProcessingAll}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessingAll ? (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {isProcessingAll ? 'Processing...' : 'Process All Uploaded'}
          </button>
          <button
            onClick={handleRetryAll}
            disabled={isRetryingAll}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRetryingAll ? (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {isRetryingAll ? 'Retrying...' : 'Retry All Failed'}
          </button>
          <button
            onClick={handleRetryAllIndexing}
            disabled={isRetryingIndexing}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRetryingIndexing ? (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {isRetryingIndexing ? 'Retrying...' : 'Retry All Indexing'}
          </button>
        </div>

        {/* Semantic Search Section */}
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="text-sm font-bold text-gray-800">Semantic Search</h3>
            <span className="text-xs text-gray-500">Search by meaning across all documents</span>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ask a question or search by meaning... (e.g., 'What is the summary?')"
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSemanticSearch()}
              className="flex-1 px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              disabled={isSearching}
            />
            <button
              onClick={handleSemanticSearch}
              disabled={isSearching || !semanticQuery.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSearching ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Searching...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Search
                </>
              )}
            </button>
            {showSearchResults && (
              <button
                onClick={handleClearSearch}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
              >
                Clear
              </button>
            )}
          </div>
          {searchError && (
            <div className="mt-2 text-sm text-red-600 flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {searchError}
            </div>
          )}
        </div>

        {/* Search Results Display */}
        {showSearchResults && searchResults.length > 0 && (
          <div className="mb-4 p-4 bg-white rounded-lg border-2 border-blue-200 shadow-md">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Search Results ({searchResults.length})
              </h3>
              <span className="text-sm text-gray-500">Query: "{semanticQuery}"</span>
            </div>
            <div className="space-y-3">
              {searchResults.map((result, index) => (
                <div 
                  key={result.chunk_id}
                  className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100 hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-1 bg-blue-600 text-white text-xs font-bold rounded"># {index + 1}</span>
                        <span className="font-semibold text-gray-800">{result.document_filename}</span>
                        {result.page_numbers.length > 0 && (
                          <span className="text-xs text-gray-500">
                            (Page {result.page_numbers.join(', ')})
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <span>Chunk {result.chunk_index + 1}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          {(result.similarity_score * 100).toFixed(1)}% match
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className={`text-sm text-gray-700 leading-relaxed ${expandedChunks.has(result.chunk_id) ? '' : 'line-clamp-3'}`}>
                    {result.chunk_content}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => toggleChunkExpansion(result.chunk_id)}
                      className="text-xs text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                    >
                      {expandedChunks.has(result.chunk_id) ? (
                        <>
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                          </svg>
                          Show less
                        </>
                      ) : (
                        <>
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                          Expand
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleDownload(result.document_id, result.document_filename)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                    >
                      Download document
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {showSearchResults && searchResults.length === 0 && !isSearching && (
          <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200 text-center">
            <p className="text-yellow-800">No results found for "{semanticQuery}". Try rephrasing your query.</p>
          </div>
        )}

        {/* Search */}
        <div className="mb-3">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>

        {/* Status Filter Pills */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setStatusFilter(undefined)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
              statusFilter === undefined
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setStatusFilter('uploaded' as ProcessingStatus)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
              statusFilter === 'uploaded'
                ? 'bg-gray-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Uploaded
          </button>
          <button
            onClick={() => setStatusFilter('processing' as ProcessingStatus)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
              statusFilter === 'processing'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Processing
          </button>
          <button
            onClick={() => setStatusFilter('completed' as ProcessingStatus)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
              statusFilter === 'completed'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setStatusFilter('failed' as ProcessingStatus)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
              statusFilter === 'failed'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Failed
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Info Message */}
      {infoMessage && (
        <div className="bg-blue-50 border border-blue-300 text-blue-800 px-4 py-3 rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {infoMessage}
        </div>
      )}

      {/* Documents Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No documents found</h3>
          <p className="text-gray-600 mb-4">Start by uploading your first document to this store</p>
          <button
            onClick={open}
            disabled={isUploading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {documents.map((doc) => (
            <div key={doc.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
              {/* Delete Confirmation Modal */}
              {deleteConfirm.documentId === doc.id && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10 rounded-xl">
                  <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm mx-4">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">Confirm Delete</h3>
                    <p className="text-gray-600 mb-4">
                      Are you sure you want to delete "{doc.filename}"? This action cannot be undone.
                    </p>
                    <div className="flex gap-3 justify-end">
                      <button
                        onClick={() => setDeleteConfirm({ show: false, documentId: null })}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Card Content */}
              <div className="p-5">
                {/* File Icon */}
                <div className="flex items-center justify-center w-16 h-16 mb-4 mx-auto">
                  {getFileIcon(doc.filename)}
                </div>

                {/* Filename */}
                <h3 className="text-sm font-semibold text-gray-900 mb-2 text-center truncate" title={doc.filename}>
                  {doc.filename}
                </h3>

                {/* Status Badge */}
                <div className="flex justify-center mb-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                    {doc.status.toUpperCase()}
                  </span>
                </div>

                {/* Error Message */}
                {doc.error_message && (
                  <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-xs text-red-700 text-center break-words">{doc.error_message}</p>
                  </div>
                )}

                {/* Document Info */}
                <div className="flex justify-between text-xs text-gray-500 mb-4 pb-4 border-b border-gray-100">
                  <span>{doc.file_size_mb.toFixed(2)} MB</span>
                  <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 justify-center">
                  {doc.status === 'uploaded' && (
                    <button
                      onClick={() => handleProcess(doc.id)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
                      title="Process document"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Process</span>
                    </button>
                  )}

                  {doc.status === 'failed' && (
                    <button
                      onClick={() => handleProcess(doc.id)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white text-xs rounded-lg hover:bg-yellow-700 transition-colors"
                      title="Retry processing"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>Retry</span>
                    </button>
                  )}

                  {(doc.status === 'indexing_failed' || doc.status === 'partially_indexed') && (
                    <button
                      onClick={() => handleRetryIndexing(doc.id)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white text-xs rounded-lg hover:bg-yellow-700 transition-colors"
                      title="Retry generating embeddings"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>Retry Indexing</span>
                    </button>
                  )}

                  <button
                    onClick={() => handleDownload(doc.id, doc.filename)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
                    title="Download document"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>Download</span>
                  </button>

                  <button
                    onClick={() => setDeleteConfirm({ show: true, documentId: doc.id })}
                    className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-xs rounded-lg hover:bg-red-700 transition-colors"
                    title="Delete document"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-8">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Page Numbers */}
          <div className="flex gap-2">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                    page === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default StoreViewPage;
