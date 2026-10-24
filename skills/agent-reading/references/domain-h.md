> 来源：llm-wiki:domains/agent/references/agent-source-reading-cheatsheet.md
> 切片：### H. 安全与权限（Security & Permissions）（L1392–L1583）｜源 commit 435ad87（2026-10-24）｜切取 2026-10-24
> 以下为 verbatim 切片，未改一字；更新方式见包根 README 的同步流程。

### H. 安全与权限（Security & Permissions）

Agent 与普通 LLM 应用最本质的差别是「模型能动手」——执行命令、改文件、发请求。这一领域回答三个问题：动作在哪里被物理限制（沙箱、网络隔离、文件与环境边界）；谁能授权什么动作（权限模式、allow/deny 规则、人工确认门）；从谁那里听来的话算指令（prompt injection 防御、不可信内容边界）。再加上支撑这三件事的密钥管理、脱敏、审计日志与 fail-closed 默认。

#### H1. 命令执行沙箱（OS 级隔离）｜P1

**是什么**：用操作系统级强制机制（macOS Seatbelt、Linux Landlock+seccomp、Docker 容器等）把模型触发的命令执行圈进受限环境，可用的系统调用、文件路径、网络都被内核或容器边界约束。

**为什么重要**：应用层的确认弹窗是「君子协定」——模型生成的一条破坏性命令在 UI 检查之外什么都不拦；只有内核强制的隔离才构成真正的防线。读一个 Agent 仓库，第一件要搞清的事就是：命令到底跑在什么边界里，以及这个边界是默认开启还是可选配置。

**快速信号**：目录/文件名 `sandbox`、`isolation`、`jail`。grep：`landlock`、`seatbelt`、`seccomp`、`bubblewrap`、`nsjail`、`chroot`、`sandbox-exec`、`container`。看 CLI flag 与配置项：`--sandbox`、`read-only`、`workspace-write`、`danger-full-access`；看 `Dockerfile` / `docker-compose`。

**代表实现**：openai/codex（macOS 走 Seatbelt、Linux 走 Landlock+seccomp，沙箱模式与审批策略是两个正交的轴）；OpenHands（每个会话一个 Docker 容器，动作都在容器内执行）；SWE-agent（整个解题过程跑在容器内的受限 bash 环境）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「命令执行沙箱」这一个知识点：模型触发的 shell 命令是在哪里、被什么机制隔离执行的？请定位沙箱的实现入口（可从 sandbox、landlock、seatbelt、seccomp、bubblewrap、container、isolation 等关键词入手，或从执行命令的模块往上游追）并引用具体 file:line；说明用的是哪种 OS 机制（macOS Seatbelt / Linux Landlock+seccomp / Docker / 其他），限制的是系统调用、文件系统还是网络，在进程生命周期的哪个阶段生效（启动时包住整个会话，还是每条命令单独套一层）；用文字讲清从「模型发出 tool call」到「命令在沙箱内执行完毕」的完整调用链和数据流；点出沙箱配置的数据结构与核心函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如沙箱初始化失败时是 fail-open 还是 fail-closed）。
```

#### H2. 网络隔离与出口控制（Network Egress Control）｜P1

**是什么**：在沙箱/容器层默认切断或白名单化出站网络，让模型触发的代码无法把本地文件与环境变量里的数据外传，也无法拉取新的恶意 payload。

**为什么重要**：数据外传（exfiltration）是几乎所有 agent 攻击链的终点——prompt injection 的经典利用就是「诱导模型读密钥、再发一次 HTTP 请求」。文件与命令管得再严，只要网络全放行，任何数据都能用一次请求漏出去；网络面是沙箱设计里与文件面同等重要的一根轴，而且经常被用户为了「装依赖」随手放开。

**快速信号**：grep：`network_access`、`egress`、`offline`、`firewall`、`proxy`、`allowed_domains`、`blocked_hosts`、`deny_network`。看沙箱配置结构体/配置文件里的 network 字段、Docker 网络模式（如 `--network none`）与出口代理实现。

**代表实现**：openai/codex（workspace-write 沙箱默认禁网，放行需显式配置）；OpenHands（会话容器的网络策略可配置）；ag2/AutoGen（代码执行器可选 Docker 隔离运行）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「网络隔离与出口控制」这一个知识点：沙箱或运行环境里的代码能不能发网络请求，由什么控制？请定位网络访问控制生效的位置（可搜 network、egress、proxy、firewall、allowed_domains、offline 等关键词，或查看沙箱/容器配置里有没有网络字段）并引用具体 file:line；说明默认策略是全放行、全禁止还是域名白名单，控制在哪一层实现（OS 沙箱 profile、Docker 网络配置、出口代理过滤、应用层拦截），若是域名白名单，DNS 解析与直连 IP 两条路径是否都覆盖；用文字讲清一次「模型请求访问某个 URL」从 tool call 到网络层放行或拒绝的完整数据流；点出关键配置结构与判定函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如把敏感数据编码进 hostname 或 URL 参数的外传手法是否会被挡住）。
```

