/**
 * Store Selector Component
 * 
 * Modal for attaching stores with max 5 validation
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Store {
  id: number;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
}

interface StoreSelectorProps {
  currentStoreIds: number[];
  onAttach: (storeIds: number[]) => Promise<void>;
  onClose: () => void;
}

const StoreSelector: React.FC<StoreSelectorProps> = ({
  currentStoreIds,
  onAttach,
  onClose,
}) => {
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>(currentStoreIds);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attaching, setAttaching] = useState(false);

  const MAX_STORES = 5;

  useEffect(() => {
    fetchStores();
  }, []);

  const fetchStores = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');
      const response = await axios.get<{ stores: Store[] }>(
        'http://localhost:8000/api/v1/stores',
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setStores(response.data.stores);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load stores');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStore = (storeId: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(storeId)) {
        return prev.filter((id) => id !== storeId);
      } else {
        if (prev.length >= MAX_STORES) {
          return prev;
        }
        return [...prev, storeId];
      }
    });
  };

  const handleAttach = async () => {
    // Only attach newly selected stores
    const newStoreIds = selectedIds.filter((id) => !currentStoreIds.includes(id));
    
    if (newStoreIds.length === 0) {
      onClose();
      return;
    }

    setAttaching(true);
    try {
      await onAttach(newStoreIds);
    } catch (err) {
      console.error('Failed to attach stores:', err);
    } finally {
      setAttaching(false);
    }
  };

  const canAddMore = selectedIds.length < MAX_STORES;
  const hasChanges = JSON.stringify(selectedIds.sort()) !== JSON.stringify(currentStoreIds.sort());

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                Select Document Stores
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Choose up to {MAX_STORES} stores to search from
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Selected Count */}
        <div className="px-6 py-3 bg-blue-50 border-b border-blue-100">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-700">
              <span className="font-semibold text-blue-600">{selectedIds.length}</span> of {MAX_STORES} stores selected
            </span>
            {!canAddMore && (
              <span className="text-orange-600 font-medium">
                Maximum reached
              </span>
            )}
          </div>
        </div>

        {/* Stores List */}
        <div className="px-6 py-4 overflow-y-auto max-h-[50vh]">
          {loading ? (
            <div className="py-8 text-center text-gray-500">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-blue-500 mx-auto mb-4"></div>
              Loading stores...
            </div>
          ) : error ? (
            <div className="py-8 text-center text-red-500">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {error}
            </div>
          ) : stores.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <p className="text-lg font-medium mb-2">No stores available</p>
              <p className="text-sm">Create a document store first</p>
            </div>
          ) : (
            <div className="space-y-2">
              {stores.map((store) => {
                const isSelected = selectedIds.includes(store.id);
                const isCurrentlyAttached = currentStoreIds.includes(store.id);
                const canSelect = isSelected || canAddMore;

                return (
                  <label
                    key={store.id}
                    className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    } ${!canSelect && !isSelected ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {/* Checkbox */}
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleStore(store.id)}
                      disabled={!canSelect && !isSelected}
                      className="mt-1 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />

                    {/* Store Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-800 truncate">
                          {store.name}
                        </h3>
                        {isCurrentlyAttached && (
                          <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                            Attached
                          </span>
                        )}
                      </div>
                      {store.description && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {store.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                          </svg>
                          {store.document_count} documents
                        </span>
                        <span>
                          Created {new Date(store.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAttach}
            disabled={!hasChanges || attaching}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              hasChanges && !attaching
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {attaching ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Attaching...
              </span>
            ) : (
              `Attach ${selectedIds.filter(id => !currentStoreIds.includes(id)).length > 0 ? selectedIds.filter(id => !currentStoreIds.includes(id)).length : ''} Store${selectedIds.filter(id => !currentStoreIds.includes(id)).length !== 1 ? 's' : ''}`
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default StoreSelector;
