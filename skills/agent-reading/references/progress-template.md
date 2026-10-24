> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 说明：本文件为设计新增模板，非 verbatim 切片；checklist 的 114 个知识点编号、名称与优先级摘自源速查表总览表（由包根 extract.sh 生成）｜源 commit 435ad87（2026-10-24）｜生成 2026-10-24
> 提示词正文不载于本文件；更新方式见包根 README 的同步流程。

# 逐仓进度文件模板（progress-template.md）

新仓库开始学习时，把「文件头 + checklist」整体复制为
`~/.agent-reading/progress/{owner}__{repo}.md` 再填写与勾选。checklist 区由包根
`extract.sh` 从源速查表总览表生成（10 域组头 + 114 点）；知识点集合变化时按包根
README 同步手册 splice 更新本模板，旧逐仓进度文件不重写（稳定 ID 键控、
append-only、未知 ID 视为未问）。

## 文件头（复制后填写）

```markdown
# 学习进度 · {owner}/{repo}

- remote: {git remote get-url origin 原文}（无 remote 时：目录名兜底，标注 approximate）
- slug: {owner}__{repo}
- 首次: YYYY-MM-DD ｜ 最近: YYYY-MM-DD
- 开场: 未做 / 已做（逐仓开场提示词，YYYY-MM-DD）/ 已做（5 问，YYYY-MM-DD）
- 收尾作业: 未做 / 进行中 / 完成（对比的仓库与知识点：…）
```

## checklist（114 点）

