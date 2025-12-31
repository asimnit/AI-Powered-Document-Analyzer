import React, { useEffect, useState } from 'react';
import storeService from '../services/storeService';
import type { StoreDetail } from '../types/store';

interface StoreSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  storeId: number;
  storeName: string;
}

/**
 * Store Summary Modal Component
 * 
 * Shows detailed statistics about a store including:
 * - Document count by status
 * - Total storage size
 * - Visual breakdown
 */

const StoreSummaryModal: React.FC<StoreSummaryModalProps> = ({ isOpen, onClose, storeId, storeName }) => {
  const [storeDetail, setStoreDetail] = useState<StoreDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchStoreDetails();
    }
  }, [isOpen, storeId]);

  const fetchStoreDetails = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const details = await storeService.getStore(storeId);
      setStoreDetail(details);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load store details');
    } finally {
      setIsLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      uploaded: 'bg-gray-500',
      processing: 'bg-yellow-500',
      completed: 'bg-green-500',
      indexing: 'bg-blue-500',
      indexed: 'bg-green-600',
      partially_indexed: 'bg-orange-500',
      indexing_failed: 'bg-red-500',
      failed: 'bg-red-600'
    };
    return colors[status] || 'bg-gray-400';
  };

  const getStatusLabel = (status: string): string => {
    return status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{storeName}</h2>
            <p className="text-gray-600 text-sm mt-1">Store Summary</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          ) : storeDetail ? (
            <div className="space-y-6">
              {/* Overview Cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-blue-600 font-medium mb-1">Total Documents</div>
                  <div className="text-3xl font-bold text-blue-900">{storeDetail.document_count}</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-sm text-purple-600 font-medium mb-1">Total Size</div>
                  <div className="text-3xl font-bold text-purple-900">{formatBytes(storeDetail.total_size)}</div>
                </div>
              </div>

              {/* Status Breakdown */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Status Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(storeDetail.status_breakdown)
                    .filter(([_, count]) => count > 0)
                    .map(([status, count]) => (
                      <div key={status} className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`}></div>
                          <span className="text-gray-700 font-medium">{getStatusLabel(status)}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${getStatusColor(status)}`}
                              style={{ width: `${(count / storeDetail.document_count) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-gray-900 font-semibold w-12 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                </div>

                {/* Empty State */}
                {storeDetail.document_count === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="w-16 h-16 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p>No documents in this store yet</p>
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="border-t border-gray-200 pt-4 text-sm text-gray-600">
                <div className="flex justify-between py-2">
                  <span>Created</span>
                  <span className="font-medium">{new Date(storeDetail.created_at).toLocaleString()}</span>
                </div>
                {storeDetail.updated_at && (
                  <div className="flex justify-between py-2">
                    <span>Last Updated</span>
                    <span className="font-medium">{new Date(storeDetail.updated_at).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default StoreSummaryModal;