#### H3. 文件写边界与路径穿越防护（Filesystem Write Boundary）｜P1

**是什么**：把文件读写（尤其是写）限制在一组显式根目录（工作区、临时目录、显式放行目录）内；用户或模型给出的路径先做 canonicalize / symlink 解析再做边界判断，防 `../`、绝对路径与 symlink 逃逸。

**为什么重要**：「只能改这个仓库里的文件」是用户对 coding agent 的最低预期；一次路径穿越足以改 shell 配置、SSH authorized_keys 或 git hooks，把一次会话升级成持久化的机器接管。校验顺序（先 resolve 再判断，还是反过来）直接决定这道防线是否真的成立。

**快速信号**：grep：`writable`、`read_only`、`realpath`、`canonicaliz`、`path_traversal`、`escape`、`is_path_inside`、`allowed_director`、`workspace`。看文件写入/编辑/apply_patch 类 tool 的入口函数与参数校验。

**代表实现**：openai/codex（沙箱的 writable roots：写路径白名单，边界外写操作被沙箱直接拒绝）；cline/cline（文件操作限制在 workspace 及用户显式放行的目录）；OpenHands（容器内挂载的工作区就是边界）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「文件写边界与路径穿越防护」这一个知识点：文件写入是怎么被限制在特定目录内的？请定位文件写入/编辑 tool 的入口（可搜 write_file、edit_file、apply_patch、writable、workspace、allowed_directories 等关键词）并引用具体 file:line；说明允许写的根目录集合在哪里定义、怎么传递，一个待写路径在落盘前经过哪些校验（realpath/canonicalize、symlink 解析、前缀判断、TOCTOU 处理），`../` 相对路径与 symlink 指向边界外这两种场景分别怎么处理；用文字讲清一次文件写入从 tool call 到落盘的完整数据流与检查顺序；点出路径策略相关的数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如写一个已存在的 symlink 时会不会先 resolve 目标再判断边界）。
```

#### H4. 子进程环境净化（env scrubbing）｜P1

**是什么**：在沙箱内执行命令或拉起子进程时，不透传宿主机的全部环境变量，只按显式白名单注入；密钥与 token 留在沙箱外的受信进程里。

**为什么重要**：沙箱内的代码是低信任的：一旦被注入的 payload 执行了 `env`，全量透传的环境变量就等于把所有 API key 摆上桌。环境净化把「最小权限」落到进程边界上，与网络隔离（H2）配合，才真正切断「读密钥 → 外传」这条最经典的利用链。

**快速信号**：grep：`env_pass`、`environment`、`inherit`、`scrub`、`sanitize`、`spawn`、`subprocess`、`exec`。看启动沙箱命令或子进程的代码里 environment 是怎么构造的；看配置里有没有环境变量白名单段。

**代表实现**：openai/codex（沙箱内命令默认只透传一小撮白名单环境变量，扩展需显式配置）；OpenHands（容器环境按需注入应用所需变量）；SWE-agent（容器内环境与宿主机隔离）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「子进程环境净化」这一个知识点：沙箱或子进程执行命令时拿到的环境变量是怎么构造的？请定位启动子进程/沙箱命令的代码（可搜 spawn、exec、subprocess、command、env、env_pass 等关键词）并引用具体 file:line；说明子进程的环境是全量继承宿主机还是从空开始按清单注入，哪些变量被刻意排除、哪些显式放行，清单在哪里定义、与沙箱策略是什么关系；用文字讲清从「模型要求执行一条命令」到「子进程带着净化后的环境变量启动」的完整数据流；点出环境构造的关键数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如沙箱内进程有没有别的途径读到宿主进程的环境变量、放行清单里会不会混进敏感变量）。
```

