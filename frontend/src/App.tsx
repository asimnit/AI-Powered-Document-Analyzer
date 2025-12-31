import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BaseLayout from './components/BaseLayout';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import DocumentsPage from './pages/DocumentsPage';
import StoresListPage from './pages/StoresListPage';
import StoreViewPage from './pages/StoreViewPage';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { useAuthStore } from './store/authStore';

/**
 * App Component - Root of the application
 * 
 * Here we set up routing:
 * - BrowserRouter: Enables routing in the app
 * - Routes: Container for all route definitions
 * - Route: Defines a path and what component to render
 * - ProtectedRoute: Wraps routes requiring authentication
 * 
 * Structure:
 * /login -> LoginPage (public)
 * /register -> RegisterPage (public)
 * / (root) -> BaseLayout wraps protected routes
 *   ├─ / -> HomePage (protected)
 *   └─ /about -> AboutPage (protected)
 */
function App() {
  const { fetchCurrentUser } = useAuthStore();

  // Check if user is logged in on app load
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <BaseLayout />
            </ProtectedRoute>
          }
        >
          {/* Index route - shows at "/" */}
          <Route index element={<HomePage />} />
          
          {/* Chat route - shows at "/chat" */}
          <Route path="chat" element={<ChatPage />} />
          
          {/* Stores routes */}
          <Route path="stores" element={<StoresListPage />} />
          <Route path="stores/:storeId" element={<StoreViewPage />} />
          
          {/* Documents route - shows at "/documents" */}
          <Route path="documents" element={<DocumentsPage />} />
          
          {/* About route - shows at "/about" */}
          <Route path="about" element={<AboutPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
