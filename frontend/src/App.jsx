import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useEffect } from 'react';
import Home from './pages/Home';
import Cart from './pages/Cart';
import Login from './pages/Login';
import Register from './pages/Register';
import ProductDetail from './pages/ProductDetail';
import ProductList from './pages/ProductList';
import Chatbot from './components/Chatbot';
import { useStore } from './store/useStore';
import { ShoppingCart, User, LogOut } from 'lucide-react';
import './App.css';

function App() {
  const cart = useStore((state) => state.cart);
  const user = useStore((state) => state.user);
  const setUser = useStore((state) => state.setUser);
  const fetchCart = useStore((state) => state.fetchCart);
  
  useEffect(() => {
    if (user) {
      fetchCart();
    }
  }, [user, fetchCart]);

  const cartItemCount = cart.reduce((total, item) => total + item.quantity, 0);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
        <header className="bg-white shadow-sm sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">AI</span>
                </div>
                <span className="font-bold text-xl tracking-tight text-gray-800">Ecommerce</span>
              </Link>
              
              <nav className="hidden md:flex space-x-8">
                <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium transition-colors">Trang chủ</Link>
                <Link to="/products" className="text-gray-600 hover:text-blue-600 font-medium transition-colors">Sản phẩm</Link>
              </nav>

              <div className="flex items-center gap-6">
                <Link to="/cart" className="relative text-gray-600 hover:text-blue-600 transition-colors">
                  <ShoppingCart size={24} />
                  {cartItemCount > 0 && (
                    <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-sm">
                      {cartItemCount}
                    </span>
                  )}
                </Link>
                
                {user ? (
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-gray-700 hidden sm:block">Chào, {user.username}</span>
                    <button onClick={() => setUser(null)} className="text-gray-500 hover:text-red-500 transition-colors" title="Đăng xuất">
                      <LogOut size={20} />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <Link to="/login" className="text-gray-600 hover:text-blue-600 font-medium transition-colors hidden sm:block">Đăng nhập</Link>
                    <Link to="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm">Đăng ký</Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/product/:id" element={<ProductDetail />} />
          </Routes>
        </main>
        
        <Chatbot />
        
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-center text-gray-500 text-sm">© 2026 AI Ecommerce. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
