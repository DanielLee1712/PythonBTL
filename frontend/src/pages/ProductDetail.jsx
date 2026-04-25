import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { trackBehavior } from '../utils/tracking';
import { ShoppingCart, Heart, Star, ArrowLeft } from 'lucide-react';

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [hasRated, setHasRated] = useState(false);
  const [inWishlist, setInWishlist] = useState(false);
  
  const user = useStore((state) => state.user);
  const addToCart = useStore((state) => state.addToCart);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const res = await axios.get(`http://localhost:8001/api/v1/products/?ids=${id}`);
        const results = res.data.results || res.data;
        if (results && results.length > 0) {
          setProduct(results[0]);
        } else {
          setProduct(null);
        }
      } catch (err) {
        console.error("Lỗi tải chi tiết sản phẩm", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [id]);

  // Track VIEW action when product data is loaded
  useEffect(() => {
    if (user && product) {
      trackBehavior(user.id, product.id, 'view');
    }
  }, [user, product]);

  const handleAddToCart = async () => {
    if (!product) return;
    try {
      await addToCart(product);
      await trackBehavior(user?.id, product.id, 'add_to_cart');
    } catch (e) {
      console.error('Lỗi khi thêm vào giỏ', e);
    }
  };

  const handleWishlist = () => {
    if (!user || !product) return;
    setInWishlist(!inWishlist);
    if (!inWishlist) {
      trackBehavior(user.id, product.id, 'wishlist');
    }
  };

  const handleRate = (stars) => {
    if (!user || !product) return;
    setRating(stars);
    setHasRated(true);
    trackBehavior(user.id, product.id, 'rate');
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Đang tải...</div>;
  }

  if (!product) {
    return <div className="p-8 text-center text-red-500">Không tìm thấy sản phẩm.</div>;
  }

  const formatPrice = (v) => Number(v || 0).toLocaleString('vi-VN');

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <Link to="/" className="inline-flex items-center gap-2 text-gray-500 hover:text-blue-600 transition-colors">
        <ArrowLeft size={20} /> Quay lại
      </Link>
      
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row">
        {/* Product Image Placeholder */}
        <div className="md:w-1/2 bg-gray-100 p-12 flex items-center justify-center min-h-[400px]">
           <div className="text-gray-300 font-bold border-4 border-dashed border-gray-300 rounded-full w-48 h-48 flex items-center justify-center bg-white text-2xl">
            {product.category_name || 'SP'}
          </div>
        </div>

        {/* Product Info */}
        <div className="md:w-1/2 p-8 md:p-12 flex flex-col justify-center">
          <div className="text-sm text-blue-600 font-bold tracking-wider uppercase mb-2">
            {product.category_name || 'Danh mục'}
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-gray-800 mb-4 leading-tight">
            {product.title || product.name}
          </h1>
          <p className="text-4xl font-black text-blue-600 mb-8">
            {formatPrice(product.price)} ₫
          </p>

          <p className="text-gray-600 mb-8 leading-relaxed">
            Sản phẩm chính hãng với chất lượng đảm bảo. Rất phù hợp cho nhu cầu của bạn.
            Chi tiết mô tả sẽ được cập nhật thêm bởi nhà bán hàng.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <button 
              onClick={handleAddToCart}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
            >
              <ShoppingCart size={20} /> Thêm vào giỏ
            </button>
            <button 
              onClick={handleWishlist}
              className={`flex-1 sm:flex-none px-6 py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all border ${inWishlist ? 'bg-pink-50 border-pink-200 text-pink-600' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}`}
            >
              <Heart size={20} className={inWishlist ? 'fill-pink-600' : ''} /> {inWishlist ? 'Đã yêu thích' : 'Yêu thích'}
            </button>
          </div>

          <div className="border-t border-gray-100 pt-6">
            <p className="text-sm font-semibold text-gray-700 mb-3">Đánh giá sản phẩm này</p>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button 
                  key={star} 
                  onClick={() => handleRate(star)}
                  disabled={hasRated}
                  className={`transition-colors ${hasRated ? 'cursor-default' : 'hover:scale-110'}`}
                >
                  <Star 
                    size={28} 
                    className={`${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`} 
                  />
                </button>
              ))}
              {hasRated && <span className="ml-3 text-sm text-green-600 font-medium">Cảm ơn đánh giá của bạn!</span>}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
