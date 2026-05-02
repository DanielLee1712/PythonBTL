import axios from 'axios';
import { PRODUCT_SERVICE_URL } from '../config';

/**
 * Fetch products by ids; bustCache avoids stale GET after stock changes (browser/proxy cache).
 */
export async function fetchProductsByIds(ids, { bustCache = false } = {}) {
  const idStr = Array.isArray(ids) ? ids.filter(Boolean).join(',') : String(ids);
  const params = { ids: idStr };
  if (bustCache) params._ = Date.now();
  const res = await axios.get(`${PRODUCT_SERVICE_URL}/api/v1/products/`, {
    params,
  });
  const rows = res.data.results ?? res.data;
  return Array.isArray(rows) ? rows : [];
}

export async function fetchProductByIdOrSlug(idOrSlug, { bustCache = false } = {}) {
  const s = String(idOrSlug ?? '').trim();
  if (!s) return null;

  // Prefer numeric id list endpoint
  const asNum = Number(s);
  if (Number.isFinite(asNum) && String(asNum) === s) {
    const rows = await fetchProductsByIds(asNum, { bustCache });
    return pickProductRow(rows, asNum) || null;
  }

  // Fallback: slug lookup (backend uses lookup_field='slug')
  const params = {};
  if (bustCache) params._ = Date.now();
  const res = await axios.get(`${PRODUCT_SERVICE_URL}/api/v1/products/${encodeURIComponent(s)}/`, {
    params,
  });
  return res.data || null;
}

export function pickProductRow(rows, productId) {
  const pid = Number(productId);
  return rows.find((r) => Number(r.id) === pid);
}
