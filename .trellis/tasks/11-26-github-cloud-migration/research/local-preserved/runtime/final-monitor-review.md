# 重试监控脚本 —— 只读审查

审查对象：`.trellis/.runtime/monitor_json_pi_requests.py`（全文 44 行）
审查时间：2026-10-26
审查方式：只读。未修改脚本，未执行 SDK / Flutter / hdc / herdr / 设备命令，未commit，未 push。

用户目标：**请求失败时，在原 Pi 会话（原 pane）内重试**。下文按此目标核查四项：重复重试、旧错误尾部、done 判定、连接异常处理。

---

## 1. 运行现状（审查时实测）

| 项 | 实测 |
| --- | --- |
| 监控进程 | 存活，PID 4464，命令行 `python .trellis/.runtime/monitor_json_pi_requests.py` |
| 启动时刻 | 2026-10-25T21:02:45Z（本地 2026-10-26 05:02:45） |
| 窗口 | 600 秒 → 截止 2026-10-25T21:12:45Z |
| 日志 | `build/pi-final-review-request-monitor.jsonl`，573 字节，5 行 |
| 已写事件 | `started` + 4 条 `state`（p3/p4/p5/p6 全部 `working`，token 分别为 `[754,null]`/`[753,null]`/`[755,null]`/`[756,null]`） |
| 未写事件 | 无 `finished`、无 `retried`、无 `observation_error` |
| 四个目标文件 | `final-window-doc-review.md`、`final-readme-review.md`、`final-evidence-hash-review.md`、`final-monitor-review.md` **全部不存在** |

**判定**：当前窗口未到期，无 `finished` 属正常，不是崩溃。但由此已可确认：四个 pane 在首轮轮询全部为 `working`，此后 7 分钟内既无状态变化也无重试，说明**没有检测到任何失败**，同时也**没有任何一个 pane 结算**。

`done` 的路径拼接经实测正确：`ROOT/".trellis/.runtime"/filename` 解析为 `D:\MyNewProjects\qfli_json\.trellis\.runtime\<file>`，`is_file()` 对该目录下既有文件返回 `True`。故 done 的缺陷不在路径，在**新鲜度**与**前置条件**（见 §4）。

---

## 2. 结论摘要

| 编号 | 问题 | 严重度 |
| --- | --- | --- |
| R1 | 去重键含会变的 `token`，旧错误尾部可反复触发重试，且无重试上限 | 高 |
| R2 | `failure_tokens[pane]=key` 写在重试成功之前，重试本身失败会永久抑制该失败的重试 | 高 |
| R3 | 已 `done` 的 pane 首次轮询不会被计入 `observed_working`，永远无法结算 | 高 |
| R4 | done 只查文件是否存在，不查新鲜度，旧文件可冒充本轮产出 | 中 |
| R5 | 已完成的 pane 若尾部仍残留错误文本，会被再次唤醒重做 | 中 |
| R6 | `blocked` 与未知状态永不处理，只能等到超时 | 中 |
| C1 | `emit` 在异常分支内可再次抛错，且无外层兜底，日志不可写会直接终止监控 | 低 |
| C2 | 永久性错误（CLI 缺失、pane 不存在）与瞬断同样对待，每 15 秒重复报错 | 低 |
| C3 | `run()` 不保留 stdout，`stderr[-500:]` 为空时错误信息为空 | 低 |

---

## 3. 重复重试

### R1（高）去重键把易变字段也算进去了

```python
key=(token,hashlib.sha256(tail.encode()).hexdigest())
if failure_tokens.get(pane)==key:continue
```

`token` 是 `(state_change_seq, completion_seq)`。每次 agent 完成一轮对话，`completion_seq` 会递增。因此：

1. 本轮失败，`tail` 含 `Retry failed after`，token 为 `T1` → 记 `(T1, h)`，发出重试。
2. agent 进入 `working`，再回到 `idle`，`tail` 里**同一段错误文本仍在最近 30 行内**，但 token 变成 `T2`。
3. `(T2, h) != (T1, h)` → **再次重试**。

也就是说，只要错误文本还留在 30 行窗口内，去重就形同虚设，每轮对话触发一次重试。

**无重试上限**：`retries[pane]` 只累加，从不参与判定。唯一约束是外层 600 秒窗口与 15 秒轮询。若单轮往返约 15–30 秒，**单个 pane 在 10 分钟内可被重复唤醒约 20–40 次**。

