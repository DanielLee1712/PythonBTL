import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { orderApiBase } from '../config';
import { Package } from 'lucide-react';

const statusLabel = {
  pending_payment: 'Chờ thanh toán',
  paid: 'Đã thanh toán',
  cancelled: 'Đã hủy',
  expired: 'Hết hạn thanh toán',
};

export default function OrderList() {
  const user = useStore((s) => s.user);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setOrders([]);
      setLoading(false);
      return;
    }
    axios
      .get(`${orderApiBase}/orders/?user_id=${user.id}`)
      .then((res) => setOrders(res.data || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto bg-white rounded-2xl p-8 text-center border border-gray-100">
        <p className="text-gray-600 mb-4">Vui lòng đăng nhập để xem đơn hàng.</p>
        <Link to="/login" className="text-blue-600 font-semibold hover:underline">
          Đăng nhập
        </Link>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-12">Đang tải đơn hàng…</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
        <Package className="text-blue-600" />
        Đơn hàng của tôi
      </h1>

      {orders.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center text-gray-500">
          Chưa có đơn hàng nào.
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left p-4 font-semibold">Mã đơn</th>
                <th className="text-left p-4 font-semibold">Trạng thái</th>
                <th className="text-right p-4 font-semibold">Tổng</th>
                <th className="text-left p-4 font-semibold">Hạn thanh toán</th>
                <th className="text-right p-4 font-semibold"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-gray-50/80">
                  <td className="p-4 font-mono font-medium">#{o.id}</td>
                  <td className="p-4">{statusLabel[o.status] || o.status}</td>
                  <td className="p-4 text-right font-semibold text-blue-600">
                    {Number(o.total || 0).toLocaleString('vi-VN')} ₫
                  </td>
                  <td className="p-4 text-gray-500">
                    {o.payment_deadline
                      ? new Date(o.payment_deadline).toLocaleString('vi-VN')
                      : '—'}
                  </td>
                  <td className="p-4 text-right">
                    <Link
                      to={`/orders/${o.id}`}
                      className="text-blue-600 font-medium hover:underline"
                    >
                      Chi tiết
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
