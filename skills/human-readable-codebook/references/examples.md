# Examples

Read this file when you need a concrete shape before calling a lifecycle tool or writing a page. Every block below is illustrative, not normative: OpenWiki owns the lifecycle and Claim contracts, and its validation errors take precedence over anything shown here. Replace every placeholder; do not copy the sample values.

## Page skeleton

Only these four frontmatter fields belong to the writer. `title` and `description` use the run language; `tags` stay stable English.

```markdown
---
type: mechanism
title: 请求如何穿过鉴权边界
description: 说明一次请求从入口到业务处理之间，身份如何被解析、校验并传递，以及失败时的分支。
tags: [authentication, request-lifecycle, middleware]
---

本章服务“首次理解仓库”这一阅读模式：读完可以说明系统如何识别调用者，以及校验失败会走向哪里。

## 问题与约束

<先讲读者能感知的问题，再讲机制。>

## 核心机制

<按运行顺序展开；每个机制给出 key call chain 和最小代码摘录。>

## 边界与失败

<说明机制失效时的行为，以及代码如何应对。>

### 关键结论

### 现在能做什么

### 重要关系

### 检查理解
```

Do not add `verified`, `sources`, `timestamp`, or any confidence label to the frontmatter.

## Plan payload

`runId` comes from `openwiki_begin`. Each page requires `path`, `title`, and `purpose`; `seedPaths`, `relatedPages`, and `instructions` are optional. Send the canonical final paths, not drafts.

```json
{
  "runId": "<runId returned by openwiki_begin>",
  "pages": [
    {
      "path": "openwiki/overview.md",
      "title": "项目概览",
      "purpose": "固定项目边界与它不负责的部分，不解释机制。",
      "seedPaths": ["README.md"],
      "relatedPages": ["openwiki/quickstart.md"]
    },
    {
      "path": "openwiki/mechanisms/request-lifecycle.md",
      "title": "请求如何穿过鉴权边界",
      "purpose": "读者能说明身份解析、校验、传递三个阶段，以及校验失败的去向。",
      "seedPaths": ["src/server.ts", "src/auth/guard.ts"],
      "relatedPages": ["openwiki/overview.md"],
      "instructions": ["用 running example 贯穿，不引入第二个案例。"]
    }
  ]
}
```

On `update`, add `deletePages` with the pages that must disappear; omit it when nothing is deleted.

## Submit-page payload

`runId` comes from `openwiki_begin`, `jobId` from the current `openwiki_next_page` job. Submit only the decisions that changed. Every `resource` is a canonical `repo://` URI, optionally with a line range; a bare path is rejected.

```json
{
  "runId": "<runId returned by openwiki_begin>",
  "jobId": "<jobId from openwiki_next_page>",
  "claims": [
    {
      "statement": "身份在中间件层解析，业务处理器只读取已校验的上下文对象。",
      "evidence": [
        { "resource": "repo://src/auth/guard.ts#L20-L48" },
        { "resource": "repo://src/server.ts#L12-L19" }
      ]
    },
    {
      "id": "<existing Claim id when revising>",
      "statement": "Inferred: 校验失败时回落到匿名上下文，因为 catch 分支未重新抛出错误。",
      "evidence": [{ "resource": "repo://src/auth/guard.ts#L50-L66" }]
    }
  ],
  "confirmedClaimIds": ["<claimId rechecked and unchanged>"],
  "retractedClaimIds": ["<claimId whose proposition no longer holds>"]
}
```

A Claim carries no confidence field. Write Verified statements plainly and prefix the other two levels with `Inferred:` or `Unverified:` here, never in page prose.

## Blocker report

When OpenWiki cannot start, stop before any analysis and report in the run language. Name what is missing and what would unblock the run; do not offer standalone chapters as an alternative.

```text
没有开始：本次未生成任何页面。

原因：缺少 OpenWiki 的 MCP 工具集。可用的工具里没有 openwiki_begin，因此无法创建运行状态、页面队列与 Claim 记录。

影响：本技能的交付物是 OpenWiki 页面。离线写出的章节无法追加 Claim 证据，也无法通过 openwiki_finish 校验，所以没有作为替代产出。

解锁方式：在宿主里挂载 OpenWiki MCP 服务并授权，然后重新发起；如果已经挂载，请确认服务地址可达、工具列表包含五个生命周期工具。
```

For a run that returns `status: "noop"`, report that the wiki is already current and stop. Do not invent a plan for an unchanged wiki.
