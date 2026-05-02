import { create } from 'zustand';
import axios from 'axios';
import { trackBehavior } from '../utils/tracking';
import { cartApiBase } from '../config';

const CART_URL = `${cartApiBase}/cart`;

function decodeUserFromToken(token) {
  if (!token) return null;
  try {
    const payloadBase64 = token.split('.')[1];
    const base64 = payloadBase64.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const payload = JSON.parse(jsonPayload);
    const id = payload.user_id ?? payload.sub ?? payload.id;
    const savedUsername =
      typeof localStorage !== 'undefined' ? localStorage.getItem('username') : null;
    const username = payload.username ?? payload.name ?? savedUsername ?? 'user';
    if (!id) return null;
    return { id: Number(id), username: String(username) };
  } catch {
    return null;
  }
}

const initialUser = decodeUserFromToken(
  typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null
);

export const useStore = create((set, get) => ({
  user: initialUser,
  cart: [],

  setUser: (user) => {
    set({ user });
    if (!user) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ cart: [] });
    } else {
      get().fetchCart();
    }
  },

  fetchCart: async () => {
    const { user } = get();
    if (!user) return;
    try {
      const res = await axios.get(`${CART_URL}/?user_id=${user.id}`);
      const formattedCart = (res.data.items || []).map((item) => ({
        id: item.product_id,
        cartItemId: item.id,
        name: item.product_name,
        title: item.product_name,
        category_name: item.category_name,
        price: item.unit_price,
        quantity: item.quantity,
      }));
      set({ cart: formattedCart });
    } catch (e) {
      console.error('Failed to fetch cart', e);
    }
  },

  addToCart: async (product, quantity = 1) => {
    const { user, fetchCart } = get();
    if (!user) return { ok: false, error: 'Chưa đăng nhập' };
    const qty = Math.max(1, Math.min(Number(quantity) || 1, 9999));
    try {
      await axios.post(`${CART_URL}/items/`, {
        user_id: user.id,
        product_id: product.id,
        product_name: product.title || product.name,
        category_name: product.category_name || '',
        unit_price: product.price,
        quantity: qty,
      });
      await fetchCart();
      return { ok: true };
    } catch (e) {
      const msg =
        e.response?.data?.detail ||
        e.response?.data?.error ||
        e.message ||
        'Không thể thêm vào giỏ';
      console.error('Failed to add to cart', e);
      return { ok: false, error: typeof msg === 'string' ? msg : JSON.stringify(msg) };
    }
  },

  removeFromCart: async (productId) => {
    const { user, cart, fetchCart } = get();
    if (!user) return;
    const item = cart.find((c) => c.id === productId);
    if (!item || !item.cartItemId) return;
    try {
      await axios.delete(`${CART_URL}/items/${item.cartItemId}/?user_id=${user.id}`);
      await fetchCart();
      trackBehavior(user.id, productId, 'remove_from_cart');
    } catch (e) {
      console.error('Failed to remove from cart', e);
    }
  },

  updateQuantity: async (productId, quantity) => {
    const { user, cart, fetchCart } = get();
    if (!user) return { ok: false, error: 'Chưa đăng nhập' };
    const item = cart.find((c) => c.id === productId);
    if (!item || !item.cartItemId) return { ok: false, error: 'Không tìm thấy dòng giỏ' };
    try {
      await axios.patch(`${CART_URL}/items/${item.cartItemId}/`, {
        user_id: user.id,
        quantity,
      });
      await fetchCart();
      return { ok: true };
    } catch (e) {
      const msg =
        e.response?.data?.detail ||
        e.response?.data?.error ||
        e.message ||
        'Không đủ tồn kho';
      console.error('Failed to update quantity', e);
      return { ok: false, error: typeof msg === 'string' ? msg : JSON.stringify(msg) };
    }
  },

  clearCart: async () => {
    const { user, fetchCart } = get();
    if (!user) return;
    try {
      await axios.delete(`${CART_URL}/clear/?user_id=${user.id}`);
      await fetchCart();
    } catch (e) {
      console.error('Failed to clear cart', e);
    }
  },

  checkout: async ({ shipping_address, shipping_method }) => {
    const { user } = get();
    if (!user) return { ok: false, error: 'Chưa đăng nhập' };
    try {
      const res = await axios.post(`${cartApiBase}/orders/checkout/`, {
        user_id: user.id,
        shipping_address,
        shipping_method,
      });
      return { ok: true, order: res.data };
    } catch (e) {
      const d = e.response?.data;
      const msg =
        (typeof d?.detail === 'string' ? d.detail : null) ||
        (Array.isArray(d?.shipping_address) ? d.shipping_address[0] : null) ||
        e.message ||
        'Checkout thất bại';
      return { ok: false, error: msg };
    }
  },
}));