#### H5. 权限模式与人工确认门（Approval Gate / Permission Modes）｜P1

**是什么**：在 tool call 与真实执行之间插入一道同步的策略检查层——按工具名和参数（命令、路径等）匹配 allow / ask / deny 规则；命中 ask 时暂停 agent loop、把即将执行的动作、参数与风险摘要呈现给用户，等待批准/拒绝后再放行或继续。权限模式（approval policy）与沙箱强度（H1）通常是两个正交的轴，组合出若干档位。

**为什么重要**：模型不能自我授权，确认门是「人类终审」的直接实现，也是人机权限博弈的主战场；Agent 的安全边界几乎全压在这层上。它的粒度——问什么、展示多少上下文、默认档位在哪——决定产品安全下限与可用性上限的平衡点；看懂一个 Agent 的安全模型，先看它的 mode 枚举和确认 UI 的触发条件。规则匹配语义与「always allow」的持久化分别见 H6、H7。

**快速信号**：grep：`approve`、`approval`、`permission`、`allow` + `deny`、`confirm`、`ask_user`、`pending`、`interrupt`、`human_input`、`dangerous`、`whitelist`。文件/目录名含 `policy`、`permission`、`sandbox`；看模式名：`suggest`、`auto`、`full-auto`、`ask`、`yolo`、`plan`、`untrusted`、`on-failure`、`on-request`、`never`；留意 config 里的默认模式枚举与确认弹窗组件。

**代表实现**：openai/codex（approval policy 四档 untrusted/on-failure/on-request/never，与 sandbox 模式正交）；OpenHands（confirmation mode：ask / always / never 三档）；cline/cline（每个 tool call 弹窗 approve/reject，auto-approval 可按工具粒度开启）；Aider-AI/aider（ask 模式只讨论不改文件，code 模式才自动落盘）；ag2/AutoGen（`UserProxyAgent` 的 `human_input_mode` 三档 NEVER/TERMINATE/ALWAYS 是人机交接的经典模式）；langchain-ai/langgraph（`interrupt()` + checkpointer 组合出可持久化、可恢复的审批中断）。

这一知识点一次问完会得到长而浅的回答，拆成两问粘贴（第一问拿到回答后，再粘第二问）：

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「权限模式与人工确认门」这一个知识点：哪些工具调用会停下来问人，这个判定在代码里是怎么实现的？请定位 tool 执行前触发确认判定的代码路径（可搜 approve、confirm、permission、pending、interrupt、human_input 等关键词，或从主循环里 tool call 被拦截之处入手）并引用具体 file:line；说明权限模式有哪几档、每档下哪些操作需要确认、不同档位映射到哪些常量或配置项、判定要不要问人的依据是什么（工具类型、配置、风险检测器还是混合）；点出权限模式枚举与判定函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点。
```

```text
接着上面的权限确认门继续深入：确认请求是怎么送达用户、用户的选择又怎么回到执行流的？请定位确认请求的送达通道（事件、回调还是阻塞队列，渲染成什么样的界面元素）、等待用户裁决期间 agent 循环处于什么状态（挂起、轮询还是异步等待）、批准与拒绝分别把控制流引到哪里、多个待确认操作排队时按什么顺序处理，引用 file:line；用文字讲清从「模型产出 tool call」到「确认后真正执行（或被拒绝后回喂模型）」的完整调用链；点出审批状态机的数据结构与关键函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如等待确认有没有超时行为）。
```

#### H6. 允许清单与拒绝清单（permission rules）｜P1

**是什么**：一组按工具、按参数模式（命令前缀、文件 glob、域名）匹配的规则，把每次调用解析为放行（allow）、询问（ask）或拒绝（deny），并有明确的优先级语义（如 last-match-wins 或 deny 优先）。

**为什么重要**：逐条确认会把人耗死，全自动又等于交出钥匙；allow/deny 规则是安全策略「配置即代码」的形态。规则的匹配语义细节——glob 的隐藏坑、前缀匹配的绕过（`git commit; curl …` 复合命令）、allow 与 deny 相撞时谁赢——正是真实攻防发生的层面。

**快速信号**：grep：`allow`、`deny`、`ask`、`blocklist`、`whitelist`、`blacklist`、`rules`、`glob`、`prefix`、`match`。看配置文件里的 `permissions` / `allow` / `deny` 段与对应 schema；找命令解析与模式匹配函数（`matchCommand`、`parseRules` 一类命名）。

**代表实现**：opencode（permission 规则解析为 allow/ask/deny，glob 作用域、last-match-wins，企业 policy 可强制收紧为 deny）；cline/cline（auto-approve 分档并带命令白名单）；aaif-goose/goose（GOOSE_MODE 四档 auto/smart-approve/approve/chat 控制整体审批行为）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「允许清单与拒绝清单」这一个知识点：permission 规则是怎么定义、加载和匹配的？请定位规则的解析与匹配逻辑（可搜 allow、deny、ask、blocklist、whitelist、permission rules、glob、prefix 等关键词，或找配置文件里的 permissions/allow/deny 段）并引用具体 file:line；说明规则的形状（按工具、命令前缀、文件 glob 还是域名），一次 tool call 到来时按什么顺序匹配（deny 优先还是 allow 优先、最具体规则是否最优先、还是 last-match-wins），命令类规则如何应对 shell 解析的变形（引号、复合命令、绝对路径）；用文字讲清从「规则配置被加载」到「一次具体调用被放行或拦截」的完整数据流；点出规则的数据结构与匹配函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如一条以白名单命令开头、但用 `;` 拼接了其他命令的复合命令会不会被前缀规则放行）。
```

