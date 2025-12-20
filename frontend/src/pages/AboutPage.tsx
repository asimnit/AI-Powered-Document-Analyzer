import React from 'react';

/**
 * About Page Component
 * 
 * Just a simple example page to demonstrate routing
 */
const AboutPage: React.FC = () => {
  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">About</h2>
      <p className="text-gray-600">
        This is the AI-Powered Document Analyzer - a learning project
        to understand modern React development with TypeScript.
      </p>
    </div>
  );
};

export default AboutPage;
