# Bài Tập Phản Ánh & Củng Cố Kiến Thức (Exercises)

## Câu 1: Nguyên tắc cấu hình 12-Factor App
**Câu hỏi**: Tại sao 12-Factor App lại nghiêm cấm lưu cấu hình (config) và bí mật (secrets) trong mã nguồn? Nêu ít nhất 2 rủi ro nghiêm trọng khi commit file `.env` chứa API key lên GitHub công khai.
**Trả lời**:
- 12-Factor App yêu cầu tách biệt hoàn toàn mã nguồn (code) và cấu hình (config) vì cấu hình biến đổi tùy theo môi trường triển khai (development, staging, production) trong khi code phải nhất quán.
- Rủi ro khi commit `.env` chứa API key lên GitHub:
  1. **Lộ lọt thông tin bảo mật và tài chính**: Các bot quét tự động trên GitHub có thể đánh cắp API key chỉ sau vài giây, dẫn đến việc bị lạm dụng tài nguyên tính toán (LLM/Cloud) gây thiệt hại tài chính nặng nề.
  2. **Vi phạm kiểm soát quyền truy cập**: Bất kỳ ai có quyền xem repo (kể cả cộng tác viên bên ngoài hoặc bên thứ ba nếu repo public) đều nắm giữ toàn quyền truy cập cơ sở dữ liệu và hệ thống nội bộ.

---

## Câu 2: Liveness Probe vs. Readiness Probe
**Câu hỏi**: Phân biệt vai trò của `/health` (Liveness) và `/ready` (Readiness). Tại sao `/health` không nên kiểm tra kết nối Redis, trong khi `/ready` thì bắt buộc phải kiểm tra?
**Trả lời**:
- **Liveness Probe (`/health`)**: Kiểm tra xem tiến trình ứng dụng có còn sống và không bị deadlock hay không. Nếu liveness thất bại, orchestrator (Docker/Kubernetes) sẽ lập tức khởi động lại (restart) container. Nếu `/health` kiểm tra Redis và Redis tạm thời nghẽn mạng, việc restart app liên tục sẽ gây ra hiện tượng crash loop mà không giải quyết được gốc rễ vấn đề mạng.
- **Readiness Probe (`/ready`)**: Kiểm tra xem ứng dụng đã sẵn sàng nhận và xử lý lưu lượng truy cập thực tế hay chưa (bao gồm trạng thái kết nối tới các dịch vụ phụ thuộc như Redis). Nếu `/ready` trả về lỗi (503), load balancer chỉ tạm thời ngừng định tuyến lưu lượng vào container này mà không giết tiến trình, đợi cho đến khi Redis phục hồi.

---

## Câu 3: Multi-stage Build trong Dockerfile
**Câu hỏi**: Cơ chế Multi-stage Build trong Docker mang lại những lợi ích gì về kích thước image và tính bảo mật?
**Trả lời**:
- **Về kích thước image**: Tách biệt môi trường build (builder stage) và môi trường chạy (runtime stage). Các công cụ nặng như gcc, build-essential, header files, compiler và file cache của pip chỉ nằm ở stage đầu và bị loại bỏ hoàn toàn khỏi image cuối cùng, giúp giảm kích thước từ hàng GB xuống chỉ còn vài chục MB.
- **Về tính bảo mật**: Image cuối cùng có bề mặt tấn công (attack surface) nhỏ nhất có thể. Nếu kẻ tấn công chiếm được quyền shell, chúng không có sẵn trình biên dịch, công cụ gỡ lỗi (debuggers) hay package manager để tải mã độc hoặc leo thang đặc quyền.

---

## Câu 4: Chạy ứng dụng dưới quyền Non-root User
**Câu hỏi**: Tại sao trong Dockerfile cần tạo user mới (`appuser`) và dùng lệnh `USER appuser` thay vì để container chạy mặc định dưới quyền `root`?
**Trả lời**:
- Mặc định tiến trình trong container chạy bằng UID 0 (`root`), tương đương với user root trên máy chủ host nếu container runtime không kích hoạt user namespace remapping.
- Nếu ứng dụng có lỗ hổng bảo mật (ví dụ: Remote Code Execution - RCE) hoặc container breakout, kẻ tấn công chiếm được shell sẽ có toàn quyền kiểm soát kernel và hệ thống tệp của host. Chạy bằng `non-root user` áp dụng nguyên tắc đặc quyền tối thiểu (Principle of Least Privilege), ngăn chặn kẻ tấn công can thiệp vào các tài nguyên nhạy cảm.

---

## Câu 5: Thiết kế Hệ thống Vô trạng thái (Stateless Service)
**Câu hỏi**: Một ứng dụng AI Agent muốn mở rộng quy mô ngang (scale out thành nhiều container) thì tại sao không được lưu session hoặc lịch sử trò chuyện trong RAM của tiến trình Python?
**Trả lời**:
- Khi scale out thành nhiều instance phía sau Load Balancer, các request tiếp theo của cùng một người dùng có thể được phân phối tới bất kỳ container ngẫu nhiên nào.
- Nếu lưu trong RAM cục bộ của tiến trình, các instance khác sẽ không có ngữ cảnh trò chuyện trước đó, làm đứt gãy trải nghiệm. Đồng thời, khi container bị crash hoặc tái triển khai (rolling update), toàn bộ dữ liệu trong RAM sẽ biến mất. Tách trạng thái sang một kho lưu trữ dùng chung như Redis giúp các container hoàn toàn stateless và có thể tăng/giảm quy mô tùy ý mà không làm mất dữ liệu.

---

