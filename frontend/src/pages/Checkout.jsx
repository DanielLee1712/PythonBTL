import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, MapPin, Truck } from 'lucide-react';
import { useStore } from '../store/useStore';
import { paymentApiBase } from '../config';
import { trackBehavior } from '../utils/tracking';

const SHIPPING_OPTIONS = [
  { id: 'standard', label: 'Standard (3–5 days)', fee: 30000 },
  { id: 'express', label: 'Express (1–2 days)', fee: 60000 },
  { id: 'same_day', label: 'Same day (within city)', fee: 120000 },
];

function buildShippingAddress({ fullName, phone, addressLine, city, note }) {
  const parts = [
    `Họ tên: ${fullName.trim()}`,
    `SĐT: ${phone.trim()}`,
    `Địa chỉ: ${addressLine.trim()}`,
    `Thành phố: ${city.trim()}`,
  ];
  if (note.trim()) parts.push(`Ghi chú: ${note.trim()}`);
  return parts.join('\n');
}

export default function Checkout() {
  const navigate = useNavigate();
  const user = useStore((s) => s.user);
  const cart = useStore((s) => s.cart);
  const checkout = useStore((s) => s.checkout);

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [addressLine, setAddressLine] = useState('');
  const [city, setCity] = useState('');
  const [note, setNote] = useState('');
  const [method, setMethod] = useState('express');
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState('');

  const subtotal = useMemo(
    () => cart.reduce((s, i) => s + Number(i.price) * i.quantity, 0),
    [cart]
  );
  const fee = SHIPPING_OPTIONS.find((o) => o.id === method)?.fee ?? 0;
  const grandTotal = subtotal + fee;

  const formatPrice = (v) => Number(v || 0).toLocaleString('vi-VN');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr('');
    if (!user) {
      navigate('/login');
      return;
    }
    if (cart.length === 0) {
      navigate('/cart');
      return;
    }
    if (fullName.trim().length < 2) {
      setErr('Vui lòng nhập họ tên.');
      return;
    }
    if (phone.trim().length < 8) {
      setErr('Vui lòng nhập số điện thoại hợp lệ.');
      return;
    }
    if (addressLine.trim().length < 4) {
      setErr('Vui lòng nhập địa chỉ (số nhà, đường…).');
      return;
    }
    if (city.trim().length < 2) {
      setErr('Vui lòng nhập thành phố / tỉnh.');
      return;
    }
    const trimmed = buildShippingAddress({ fullName, phone, addressLine, city, note });
    if (trimmed.length < 8) {
      setErr('Vui lòng điền đầy đủ thông tin giao hàng.');
      return;
    }
    setSubmitting(true);
    for (const item of cart) {
      await trackBehavior(user.id, item.id, 'purchase');
    }
    const res = await checkout({
      shipping_address: trimmed,
      shipping_method: method,
    });
    if (!res.ok) {
      setSubmitting(false);
      setErr(res.error || 'Không tạo được đơn hàng');
      return;
    }
    const orderId = res.order?.id;
    try {
      const init = await axios.post(`${paymentApiBase}/payments/init/`, {
        order_id: orderId,
        user_id: user.id,
      });
      if (init.data?.vnpay_payment_url) {
        window.location.href = init.data.vnpay_payment_url;
        return;
      }
    } catch (e) {
      setErr(e.response?.data?.detail || 'Không khởi tạo được thanh toán VNPAY');
    }
    setSubmitting(false);
    navigate(`/orders/${orderId}`);
  };

  if (!user) {
    return (
      <div className="max-w-xl mx-auto bg-white rounded-2xl p-8 border text-center">
        <p className="text-gray-600 mb-4">Đăng nhập để thanh toán.</p>
        <Link to="/login" className="text-blue-600 font-semibold">
          Đăng nhập
        </Link>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="max-w-xl mx-auto bg-white rounded-2xl p-8 border text-center space-y-4">
        <p className="text-gray-600">Giỏ hàng trống.</p>
        <Link to="/cart" className="text-blue-600 font-semibold">
          Về giỏ hàng
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/cart" className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600 text-sm">
        <ArrowLeft size={16} /> Giỏ hàng
      </Link>

      <h1 className="text-2xl font-bold text-gray-800">Thanh toán</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-6">
        {err && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">{err}</div>
        )}

        <section className="space-y-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
            <MapPin size={18} className="text-blue-600" />
            Địa chỉ giao hàng
          </p>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Họ và tên</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Nguyễn Văn A"
                autoComplete="name"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Số điện thoại</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="09xxxxxxxx"
                autoComplete="tel"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Địa chỉ (số nhà, đường, phường/xã)</label>
              <input
                type="text"
                value={addressLine}
                onChange={(e) => setAddressLine(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="255 Mộ Lao"
                autoComplete="street-address"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Thành phố / Tỉnh</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Hà Nội"
                autoComplete="address-level2"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ghi chú (tùy chọn)</label>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Hàng dễ vỡ…"
              />
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
            <Truck size={18} className="text-blue-600" />
            Hình thức vận chuyển
          </p>
          <div className="space-y-2">
            {SHIPPING_OPTIONS.map((opt) => (
              <label
                key={opt.id}
                className={`flex items-center justify-between gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                  method === opt.id ? 'border-blue-500 bg-blue-50/50' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <span className="flex items-center gap-3">
                  <input
                    type="radio"
                    name="ship"
                    value={opt.id}
                    checked={method === opt.id}
                    onChange={() => setMethod(opt.id)}
                    className="text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-800">{opt.label}</span>
                </span>
                <span className="text-sm font-bold text-blue-600 shrink-0">Fee: {formatPrice(opt.fee)} đ</span>
              </label>
            ))}
          </div>
        </section>

        <div className="border-t border-gray-100 pt-4 space-y-2 text-sm">
          <div className="flex justify-between text-gray-600">
            <span>Items</span>
            <span className="font-medium text-gray-900">{formatPrice(subtotal)} đ</span>
          </div>
          <div className="flex justify-between text-gray-600">
            <span>Shipping</span>
            <span className="font-medium text-gray-900">{formatPrice(fee)} đ</span>
          </div>
          <div className="flex justify-between text-lg font-black text-blue-600 pt-2">
            <span>Total</span>
            <span>{formatPrice(grandTotal)} đ</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-bold py-4 rounded-xl shadow-lg transition-all"
        >
          {submitting ? 'Đang xử lý…' : 'Pay with VNPAY'}
        </button>
        <p className="text-xs text-gray-500 text-center">
          Bạn sẽ sang trang VNPAY (sandbox) để nhập thẻ test — không nhập thẻ trên ElecStore.{' '}
          <a
            href="https://sandbox.vnpayment.vn/apis/vnpay-demo/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline"
          >
            Hướng dẫn thẻ test
          </a>
        </p>
      </form>
    </div>
  );
}