**去重不跨进程**：`failure_tokens` 与 `states` 都是进程内内存。重启监控即重置，同一失败可再次重试。日志虽然是持久追加的，但没有被用作去重依据——这正是该脚本引入日志后仍缺少的一环。

### R2（高）先记已重试、后发请求，失败的重试被永久吞掉

```python
failure_tokens[pane]=key
result=run("agent","prompt",pane,"...")   # 若这里抛异常
retries[pane]+=1
```

赋值在调用**之前**。若 `agent prompt` 因连接异常返回非零（`run()` 抛 `RuntimeError`）：

- 异常被外层 `except Exception` 捕获，只写一条 `observation_error`；
- 但 `failure_tokens[pane]` 已经是该 `key`，下一轮同一 token、同一尾部 → `continue`，**该失败再也不会被重试**；
- 且 `retries[pane]+=1` 未执行，`finished` 里的计数**低估**了真实尝试次数。

对用户目标（在原会话内重试）而言，这是最直接的失效路径：**重试动作本身失败后，失败就不再被重试，且日志看不出发生过尝试**。

### R5（中）已完成的 pane 会被旧错误尾部唤醒

判定顺序是「先查失败再查 done」：

```python
failed=(...)
if failed: 重试; continue
if pane in observed_working and 文件存在: done
```

若某 pane 已经写完文件、状态为 `done`，但最近 30 行里仍留着上一轮的 `Retry failed after`，脚本会把它**当作未完成而再次重试**。重做可能导致文件内容重复追加或覆盖。

---

## 4. done 判定

### R3（高）首次轮询即 `done` 的 pane 永远无法结算

```python
if state=="working":observed_working.add(pane);continue
...
if pane in observed_working and (ROOT/".trellis/.runtime"/filename).is_file():
    done.add(pane)
```

`observed_working` 只在**本进程内**观察到 `working` 时才加入。若监控启动（或重启）时某 pane 已经是 `done`，它永远不会进入该集合，于是**即使文件已经写好，也永远不算完成**，只能落到 `remaining`。

这是**从源码即可证明**的缺陷，且有同族运行日志佐证：

```text
{"utc":"2026-10-25T19:22:35Z","event":"state","pane":"w29:p5","state":"done","token":[561,561]}
...
{"utc":"2026-10-25T19:32:36Z","event":"finished","settled":["w29:p3","w29:p4"],
 "retries":{...全 0...},"remaining":["w29:p5","w29:p6"]}
```

p5 首轮即 `done`，最终未进 `settled`。（该文件来自同族监控脚本，事件词汇完全一致；结论本身由源码独立成立。）

### R4（中）只查存在性，不查新鲜度

`is_file()` 无法区分「本轮产出」与「上一轮遗留」。当前四个目标文件恰好都不存在，所以本轮未误判；但一旦某文件在监控启动前就已存在（上一轮已写、或人工预置），`observed_working` + `is_file()` 就会**在没有任何新产出的情况下判 done**。

缺少的保护：启动时记录每个目标文件的 `mtime`/`sha256`，结算时要求**发生变化**。

### R6（中）`blocked` 与未知状态永不处理

- `blocked`：只写一条事件就 `continue`，既不解除阻塞、也不重试、也不结算。
- `state not in ("idle","done")`：静默跳过。除 `working`/`blocked`/`idle`/`done` 之外的状态（例如 `error`、`stopped`、`unknown`）**既不报错也不重试**，直接等到超时。

对用户目标而言，`blocked` 很可能正是「等待输入」的状态，而脚本对它没有任何动作。

---

## 5. 旧错误尾部（stale tail）

`agent read ... --source recent-unwrapped --lines 30` 取最近 30 行做子串匹配：

```python
failed=("Retry failed after" in tail or "Error: Connection error." in tail)
```

三个方向都没有护栏：

1. **误报（旧）**：错误文本在 30 行窗口内但属于上一轮 → 重复重试（R1/R5）。
2. **漏报（新）**：失败后 agent 又输出了超过 30 行，错误文本被挤出窗口 → **不重试**，直接等到超时。
3. **无归属**：脚本没有把错误文本与「本轮 prompt」绑定。没有「本次 prompt 之后新出现的错误」这种判定，因此无法区分旧错与新错。

