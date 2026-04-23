# 📚 Therapy Wiki

### *本地优先的 agent harness，在 [Codex](https://openai.com/codex) 或 [Claude Code](https://www.anthropic.com/claude-code) 里把咨询录音、语音备忘、聊天记录、日记编译成一个长期维护的心理学 wiki。*

[English README](./README.md) · [环境配置](./schema/setup.md) · [Wiki 维护规范](./schema/wiki-maintainer.md) · [CLI 规范](./schema/cli.md)

---

Therapy Wiki 是一个直接在 agent 运行时里打开的仓库 —— repo 本身就是 harness。把咨询录音、语音备忘、聊天记录或日记丢进去，它会帮你编译成一份可长期维护、可追溯回原始材料的心理学 wiki。

> 它要做的是把 wiki 持续编译得越来越完整，
> 让你在下一次对话里不用再从零推一遍自己。

## ✨ 为什么做这个

一个人可能习惯保留很多谈话（心理咨询）录音、文本，但是往往很难整合：

- 🎙️ **录音越堆越多**，但基本不会回听。
- 💬 **聊天上下文一次性**，每开一个新对话都要从零解释自己。
- 📝 **结论留不住**，一次讨论出来的洞见没有地方沉淀。

Therapy Wiki 用尽量轻量的工作流来解决问题：一棵文件树加一组 Codex / Claude 的 skills 就完事了。没有 hosted service、 web UI、向量数据库、要维护的后端 （这些东西在最近几个月开启的AI agent时代已经过时了！😱） 如果你已经在用 Codex 或 Claude Code，交互界面就是现成的。

## 👤 适合谁

- 长期积累 voice memo / 日记 / 自我观察材料的人。
- 在做线上心理咨询、并且保留录音或笔记的人。
- 想把同一批材料反复从不同视角看的人。
- 喜欢 agent workflow，但不想再搭重系统的人。
- 想把自己的个人材料库变成可持续知识结构的人。
- （致力于成为 Uploaded Intelligence 的人


## 🧱 核心结构

遵循 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#file-llm-wiki-md) 原则的三层结构：


| 层            | 职责                                                      | 写入权限   |
| ------------ | ------------------------------------------------------- | ------ |
| `raw/`       | ingest 时拷进来的原始录音                                        | 不可变    |
| `artifacts/` | transcript、diarization、speaker map、review、summary 等中间产物 | 机器生成   |
| `wiki/`      | 长期知识库，人工 + agent 共同维护                                   | 持续增量编译 |


所有东西都是 plain Markdown / JSON，方便人类和 AI 读写、 diff、grep。

## 🔄 内置工作流

1. **Ingest** —— 把音频拷到 `raw/`，转写、diarize，生成 review 产物。
2. **Review** —— 人工修 transcript 和 speaker map（只改值得改的地方）。
3. **Rebuild** —— 重新编译对应 session 的 wiki 页面。
4. **Report** —— 生成单次复盘或跨 session 纵向报告。
5. **Discuss** —— 用某个 persona 做讨论，必要时把结论 file back 回 wiki。

整套流程由一个 CLI 入口（`./therapy`）加一组 Codex skills 驱动。

## 🔬 消化流程底层

第一步 `Ingest` 是一条确定性的本地流水线，核心完全跑在开源模型上 —— 没有云端 STT、没有云端 LLM、零 API 费用。

```text
音频
  ├─▶ prepared.wav                              (ffmpeg：16 kHz 单声道 wav)
  ├─▶ transcript.raw.json                       (STT：MLX Whisper*)
  ├─▶ diarization.json                          (说话人分离：pyannote.audio)
  ├─▶ speaker_map.json + transcript.turns.json  (确定性对齐 + 标签建议)
  ├─▶ summary.json + review.md                  (确定性主题 / 模式提取)
  └─▶ wiki/sessions/<id>.md                     (确定性 wiki 编译)
```

各阶段和使用的开源模型：

