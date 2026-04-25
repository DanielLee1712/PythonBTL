import React, { useState } from 'react';
import { User, Lock, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../store/useStore';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setUser = useStore((state) => state.setUser);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const res = await axios.post('http://localhost:8080/api/customers/api/accounts/login/', {
        username,
        password
      });
      
      const token = res.data.access;
      // Store token (optional, depending on auth strategy)
      localStorage.setItem('access_token', token);
      if (res.data.refresh) localStorage.setItem('refresh_token', res.data.refresh);

      // Decode JWT to extract user info
      const payloadBase64 = token.split('.')[1];
      // Fix base64 padding if necessary
      const base64 = payloadBase64.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      const payload = JSON.parse(jsonPayload);
      
      setUser({ id: payload.user_id, username: username });
      navigate('/');
    } catch (err) {
      console.error('Login error:', err);
      setError('Tên đăng nhập hoặc mật khẩu không chính xác.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="max-w-md w-full bg-white border border-gray-100 rounded-3xl shadow-sm overflow-hidden z-10 transition-all hover:shadow-md">
        <div className="p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-extrabold text-gray-800 tracking-tight mb-2">Đăng nhập</h2>
            <p className="text-gray-500">Vui lòng đăng nhập để tiếp tục</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded-r-xl">
              <p>{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700 ml-1" htmlFor="username">Tên đăng nhập</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all"
                  placeholder="Nhập tên đăng nhập"
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between ml-1">
                <label className="text-sm font-medium text-gray-700" htmlFor="password">Mật khẩu</label>
                <Link to="/forgot-password" className="text-xs text-blue-600 hover:text-blue-800 transition-colors">Quên mật khẩu?</Link>
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  Đăng nhập
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>
        
        <div className="py-4 bg-gray-50 text-center border-t border-gray-100">
          <p className="text-sm text-gray-500">
            Chưa có tài khoản?{' '}
            <Link to="/register" className="font-bold text-blue-600 hover:text-blue-700 hover:underline transition-all">
              Đăng ký ngay
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
