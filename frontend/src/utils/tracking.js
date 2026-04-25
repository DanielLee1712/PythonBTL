import axios from 'axios';

/**
 * Gửi action của người dùng lên hệ thống AI để cập nhật vào Neo4j Knowledge Graph.
 *
 * Các action được hỗ trợ:
 * - 'view'
 * - 'add_to_cart'
 * - 'remove_from_cart'
 * - 'purchase'
 * - 'search'
 * - 'rate'
 * - 'wishlist'
 * - 'click'
 *
 * @param {string|number} userId - ID của người dùng (bắt buộc)
 * @param {string|number} productId - ID của sản phẩm (bắt buộc)
 * @param {string} action - Tên action (bắt buộc)
 */
export const trackBehavior = async (userId, productId, action) => {
  if (!userId || !productId) return;
  try {
    await axios.post('http://localhost:8002/api/v1/track-behavior/', {
      user_id: userId,
      product_id: productId,
      action: action.toLowerCase()
    });
  } catch (error) {
    console.error(`Graph Tracking Failed for action: ${action}`, error);
  }
};
