import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import { PRODUCT_SERVICE_URL } from '../config';
import ProductCard from '../components/ProductCard';
import { Search, X, SlidersHorizontal } from 'lucide-react';

function toNumber(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export default function ProductList() {
  const location = useLocation();
  const catFromUrl = useMemo(() => {
    const qs = new URLSearchParams(location.search);
    const v = qs.get('cat');
    return v ? Number(v) : null;
  }, [location.search]);

  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [activeCatId, setActiveCatId] = useState(null);

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  const [q, setQ] = useState('');
  const [brandId, setBrandId] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [sort, setSort] = useState('newest'); // newest | price_asc | price_desc
  const [page, setPage] = useState(1);
  const pageSize = 16;

  useEffect(() => {
    setErr('');
    // categories (for label)
    axios
      .get(`${PRODUCT_SERVICE_URL}/api/v1/categories/`, {
        params: { is_active: true, page_size: 200, _: Date.now() },
      })
      .then((res) => {
        const rows = res.data?.results ?? res.data ?? [];
        const list = Array.isArray(rows) ? rows : [];
        setCategories(list);
        if (catFromUrl && list.some((c) => Number(c.id) === Number(catFromUrl))) setActiveCatId(catFromUrl);
        else setActiveCatId(null);
      })
      .catch(() => setCategories([]));

    // brands for filter
    axios
      .get(`${PRODUCT_SERVICE_URL}/api/v1/brands/`, {
        params: { is_active: true, page_size: 200, _: Date.now() },
      })
      .then((res) => {
        const rows = res.data?.results ?? res.data ?? [];
        setBrands(Array.isArray(rows) ? rows : []);
      })
      .catch(() => setBrands([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setActiveCatId(catFromUrl || null);
    setQ('');
    setPage(1);
  }, [catFromUrl, activeCatId]);

  useEffect(() => {
    setLoading(true);
    setErr('');
    const url = activeCatId
      ? `${PRODUCT_SERVICE_URL}/api/v1/products/by-category/${activeCatId}/`
      : `${PRODUCT_SERVICE_URL}/api/v1/products/`;
    axios
      .get(url, { params: { page_size: 500, _: Date.now() } })
      .then((res) => {
        const rows = res.data?.results ?? res.data ?? [];
        setProducts(Array.isArray(rows) ? rows : []);
        setPage(1);
      })
      .catch((e) => {
        setErr(e.response?.data?.detail || 'Không tải được sản phẩm theo danh mục');
        setProducts([]);
      })
      .finally(() => setLoading(false));
  }, [activeCatId]);

  const filtered = useMemo(() => {
    const q2 = q.trim().toLowerCase();
    const min = toNumber(minPrice);
    const max = toNumber(maxPrice);
    const bid = brandId ? Number(brandId) : null;

    let rows = products.slice();
    if (q2) {
      rows = rows.filter((p) => (p.name || '').toLowerCase().includes(q2));
    }
    if (bid) {
      rows = rows.filter((p) => Number(p.brand) === bid);
    }
    if (min != null) {
      rows = rows.filter((p) => Number(p.price || 0) >= min);
    }
    if (max != null) {
      rows = rows.filter((p) => Number(p.price || 0) <= max);
    }

    if (sort === 'price_asc') {
      rows.sort((a, b) => Number(a.price || 0) - Number(b.price || 0));
    } else if (sort === 'price_desc') {
      rows.sort((a, b) => Number(b.price || 0) - Number(a.price || 0));
    } else {
      // newest (best effort: fallback to id desc if created_at missing)
      rows.sort((a, b) => {
        const da = Date.parse(a.created_at || '') || 0;
        const db = Date.parse(b.created_at || '') || 0;
        if (da !== db) return db - da;
        return Number(b.id || 0) - Number(a.id || 0);
      });
    }

    return rows;
  }, [products, q, brandId, minPrice, maxPrice, sort]);

  useEffect(() => {
    setPage(1);
  }, [q, brandId, minPrice, maxPrice, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageClamped = Math.min(Math.max(1, page), totalPages);
  const pageItems = useMemo(() => {
    const start = (pageClamped - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, pageClamped]);

  const activeCat = categories.find((c) => Number(c.id) === Number(activeCatId));

  return (
    <div className="space-y-6">
      {/* Search + filters */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-bold text-gray-800">Sản phẩm</h1>
          <span className="text-xs text-gray-500">{activeCat ? activeCat.name : 'Tất cả sản phẩm'}</span>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Tìm sản phẩm…"
              className="w-full border border-gray-200 rounded-xl pl-10 pr-10 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            />
            {q.trim() && (
              <button
                type="button"
                onClick={() => setQ('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-700"
                title="Xóa tìm kiếm"
              >
                <X size={16} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <SlidersHorizontal size={18} className="text-gray-400" />
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="newest">Mới nhất</option>
              <option value="price_asc">Giá tăng dần</option>
              <option value="price_desc">Giá giảm dần</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <select
            value={brandId}
            onChange={(e) => setBrandId(e.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-white outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tất cả hãng</option>
            {brands.map((b) => (
              <option key={`brand-${b.id}`} value={String(b.id)}>
                {b.name}
              </option>
            ))}
          </select>
          <input
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            placeholder="Giá từ"
            className="border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            placeholder="Giá đến"
            className="border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={() => {
              setBrandId('');
              setMinPrice('');
              setMaxPrice('');
              setSort('newest');
              setQ('');
            }}
            className="border border-gray-200 rounded-xl px-3 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50"
          >
            Reset filter
          </button>
        </div>
      </div>

      {err && <div className="text-sm text-red-700 bg-red-50 border border-red-100 p-3 rounded-xl">{err}</div>}

      {loading ? (
        <div className="text-center py-12 text-gray-500">Đang tải…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500">Không có sản phẩm phù hợp.</div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            Hiển thị {pageItems.length} / {filtered.length} sản phẩm
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {pageItems.map((p) => (
              <ProductCard p={p} key={`pl-${p.id}`} />
            ))}
          </div>

          <div className="flex items-center justify-center gap-2 pt-2">
            <button
              type="button"
              disabled={pageClamped <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-2 rounded-lg border border-gray-200 text-sm font-semibold text-gray-700 disabled:opacity-50 hover:bg-gray-50"
            >
              Trước
            </button>
            <div className="text-sm text-gray-600 px-2">
              Trang {pageClamped} / {totalPages}
            </div>
            <button
              type="button"
              disabled={pageClamped >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-2 rounded-lg border border-gray-200 text-sm font-semibold text-gray-700 disabled:opacity-50 hover:bg-gray-50"
            >
              Sau
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