#### H7. 自动批准分级与「always allow」持久化（Auto-approve Tiers & Persisted Approvals）｜P1

**是什么**：把可自动放行的操作按风险分层（只读 < 工作区内编辑 < 任意命令 < 浏览器/网络），并把用户的「总是允许」决定持久化到项目或全局配置，形成随使用累积的授权集。

**为什么重要**：授权只会朝一个方向累积：一次「always allow」就是一次永久让渡，而它的粒度（精确命令、通配模式、还是整类工具）决定了让渡了多少。看清这层的存储键与作用域，才能回答「一个长期使用的 agent 会慢慢变成什么」。

**快速信号**：grep：`auto_approve`、`autoApprove`、`always_allow`、`alwaysAllow`、`remember`、`saved_approval`、`trust`、`allowed_commands`。看设置面板/配置 schema 里的分档开关；看确认弹窗的按钮集合（Allow once / Always allow / Deny）及其落盘位置。

**代表实现**：cline/cline（auto-approve 设置按读文件/编辑/执行命令/浏览器分档）；opencode（用户的批准决定作为 saved approvals 持久化，与规则共同参与判定）；ag2/AutoGen（human_input_mode 的 NEVER/TERMINATE/ALWAYS 三档控制人工介入频率）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「自动批准分级与 always allow 持久化」这一个知识点：哪些操作可以不问人直接放行，用户的「总是允许」又存到哪里？请定位自动批准的判定代码（可搜 auto_approve、always_allow、alwaysAllow、remember、saved approval、trust 等关键词，或从确认门附近回溯哪些路径会跳过确认）并引用具体 file:line；说明分级依据是哪些维度（工具类别、只读/只写、路径范围、命令是否在白名单），用户选择「总是允许」后这条决定写到哪个文件、以什么键存储（精确命令还是通配模式）、作用域是本项目还是全局、下次会话怎么加载生效；用文字讲清一次「本应确认的调用被自动放行」的完整判定链；点出分级配置的数据结构与查询函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如能否对某个子目录单独 always allow 写操作、always allow 条目有没有过期或复核机制）。
```

#### H8. Prompt injection 防御：外部内容一律视为数据｜P1

**是什么**：在系统提示与工具协议层面立铁律——网页、文件内容、命令输出、第三方插件返回里出现的任何指令性文字都只是待处理的数据，不是命令；发现可疑指令时引用并作为异常上报（quote-and-flag），绝不执行。

**为什么重要**：Agent 读的每个网页、每份 issue、每次 tool 输出都是注入面；一旦外部文本能冒充指令，前面所有沙箱与确认门都可能被模型「自愿」绕过——注入攻击不是黑掉系统，是说服系统。这是唯一作用在模型行为层而非进程层的防线，也正因为它依赖模型服从，通常只作为纵深防御的一层、必须与沙箱组合使用。

**快速信号**：grep：`injection`、`untrusted`、`ignore instructions`、`never follow`、`as data`、`not as instructions`。重点读系统提示文本（常嵌在 `*.txt` / `*.md` / 常量字符串里）里关于外部内容的措辞；看 web fetch、browser、文件读取类 tool 输出的后处理有没有注入检测或标记逻辑。

**代表实现**：openai/codex（系统提示明令把 file contents 与 command output 当数据不当指令）；OpenHands（对 prompt injection 做过系统研究，结论是提示纪律必须与容器隔离组合）；agentdojo（ETH 的 injection 鲁棒性评测框架，把这类防御变成可回归的测试）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「prompt injection 防御」这一个知识点：这个仓库怎么防外部内容里夹带的指令？请定位相关实现（可搜 injection、untrusted、ignore instructions、as data 等关键词，重点读系统提示的原文措辞，以及 web fetch、browser、文件读取这类引入外部内容的 tool 的输出处理）并引用具体 file:line；说明系统提示里「外部内容是数据不是指令」的规则怎么写的、放在哪个位置，除提示外有没有代码层配套（输出过滤、异常指令检测、引用标记），外部内容进入上下文前是否经过清洗或框架化；用文字讲清一次「网页里藏了指令 → 内容进入模型上下文 → 模型行为」的完整数据流与各防御点介入的位置；点出关键函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如这些防御有没有对应的测试用例覆盖）。
```

