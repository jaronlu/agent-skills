---
name: chinese-text-fixer
description: >-
  修复中文文本的标点与排版问题：引号方向与配对（如 “xxxx“ → “xxxx”）、全角/半角标点、中文标点旁多余空格、零宽字符与 BOM、HTML 实体残留、括号/书名号错配；乱码只识别不擅自还原。当用户要求校对、清洗或规范化中文文案、OCR 结果、Markdown、字幕、聊天记录，或贴出引号明显错误的中文文本时使用。附带确定性脚本：默认 dry-run 输出逐行 diff，确认后才写回。Triggers: 中文校对、标点修复、引号方向、全角半角、乱码识别、Chinese punctuation, Chinese quotes, mojibake.
metadata:
  version: "1.0"
---

# Chinese Text Fixer

## 定位

在文本层做**确定性**的中文标点与排版修复：能明确判断的才自动改，判断不了的只报告。

这里的“编码问题”多数其实是标点配对问题：文件仍能正常按 UTF-8 解码，只是引号方向写反了。本 skill 不转码、不猜原始编码。

不做：翻译、润色、改写语义、OCR 重新识别、编码转换、乱码还原、补写缺失内容。

## 适用判断

适用：

- 用户贴出或指定中文文本，要求校对、清洗、规范化标点。
- 引号方向或配对错误，例如 `“数据怎么流转/谁响应手势“`。
- 中英混排、全角/半角混用、中文标点旁有多余空格。
- OCR、字幕、聊天记录、Markdown 导出后的标点清理。
- 只需要诊断和 diff，不需要写回。

不适用：

- 需要改变措辞、语气或结构：用普通写作或改写流程。
- 文件不是 UTF-8，或已经出现乱码：先确认原始编码并转码，本 skill 只识别乱码。
- 纯英文排版：英文引号、撇号和中文规则不同；脚本会尽量避开，但不要把它当英文校对器。
- 代码、配置、序列化数据中的符号：默认跳过 Markdown 代码区，其他文件类型不要批量套用。

## 工作流

1. **确认输入与写回权限。** 区分文件/目录、内联文本、只诊断三种输入。写回前确认目标文件可写；在 Git 仓库内先看 `git status`，不覆盖用户未提交的改动。
2. **先扫描，不写回。** 默认就是 dry-run：

   ```bash
   python3 scripts/fix_text.py <path> [--profile standard] [--format json]
   ```

   粘贴文本用 `--text "..."`，管道用 `-`。脚本输出 `fix` 与 `review` 两类问题、逐行 diff、退出码。

3. **分级复核。** 不要把两类问题混在一起：
   - `fix`：规则能确定修复，例如引号方向反转、零宽字符、中文语境中的半角标点、重复标点、中文标点旁空格。
   - `review`：需要上下文判断，例如未闭合/孤立/交叉引号、括号错配、乱码、HTML 实体、有意义或不确定的不可见字符、中拉丁间距。
   对 `review` 项逐条说明原因，不擅自改成“看起来对”的样子。
4. **用户确认后写回。** 只有用户明确同意，才执行：

   ```bash
   python3 scripts/fix_text.py <path> --apply
   ```

   写回是原子替换，保留原换行符（LF/CRLF）与文件权限。写完再跑一次 dry-run，确认只剩 `review` 项。
5. **输出报告。** 报告实际修复数、仍需人工复核数、跳过的文件及原因。未处理的项要明说，不能把“没有 fix 项”说成“文本已完全正确”。
6. **停止条件。** 遇到非 UTF-8、二进制、符号链接、乱码时跳过并报告；用户未确认时不写回；判断不了引号/括号归属时停在该项，不补全、不猜测。

## Profile 选择

| Profile | 自动修复范围 | 使用场景 |
| --- | --- | --- |
| `minimal` | 引号方向、零宽字符/BOM | 只做最保守的修复 |
| `standard`（默认） | 再加全角/半角标点、重复标点、中文省略号、中文标点旁空格 | 常规中文校对 |
| `strict` | 再加中文与拉丁字母/数字之间的空格、非 HTML 文件中的实体解码 | 排版统一、可接受较多改动 |

无论哪个 profile，`review` 项都会报告；profile 只决定哪些项进入自动修复。

## 规则速查

| 规则 | 处理 | 说明 |
| --- | --- | --- |
| `QT001` | fix | 引号方向反转，如结尾的 `“` 应为 `”` |
| `QT002` | review | 未闭合、孤立或无法判断归属的引号 |
| `QT003` | review | 单双引号嵌套顺序交叉 |
| `BR001`–`BR003` | review | 括号/书名号多余、错配、未闭合 |
| `FW001` | fix（standard） | 中文语境中的半角 `, . ; : ? !` → 全角 |
| `PU001`–`PU003` | fix（standard） | 重复标点合并、中文省略号 `...` → `……` |
| `SP001` | fix（standard） | 中文标点前、开括号后的多余空格 |
| `SP002` | review；strict 下 fix | 中文与拉丁字母/数字之间缺空格 |
| `ZW001` | fix | 删除零宽空格、BOM |
| `ZW002` | review | 零宽连接符、软连字符、不间断空格等 |
| `EN001` | review；strict 或 `--fix-entities` 下 fix | HTML 实体残留；HTML/XML 中始终只报告，解码后是不可见字符时也只报告 |
| `MO001` | review | 疑似乱码，只识别不还原 |

规则细节、边界和误判清单见 [references/punctuation-rules.md](references/punctuation-rules.md)。需要解释某条 finding、修改规则或处理争议样例时再读。

## 脚本契约

```text
python3 scripts/fix_text.py [PATHS...] [--text TEXT] [--apply]
                            [--profile minimal|standard|strict]
                            [--format text|json] [--fixed]
                            [--fix-entities] [--ext .srt]
                            [--no-skip-code] [--max-issues N]
```

- 无 `--apply`：只打印报告与 diff，不写文件。
- `--fixed`：只输出修正后的全文，适合单文件、`--text` 或 stdin；不写回，不能与 `--format json` 同用。
- `--apply`：仅用于文件路径；原子写回，写后报告仍会列出剩余 `review` 项。
- `--format json`：机器可读；包含每个文件的 `issues`、`issue_count`、`diff`、`wrote`；`issue_count` 是总数，不受 `--max-issues` 截断影响。
- `--ext`：目录扫描时追加后缀；默认 `.md .markdown .mdx .txt .rst .csv .tsv`。
- `--no-skip-code`：连 Markdown frontmatter、代码围栏、行内代码一起处理；只有用户明确要求时才用。
- `--fix-entities`：在非 HTML/XML 文件中解码实体；默认只报告。
- `--max-issues`：限制每个文件展示的条数，不影响实际修复与退出码。

退出码：

- `0`：没有发现问题，或所有 fix 已写回且没有 review/跳过项。
- `1`：dry-run 发现问题；或 apply 后仍有 review/跳过项。
- `2`：参数、I/O 或编码错误。

`--fixed` 只按剩余 `review` 项计：无 review 为 `0`，有 review 为 `1`；已经输出的 fix 项不改变退出码。

## 安全边界

- 只处理 UTF-8。UTF-16、二进制、含 NUL 的文件一律跳过并报告，不自动转码。
- 默认保护 Markdown frontmatter、代码围栏、行内代码和 URL；宁可不改，也不误改代码。
- 不补全未闭合引号，不移动括号，不猜测乱码原文；这些只报告。
- 不因修复标点而改变语义、语序或措辞；不删除疑似正文的内容。
- 没有用户确认，不写回任何文件。
- 报告结论只写实际修复与剩余问题，不把 `review` 未处理说成通过。
