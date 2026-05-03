export const GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8080';
// Use gateway by default to avoid CORS and centralize auth rules.
export const PRODUCT_SERVICE_URL = import.meta.env.VITE_PRODUCT_SERVICE_URL || `${GATEWAY_URL}/api/products`;
export const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8002';

export const cartApiBase = `${GATEWAY_URL}/api/cart/api/v1`;
export const orderApiBase = `${GATEWAY_URL}/api/order/api/v1`;
export const paymentApiBase = `${GATEWAY_URL}/api/payment/api/v1`;
export const customersApiBase = `${GATEWAY_URL}/api/customers`;
export const interactionsApiBase = `${GATEWAY_URL}/api/customers/api/interactions`;