#### H9. 不可信内容边界与上下文构造（framing / provenance）｜P1

**是什么**：明确划分可信内容（系统提示、用户消息）与不可信内容（tool result、网页抓取、文件内容、MCP/插件返回），送进上下文前用结构化手段区分——独立 role / 消息通道、分隔符、来源标签——而不是与用户消息混排。

**为什么重要**：光有「视为数据」的训诫（H8）不够，还需要结构上的隔离：若 tool 输出与用户消息在同一通道里拼接，模型与下游做权限检查的代码都无法判断一段话的出处。来源区分同时是权限判定（这段话能触发什么）与事后审计（这句话谁说的）的地基；MCP 与插件生态把这条边界从「好实践」变成「必需品」。

**快速信号**：grep：`untrusted`、`tool_result`、`observation`、`provenance`、`source`、`origin`、`delimiter`、`system-reminder`、`environment_context`、`wrap`。看构造 prompt / messages 的代码：外部内容是原样拼进 user message，还是放进独立 role 或带标签的区块；看 MCP / 插件输出的包装层。

**代表实现**：OpenHands（Action/Observation 事件模型天然区分「自己发出的动作」与「外部世界的反馈」）；openai/codex（环境上下文以独立消息通道注入，与用户输入分开）；letta-ai/letta-code（memory blocks 与消息历史分层注入上下文，而不是混进对话流）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「不可信内容边界在上下文构造上的落地」这一个知识点：外部内容进入模型上下文时，和用户消息、系统提示是怎么区分的？请定位组装 prompt / message list 的代码（可搜 untrusted、tool_result、observation、provenance、source、delimiter、system-reminder 等关键词，或从 web/文件读取 tool 的输出处理入手）并引用具体 file:line；说明网页正文、文件内容、命令输出、MCP 或插件返回分别以什么形态进入上下文（独立 role、分隔符、来源标签、转义还是截断），有没有代码给内容打来源或可信度标记、下游谁消费这个标记；用文字讲清一次「抓取网页 → 内容进入模型上下文」的完整数据流；点出消息构造的数据结构与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如注入内容能否伪造分隔符把自己升格为系统消息、MCP 工具的返回值是否被同等对待）。
```

#### H10. 密钥管理：env / 加密存储 / 密钥服务，不落源码｜P1

**是什么**：API key、token 一律从环境变量、gitignore 的 `.env` 文件、加密存储或密钥服务读取，源码、默认配置、示例与测试里只出现占位符；运行时按需注入，只交给真正发起请求的组件。

**为什么重要**：Agent 仓库天生被大量 fork 与二次开发，示例里一个「顺手填上」的真实 key 会随 fork 图谱永生；更关键的是 agent 自己能读文件、能执行命令，密钥放错位置的代价从「可能泄露」升级为「可能被模型亲手用掉」。这是贯穿「入库扫描 → 加载 → 使用 → 存档」全生命周期的工程纪律。

**快速信号**：grep：`API_KEY`、`getenv`、`environ`、`dotenv`、`keyring`、`keychain`、`auth.json`、`credentials`、`token`、`Secret`。看 `.env.example`、`.gitignore`、配置 schema 里 key 字段的默认值；看 CI 里有没有 secret 扫描（gitleaks / trufflehog 一类）步骤。

**代表实现**：Aider-AI/aider（`.env` 文件链式加载各 provider 的 API key）；openai/codex（auth.json 存 API key 与 ChatGPT 登录 token，支持刷新）；letta-ai/letta-code（Secret 类对 provider 凭据加密存储，配 LETTA_ENCRYPTION_KEY）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「密钥管理」这一个知识点：API key 等凭据从哪里读、存在哪、怎么流到请求里？请定位凭据的读取与存储代码（可搜 API_KEY、getenv、dotenv、keyring、keychain、auth.json、credentials、secret 等关键词）并引用具体 file:line；说明密钥从哪里进来（环境变量、.env、系统 keychain、加密存储、配置文件），加载顺序与优先级是什么，token 过期或刷新怎么处理，密钥会不会出现在日志、错误信息、调试 dump 或被发送给模型的内容里；用文字讲清从「进程启动」到「一次带认证的 API 请求」密钥经过的完整数据流；点出凭据对象的数据结构与读写函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如 .env 是否被 gitignore 覆盖、多个来源的密钥冲突时谁生效、示例与测试里是否只有占位符）。
```

