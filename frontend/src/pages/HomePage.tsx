import React from 'react';

/**
 * Home Page Component
 * 
 * This is a simple page component that will be displayed at the root route "/"
 */
const HomePage: React.FC = () => {
  return (
    <div className="text-center">
      <h2 className="text-4xl font-bold text-gray-900 mb-4">
        Welcome to AI Document Analyzer
      </h2>
      <p className="text-xl text-gray-600 mb-8">
        Upload, analyze, and query your documents with AI
      </p>
      
      {/* Example of Tailwind styling */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">📄 Upload</h3>
          <p className="text-gray-600">
            Upload your documents in various formats
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">🤖 Analyze</h3>
          <p className="text-gray-600">
            AI-powered document analysis and insights
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">💬 Query</h3>
          <p className="text-gray-600">
            Ask questions about your documents
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
