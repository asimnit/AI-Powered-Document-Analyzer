import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStoreStore } from '../store/storeStore';
import CreateStoreModal from '../components/CreateStoreModal';
import StoreSummaryModal from '../components/StoreSummaryModal';
import type { DocumentStore } from '../types/store';

/**
 * Stores List Page Component
 * 
 * Landing page showing all document stores in grid layout
 * Allows creating, editing, and deleting stores
 */

const StoresListPage: React.FC = () => {
  const navigate = useNavigate();
  const { stores, isLoading, error, fetchStores, deleteStore } = useStoreStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [selectedStore, setSelectedStore] = useState<DocumentStore | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    fetchStores();
  }, [fetchStores]);

  const handleStoreClick = (store: DocumentStore) => {
    navigate(`/stores/${store.id}`);
  };

  const handleShowSummary = (store: DocumentStore, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedStore(store);
    setShowSummaryModal(true);
  };

  const handleDelete = async (storeId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (deleteConfirm === storeId) {
      try {
        await deleteStore(storeId);
        setDeleteConfirm(null);
      } catch (error) {
        console.error('Failed to delete store:', error);
      }
    } else {
      setDeleteConfirm(storeId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (isLoading && stores.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header with Animated Background */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-8 mb-8 shadow-2xl">
          {/* Animated Blobs */}
          <div className="absolute top-0 -right-4 w-72 h-72 bg-white/20 rounded-full mix-blend-overlay filter blur-3xl opacity-70 animate-blob"></div>
          <div className="absolute -bottom-8 -left-4 w-72 h-72 bg-white/20 rounded-full mix-blend-overlay filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
          
          <div className="relative z-10 flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                <span className="animate-bounce inline-block">📁</span>
                Document Stores
              </h1>
              <p className="text-blue-100 text-lg">Organize your documents into beautiful collections</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-white text-blue-600 px-8 py-4 rounded-xl font-bold hover:bg-blue-50 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 hover:scale-105 flex items-center gap-2"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Store
            </button>
          </div>
        </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-6 py-4 rounded-lg mb-6 shadow-md animate-shake">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {stores.length === 0 && !isLoading && (
        <div className="text-center py-20 animate-fade-in">
          <div className="relative inline-block mb-6">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full blur-2xl opacity-30 animate-pulse"></div>
            <svg className="relative w-32 h-32 mx-auto text-gradient animate-float" fill="none" stroke="url(#gradient)" viewBox="0 0 24 24" strokeWidth={1.5}>
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3B82F6" />
                  <stop offset="100%" stopColor="#A855F7" />
                </linearGradient>
              </defs>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <h3 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            No Stores Yet
          </h3>
          <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">Create your first document store to organize your documents beautifully</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 rounded-xl font-bold transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:-translate-y-1 hover:scale-105"
          >
            Create Your First Store ✨
          </button>
        </div>
      )}

      {/* Stores Grid */}
      {stores.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {stores.map((store, index) => (
            <div
              key={store.id}
              onClick={() => handleStoreClick(store)}
              className="group relative bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 cursor-pointer border-2 border-transparent hover:border-blue-300 overflow-hidden transform hover:-translate-y-2 hover:scale-105"
              style={{
                animation: `fadeInUp 0.6s ease-out ${index * 0.1}s both`
              }}
            >
              {/* Gradient Background Animation */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              
              {/* Animated Border Glow */}
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-2xl opacity-0 group-hover:opacity-20 blur transition-opacity duration-500"></div>
              
              <div className="relative">
                {/* Store Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      {/* Folder Icon with Gradient */}
                      <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white mb-3 transform group-hover:rotate-6 group-hover:scale-110 transition-all duration-300 shadow-lg">
                        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                      </div>
                      
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-purple-600 group-hover:bg-clip-text transition-all duration-300 mb-2">
                        {store.name}
                      </h3>
                      {store.description && (
                        <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">{store.description}</p>
                      )}
                    </div>
                    <svg className="w-6 h-6 text-gray-300 group-hover:text-blue-600 transform group-hover:translate-x-1 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>

                  {/* Document Count with Badge */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100 group-hover:border-blue-300 transition-colors">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="font-bold text-gray-900">{store.document_count}</span>
                      <span className="text-gray-600 text-sm">documents</span>
                    </div>
                  </div>

                  {/* Created Date with Icon */}
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>Created {formatDate(store.created_at)}</span>
                  </div>
                </div>

                {/* Actions with Gradient Buttons */}
                <div className="border-t border-gray-100 px-6 py-4 bg-gradient-to-r from-gray-50 to-white flex gap-3">
                  <button
                    onClick={(e) => handleShowSummary(store, e)}
                    className="flex-1 px-4 py-2.5 text-sm font-semibold text-blue-600 bg-blue-50 hover:bg-gradient-to-r hover:from-blue-600 hover:to-purple-600 hover:text-white rounded-lg transition-all duration-300 transform hover:scale-105 shadow-sm hover:shadow-md"
                  >
                    📊 Summary
                  </button>
                  <button
                    onClick={(e) => handleDelete(store.id, e)}
                    className={`flex-1 px-4 py-2.5 text-sm font-semibold rounded-lg transition-all duration-300 transform hover:scale-105 shadow-sm hover:shadow-md ${
                      deleteConfirm === store.id
                        ? 'bg-gradient-to-r from-red-600 to-pink-600 text-white animate-pulse'
                        : 'text-red-600 bg-red-50 hover:bg-gradient-to-r hover:from-red-600 hover:to-pink-600 hover:text-white'
                    }`}
                  >
                    {deleteConfirm === store.id ? '⚠️ Confirm?' : '🗑️ Delete'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Store Modal */}
      <CreateStoreModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => fetchStores()}
      />

      {/* Summary Modal */}
      {selectedStore && (
        <StoreSummaryModal
          isOpen={showSummaryModal}
          onClose={() => {
            setShowSummaryModal(false);
            setSelectedStore(null);
          }}
          storeId={selectedStore.id}
          storeName={selectedStore.name}
        />
      )}
      </div>
    </div>
  );
};

export default StoresListPage;
