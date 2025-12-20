import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * BaseLayout Component
 * 
 * This is the main layout wrapper for the application.
 * - It will contain common elements like navbar, sidebar, footer
 * - The <Outlet /> component renders the child routes
 * - Shows user info and logout button in navbar
 * 
 * Think of it as a frame that stays the same while content changes
 */
const BaseLayout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header/Navbar - will be visible on all pages */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-blue-600">
              AI Document Analyzer
            </Link>
            
            <nav className="flex items-center gap-6">
              <Link to="/" className="text-gray-600 hover:text-gray-900">
                Home
              </Link>
              <Link to="/about" className="text-gray-600 hover:text-gray-900">
                About
              </Link>
              
              <div className="flex items-center gap-4 border-l pl-6">
                <span className="text-sm text-gray-600">
                  {user?.full_name || user?.username}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                >
                  Logout
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content Area - this changes based on the route */}
      <main className="max-w-7xl mx-auto px-4 py-8 flex-1">
        <Outlet /> {/* Child routes render here */}
      </main>

      {/* Footer - will be visible on all pages */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-gray-600">
          <p>© 2025 AI Document Analyzer</p>
        </div>
      </footer>
    </div>
  );
};

export default BaseLayout;
