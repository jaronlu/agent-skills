# 脚本契约

`scripts/fix_text.py` 的参数、退出码与已知坑。`SKILL.md` 只保留常用项，细节读这里。

## 签名

```text
python3 scripts/fix_text.py [PATHS...] [--text TEXT] [--apply]
                            [--profile minimal|standard|strict]
                            [--format text|json] [--fixed]
                            [--fix-entities] [--ext .srt]
                            [--no-skip-code] [--max-issues N]
```

## 参数

- 无 `--apply`：只打印报告与 diff，不写文件。
- `--fixed`：只输出修正后的全文，适合单文件、`--text` 或 stdin；不写回，不能与 `--format json` 同用。
- `--apply`：仅用于文件路径；原子写回，写后报告仍会列出剩余 `review` 项。
- `--format json`：机器可读；包含每个文件的 `issues`、`issue_count`、`diff`、`wrote`；`issue_count` 是总数，不受 `--max-issues` 截断影响。
- `--ext`：目录扫描时追加后缀；默认 `.md .markdown .mdx .txt .rst .csv .tsv`。所有输入都没匹配到文件时报错并返回 `2`，不会输出 `clean`。
- `--text` 与 stdin：默认按 Markdown 处理，同样保护代码围栏、行内代码和 frontmatter。
- `--no-skip-code`：关闭上述保护，连 frontmatter、代码围栏、行内代码一起处理；只有用户明确要求时才用。
- `--fix-entities`：在非 HTML/XML 文件中解码实体；默认只报告。
- `--max-issues`：限制每个文件展示的条数，不影响实际修复与退出码（`issue_count` 仍是总数）。

## 退出码

- `0`：没有发现问题，或所有 fix 已写回且没有 review/跳过项。
- `1`：dry-run 发现问题；或 apply 后仍有 review/跳过项。
- `2`：参数、I/O 或编码错误，或目录里没有匹配的文件。

`--fixed` 只按剩余 `review` 项计：无 review 为 `0`，有 review 为 `1`；已输出的 fix 项不改变退出码。因此存在可修项时 `--fixed` 仍返回 `0`，不要用它判断「是否有待修」，那种场景用默认 dry-run。

## 已知坑

- `--apply` 会重新扫描当前文件再写入。dry-run 之后文件若被外部改动，写入内容可能与用户确认的 diff 不同；写前用 `git status` 或文件大小核对。
- `--apply` 对目录是整批写入，无备份、不可撤销。
- `--max-issues` 只截断展示，不限制修复条数。
- `..`（两个点）与四个及以上点不进任何规则，既不修改也不报告。

## 输出格式

```text
chinese-text-fixer · profile=standard · dry-run

path/to/file.md:12:8  [QT001 fix] 引号方向：此处应为闭引号 ”
path/to/file.md:20:3  [BR003 review] 开括号 （ 未闭合，未自动补全

--- path/to/file.md
+++ path/to/file.md (fixed)
@@ ...
```

- `fix` 计数包含已进入 diff 的修复；apply 后这些修复已写回。
- `review` 计数是仍需人工判断的项。
- 跳过文件单独列出原因：非 UTF-8、UTF-16、二进制/NUL、符号链接。
- 报告头、`summary` 与 `error` 行是英文（便于解析），finding 消息是中文。转述给用户时按中文写。