## Câu 6: Thuật toán Rate Limiting bằng Redis
**Câu hỏi**: Trình bày nguyên lý hoạt động của thuật toán Sliding Window Counter (hoặc Fixed Window) sử dụng Redis để giới hạn tần suất gọi API.
**Trả lời**:
- Với **Sliding Window Counter** sử dụng cấu trúc Redis Sorted Set (`ZSET`):
  1. Mỗi request gửi đến, hệ thống dùng khóa theo user (ví dụ `rate:{user_id}`).
  2. Dùng lệnh `ZREMRANGEBYSCORE` để loại bỏ tất cả các bản ghi có timestamp cũ hơn thời điểm hiện tại trừ đi độ dài cửa sổ (ví dụ 60 giây).
  3. Đếm số lượng request còn lại trong cửa sổ trượt bằng lệnh `ZCARD`.
  4. Nếu số lượng vượt quá ngưỡng cho phép (`limit`), từ chối request với mã HTTP 429 Too Many Requests.
  5. Nếu chưa vượt, dùng `ZADD` thêm request hiện tại (với score là timestamp hiện tại) và đặt TTL (`EXPIRE`) cho key để tự động giải phóng bộ nhớ.

---

## Câu 7: Quản trị chi phí (Cost Guard / Token Budgeting)
**Câu hỏi**: Tại sao việc tích hợp Cost Guard là bắt buộc đối với các ứng dụng triển khai Agent sử dụng mô hình ngôn ngữ lớn (LLM)?
**Trả lời**:
- Các LLM thương mại tính phí theo số lượng token đầu vào (prompt) và đầu ra (completion).
- Nếu không có cơ chế chặn trần chi phí (Cost Guard), hệ thống sẽ đối mặt với các nguy cơ:
  1. Vòng lặp vô hạn (infinite loop) trong quá trình Agent tự suy luận và gọi tool.
  2. Bị tấn công từ chối dịch vụ tài chính (Financial Denial of Wallet - DoW), kẻ xấu liên tục gửi prompt dung lượng tối đa để làm cạn kiệt ngân sách.
  3. Cost Guard tự động ghi nhận số tiền tích lũy và chặn khẩn cấp (HTTP 402 hoặc 429) khi vượt ngân sách quy định giúp kiểm soát chi phí vận hành an toàn.

---

## Câu 8: Cơ chế Graceful Shutdown
**Câu hỏi**: Khi nền tảng Cloud (Render, Railway, Kubernetes) gửi tín hiệu `SIGTERM`, ứng dụng cần xử lý những gì trước khi tắt hẳn? Nếu tắt đột ngột (`SIGKILL`) thì hậu quả là gì?
**Trả lời**:
- **Quy trình Graceful Shutdown**:
  1. Bật cờ trạng thái đang tắt (`shutting_down = True`) để các probe `/health` và `/ready` trả về HTTP 503, khiến load balancer ngừng phân bổ request mới vào container.
  2. Tiếp tục xử lý cho xong các request đang chạy dở dang (in-flight requests).
  3. Đóng an toàn các kết nối cơ sở dữ liệu, Redis pool, giải phóng file descriptors và flush log ra hệ thống.
  4. Thoát tiến trình an toàn với mã trạng thái 0.
- **Hậu quả nếu bị `SIGKILL` đột ngột**: Các request đang xử lý bị ngắt quãng lập tức gây lỗi 502/504 cho client, dữ liệu đang ghi dở có thể bị phân mảnh hoặc lỗi tính toàn vẹn (corrupted data).

---

## Câu 9: Structured Logging (Ghi log có cấu trúc)
**Câu hỏi**: So sánh Structured Logging (dạng JSON) với log văn bản thuần túy (Plain Text). Tại sao trên production bắt buộc phải dùng Structured Logging?
**Trả lời**:
- **Plain Text**: Khó bóc tách bằng máy, định dạng tự do, khi tìm kiếm các chỉ số như `user_id`, `latency`, `cost` phải dùng regular expression phức tạp và tốn hiệu năng.
- **Structured Logging (JSON)**: Mỗi dòng log là một JSON object với các trường khóa - giá trị cố định (`timestamp`, `level`, `user_id`, `event`, `path`, `duration`).
- **Lý do bắt buộc trên production**: Các hệ thống thu thập và giám sát tập trung (Elasticsearch/Kibana, Datadog, CloudWatch, Loki) có thể lập chỉ mục (index), lọc, truy vấn và dựng biểu đồ cảnh báo theo thời gian thực một cách chính xác mà không cần viết bộ parser thủ công.

---

## Câu 10: Quy trình CI/CD và Rollback
**Câu hỏi**: Trong quy trình CI/CD tự động, tại sao bước chạy Unit Test và Integration Test phải hoàn thành trước bước Build Docker Image và Deploy? Trình bày khái niệm Zero-Downtime Deployment.
**Trả lời**:
- **Thứ tự trong CI/CD**: Chạy test trước nhằm tuân thủ nguyên tắc "Fail Fast" — phát hiện sớm các lỗi logic, bảo mật hoặc hồi quy mã nguồn ngay ở tầng code. Nếu có test fail, pipeline dừng lập tức, ngăn việc tốn tài nguyên build Docker image chứa lỗi và ngăn chặn rủi ro làm sập môi trường production.
- **Zero-Downtime Deployment**: Kỹ thuật triển khai phiên bản ứng dụng mới mà hệ thống không ngừng tiếp nhận request của người dùng bất kỳ giây nào. Hệ thống khởi tạo container mới song song với container cũ, chờ đến khi container mới vượt qua Readiness Probe thành công mới bắt đầu chuyển lưu lượng mạng sang và sau đó graceful shutdown container cũ.