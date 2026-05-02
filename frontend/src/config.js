export const GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8080';
export const PRODUCT_SERVICE_URL = import.meta.env.VITE_PRODUCT_SERVICE_URL || 'http://localhost:8001';
export const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8002';

export const cartApiBase = `${GATEWAY_URL}/api/cart/api/v1`;
export const orderApiBase = `${GATEWAY_URL}/api/order/api/v1`;
export const paymentApiBase = `${GATEWAY_URL}/api/payment/api/v1`;
export const customersApiBase = `${GATEWAY_URL}/api/customers`;
