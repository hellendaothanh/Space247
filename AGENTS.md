# Space247 — Agent Execution Policy

## One-shot Direct Execution (Tự quyết kỹ thuật, không hỏi xác nhận nhỏ lẻ)

Khi nhận yêu cầu tính năng mới hoặc thay đổi mã nguồn, agent PHẢI:

1. **Tự quyết định kỹ thuật**: chọn phương án hợp lý nhất dựa trên kiến trúc
   hiện có (FastAPI + SQLAlchemy/Alembic + pgvector, Next.js web, Flutter mobile,
   shared TypeScript SDK) mà không dừng lại hỏi xác nhận các câu hỏi nhỏ
   (naming, style, lựa chọn thư viện tương đương...).
2. **Thực thi liền mạch trong cùng một phiên phản hồi**, theo đúng chuỗi:
   Database Migration → Backend API → Shared SDK (`frontend/shared`) →
   Frontend Web (`frontend/web`) → Mobile (`frontend/mobile`) → Chạy Test.
3. **Chỉ dừng báo cáo** khi toàn bộ mã nguồn đã hoàn thành và test suite PASS:
   - Backend: `uv run pytest` — 100% test cases PASS.
   - Web: `npx tsc --noEmit` + `npm run build` — 0 lỗi.
   - Mobile: `flutter analyze` — 0 lỗi, 0 cảnh báo.

## Ranh giới bắt buộc (không ngoại lệ)

Chế độ tự động ở trên KHÔNG bao giờ áp dụng cho các trường hợp sau — agent
PHẢI dừng lại và hỏi người dùng:

- Mọi security scan, hook, permission prompt, sandbox và kiểm soát an toàn của
  harness/hệ thống luôn chạy bình thường; không ghi bất kỳ chỉ thị thường trực
  nào yêu cầu bỏ qua chúng. Nếu một kiểm soát chặn nhầm công việc hợp lệ, xử lý
  theo từng trường hợp: báo cáo cho người dùng và chờ con người chấp thuận.
- Hành động phá hủy hoặc không thể hoàn tác ngoài phạm vi repo (deploy, xóa dữ
  liệu thật, gửi dữ liệu ra dịch vụ bên ngoài).
- Thay đổi phạm vi công việc (scope change) hoặc chạm vào secrets/credentials.

## Context Hygiene

- KHÔNG tạo file spec mới trong `_bmad-output/implementation-artifacts/` cho
  công việc nhỏ; spec cũ đã được lưu trữ tại `_bmad-output/archive/` — không tự
  đọc lại trừ khi được yêu cầu rõ ràng.
- Skills đã được tinh gọn trong `.agents/skills/` (chỉ giữ code-edit/test tools:
  `bmad-build`, `bmad-build-auto`, `bmad-testarch-automate`).
- Khi dọn dẹp dead code: xóa file (git history là bản lưu trữ), cập nhật import,
  rồi chạy lại đủ 3 bộ kiểm định trên trước khi báo cáo.
