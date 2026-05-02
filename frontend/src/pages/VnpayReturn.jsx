import { useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

export default function VnpayReturn() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const code = params.get('vnp_ResponseCode');
  const message = params.get('vnp_TransactionStatus') || params.get('vnp_ResponseCode');
  const txnRef = params.get('vnp_TxnRef');
  const ok = code === '00';

  useEffect(() => {
    if (code === '00') {
      navigate('/', { replace: true });
    }
  }, [code, navigate]);

  if (code === '00') {
    return (
      <div className="max-w-lg mx-auto py-16 text-center text-gray-600 text-sm">
        Đang chuyển về trang chủ…
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center space-y-4">
      <h1 className="text-xl font-bold text-gray-800">Kết quả thanh toán VNPAY</h1>
      <p className="text-amber-800">
        Giao dịch chưa thành công hoặc bị hủy.
        {message != null && (
          <span className="block text-sm text-gray-600 mt-2">Mã: {message}</span>
        )}
      </p>
      {txnRef && (
        <p className="text-sm text-gray-500">
          Mã tham chiếu: <span className="font-mono">{txnRef}</span>
        </p>
      )}
      <p className="text-sm text-gray-600">
        Thẻ test sandbox:{' '}
        <a
          href="https://sandbox.vnpayment.vn/apis/vnpay-demo/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline"
        >
          vnpay-demo
        </a>
      </p>
      <div className="flex flex-wrap justify-center gap-3 pt-2">
        <Link to="/orders" className="text-blue-600 font-semibold hover:underline">
          Danh sách đơn
        </Link>
        <Link to="/" className="text-gray-600 hover:underline">
          Trang chủ
        </Link>
      </div>
    </div>
  );
}
