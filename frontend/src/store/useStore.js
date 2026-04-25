import { create } from 'zustand';
import axios from 'axios';
import { trackBehavior } from '../utils/tracking';

const API_URL = 'http://localhost:8080/api/cart/api/v1/cart';

export const useStore = create((set, get) => ({
  user: { id: 1, username: 'customer1' }, // Dummy user for testing
  cart: [],
  
  setUser: (user) => {
    set({ user });
    if (user) {
      get().fetchCart();
    } else {
      set({ cart: [] });
    }
  },

  fetchCart: async () => {
    const { user } = get();
    if (!user) return;
    try {
      const res = await axios.get(`${API_URL}/?user_id=${user.id}`);
      const formattedCart = res.data.items.map(item => ({
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

  addToCart: async (product) => {
    const { user, fetchCart } = get();
    if (!user) return;
    try {
      await axios.post(`${API_URL}/items/`, {
        user_id: user.id,
        product_id: product.id,
        product_name: product.title || product.name,
        category_name: product.category_name || '',
        unit_price: product.price,
        quantity: 1,
      });
      await fetchCart();
    } catch (e) {
      console.error('Failed to add to cart', e);
    }
  },

  removeFromCart: async (productId) => {
    const { user, cart, fetchCart } = get();
    if (!user) return;
    const item = cart.find(c => c.id === productId);
    if (!item || !item.cartItemId) return;
    try {
      await axios.delete(`${API_URL}/items/${item.cartItemId}/?user_id=${user.id}`);
      await fetchCart();
      // Track action
      trackBehavior(user.id, productId, 'remove_from_cart');
    } catch (e) {
      console.error('Failed to remove from cart', e);
    }
  },

  updateQuantity: async (productId, quantity) => {
    const { user, cart, fetchCart } = get();
    if (!user) return;
    const item = cart.find(c => c.id === productId);
    if (!item || !item.cartItemId) return;
    try {
      await axios.patch(`${API_URL}/items/${item.cartItemId}/`, {
        user_id: user.id,
        quantity: quantity,
      });
      await fetchCart();
    } catch (e) {
      console.error('Failed to update quantity', e);
    }
  },

  clearCart: async () => {
    const { user, fetchCart } = get();
    if (!user) return;
    try {
      await axios.delete(`${API_URL}/clear/?user_id=${user.id}`);
      await fetchCart();
    } catch (e) {
      console.error('Failed to clear cart', e);
    }
  }
}));