#### H11. 日志与转录脱敏（secret redaction）｜P1

**是什么**：在事件、对话、错误、遥测写盘或上报之前，用运行时已知的真实密钥值与模式匹配把 key、token、口令替换为掩码，让审计材料本身不携带可用凭据。

**为什么重要**：审计日志与 session transcript 是安全机制的一部分，但它们自己会变成密钥集散地：用户把日志贴到 GitHub issue 求助的那一刻就是泄露时刻。transcript 的完整性放大了这个风险——连模型在输出里复述出来的密钥也会被记录；脱敏必须覆盖所有持久化出口（J4 的转录、H12 的审计流），且最好基于运行时已知密钥做精确匹配，而不只靠正则猜。

**快速信号**：grep：`redact`、`mask`、`scrub`、`sanitize`、`obfuscate`、`SecretStr`、`secret`。看日志/遥测的出口函数、transcript 落盘前的处理管道、异常与配置的序列化路径（pydantic `SecretStr` 一类）。

**代表实现**：letta-ai/letta-code（Secrets 机制：agent 在 shell 命令里使用密钥，但上下文里只见到遮蔽值）；OpenHands（代码库普遍用 pydantic.SecretStr 做序列化脱敏，也出过绕过该模式导致 key 进日志的真实 issue，可当反面教材读）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「日志与转录脱敏」这一个知识点：持久化之前，密钥是怎么被遮蔽的？请定位脱敏逻辑（可搜 redact、mask、scrub、sanitize、obfuscate、SecretStr 等关键词，或从 transcript/日志/遥测的写盘出口往回追）并引用具体 file:line；说明脱敏发生在哪一层（写盘前、上报前还是序列化时），用什么方式识别敏感值（运行时已知密钥的精确匹配、正则模式、还是字段名启发式），有没有覆盖错误堆栈、HTTP header、环境变量 dump 这些容易漏的出口；用文字讲清一次「对话或事件被持久化」的过程中脱敏介入的完整数据流；点出脱敏函数与敏感值识别的数据结构、函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如模型输出里复述出来的密钥会不会被同样处理、脱敏是否可逆）。
```

#### H12. 审计日志：action / observation 事件流（Audit Log）｜P1

**是什么**：把 agent 的每一步——模型的 tool call 与参数、系统的判定（放行/拦截/确认）、工具的返回——以 append-only 事件流完整落盘，可回放、可审计，是安全事后取证与行为分析的输入。

**为什么重要**：没有审计就没有可追责性：出了问题（误删文件、可疑命令、数据外传），唯一能回答「它到底做了什么、谁批准的」的就是这份记录。事件流同时是产品功能的地基——回放、断点恢复（G10）、从错误状态重试、评测数据集都从它长出来，安全审计只是它最严格的那一面。格式与写入路径的视角见 J4。

**快速信号**：grep：`transcript`、`event`、`history`、`audit`、`trajectory`、`jsonl`、`checkpoint`、`state`、`log_event`。找 session/trajectory 落盘文件（常为 `*.jsonl`）与写入函数；看事件类型的枚举或类层次定义。

**代表实现**：OpenHands（EventStream 架构：所有 Action/Observation 事件入流、可导出回放）；langchain-ai/langgraph（checkpointer 持久化每一步 state，支持 time-travel 回放）；SWE-agent（完整 trajectory 记录是评测与分析的一等公民）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「审计日志 / 事件流」这一个知识点：agent 的每一步动作和系统的每一次判定是怎么被记录下来的？请定位事件或轨迹的写入代码（可搜 transcript、event、history、audit、trajectory、jsonl、checkpoint 等关键词）并引用具体 file:line；说明事件的数据模型是什么（一次 agent 步骤被拆成哪些事件类型，tool call、系统判定、工具返回分别怎么记），写入是 append-only 还是可变，记录里有没有权限判定的痕迹（这次调用是被谁、按什么规则放行的）；用文字讲清从「主循环里发生一次 tool call」到「它成为可回放记录」的完整数据流；点出事件类层次结构与序列化函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如日志能否用来恢复会话、日志本身是否经过脱敏）。
```