这也是 R1 无法靠去重解决的根因：去重只能识别「完全相同的尾部」，识别不了「同一错误换了 token」。

---

## 6. 连接异常处理

### C1（低）`emit` 无兜底，日志不可写会终止监控

`emit()` 每次 `LOG.open("a")`。它被调用在 `except Exception` 分支内：

```python
except Exception as e:emit("observation_error",pane=pane,error=str(e))
```

若此时磁盘满、目录被删或权限变化，`emit` 自己抛出的异常会穿出 `for` 与 `while`，**整个监控直接退出**，`finished` 也不会写。脚本没有任何外层 `try`。

### C2（低）永久性错误与瞬断同样对待

`herdr` 缺失（`FileNotFoundError`）、pane 名不存在、CLI 返回非零，全部走同一条 `observation_error`，每 15 秒重复一次，没有退避、没有「连续 N 次失败即放弃并报告」的分级。对永久性错误，这会刷满日志且永不收敛。

### C3（低）错误信息可丢失

```python
if r.returncode:raise RuntimeError(r.stderr[-500:])
```

只取 `stderr` 尾部。若 stderr 为空（常见于某些 CLI 把错误写进 stdout），错误信息为空串，日志里只剩一个没有内容的 `observation_error`。

### 做得正确的部分

- `subprocess.run(...,timeout=15)` 会抛 `subprocess.TimeoutExpired`，被外层捕获 → `observation_error`，不会挂死。
- 单 pane 的 `try/except` 在 `for` 循环**内部**，一个 pane 出错不影响其他 pane 继续轮询。
- `run()` 失败不会静默返回空串，而是抛错，避免了把 CLI 失败误当成正常输出。

---

## 7. 与用户目标的偏差

目标：**在原 Pi 会话内重试**。脚本的重试文本：

```python
"已确认本轮请求失败。"+prompt+" 不执行SDK、Flutter、hdc或设备操作，不改他人文件，不commit。"
```

- 方向正确：`agent prompt <pane>` 确实作用于原 pane，不是新开会话。
- 约束正确：把用户的禁止项一并带进重试提示。
- **不足**：重试只是原样重发指令，不带「已完成部分请勿重复」「先检查目标文件现状」之类的前置约束。结合 R5（已完成仍被唤醒）与 R4（存在即算完成），可能产生重复写入。
- **不足**：重试次数与终止条件没有上报到最终结论。`finished` 只有 `retries` 计数，没有「某 pane 因重试耗尽而失败」的终态。

---

## 8. 建议修改清单（仅列方向，未改代码）

1. **R2 优先**：把 `failure_tokens[pane]=key` 移到 `run("agent","prompt",...)` **成功之后**；失败时不要记账，让下一轮可以再试。同时把 `retries[pane]+=1` 改为「尝试计数」，与「成功计数」分开。
2. **R1**：去重键去掉 `token`，只用「尾部内容 + 目标文件状态」或加入重试计数上限（例如每 pane 最多 3 次），并设全局上限。
3. **R3**：`observed_working` 不再作为 done 的必要条件；改为「状态为 `done`/`idle` 且目标文件在本次启动后发生变化」。或允许 `done` 状态直接结算。
4. **R4**：启动时记录每个目标文件的 `mtime`+`sha256`，结算时要求变化。
5. **R5**：判定失败时排除已 `done` 的 pane，或要求错误出现在本次 prompt 之后的增量输出中。
6. **R6**：`blocked` 与未知状态显式上报并在最终 `finished` 中列为原因；不要静默跳过。
7. **C1**：`emit` 外层加 `try`，日志失败时退化为 `print`，保证 `finished` 一定写出。
8. **C2**：区分永久性错误与瞬断，连续失败 N 次后放弃该 pane 并在 `finished` 中标注。

---

## 9. 本次审查未做的事

- 未修改 `monitor_json_pi_requests.py`，未修改任何仓库文件。
- 未执行 `herdr`、SDK、Flutter、hdc 或任何设备命令；未接触任何 Pi 会话。
- 未 commit，未 push。
- 只读操作：读取脚本、读取两份监控日志、`Get-CimInstance` 查询进程存活、`Test-Path`/`Get-FileHash` 查询文件、用 Python 验证一次路径拼接语义。
- 未对运行中的监控进程（PID 4464）做任何干预；其 `finished` 事件在 2026-10-25T21:12:45Z 之后才会出现，本次审查未等待该结果。