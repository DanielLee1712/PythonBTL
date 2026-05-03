import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { GATEWAY_URL } from '../config';

function ProductThumb({ product, size = 48 }) {
  const url = (product?.image_url || '').trim();
  const label = (product?.category_name || 'SP').toString().slice(0, 10);
  if (url) {
    return (
      <img
        src={url}
        alt={product?.name || 'product'}
        className="rounded-xl object-cover border bg-white"
        style={{ width: size, height: size }}
        onError={(e) => {
          // fallback to placeholder
          e.currentTarget.style.display = 'none';
        }}
      />
    );
  }
  return (
    <div
      className="rounded-xl border bg-white text-gray-400 font-bold text-[10px] flex items-center justify-center text-center leading-tight"
      style={{ width: size, height: size }}
      title={product?.category_name || 'SP'}
    >
      {label}
    </div>
  );
}

export default function Staff() {
  const user = useStore((s) => s.user);
  const canAccess = Boolean(user?.isStaff || user?.isAdmin);

  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;
  const authHeaders = useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token]
  );

  const api = useMemo(
    () => ({
      products: `${GATEWAY_URL}/api/products/api/v1/products/`,
      adjustStock: `${GATEWAY_URL}/api/products/api/v1/products/adjust-stock/`,
      categories: `${GATEWAY_URL}/api/products/api/v1/categories/`,
      brands: `${GATEWAY_URL}/api/products/api/v1/brands/`,
      productTypes: `${GATEWAY_URL}/api/products/api/v1/product-types/`,
    }),
    []
  );

  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const [editing, setEditing] = useState(null); // product object or null
  const [form, setForm] = useState({
    name: '',
    description: '',
    price: '',
    image_url: '',
    is_active: true,
    category: '',
    brand: '',
    product_type: '',
    attributes: '{}',
  });
  const [stockTarget, setStockTarget] = useState('');

  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [productTypes, setProductTypes] = useState([]);

  const loadMeta = async () => {
    if (!canAccess) return;
    try {
      const [c, b, t] = await Promise.all([
        axios.get(api.categories, { params: { page_size: 200, _: Date.now() } }),
        axios.get(api.brands, { params: { page_size: 200, _: Date.now() } }),
        axios.get(api.productTypes, { params: { page_size: 200, _: Date.now() } }),
      ]);
      setCategories(c.data?.results ?? c.data ?? []);
      setBrands(b.data?.results ?? b.data ?? []);
      setProductTypes(t.data?.results ?? t.data ?? []);
    } catch {
      // metadata is optional for basic CRUD
    }
  };

  const load = async () => {
    if (!canAccess) return;
    setBusy(true);
    setMsg('');
    try {
      const res = await axios.get(api.products, {
        headers: authHeaders,
        params: { page, page_size: pageSize, search: search || undefined, _: Date.now() },
      });
      const data = res.data;
      const list = data.results ?? data ?? [];
      setRows(Array.isArray(list) ? list : []);
      setCount(Number(data.count ?? (Array.isArray(list) ? list.length : 0)));
    } catch (err) {
      const d2 = err.response?.data;
      setMsg(d2?.detail || d2?.error || err.message || 'Không tải được danh sách sản phẩm');
      setRows([]);
      setCount(0);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    loadMeta();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canAccess, page]);

  const openCreate = () => {
    setEditing({ __new: true });
    setForm({
      name: '',
      description: '',
      price: '',
      image_url: '',
      is_active: true,
      category: '',
      brand: '',
      product_type: '',
      attributes: '{}',
    });
    setStockTarget('');
    setMsg('');
  };

  const openEdit = async (p) => {
    setBusy(true);
    setMsg('');
    try {
      const res = await axios.get(`${api.products}${encodeURIComponent(p.slug)}/`, {
        headers: authHeaders,
        params: { _: Date.now() },
      });
      const full = res.data || p;
      setEditing(full);
      setForm({
        name: full.name ?? '',
        description: full.description ?? '',
        price: String(full.price ?? ''),
        image_url: full.image_url ?? '',
        is_active: Boolean(full.is_active),
        category: full.category ?? '',
        brand: full.brand ?? '',
        product_type: full.product_type ?? '',
        attributes: JSON.stringify(full.attributes ?? {}, null, 2),
      });
      setStockTarget(String(full.quantity ?? ''));
    } catch (err) {
      const d2 = err.response?.data;
      setMsg(d2?.detail || d2?.error || err.message || 'Không tải được chi tiết sản phẩm');
    } finally {
      setBusy(false);
    }
  };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg('');
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description ?? '',
        price: form.price === '' ? 0 : Number(form.price),
        image_url: form.image_url ?? '',
        is_active: Boolean(form.is_active),
        category: form.category === '' ? null : Number(form.category),
        brand: form.brand === '' ? null : Number(form.brand),
        product_type: form.product_type === '' ? null : Number(form.product_type),
        attributes: (() => {
          try {
            return JSON.parse(form.attributes || '{}');
          } catch {
            return {};
          }
        })(),
      };

      let saved = null;
      if (editing?.__new) {
        const res = await axios.post(api.products, payload, { headers: authHeaders });
        saved = res.data;
      } else if (editing?.slug) {
        const res = await axios.patch(`${api.products}${encodeURIComponent(editing.slug)}/`, payload, {
          headers: authHeaders,
        });
        saved = res.data;
      }

      // Stock target: update via adjust-stock (quantity is read-only in serializer)
      const target = stockTarget === '' ? null : Number(stockTarget);
      const current = Number(saved?.quantity ?? editing?.quantity ?? 0);
      if (saved && target != null && Number.isFinite(target) && target >= 0 && target !== current) {
        await axios.post(
          api.adjustStock,
          { product_id: saved.id, delta: target - current },
          { headers: authHeaders }
        );
      }

      setEditing(null);
      await load();
      setMsg('Lưu thành công.');
    } catch (err) {
      const d2 = err.response?.data;
      setMsg(d2?.detail || d2?.error || err.message || 'Lưu thất bại');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (p) => {
    if (!window.confirm(`Xóa sản phẩm "${p.name}"?`)) return;
    setBusy(true);
    setMsg('');
    try {
      await axios.delete(`${api.products}${encodeURIComponent(p.slug)}/`, { headers: authHeaders });
      await load();
      setMsg('Đã xóa sản phẩm.');
    } catch (err) {
      const d2 = err.response?.data;
      setMsg(d2?.detail || d2?.error || err.message || 'Xóa thất bại');
    } finally {
      setBusy(false);
    }
  };

  if (!canAccess) {
    return (
      <div className="max-w-xl mx-auto bg-white rounded-2xl p-8 border text-center">
        <p className="text-gray-700 font-semibold">Bạn không có quyền Staff/Admin.</p>
        <p className="text-sm text-gray-500 mt-2">Hãy đăng nhập bằng tài khoản staff hoặc admin.</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Quản lý sản phẩm</h1>
          <p className="text-sm text-gray-500">CRUD sản phẩm, ảnh (URL), tồn kho.</p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2.5 rounded-xl"
        >
          + Thêm sản phẩm
        </button>
      </div>

      <div className="bg-white rounded-2xl border p-4 flex flex-wrap items-center gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Tìm theo tên…"
          className="border border-gray-200 rounded-xl px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 w-64"
        />
        <button
          type="button"
          onClick={() => {
            setPage(1);
            load();
          }}
          className="bg-gray-900 hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-xl text-sm"
        >
          Tìm
        </button>
        <div className="ml-auto text-sm text-gray-500">
          {busy ? 'Đang tải…' : `Tổng: ${count}`}
        </div>
      </div>

      {msg && <div className="text-sm text-gray-800 bg-gray-50 border rounded-xl p-3">{msg}</div>}

      <div className="bg-white rounded-2xl border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-4 py-3">Ảnh</th>
                <th className="text-left px-4 py-3">ID</th>
                <th className="text-left px-4 py-3">Tên</th>
                <th className="text-left px-4 py-3">Giá</th>
                <th className="text-left px-4 py-3">Tồn</th>
                <th className="text-left px-4 py-3">Active</th>
                <th className="text-left px-4 py-3">Ảnh (URL)</th>
                <th className="text-right px-4 py-3">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rows.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <ProductThumb product={p} size={44} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{p.id}</td>
                  <td className="px-4 py-3 font-semibold text-gray-800">{p.name}</td>
                  <td className="px-4 py-3">{Number(p.price || 0).toLocaleString('vi-VN')} ₫</td>
                  <td className="px-4 py-3">{p.quantity ?? 0}</td>
                  <td className="px-4 py-3">{p.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500 break-all">{p.image_url || '-'}</span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      type="button"
                      onClick={() => openEdit(p)}
                      className="text-blue-600 font-semibold hover:underline"
                    >
                      Sửa
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(p)}
                      className="text-red-600 font-semibold hover:underline"
                    >
                      Xóa
                    </button>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-gray-500">
                    Không có dữ liệu.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between p-4 border-t bg-gray-50 text-sm">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="px-3 py-1.5 rounded-lg border bg-white disabled:opacity-50"
          >
            ← Trang trước
          </button>
          <div className="text-gray-600">Trang {page}</div>
          <button
            type="button"
            disabled={rows.length < pageSize}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 rounded-lg border bg-white disabled:opacity-50"
          >
            Trang sau →
          </button>
        </div>
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50">
          <div className="bg-white w-full max-w-2xl rounded-2xl border shadow-lg p-6 space-y-4 max-h-[92vh] overflow-hidden">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800">
                {editing.__new ? 'Thêm sản phẩm' : `Sửa: ${editing.name}`}
              </h2>
              <button
                type="button"
                onClick={() => setEditing(null)}
                className="text-gray-500 hover:text-gray-800"
              >
                ✕
              </button>
            </div>

            <form onSubmit={save} className="space-y-3 overflow-y-auto pr-1" style={{ maxHeight: 'calc(92vh - 92px)' }}>
              <div className="flex items-center gap-3 bg-gray-50 border rounded-xl p-3">
                <ProductThumb
                  product={{
                    ...editing,
                    name: form.name,
                    image_url: form.image_url,
                  }}
                  size={56}
                />
                <div className="text-sm text-gray-700">
                  <div className="font-semibold">{form.name || '(Chưa có tên)'}</div>
                  <div className="text-xs text-gray-500">Preview ảnh (nếu URL trống sẽ dùng ảnh mặc định).</div>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Tên</label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Giá</label>
                  <input
                    value={form.price}
                    onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Ảnh (image_url)</label>
                  <input
                    value={form.image_url}
                    onChange={(e) => setForm((f) => ({ ...f, image_url: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://..."
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Mô tả</label>
                  <textarea
                    rows={3}
                    value={form.description}
                    onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Category ID</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">(None)</option>
                    {categories.map((c) => (
                      <option key={`c-${c.id}`} value={String(c.id)}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Brand ID</label>
                  <select
                    value={form.brand}
                    onChange={(e) => setForm((f) => ({ ...f, brand: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">(None)</option>
                    {brands.map((b) => (
                      <option key={`b-${b.id}`} value={String(b.id)}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Product Type ID</label>
                  <select
                    value={form.product_type}
                    onChange={(e) => setForm((f) => ({ ...f, product_type: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">(None)</option>
                    {productTypes.map((t) => (
                      <option key={`t-${t.id}`} value={String(t.id)}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Tồn kho (set giá trị)</label>
                  <input
                    type="number"
                    value={stockTarget}
                    onChange={(e) => setStockTarget(e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="(optional)"
                    min={0}
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Attributes (JSON)</label>
                  <textarea
                    rows={5}
                    value={form.attributes}
                    onChange={(e) => setForm((f) => ({ ...f, attributes: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm font-mono outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                  />
                  Active
                </label>
              </div>

              {msg && <div className="text-sm text-gray-800 bg-gray-50 border rounded-xl p-3">{msg}</div>}

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setEditing(null)}
                  className="px-4 py-2.5 rounded-xl border font-semibold"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-60"
                >
                  {busy ? 'Đang lưu…' : 'Lưu'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

