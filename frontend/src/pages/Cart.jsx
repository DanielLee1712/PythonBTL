import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { Trash2, Plus, Minus, ArrowRight, Sparkles, TrendingUp } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { AI_SERVICE_URL, PRODUCT_SERVICE_URL } from '../config';
import { fetchProductsByIds, pickProductRow } from '../utils/productRefresh';
import ProductCard from '../components/ProductCard';
export default function Cart() {
  const navigate = useNavigate();
  const user = useStore((state) => state.user);
  const cart = useStore((state) => state.cart);
  const removeFromCart = useStore((state) => state.removeFromCart);
  const updateQuantity = useStore((state) => state.updateQuantity);
  const clearCart = useStore((state) => state.clearCart);

  const [recommended, setRecommended] = useState([]);

  useEffect(() => {
    if (cart.length > 0) {
      const lastItem = cart[cart.length - 1];
      axios.get(`${AI_SERVICE_URL}/api/ai/graph/products/${lastItem.id}/similar/?k=8`)
        .then(res => {
          const similar = res.data.similar_products || [];
          const ids = similar.map(item => item.product_id);
          
          if (ids.length > 0) {
            axios.get(`${PRODUCT_SERVICE_URL}/api/v1/products/?ids=${ids.join(',')}`)
              .then(pRes => {
                const fetchedProducts = pRes.data.results || pRes.data;
                const filtered = fetchedProducts.filter(p => !cart.find(c => c.id === p.id));
                setRecommended(filtered.slice(0, 4)); // Giữ tối đa 4 sản phẩm
              })
              .catch(() => console.log("Lỗi fetch chi tiết products"));
          } else {
            setRecommended([]);
          }
        }).catch(err => console.log("GNN similar products error", err));
    } else {
      setRecommended([]);
    }
  }, [cart]);

  const refreshProductById = useCallback((productId, opts = {}) => {
    const pid = Number(productId);
    const delta = Number(opts?.delta || 0);
    if (Number.isFinite(pid) && delta) {
      setRecommended((prev) =>
        prev.map((p) => {
          if (Number(p.id) !== pid) return p;
          const cur = Number(p.quantity ?? p.stock_quantity ?? 0);
          const next = Math.max(0, cur + delta);
          return { ...p, quantity: next, stock_quantity: next };
        })
      );
    }

    fetchProductsByIds(productId, { bustCache: opts?.bustCache ?? true })
      .then((rows) => {
        const updated = pickProductRow(rows, productId);
        if (!updated) return;
        setRecommended((prev) =>
          prev.map((p) => (Number(p.id) === pid ? { ...p, ...updated } : p))
        );
      })
      .catch(() => {});
  }, []);

  const total = cart.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0);
  const formatPrice = (v) => Number(v || 0).toLocaleString('vi-VN');

  const handleCheckout = () => {
    if (!user || cart.length === 0) return;
    navigate('/checkout');
  };

  if (cart.length === 0) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-gray-100 max-w-3xl mx-auto">
        <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-4xl">🛒</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Giỏ hàng của bạn đang trống</h2>
        <p className="text-gray-500 mb-8">Hãy quay lại trang chủ và chọn cho mình những sản phẩm ưng ý nhé!</p>
        <Link to="/" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-xl transition-colors">
          Tiếp tục mua sắm <ArrowRight size={18} />
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Giỏ hàng</h1>
        <button onClick={clearCart} className="text-red-500 hover:text-red-600 font-medium text-sm flex items-center gap-1">
          <Trash2 size={16} /> Xóa tất cả
        </button>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 divide-y divide-gray-100">
          {cart.map((item) => (
            <div key={item.id} className="py-6 flex flex-col sm:flex-row items-center gap-6 first:pt-0 last:pb-0">
              <div className="w-24 h-24 bg-gray-50 rounded-xl flex items-center justify-center shrink-0">
                <span className="text-gray-400 font-bold text-xs">{item.category_name || 'SP'}</span>
              </div>
              
              <div className="flex-1 text-center sm:text-left">
                <h3 className="font-bold text-lg text-gray-800 mb-1">{item.title || item.name}</h3>
                <p className="text-blue-600 font-black">{formatPrice(item.price)} ₫</p>
              </div>
              
              <div className="flex items-center gap-3 bg-gray-50 p-2 rounded-lg">
                <button 
                  onClick={async () => {
                    const r = await updateQuantity(item.id, Math.max(1, item.quantity - 1));
                    if (r && !r.ok) window.alert(r.error || 'Cập nhật thất bại');
                  }}
                  className="w-8 h-8 flex items-center justify-center bg-white rounded-md shadow-sm hover:text-blue-600"
                >
                  <Minus size={16} />
                </button>
                <span className="w-8 text-center font-bold text-gray-700">{item.quantity}</span>
                <button 
                  onClick={async () => {
                    const r = await updateQuantity(item.id, item.quantity + 1);
                    if (r && !r.ok) window.alert(r.error || 'Cập nhật thất bại');
                  }}
                  className="w-8 h-8 flex items-center justify-center bg-white rounded-md shadow-sm hover:text-blue-600"
                >
                  <Plus size={16} />
                </button>
              </div>
              
              <div className="text-right sm:w-32">
                <p className="font-bold text-gray-800 hidden sm:block mb-2">{formatPrice(item.price * item.quantity)} ₫</p>
                <button 
                  onClick={() => removeFromCart(item.id)}
                  className="text-gray-400 hover:text-red-500 transition-colors p-2"
                  title="Xóa sản phẩm"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="bg-gray-50 p-6 sm:px-8 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-6">
          <div>
            <p className="text-gray-500 text-sm mb-1">Tổng cộng</p>
            <p className="text-3xl font-black text-blue-600">{formatPrice(total)} ₫</p>
          </div>
          <button 
            onClick={handleCheckout}
            className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-4 px-10 rounded-xl shadow-lg transform hover:-translate-y-1 transition-all"
          >
            Tiến hành thanh toán
          </button>
        </div>
      </div>

      {/* ── AI Recommendations Section ── */}
      {recommended.length > 0 && (
        <section className="bg-gradient-to-r from-blue-50 to-purple-50 p-8 rounded-3xl border border-blue-100 shadow-sm relative overflow-hidden mt-8">
          <div className="absolute top-0 right-0 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
          <div className="absolute top-0 right-32 w-64 h-64 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
          
          <div className="flex items-center gap-3 mb-6 relative z-10">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-md">
              <TrendingUp size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-purple-700">
                Gợi Ý Thêm Cho Giỏ Hàng
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">Sản phẩm thường được mua cùng với các món trong giỏ của bạn</p>
            </div>
            <span className="ml-auto text-xs bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full font-bold border border-purple-200 shadow-sm flex items-center gap-1">
              <Sparkles size={10} /> Powered by AI
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 relative z-10">
            {recommended.map((p) => (
              <ProductCard p={p} key={`cart-rec-${p.id}`} onAfterAddToCart={refreshProductById} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
