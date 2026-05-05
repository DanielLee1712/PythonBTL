import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import Home from './pages/Home';
import Cart from './pages/Cart';
import Login from './pages/Login';
import Register from './pages/Register';
import ProductDetail from './pages/ProductDetail';
import OrderList from './pages/OrderList';
import OrderDetail from './pages/OrderDetail';
import VnpayReturn from './pages/VnpayReturn';
import Checkout from './pages/Checkout';
import Staff from './pages/Staff';
import Chatbot from './components/Chatbot';
import { useStore } from './store/useStore';
import { Package, ShoppingCart, LogOut } from 'lucide-react';
import './App.css';
import { PRODUCT_SERVICE_URL } from './config';

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

function CategoryTopTabs() {
  const navigate = useNavigate();
  const query = useQuery();
  const catFromUrl = query.get('cat');

  const [categories, setCategories] = useState([]);
  const [activeCatId, setActiveCatId] = useState(catFromUrl ? Number(catFromUrl) : null);

  useEffect(() => {
    axios
      .get(`${PRODUCT_SERVICE_URL}/api/v1/categories/`, {
        params: { is_active: true, page_size: 300, _: Date.now() },
      })
      .then((res) => {
        const rows = res.data?.results ?? res.data ?? [];
        setCategories(Array.isArray(rows) ? rows : []);
      })
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    if (catFromUrl) setActiveCatId(Number(catFromUrl));
    else setActiveCatId(null);
  }, [catFromUrl]);

  const electronicsChildren = useMemo(() => {
    if (!categories.length) return [];
    const electronics = categories.find((c) => (c.slug || '') === 'electronics') || null;
    const electronicsId = electronics?.id ?? null;

    const children = categories.filter((c) => {
      const parent = c.parent;
      const parentId = typeof parent === 'object' && parent ? parent.id : parent;
      return electronicsId != null && Number(parentId) === Number(electronicsId);
    });

    // Fallback: if API doesn't expose parent id properly, just show common electronics tabs by slug.
    if (children.length > 0) return children;
    const preferredSlugs = new Set(['dien-thoai', 'laptop', 'phu-kien', 'dong-ho']);
    return categories.filter((c) => preferredSlugs.has(c.slug));
  }, [categories]);

  return (
    <div className="bg-white border-t border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex gap-8 overflow-x-auto whitespace-nowrap no-scrollbar">
          <button
            key="topcat-all"
            type="button"
            onClick={() => {
              setActiveCatId(null);
              navigate(`/`);
            }}
            className={`py-3 text-sm font-semibold border-b-2 transition-colors ${
              activeCatId == null
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-600 hover:text-blue-600'
            }`}
          >
            Tất cả sản phẩm
          </button>
          {electronicsChildren.map((c) => {
            const active = Number(c.id) === Number(activeCatId);
            return (
              <button
                key={`topcat-${c.id}`}
                type="button"
                onClick={() => {
                  setActiveCatId(c.id);
                  navigate(`/?cat=${c.id}`);
                }}
                className={`py-3 text-sm font-semibold border-b-2 transition-colors ${
                  active
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-600 hover:text-blue-600'
                }`}
              >
                {c.name}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

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

  const cartLineCount = cart.length;

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
        <header className="bg-white shadow-sm sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <Link to="/" reloadDocument className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm tracking-tight">ES</span>
                </div>
                <span className="font-bold text-xl tracking-tight text-gray-800">ElecStore</span>
              </Link>
              
              <nav className="hidden md:flex space-x-8">
                {(user?.isStaff || user?.isAdmin) && (
                  <Link to="/staff" className="text-gray-600 hover:text-blue-600 font-medium transition-colors">Staff</Link>
                )}
              </nav>

              <div className="flex items-center gap-6">
                <Link to="/cart" className="relative text-gray-600 hover:text-blue-600 transition-colors">
                  <ShoppingCart size={24} />
                  {cartLineCount > 0 && (
                    <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold min-w-[1.25rem] h-5 px-1 rounded-full flex items-center justify-center shadow-sm">
                      {cartLineCount > 99 ? '99+' : cartLineCount}
                    </span>
                  )}
                </Link>

                {user && (
                  <Link
                    to="/orders"
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                    title="Đơn hàng"
                  >
                    <Package size={22} />
                  </Link>
                )}
                
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
          <CategoryTopTabs />
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/login" element={<Login />} />
            <Route path="/staff/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/products" element={<Navigate to="/" replace />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/orders" element={<OrderList />} />
            <Route path="/orders/:id" element={<OrderDetail />} />
            <Route path="/staff" element={<Staff />} />
            <Route path="/vnpay-return" element={<VnpayReturn />} />
          </Routes>
        </main>
        
        <Chatbot />
        
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-center text-gray-500 text-sm">© 2026 ElecStore. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
