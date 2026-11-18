# API 快速使用（开发阶段）

启动容器后访问 `http://localhost:8000/docs` 查看 OpenAPI。

1. 创建管理员：`docker compose exec api python -m app.bootstrap_admin`
2. 登录：`POST /api/auth/token`
3. 在 Swagger 的 Authorize 中填入 `Bearer <access_token>`。
4. 先创建客户，再创建合同并通过合同评审；合同评审通过后才能登记样品。
5. 创建受控文件，审批文件版本后可用于试验模板；创建设备和试验模板后即可创建试验任务。
6. 样品流转记录可通过 `/api/samples/{id}/events` 追加并查询。

本阶段 API 是早期 MVP 实现：尚未包含数据库迁移、完整状态机、数据文件存储、最终报告签发、非符合工作流程及自动化测试。请勿用于未验证的正式检测记录。
