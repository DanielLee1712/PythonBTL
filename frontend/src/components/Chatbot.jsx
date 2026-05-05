import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useStore } from '../store/useStore';
import {
  X, Send,
  Sparkles, Bot, User
} from 'lucide-react';

const QUICK_PROMPTS = [
  { icon: '🔥', text: 'Sản phẩm bán chạy nhất?' },
  { icon: '💰', text: 'Gợi ý phụ kiện dưới 500k' },
  { icon: '💻', text: 'Tư vấn mua laptop học tập & văn phòng' },
  { icon: '📱', text: 'Tư vấn mua điện thoại theo nhu cầu' },
  { icon: '⌚', text: 'Gợi ý đồng hồ thông minh' },
];

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const user = useStore(state => state.user);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = async (text) => {
    const userMsg = (text || input).trim();
    if (!userMsg || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8002/api/v1/chat/', {
        user_id: user ? user.id : 1,
        message: userMsg
      });

      const reply = res.data.reply || 'Xin lỗi, tôi không thể trả lời lúc này.';

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: reply,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Xin lỗi, hệ thống AI đang bảo trì. Vui lòng thử lại sau!',
      }]);
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        /* ── Floating Action Button ── */
        <button
          onClick={() => setIsOpen(true)}
          className="group relative bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105 active:scale-95"
          id="chat-toggle-btn"
        >
          <Bot size={28} />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 border-2 border-white rounded-full animate-pulse"></span>
          {/* Tooltip */}
          <span className="absolute bottom-full right-0 mb-3 bg-gray-800 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-lg">
            AI Tư vấn mua sắm
          </span>
        </button>
      ) : (
        /* ── Chat Panel ── */
        <div className="bg-white rounded-3xl shadow-2xl w-[380px] sm:w-[420px] overflow-hidden flex flex-col h-[620px] border border-gray-200 transition-all" id="chat-panel">

          {/* ── Header ── */}
          <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 p-5 text-white relative overflow-hidden">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTAiIGN5PSIxMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIvPjwvc3ZnPg==')] opacity-50"></div>
            <div className="relative z-10 flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/20">
                  <Sparkles size={22} className="text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg tracking-wide">ElecStore Assistant</h3>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-blue-100 text-xs font-medium">Online</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-white/20 p-2 rounded-xl transition-colors"
                id="chat-close-btn"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* ── Messages Area ── */}
          <div className="flex-1 overflow-y-auto bg-gray-50 px-4 py-5 space-y-5" id="chat-messages">
            {/* Welcome card */}
            {messages.length === 0 && (
              <div className="space-y-5">
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Bot size={18} className="text-blue-600" />
                    </div>
                    <p className="font-bold text-gray-800">Xin chào! 👋</p>
                  </div>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Mình có thể tư vấn <strong>laptop</strong>, <strong>điện thoại</strong>, <strong>phụ kiện</strong> và <strong>đồng hồ</strong> theo nhu cầu và ngân sách của bạn.
                  </p>
                </div>

                {/* Quick prompt chips */}
                <div>
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-3 px-1">Bắt đầu nhanh</p>
                  <div className="grid grid-cols-2 gap-2">
                    {QUICK_PROMPTS.map((prompt, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(prompt.text)}
                        className="bg-white hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-gray-700 transition-all hover:shadow-sm flex items-center gap-2 group"
                      >
                        <span className="text-base">{prompt.icon}</span>
                        <span className="truncate group-hover:text-blue-700">{prompt.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Chat messages */}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center shrink-0 mr-2 mt-1 shadow-sm">
                    <Bot size={14} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] ${m.role === 'user' ? '' : ''}`}>
                  {/* Text bubble */}
                  <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-md shadow-md'
                      : 'bg-white text-gray-800 rounded-bl-md shadow-sm border border-gray-100'
                  }`}>
                    {m.content}
                  </div>


                </div>
                {m.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center shrink-0 ml-2 mt-1">
                    <User size={14} className="text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex items-start gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center shrink-0 shadow-sm">
                  <Bot size={14} className="text-white" />
                </div>
                <div className="bg-white shadow-sm px-4 py-3 rounded-2xl rounded-bl-md text-gray-500 border border-gray-100 flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  <span className="text-xs text-gray-400">Đang phân tích...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── Input Area ── */}
          <div className="bg-white border-t border-gray-100 p-3">
            {/* Context chip */}
            {user && (
              <div className="flex items-center gap-1.5 px-2 mb-2">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                <span className="text-[10px] text-gray-400 font-medium">
                  Đang tư vấn cho <span className="text-blue-500 font-bold">{user.username}</span> • Dữ liệu cá nhân hóa
                </span>
              </div>
            )}
            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2 items-center">
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Hỏi về sản phẩm, tư vấn mua sắm..."
                className="flex-1 outline-none border border-gray-200 rounded-xl px-4 py-3 bg-gray-50 focus:bg-white focus:ring-2 ring-blue-200 focus:border-blue-400 transition-all text-sm"
                disabled={loading}
                id="chat-input"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-xl hover:shadow-lg disabled:opacity-40 disabled:from-gray-400 disabled:to-gray-400 shadow-md transition-all hover:scale-105 active:scale-95"
                id="chat-send-btn"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
