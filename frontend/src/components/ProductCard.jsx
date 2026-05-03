import { useMemo, useState } from 'react';
import { ShoppingCart, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { trackBehavior } from '../utils/tracking';

export default function ProductCard({ p, onAfterAddToCart }) {
  const user = useStore((state) => state.user);
  const addToCart = useStore((state) => state.addToCart);

  const formatPrice = (v) => Number(v || 0).toLocaleString('vi-VN');
  const img = (p?.image_url || '').trim();
  const [imgError, setImgError] = useState(false);
  const showImage = Boolean(img) && !imgError;
  const fallbackLabel = useMemo(
    () => (p?.category_name || 'SP').toString().slice(0, 10),
    [p?.category_name]
  );

  const handleAddToCart = async (product) => {
    const res = await addToCart(product);
    if (!res?.ok) {
      window.alert(res?.error || 'Không thể thêm vào giỏ');
      return;
    }
    await trackBehavior(user?.id, product.id, 'add_to_cart');
    // Optimistic stock decrement (qty=1 on this button), then refetch by id in parent.
    onAfterAddToCart?.(product.id, { delta: -1, bustCache: true });
  };

  return (
    <div className="bg-white rounded-2xl shadow border border-gray-100 overflow-hidden hover:shadow-xl transition-all transform hover:-translate-y-1 group flex flex-col">
      <Link to={`/product/${p.id}`} className="block">
        <div className="h-48 bg-gray-100 flex items-center justify-center p-4">
          {showImage ? (
            <img
              src={img}
              alt={p.title || p.name || 'product'}
              className="w-full h-full object-contain bg-white rounded-xl border"
              onError={() => setImgError(true)}
            />
          ) : (
            <div className="text-gray-300 font-medium border-2 border-dashed border-gray-300 rounded-full w-32 h-32 flex items-center justify-center bg-white text-center text-sm">
              {fallbackLabel}
            </div>
          )}
        </div>
      </Link>
      <div className="p-5 flex flex-col flex-grow">
        <Link to={`/product/${p.id}`} className="block">
          <h3 className="font-bold text-lg text-gray-800 mb-2 truncate hover:text-blue-600 transition-colors" title={p.title || p.name}>
            {p.title || p.name}
          </h3>
        </Link>
        <p className="text-blue-600 font-black mb-1 tracking-tight flex-grow">
          {formatPrice(p.price)} ₫
        </p>
        <p className="text-xs text-gray-500 mb-4">
          Còn: <span className="font-semibold text-gray-700">{p.quantity ?? p.stock_quantity ?? 0}</span>
        </p>
        <div className="flex gap-2 mt-auto">
          <Link 
            to={`/product/${p.id}`}
            className="flex-1 bg-gray-50 hover:bg-gray-200 text-gray-700 font-medium py-2.5 rounded-xl flex justify-center items-center gap-2 transition-colors"
          >
            <Eye size={18} /> Xem
          </Link>
          <button 
            onClick={() => handleAddToCart(p)} 
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-xl flex justify-center items-center gap-2 transition-colors shadow-sm"
          >
            <ShoppingCart size={18} /> Mua
          </button>
        </div>
      </div>
    </div>
  );
}