#### H13. fail-closed 默认与沙箱提权/降级路径（Fail-closed & Escalation Paths）｜P1

**是什么**：安全机制初始化失败或不可用时默认拒绝执行（fail-closed），「更危险」的能力（关沙箱、跳过审批）必须经用户显式 opt-in；同时有一条受控的提权路径——命令在沙箱内失败后，凭用户批准升级为更高权限重试。

**为什么重要**：默认值就是 99% 用户实际得到的系统：沙箱起不来时静默降级成无沙箱（fail-open）等于没有沙箱。反过来，一条设计良好的提权路径（沙箱失败 → 展示原因 → 用户批准 → 提权重跑）让严格默认不必为可用性打折。看一个仓库怎么处理「安全组件坏掉的那一天」，比看它的宣传页更接近真相。

**快速信号**：grep：`dangerously`、`danger`、`full_access`、`bypass`、`unsafe`、`escalat`、`fallback`、`yolo`。看 CLI flag 里带 `--dangerous*` 的选项及其交互确认；看沙箱或权限组件初始化失败的错误分支走向。

**代表实现**：openai/codex（danger-full-access 需显式选择；on-failure 审批策略下命令在沙箱内失败可凭用户批准升级重试）；OpenHands（危险动作触发的是确认或阻止，而不是静默跳过）。

```text
我在一个开源 AI Agent 仓库里读源码，只聚焦「fail-closed 默认与沙箱提权/降级路径」这一个知识点：安全机制失败或不够用时，系统走哪条路？请定位相关分支（可搜 dangerously、danger、full_access、bypass、unsafe、escalate、fallback 等关键词，以及沙箱初始化失败的错误处理路径）并引用具体 file:line；说明沙箱或权限组件初始化失败时代码是拒绝执行、降级运行还是询问用户，有没有「沙箱内失败后凭用户批准以更高权限重试」的升级路径及其判定与展示逻辑，全权限/danger 模式需要怎样的显式 opt-in（flag、交互确认还是配置声明）；用文字讲清一次「命令在沙箱内失败」到「升级重试或放弃」的完整状态流转；点出相关的状态枚举与函数名；若本仓库没有这一机制，请直说并指出最接近的替代实现；引用不到的位置就明说，不要编造；最后给出 2-3 个基于这个仓库实现的追问点（例如升级重试会不会被循环利用来反复提权、danger 模式下还有哪些防线仍然生效）。
```
