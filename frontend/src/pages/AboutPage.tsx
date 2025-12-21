import React from 'react';

/**
 * About Page Component
 * 
 * Modern about page with feature showcase and tech stack
 */
const AboutPage: React.FC = () => {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto">
        <h1 className="text-5xl font-bold mb-6">
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            About Our Platform
          </span>
        </h1>
        <p className="text-xl text-gray-600 leading-relaxed">
          AI Document Analyzer is a modern full-stack application that leverages artificial intelligence 
          to transform how you interact with documents. Built with cutting-edge technologies for 
          performance, scalability, and user experience.
        </p>
      </div>

      {/* Mission Section */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 md:p-12 border border-blue-100">
        <div className="max-w-3xl mx-auto text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center text-white mx-auto mb-6 shadow-lg">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Our Mission</h2>
          <p className="text-lg text-gray-700 leading-relaxed">
            To democratize document analysis by making AI-powered insights accessible to everyone. 
            We believe that understanding your documents shouldn't require specialized knowledge or 
            expensive tools.
          </p>
        </div>
      </div>

      {/* Key Features */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Feature 1 */}
          <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Multi-Format Support</h3>
                <p className="text-gray-600">
                  Upload and analyze documents in PDF, Word, Excel, and text formats with seamless processing.
                </p>
              </div>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Smart AI Analysis</h3>
                <p className="text-gray-600">
                  Advanced machine learning algorithms extract key insights, summaries, and important information automatically.
                </p>
              </div>
            </div>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Natural Language Queries</h3>
                <p className="text-gray-600">
                  Ask questions about your documents in plain English and get instant, accurate answers.
                </p>
              </div>
            </div>
          </div>

          {/* Feature 4 */}
          <div className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Secure & Private</h3>
                <p className="text-gray-600">
                  Your documents are encrypted and stored securely. We prioritize your privacy and data protection.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
        <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Built With Modern Technologies</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Frontend */}
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white text-sm">FE</span>
              Frontend
            </h3>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span><strong>React 19</strong> - Modern UI library</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span><strong>TypeScript</strong> - Type-safe development</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span><strong>Tailwind CSS</strong> - Utility-first styling</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span><strong>Zustand</strong> - State management</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span><strong>Vite</strong> - Lightning-fast build tool</span>
              </li>
            </ul>
          </div>

          {/* Backend */}
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center text-white text-sm">BE</span>
              Backend
            </h3>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span><strong>FastAPI</strong> - High-performance Python API</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span><strong>PostgreSQL</strong> - Robust database</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span><strong>Redis</strong> - Fast caching layer</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span><strong>JWT</strong> - Secure authentication</span>
              </li>
              <li className="flex items-center gap-3 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span><strong>Alembic</strong> - Database migrations</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 md:p-12 text-white text-center shadow-2xl">
        <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p className="text-blue-100 text-lg mb-6 max-w-2xl mx-auto">
          Start analyzing your documents today and unlock the power of AI-driven insights.
        </p>
        <button className="bg-white text-blue-600 px-8 py-3 rounded-xl font-semibold hover:bg-blue-50 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
          Upload Your First Document
        </button>
      </div>
    </div>
  );
};

export default AboutPage;
