import { useEffect, useState, useCallback, useRef } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Clock, XCircle, RefreshCw, ExternalLink } from 'lucide-react';
import { useStore } from '../store/useStore';
import { orderApiBase, paymentApiBase } from '../config';

const statusLabel = {
  pending_payment: 'Chờ thanh toán (5 phút)',
  paid: 'Đã thanh toán',
  cancelled: 'Đã hủy',
  expired: 'Hết hạn thanh toán',
};

export default function OrderDetail() {
  const { id } = useParams();
  const user = useStore((s) => s.user);
  const [order, setOrder] = useState(null);
  const [vnpayPaymentUrl, setVnpayPaymentUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [now, setNow] = useState(Date.now());
  const prevSecondsLeft = useRef(null);

  const load = useCallback(async () => {
    if (!user || !id) return;
    setLoading(true);
    setErr('');
    try {
      const res = await axios.get(`${orderApiBase}/orders/${id}/?user_id=${user.id}`);
      const o = res.data;
      setOrder(o);
      setVnpayPaymentUrl(null);
      if (o.status === 'pending_payment') {
        try {
          const pr = await axios.post(`${paymentApiBase}/payments/init/`, {
            order_id: o.id,
            user_id: user.id,
          });
          setVnpayPaymentUrl(pr.data.vnpay_payment_url || null);
        } catch {
          setVnpayPaymentUrl(null);
        }
      }
    } catch (e) {
      setErr(e.response?.data?.detail || 'Không tải được đơn hàng');
      setOrder(null);
    } finally {
      setLoading(false);
    }
  }, [user, id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    prevSecondsLeft.current = null;
  }, [order?.id]);

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!order || order.status !== 'pending_payment') {
      prevSecondsLeft.current = null;
      return;
    }
    const deadline = order.payment_deadline ? new Date(order.payment_deadline).getTime() : 0;
    if (!deadline) return;
    const left = Math.max(0, Math.floor((deadline - now) / 1000));
    const prev = prevSecondsLeft.current;
    prevSecondsLeft.current = left;
    if (prev !== null && prev > 0 && left === 0) {
      load();
    }
  }, [now, order, load]);

  const cancel = async () => {
    if (!user || !id) return;
    if (!window.confirm('Hủy đơn hàng này? Tồn kho sẽ được hoàn lại.')) return;
    try {
      const res = await axios.post(`${orderApiBase}/orders/${id}/cancel/`, { user_id: user.id });
      setOrder(res.data);
      setVnpayPaymentUrl(null);
    } catch (e) {
      setErr(e.response?.data?.detail || 'Không hủy được đơn');
    }
  };

  const retryPay = async () => {
    if (!user || !id) return;
    try {
      await axios.post(`${orderApiBase}/orders/${id}/retry-payment/`, {
        user_id: user.id,
      });
      setErr('');
      await load();
    } catch (e) {
      setErr(e.response?.data?.detail || 'Không thể mở lại thanh toán');
    }
  };

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto bg-white rounded-2xl p-8 text-center border">
        <Link to="/login" className="text-blue-600 font-semibold">
          Đăng nhập
        </Link>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Đang tải…</div>;
  }

  if (!order) {
    return (
      <div className="max-w-2xl mx-auto bg-white rounded-2xl p-8 border text-center">
        <p className="text-red-600 mb-4">{err || 'Không tìm thấy đơn.'}</p>
        <Link to="/orders" className="text-blue-600">
          ← Danh sách đơn
        </Link>
      </div>
    );
  }

  const deadline = order.payment_deadline ? new Date(order.payment_deadline).getTime() : 0;
  const secondsLeft =
    order.status === 'pending_payment' && deadline
      ? Math.max(0, Math.floor((deadline - now) / 1000))
      : 0;
  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, '0');
  const ss = String(secondsLeft % 60).padStart(2, '0');

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/orders" className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600 text-sm">
        <ArrowLeft size={16} /> Danh sách đơn
      </Link>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
        <div className="flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-800">Đơn #{order.id}</h1>
            <p className="text-gray-500 text-sm mt-1">{statusLabel[order.status] || order.status}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Tổng thanh toán</p>
            <p className="text-2xl font-black text-blue-600">
              {Number(order.total || 0).toLocaleString('vi-VN')} ₫
            </p>
          </div>
        </div>

        {err && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">{err}</div>
        )}

        {(order.shipping_address || order.shipping_method) && (
          <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-4 text-sm space-y-2">
            <p className="font-semibold text-gray-800">Giao hàng</p>
            {order.shipping_method_label && (
              <p className="text-gray-700">
                <span className="text-gray-500">Hình thức:</span> {order.shipping_method_label}
              </p>
            )}
            {order.shipping_address && (
              <p className="text-gray-700 whitespace-pre-wrap">
                <span className="text-gray-500">Địa chỉ:</span> {order.shipping_address}
              </p>
            )}
            <div className="flex flex-wrap gap-4 pt-1 text-gray-600">
              {order.subtotal != null && (
                <span>
                  Tạm tính:{' '}
                  <strong className="text-gray-900">{Number(order.subtotal).toLocaleString('vi-VN')} ₫</strong>
                </span>
              )}
              {order.shipping_fee != null && Number(order.shipping_fee) > 0 && (
                <span>
                  Phí ship:{' '}
                  <strong className="text-gray-900">{Number(order.shipping_fee).toLocaleString('vi-VN')} ₫</strong>
                </span>
              )}
            </div>
          </div>
        )}

        {order.status === 'pending_payment' && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-4">
            <div className="flex items-center gap-2 text-amber-900 font-semibold">
              <Clock size={18} />
              Thanh toán trong: {mm}:{ss}
              {secondsLeft === 0 && (
                <span className="text-sm font-normal text-amber-800 ml-2">
                  (Hết hạn — tải lại trang để cập nhật trạng thái)
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600">
              {vnpayPaymentUrl
                ? 'Bấm nút bên dưới để sang cổng VNPAY (sandbox). Sau khi thanh toán xong, trình duyệt sẽ quay về trang chủ; đơn sẽ thành “Đã thanh toán” khi cổng xử lý xong (có IPN thì nhanh hơn).'
                : 'Chưa tạo được link thanh toán. Bấm “Cập nhật trạng thái” hoặc tải lại trang.'}
            </p>
            {vnpayPaymentUrl && (
              <>
                <a
                  href={vnpayPaymentUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-3 rounded-xl"
                >
                  <ExternalLink size={18} /> Mở cổng VNPAY thanh toán
                </a>
                <p className="text-xs text-gray-500">
                  Thẻ thử nghiệm (sandbox):{' '}
                  <a
                    href="https://sandbox.vnpayment.vn/apis/vnpay-demo/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    vnpay-demo
                  </a>
                </p>
              </>
            )}
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => load()}
                disabled={loading}
                className="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-900 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-xl"
              >
                <RefreshCw size={18} /> Cập nhật trạng thái đơn
              </button>
              <button
                type="button"
                onClick={cancel}
                className="inline-flex items-center gap-2 border border-red-200 text-red-600 hover:bg-red-50 font-semibold px-5 py-2.5 rounded-xl"
              >
                <XCircle size={18} /> Hủy đơn
              </button>
            </div>
          </div>
        )}

        {(order.status === 'expired' || order.status === 'cancelled') && (
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 flex flex-wrap gap-3 items-center">
            <p className="text-sm text-gray-600 flex-1 min-w-[200px]">
              Đơn chưa hoàn tất thanh toán. Bạn có thể bấm Thanh toán tiếp để giữ chỗ tồn kho và mở lại cửa sổ thanh toán 5 phút.
            </p>
            <button
              type="button"
              onClick={retryPay}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl"
            >
              <RefreshCw size={18} /> Thanh toán tiếp
            </button>
          </div>
        )}

        <div>
          <h2 className="font-semibold text-gray-800 mb-2">Sản phẩm</h2>
          <ul className="divide-y divide-gray-100 border rounded-xl overflow-hidden">
            {(order.items || []).map((line) => (
              <li key={line.id} className="flex justify-between p-3 text-sm bg-white">
                <span>
                  {line.product_name}{' '}
                  <span className="text-gray-400">×{line.quantity}</span>
                </span>
                <span className="font-medium">
                  {(Number(line.unit_price) * line.quantity).toLocaleString('vi-VN')} ₫
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