## A 核心循环与执行模型（8）
- [ ] A1 Agentic Loop 本体 ｜P0｜
- [ ] A2 循环停止条件 ｜P0｜
- [ ] A3 流式输出与增量解析 ｜P1｜
- [ ] A4 会话状态与单/多轮对话 ｜P1｜
- [ ] A5 CLI REPL 事件循环 ｜P1｜
- [ ] A6 Headless/Exec 单次执行 ｜P1｜
- [ ] A7 中断、审批挂起与恢复 ｜P1｜
- [ ] A8 隐式循环 vs 显式图 ｜P0｜
## B 上下文工程与 Token 压缩（9）
- [ ] B1 System Prompt 分层组装 ｜P0｜
- [ ] B2 Token 计数与估算 ｜P1｜
- [ ] B3 上下文窗口预算分配 ｜P1｜
- [ ] B4 仓库地图 Repo Map ｜P1｜
- [ ] B5 按需上下文加载 ｜P1｜
- [ ] B6 上下文编辑 Context Editing ｜P1｜
- [ ] B7 历史压缩与摘要 Compaction ｜P1｜
- [ ] B8 超限策略 ｜P1｜
- [ ] B9 Prompt Caching 与前缀稳定性 ｜P1｜
## C 工具系统（13）
- [ ] C1 工具定义 Schema ｜P0｜
- [ ] C2 工具的 Prompt 表征 ｜P0｜
- [ ] C3 注册与发现 Registry ｜P1｜
- [ ] C4 Tool Call 解析与分发 ｜P0｜
- [ ] C5 参数校验与错误回喂 ｜P1｜
- [ ] C6 工具结果格式化与大小限制 ｜P1｜
- [ ] C7 MCP 接入 ｜P1｜
- [ ] C8 动态加载与热更新工具 ｜P1｜
- [ ] C9 工具过多：检索与子集注入 ｜P2｜
- [ ] C10 并行工具调用 ｜P1｜
- [ ] C11 工具执行生命周期 ｜P1｜
- [ ] C12 文件编辑格式与 Patch 应用器 ｜P1｜
- [ ] C13 CodeAct 代码行动 ｜P1｜
## D 记忆系统（12）
- [ ] D1 会话内短期记忆 ｜P0｜
- [ ] D2 会话持久化与恢复 ｜P1｜
- [ ] D3 文件型长期记忆 ｜P1｜
- [ ] D4 自动记忆 ｜P1｜
- [ ] D5 数据库型长期记忆 ｜P1｜
- [ ] D6 写入决策与淘汰策略 ｜P1｜
- [ ] D7 关键词式检索 ｜P1｜
- [ ] D8 向量检索 ｜P1｜
- [ ] D9 MemGPT 式上下文分页 ｜P1｜
- [ ] D10 分层记忆架构 ｜P1｜
- [ ] D11 记忆的数据模型 ｜P1｜
- [ ] D12 记忆与上下文工程的边界 ｜P1｜
## E 单 Agent 与多 Agent 协作（14）
- [ ] E1 单 Agent 的适用边界 ｜P1｜
- [ ] E2 Subagent 派生 Agent-as-Tool ｜P1｜
- [ ] E3 上下文隔离与干净上下文 ｜P1｜
- [ ] E4 Supervisor / Orchestrator ｜P1｜
- [ ] E5 Planner–Executor ｜P1｜
- [ ] E6 Pipeline / 状态图工作流 ｜P1｜
- [ ] E7 Fan-out 并行派发 ｜P1｜
- [ ] E8 Agent 间通信：消息与 Channel ｜P1｜
- [ ] E9 Handoff 控制权转移 ｜P1｜
- [ ] E10 共享状态 vs 隔离状态 ｜P1｜
- [ ] E11 群聊与发言者选择 ｜P2｜
- [ ] E12 结果汇总与冲突处理 ｜P1｜
- [ ] E13 并行度控制与资源治理 ｜P1｜
- [ ] E14 子代理注册与路由 ｜P1｜
## F 规划与推理（11）
- [ ] F1 Plan Mode ｜P1｜
- [ ] F2 TODO 列表驱动执行 ｜P1｜
- [ ] F3 任务分解 ｜P1｜
- [ ] F4 ReAct 循环范式 ｜P0｜
- [ ] F5 结构化思考输出 ｜P1｜
- [ ] F6 推理预算与思考分级 ｜P1｜
- [ ] F7 反思与自我批评 ｜P1｜
- [ ] F8 编辑-验证循环 ｜P1｜
- [ ] F9 探索与收敛的节奏控制 ｜P1｜
- [ ] F10 计划持久化与重规划 ｜P1｜
- [ ] F11 多路径探索与回溯 ｜P2｜
## G 容错与可靠性（13）
- [ ] G1 网络重试与指数退避 ｜P1｜
- [ ] G2 限流感知与并发控制 ｜P1｜
- [ ] G3 Provider Failover 回退链 ｜P1｜
- [ ] G4 分层超时控制 ｜P1｜
- [ ] G5 流式中断与恢复 ｜P1｜
- [ ] G6 结构化输出校验与再生成 ｜P1｜
- [ ] G7 工具错误回喂 ｜P1｜
- [ ] G8 Checkpoint 与 Resume ｜P1｜
- [ ] G9 幂等与去重 ｜P1｜
- [ ] G10 崩溃恢复与事件回放 ｜P1｜
- [ ] G11 优雅降级策略 ｜P1｜
- [ ] G12 循环失控与预算保护 ｜P1｜
- [ ] G13 Provider 抽象与消息归一化 ｜P1｜
## H 安全与权限（13）
- [ ] H1 命令执行沙箱 ｜P1｜
- [ ] H2 网络隔离与出口控制 ｜P1｜
- [ ] H3 文件写边界与路径穿越防护 ｜P1｜
- [ ] H4 子进程环境净化 ｜P1｜
- [ ] H5 权限模式与人工确认门 ｜P1｜
- [ ] H6 允许清单与拒绝清单 ｜P1｜
- [ ] H7 自动批准分级与 always allow ｜P1｜
- [ ] H8 Prompt injection 防御 ｜P1｜
- [ ] H9 不可信内容边界 ｜P1｜
- [ ] H10 密钥管理 ｜P1｜
- [ ] H11 日志与转录脱敏 ｜P1｜
- [ ] H12 审计日志事件流 ｜P1｜
- [ ] H13 fail-closed 与提权路径 ｜P1｜
## I 交互与工程化（9）
- [ ] I1 CLI 流式渲染 ｜P1｜
- [ ] I2 diff/patch 审批与回滚 UX ｜P1｜
- [ ] I3 编辑器与 GUI 前端集成 ｜P1｜
- [ ] I4 斜杠命令与自定义命令 ｜P1｜
- [ ] I5 配置体系与优先级 ｜P1｜
- [ ] I6 Hooks 与生命周期事件 ｜P1｜
- [ ] I7 插件与扩展机制 ｜P1｜
- [ ] I8 多模态输入管道 ｜P2｜
- [ ] I9 机器可读事件流输出 ｜P1｜
## J 可观测与评估（12）
- [ ] J1 执行追踪与 span 树 ｜P1｜
- [ ] J2 Telemetry 埋点与指标上报 ｜P2｜
- [ ] J3 结构化日志 ｜P1｜
- [ ] J4 会话转录与事件持久化 ｜P1｜
- [ ] J5 Token 用量与成本核算 ｜P1｜
- [ ] J6 Debug 模式与诊断输出 ｜P1｜
- [ ] J7 Replay 与时间旅行 ｜P1｜
- [ ] J8 确定性与可复现 ｜P1｜
- [ ] J9 LLM Mock 与离线测试 ｜P1｜
- [ ] J10 评测 Harness ｜P1｜
- [ ] J11 判定器与指标 ｜P1｜
- [ ] J12 评测产物与结果聚合 ｜P2｜

## 勾选形态

- 未问：`- [ ] A1 Agentic Loop 本体 ｜P0｜`
- 已问：`- [x] A1 Agentic Loop 本体 ｜P0｜ 2026-10-24：主循环 core/loop.py:120，while not done 驱动`（一行收获，含 file:line）
- 跳过：`- [x] A2 循环停止条件 ｜skip｜ 已掌握`（`｜skip｜ 原因`，同样算关闭）

## INDEX.md（`~/.agent-reading/progress/INDEX.md`，逐仓一行）

```markdown
| 仓库 | slug | 首次 | 最近 | 完成/114 | 开场 | 收尾作业 | 备注 |
|---|---|---|---|---|---|---|---|
| {owner}/{repo} | {owner}__{repo} | 2026-10-24 | 2026-10-24 | 0/114 | 未做 | 未做 | |
```

## 约定

- 勾选时机：该点提示词在本仓库被完整问过并得到回答（Step 5）。
- 收尾总结草稿（Step 7）：默认在会话中给出；用户要求留存时写同目录 `{slug}-summary.md`。
- skill 写域始终限于 `~/.agent-reading/`，绝不写被读仓库与 skill 目录。
