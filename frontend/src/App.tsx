import { Navigate, Route, Routes } from "react-router-dom";
import { BrowserRouter } from "react-router-dom";
import { useState, useEffect } from "react";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ProfileSettings from "./pages/ProfileSettings";
import ListingDetail from "./pages/ListingDetail";
import Favorites from "./pages/Favorites";
import Statistics from "./pages/Statistics";
import NotificationSettingsPage from "./pages/NotificationSettingsPage";
import Layout from "./components/Layout";

function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem("access_token")
  );
  useEffect(() => {
    const handler = () => setIsAuthenticated(!!localStorage.getItem("access_token"));
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);
  return isAuthenticated;
}

function PrivateRoute({ children }: { children: JSX.Element }) {
  const isAuthenticated = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="profile" element={<ProfileSettings />} />
          <Route path="listing/:id" element={<ListingDetail />} />
          <Route path="favorites" element={<Favorites />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="notifications" element={<NotificationSettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
