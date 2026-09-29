# Tài liệu Triển khai Ứng dụng (Deployment Documentation)

## 1. Thông tin cá nhân
- **Họ và tên**: Phạm Hương Giang
- **Mã sinh viên**: 2A202602359
- **Lớp**: K4-L3B-DAY12

## 2. Nền tảng triển khai (Deployment Platform)
- **Platform**: Render
- **Loại dịch vụ**: Web Service (Docker runtime)
- **Khu vực (Region)**: Singapore (Southeast Asia)

## 3. Đường dẫn công khai (Public URL)
- **Public URL**: https://k4-l3b-phamhuonggiang.onrender.com

## 4. Danh sách biến môi trường (Environment Variables)
Các biến môi trường được cấu hình trực tiếp trên Dashboard của nhà cung cấp Cloud (không commit giá trị nhạy cảm vào Git):
- `PORT`: Cổng lắng nghe của ứng dụng (mặc định: 8000).
- `AGENT_API_KEY`: Khóa xác thực API dùng để bảo vệ endpoint `/ask` (secret được che giấu trên dashboard).
- `REDIS_URL`: Địa chỉ kết nối Redis instance để lưu trữ session và rate limit.
- `RATE_LIMIT_PER_MINUTE`: Số lượng request tối đa trong 1 phút cho mỗi user.
- `MONTHLY_BUDGET_USD`: Ngân sách trần tính bằng USD cho mỗi user trong tháng.
- `LOG_LEVEL`: Mức độ ghi log của hệ thống (info, warning, error).

## 5. Quy trình xác minh sau triển khai (Verification Steps)
1. Kiểm tra liveness probe: `curl https://k4-l3b-phamhuonggiang.onrender.com/health` nhận về HTTP 200 `{"status": "ok"}`.
2. Kiểm tra readiness probe: `curl https://k4-l3b-phamhuonggiang.onrender.com/ready` nhận về HTTP 200 `{"status": "ready"}`.
3. Kiểm tra bảo mật auth: Gọi `POST /ask` không kèm header `X-API-Key` nhận về HTTP 401 Unauthorized.