| 阶段 | 产物 | 后端 | 许可 |
| --- | --- | --- | --- |
| 音频预处理 | `prepared.wav` | [`ffmpeg`](https://ffmpeg.org/) | LGPL |
| 语音转写 | `transcript.raw.json` | [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper)，模型 `whisper-large-v3-turbo`（快）或 `whisper-large-v3`（准） | MIT（OpenAI Whisper 权重） |
| 说话人分离 | `diarization.json` | [`pyannote.audio`](https://github.com/pyannote/pyannote-audio)，模型 `speaker-diarization-community-1`（fallback `speaker-diarization-3.1`） | 代码 MIT；权重在 Hugging Face 上 gated |
| 说话人对齐 + 标签建议 | `speaker_map.json`、`transcript.turns.json` | 纯 Python 启发式，见 [src/therapy_wiki/speaker_map.py](src/therapy_wiki/speaker_map.py) | — |
| 会谈摘要 + 审阅笔记 | `summary.json`、`review.md` | 纯 Python 主题 / 模式提取，见 [src/therapy_wiki/summarize.py](src/therapy_wiki/summarize.py) | — |
| Wiki 编译 | `wiki/sessions/<id>.md`、`wiki/index.md`、`wiki/log.md` | [src/therapy_wiki/wiki.py](src/therapy_wiki/wiki.py) | — |

\*macOS Intel / Linux 上没有 `mlx-whisper` wheel，替代 STT 方案见 [schema/setup.md](./schema/setup.md)。

整条流水线里，唯一期望 frontier LLM 做重活的只有 **Report** 和 **Discuss**，而且它们只在已经编译好的 wiki 上推理，不会直接碰原始音频。上面表格里的每一步都是本地的、可复现的，模型权重缓存后可以离线跑。

## 🎭 Personas

对同一批材料的不同视角。针对每个 persona 设计了自己的方法卡和 skill，有不同的结构、问题、关注点、输出框架。


| Persona        | 从什么视角读材料                            |
| -------------- | ----------------------------------- |
| `therapist`    | 过程、情绪、防御、关系姿态、下一步工作点                |
| `supervisor`   | 干预选择、节奏、治疗联盟、错过与替代做法                |
| `psychologist` | formulation、机制、竞争性解释、纵向模式           |
| `intp-lens`    | 结构、回路、矛盾、隐含规则                       |
| `close-friend` | 直率的现实检查 —— **和正式 formulation 明确分开** |


如果有需要新的Personas，叫 agent 直接添加就行。

## 📄 生成报告

- **单次复盘** —— 针对一次 session 的结构化输出。
- **纵向报告** —— 对 wiki 里所有 session 做综合。

报告默认用中文输出，要求 source-grounded，每个判断都要引用 `session_id + timestamp`。

## 🚀 Quick start

### 写给人类看的

1. `git clone` 这个仓库。
2. 用 Claude Code 或 Codex 打开。
3. 让它帮你把环境装好、skills 装好、跑通第一次 ingest。

就行了。下面这节给 agent 自己读：

### 写给 AI 看的

<details>
<summary>点击展开：环境准备、skills 安装、常用命令</summary>

```bash
# 1. 系统依赖
brew install ffmpeg          # macOS；其他系统用你的包管理器

# 2. Clone
git clone <this-repo>
cd my-therapist

# 3. 把项目里的 skills 装到 ~/.codex/skills/
python3 scripts/install_skills.py

# 4. Ingest 一段录音或一个目录
./therapy ingest ~/path/to/new-session.m4a
```

新机器上第一次配 STT + diarization（mlx-whisper、pyannote 等）请看 `[schema/setup.md](./schema/setup.md)`；CLI 的完整行为见 `[schema/cli.md](./schema/cli.md)`；wiki 维护规则见 `[schema/wiki-maintainer.md](./schema/wiki-maintainer.md)`。

</details>

## 🛠️ 常见用法

### 给人类用户

日常使用不需要记任何命令行参数。在仓库目录里打开 Codex 或 Claude Code，直接用自然语言告诉 agent 三件事就行：**scope（针对哪些材料）** × **persona（用什么视角）** × **task（做什么）**。agent 会自己选 skill、调用 CLI。

**可选的 scope**

- `latest` —— 最近一次 session
- `session <id>` —— 某一次具体 session（比如 `session 2025-04-20`）
- `all` —— wiki 里全部 session

**可选的 persona**

- `therapist` —— 过程、情绪、防御、关系姿态、下一步工作点
- `supervisor` —— 干预选择、节奏、治疗联盟、错过与替代做法
- `psychologist` —— formulation、机制、竞争性解释、纵向模式
- `intp-lens` —— 结构、回路、矛盾、隐含规则
- `close-friend` —— 直率的现实检查（和正式 formulation 明确分开）

**可选的 task**

- **Ingest** —— 把新的录音消化进 `raw/` + `artifacts/` + `wiki/`
- **Refresh** —— 手动修过 `transcript.edited.md` 或 `speaker_map.json` 之后，重新编译那一次 session
- **单次复盘** —— 针对一次 session 的结构化报告
- **纵向报告** —— 跨 session 综合
- **讨论某个具体问题** —— 提问，让某个 persona 给结构化回答
- **File back** —— 把这次讨论里值得长期保留的结论，写回该 persona 的 wiki 笔记
- **Lint** —— 检查 wiki 结构是否健康

**示例对话**

> "帮我 ingest `~/voice/2025-04-20.m4a`，然后用 `therapist` persona 写一份单次复盘。"

> "用 `psychologist` 视角看 `all` scope 的纵向模式，输出一份综合报告。"

> "用 `close-friend` 视角讨论 `latest` session：我是不是还在回避什么？值得保留的结论请 file back。"

> "我刚手动改完 `2025-04-20` 这次的 `transcript.edited.md`，帮我 refresh 一下这次 session。"

### 给 agent 看的 CLI

<details>
<summary>点击展开：对应的 <code>./therapy</code> 命令</summary>

**新增一次 session 后**

```bash
./therapy ingest ~/path/to/new-session.m4a
./therapy report latest --persona therapist
```

**想做跨 session 梳理时**

```bash
./therapy report all --persona psychologist
./therapy discuss --persona supervisor --scope all \
  --question "真正稳定的模式是什么，哪些只是近期波动？"
```

**想要更直接的版本时**

```bash
./therapy discuss --persona close-friend --scope latest \
  --question "我现在到底还在替自己绕开什么？" --file-back
```

**手动修完 transcript / speaker map 后**

```bash
./therapy ingest --refresh <session-id>
```

</details>

## 📦 仓库结构

```text
src/therapy_wiki/      Python CLI 与 workflow 逻辑
skills/                Codex skills：ingest、report、discuss、各 persona
schema/                persona cards、报告模板、wiki 维护规范、运行时说明
tests/                 workflow 测试（带 fake backend）
therapy                仓库内可直接运行的 CLI 入口
```

运行时会生成并默认 git-ignore 的目录：

```text
raw/                   不可变的原始录音
artifacts/             transcript、diarization、summary、review 产物
wiki/                  长期 Markdown 知识库
outputs/               报告、lint 报告
```

内置 skills：`therapy-ingest` · `therapy-report` · `therapy-discuss` · `therapy-therapist` · `therapy-supervisor` · `therapy-psychologist` · `therapy-intp-lens` · `therapy-close-friend`


当前 ingest 路径是音频优先的，但整个结构本来就是朝更广义的个人材料库设计的。