import { useState } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { authAPI } from './services/api';
import Navbar from "./Navbar";
import HomePage from "./HomePage";
import LoginPage from "./LoginPage";
import Menu from "./Menu"; 
import ReservePage from "./ReservePage";
import About from "./About";
import Contact from "./Contact";
import Footer from "./Footer";
import RegisterPage from "./RegisterPage";
import StaffLogin from "./StaffLogin";
import AdminDashboard from "./AdminDashboard";
import AddMenuItemPage from "./AddMenuItemPage";

const App = () => {
  const [menuItems] = useState([]);
  const [user, setUser] = useState(null);

  const handleLogout = async () => {
    await authAPI.logout();
    setUser(null);
  };
  const handleLoginSuccess = (userData) => setUser(userData);

  const Layout = ({ children }) => (
    <div>
      <Navbar user={user} onLogout={handleLogout} />
      {children}
      <Footer />
    </div>
  );

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><HomePage /></Layout>} />

        <Route
          path="/login"
          element={
            <LoginPage onLoginSuccess={handleLoginSuccess} />
          }
        />
        <Route path="/register" element={<RegisterPage onLoginSuccess={handleLoginSuccess} />} />

        <Route
          path="/menu"
          element={
            <Layout>
              <div style={{ height: '72px' }} />
              <Menu user={user} />
            </Layout>
          }
        />

        <Route
          path="/reservations"
          element={
            <Layout>
              <div style={{ height: '72px' }} />
              <ReservePage />
            </Layout>
          }
        />

        <Route
          path="/about"
          element={
            <Layout>
              <div style={{ height: '72px' }} />
              <About />
            </Layout>
          }
        />

        <Route
          path="/contact"
          element={
            <Layout>
              <div style={{ height: '72px' }} />
              <Contact />
            </Layout>
          }
        />
        <Route path="/staff-login" element={<StaffLogin onLoginSuccess={handleLoginSuccess} />} />
        <Route path="/admin" element={<AdminDashboard onLogout={handleLogout} />} />
        <Route path="/admin/add-item" element={<AddMenuItemPage />} />
        <Route path="*" element={<Layout><HomePage /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
