import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { AI_SERVICE_URL, PRODUCT_SERVICE_URL } from '../config';
import { fetchProductsByIds, pickProductRow } from '../utils/productRefresh';
import { Search as SearchIcon, Sparkles, TrendingUp } from 'lucide-react';
import ProductCard from '../components/ProductCard';

export default function Home() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchSource, setSearchSource] = useState('');
  const user = useStore((state) => state.user);

  const refreshProductById = useCallback((productId, opts = {}) => {
    const pid = Number(productId);
    const delta = Number(opts?.delta || 0);
    if (Number.isFinite(pid) && delta) {
      const patchLocal = (row) => {
        if (Number(row.id) !== pid) return row;
        const cur = Number(row.quantity ?? row.stock_quantity ?? 0);
        const next = Math.max(0, cur + delta);
        return { ...row, quantity: next, stock_quantity: next };
      };
      setProducts((prev) => prev.map(patchLocal));
      setSearchResults((prev) => prev.map(patchLocal));
      setRecommended((prev) => prev.map(patchLocal));
    }

    fetchProductsByIds(productId, { bustCache: opts?.bustCache ?? true })
      .then((rows) => {
        const updated = pickProductRow(rows, productId);
        if (!updated) return;
        const pid2 = Number(updated.id);
        const patch = (row) => (Number(row.id) === pid2 ? { ...row, ...updated } : row);
        setProducts((prev) => prev.map(patch));
        setSearchResults((prev) => prev.map(patch));
        setRecommended((prev) => prev.map(patch));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (params.get('paid') === '1') {
      window.alert('Thanh toán thành công. Đơn hàng đã được cập nhật.');
      navigate('/', { replace: true });
      return;
    }
    if (params.get('payment_failed') === '1') {
      window.alert('Thanh toán chưa hoàn tất hoặc thất bại.');
      navigate('/', { replace: true });
      return;
    }
    const keys = [...params.keys()];
    if (!keys.some((k) => k.startsWith('vnp_'))) return;
    const code = params.get('vnp_ResponseCode');
    if (code === '00') {
      window.alert('Thanh toán VNPAY thành công. Xem đơn tại mục Đơn hàng.');
    } else if (code != null) {
      window.alert('Thanh toán chưa hoàn tất hoặc không thành công.');
    }
    navigate('/', { replace: true });
  }, [params, navigate]);

  useEffect(() => {
    // Port 8001 is Product Service
    axios.get(`${PRODUCT_SERVICE_URL}/api/v1/products/`)
      .then(res => setProducts(res.data.results || res.data))
      .catch(() => setProducts([
        {id: 1, title: 'Laptop Gaming Alienware', price: 45000000, category_name: 'Electronics'},
        {id: 2, title: 'Son Tom Ford', price: 1500000, category_name: 'Cosmetics'},
        {id: 3, title: 'Khóa học Đồ Họa 3D', price: 900000, category_name: 'Education'},
        {id: 4, title: 'Chuột Razer DeathAdder', price: 800000, category_name: 'Electronics'}
      ]));

    if (user) {
      // Fetch GNN Recommendations from AI-Service
      axios.get(`${AI_SERVICE_URL}/api/v1/recommendations/${user.id}/`)
        .then(res => {
          const ids = res.data.recommendations || [];
          if (ids.length > 0) {
            axios.get(`${PRODUCT_SERVICE_URL}/api/v1/products/?ids=${ids.join(',')}`)
              .then(pRes => setRecommended(pRes.data.results || pRes.data))
              .catch(() => console.log("Lỗi fetch recommended products"));
          }
        }).catch(err => console.log("GNN service error", err));
    }
  }, [user]);

  const handleSearch = async (e) => {
    e.preventDefault();
    const keyword = searchTerm.trim().toLowerCase();
    setHasSearched(true);

    if (!keyword) {
      setSearchResults(products);
      setSearchSource('all');
      return;
    }

    setSearching(true);
    try {
      const res = await axios.post(`${AI_SERVICE_URL}/api/v1/search/`, {
        user_id: user ? user.id : null,
        query: keyword,
        k: 40,
      });
      const results = res.data.results || [];
      setSearchResults(results);
      setSearchSource('ai');
      
      // Track SEARCH if exactly 1 result is returned
      if (results.length === 1 && user) {
        import('../utils/tracking').then(({ trackBehavior }) => {
          trackBehavior(user.id, results[0].id, 'search');
        });
      }
    } catch {
      // fallback to local filter if AI search is unavailable
      const results = products.filter((item) => {
        const productName = (item.title || item.name || '').toLowerCase();
        const categoryName = (item.category_name || '').toLowerCase();
        return productName.includes(keyword) || categoryName.includes(keyword);
      });
      setSearchResults(results);
      setSearchSource('local');
      
      // Track SEARCH if exactly 1 result is returned
      if (results.length === 1 && user) {
        import('../utils/tracking').then(({ trackBehavior }) => {
          trackBehavior(user.id, results[0].id, 'search');
        });
      }
    } finally {
      setSearching(false);
    }
  };



  return (
    <div className="space-y-12">
      {/* ── AI Search Section ── */}
      <section className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-sm">
            <SearchIcon size={18} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">Tìm kiếm sản phẩm</h2>
          </div>
        </div>
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Nhập tên sản phẩm hoặc danh mục..."
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 outline-none focus:ring-2 ring-blue-200 focus:border-blue-400 transition-all"
          />
          <button
            type="submit"
            disabled={searching}
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl font-semibold transition-colors flex items-center gap-2 disabled:opacity-60"
          >
            {searching ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Đang tìm...
              </>
            ) : (
              <>
                <SearchIcon size={16} /> Search
              </>
            )}
          </button>
        </form>

        {hasSearched && (
          <div className="mt-6">
            <div className="flex items-center gap-3 mb-4">
              <h3 className="font-semibold text-gray-700">
                Kết quả: {searchResults.length} sản phẩm
              </h3>
              {searchSource === 'ai' && (
                <span className="text-xs bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full font-bold border border-purple-200 flex items-center gap-1">
                  <Sparkles size={10} /> AI-Powered + Personalized
                </span>
              )}
              {searchSource === 'local' && (
                <span className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full font-medium">
                  Tìm kiếm cơ bản
                </span>
              )}
            </div>
            {searchResults.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {searchResults.map((p) => (
                  <ProductCard p={p} key={`search-${p.id}`} onAfterAddToCart={refreshProductById} />
                ))}
              </div>
            ) : (
              <div className="text-center py-10">
                <p className="text-gray-400 text-lg mb-2">Không tìm thấy sản phẩm phù hợp</p>
                <p className="text-gray-400 text-sm">Thử từ khóa khác hoặc hỏi AI Assistant</p>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ── AI Recommendations Section ── */}
      {user && recommended.length > 0 && (
        <section className="bg-gradient-to-r from-blue-50 to-purple-50 p-8 rounded-3xl border border-blue-100 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
          <div className="absolute top-0 right-32 w-64 h-64 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
          
          <div className="flex items-center gap-3 mb-6 relative z-10">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-md">
              <TrendingUp size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-purple-700">
                Dành Riêng Cho Bạn
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">Gợi ý từ GNN + Sequence Model dựa trên lịch sử mua sắm</p>
            </div>
            <span className="ml-auto text-xs bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full font-bold border border-purple-200 shadow-sm flex items-center gap-1">
              <Sparkles size={10} /> Powered by AI
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 relative z-10">
            {recommended.map(p => <ProductCard p={p} key={`rec-${p.id}`} onAfterAddToCart={refreshProductById} />)}
          </div>
        </section>
      )}

      {/* ── All Products Section ── */}
      <section>
        <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">Tất Cả Sản Phẩm</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {products.map(p => <ProductCard p={p} key={p.id} onAfterAddToCart={refreshProductById} />)}
        </div>
      </section>
    </div>
  );
}
