/**
 * Source Citation Component
 * 
 * Display source info with similarity score and document preview modal
 */

import React, { useState } from 'react';
import type { SourceCitation as SourceCitationType } from '../types/chat';

interface SourceCitationProps {
  source: SourceCitationType;
  index: number;
  compact?: boolean;
}

const SourceCitation: React.FC<SourceCitationProps> = ({ source, index, compact = false }) => {
  const [showPreview, setShowPreview] = useState(false);

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-700 border-green-300';
    if (score >= 0.6) return 'bg-blue-100 text-blue-700 border-blue-300';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };

  const getSimilarityLabel = (score: number) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    if (score >= 0.4) return 'Low';
    return 'Very Low';
  };

  // Compact view - single line
  if (compact) {
    return (
      <>
        <button
          onClick={() => setShowPreview(true)}
          className="inline-flex items-center gap-1.5 px-2 py-1 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:border-blue-400 transition-colors"
        >
          <span className="w-4 h-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white text-[10px] font-bold flex items-center justify-center">
            {index + 1}
          </span>
          <span className="text-gray-700 font-medium truncate max-w-[120px]">
            {source.document_name}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${getSimilarityColor(source.similarity_score)}`}>
            {(source.similarity_score * 100).toFixed(0)}%
          </span>
        </button>

        {/* Preview Modal */}
        {showPreview && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowPreview(false)}
          >
            <div
              className="bg-white rounded-lg shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-gray-800 truncate">
                      {source.document_name}
                    </h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                          />
                        </svg>
                        {source.store_name}
                      </span>
                      <span>Chunk {source.chunk_id}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getSimilarityColor(
                          source.similarity_score
                        )}`}
                      >
                        {(source.similarity_score * 100).toFixed(1)}% match
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowPreview(false)}
                    className="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
                <div className="prose prose-sm max-w-none">
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 whitespace-pre-wrap">
                    {source.chunk_text}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
                <button
                  onClick={() => setShowPreview(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Full view - original layout
  return (
    <>
      <div
        onClick={() => setShowPreview(true)}
        className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      >
        {/* Source Number */}
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white text-xs font-bold flex items-center justify-center">
          {index + 1}
        </div>

        {/* Source Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-purple-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
            <span className="text-sm font-semibold text-gray-800 truncate">
              {source.store_name}
            </span>
          </div>

          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span className="text-sm text-gray-700 truncate">
              {source.document_name}
            </span>
          </div>

          <div className="text-xs text-gray-500">
            Chunk {source.chunk_id}
          </div>
        </div>

        {/* Similarity Score */}
        <div
          className={`flex-shrink-0 px-2 py-1 rounded-full text-xs font-semibold border ${getSimilarityColor(
            source.similarity_score
          )}`}
        >
          {getSimilarityLabel(source.similarity_score)}
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowPreview(false)}
        >
          <div
            className="bg-white rounded-lg shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-bold text-gray-800 truncate">
                    {source.document_name}
                  </h3>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                        />
                      </svg>
                      {source.store_name}
                    </span>
                    <span>Chunk {source.chunk_id}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getSimilarityColor(
                        source.similarity_score
                      )}`}
                    >
                      {(source.similarity_score * 100).toFixed(1)}% match
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => setShowPreview(false)}
                  className="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
              <div className="prose prose-sm max-w-none">
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 whitespace-pre-wrap">
                  {source.chunk_text}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SourceCitation;
