"""Build the offline JSON curriculum; no package or network access is needed.

The 100 inherited examples and lesson snippets are preserved byte for byte.
Their fake runtime output is replaced with the formatter's actual result and
prose exercise answers are represented as JSON objects without discarding text.
New records below are individually authored data models, not numbered variants.
Run from the product root: python tool/build_json_content.py [--check]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_CONTENT = ROOT.parent / "qflistudio-core" / "assets" / "content"
OUTPUT = ROOT / "assets" / "content"
UPDATED = "2026-10-22"

# Section headers name the category; records contain slug, title, explanation,
# and a JSON document separated by the first three vertical bars.
RECORDS = r'''
# foundations|基础类型与边界
root-string|根节点字符串|JSON 文档不必以对象开头。双引号中的文本也是完整根值；复制到工具页校验可以确认它的根类型为 string。|"离线编辑器"
root-number|根节点整数|单个数值可作为合法文档。42 是整数；把它加上引号就变成字符串，两个类型不能在业务规则中混为一谈。|42
root-false|根节点布尔值|false 是合法根值，并不表示解析失败。调用方必须用解析状态判断成功，不能用值的真假判断文档是否有效。|false
root-null|根节点空值|null 表示明确存在的空值。它与缺少文档不同，也与内容为四个字符的字符串 "null" 不同。|null
root-array|根节点数组|根数组适合没有额外分页元数据的同类数据集合。数组顺序属于数据的一部分，排序工具不应该擅自重排成员。|["draft","review","published"]
empty-containers|空容器与空字符串|空对象、空数组、空字符串和 null 分别表达四种状态。保留区别可以让表单知道尚未填写与已选择为空的差异。|{"preferences":{},"attachments":[],"nickname":"","avatar":null}
typed-lookalikes|看起来相同的不同类型|文本编号应保留前导零，计数才使用整数。布尔值不能写成大小写混用的 True，也不能用字符串代替。|{"postalCode":"00120","count":120,"enabled":true,"enabledLabel":"true"}
escaped-text|换行、制表符与引号|字符串里的换行使用转义序列，不能直接断行。反斜线和双引号也必须转义，格式化后仍应解码为同一段文本。|{"message":"第一行\n第二行\t\"完成\"","path":"notes\\draft.json"}
unicode-text|中文与表情字符|JSON 字符串直接保存 Unicode。中文、组合字符与表情不需要强制转成 ASCII 转义，显示长度也不等于 UTF-16 代码单元数。|{"中文键":"可离线阅读","emoji":"🧭","accent":"café","rtl":"مرحبا"}
number-models|数值与精确金额|近似测量可以用小数，金额则用整数最小单位和币种避免浮点累加误差。超出安全交换范围的标识符应保存为字符串。|{"temperatureC":23.5,"priceMinor":1299,"currency":"CNY","largeId":"9223372036854775807"}
# pointers|路径与树形结构
pointer-slash|带斜杠的键|JSON Pointer 用斜杠分段，因此键中的斜杠必须写成 ~1。这里 /a~1b 可以选择普通键 a/b，不能误当成两层对象。|{"a/b":{"label":"目录名不是路径"},"plain":7}
pointer-tilde|带波浪号的键|Pointer 的波浪号使用 ~0 转义。选择 ~draft 的路径是 /~0draft，转义顺序错误会使键名改变。|{"~draft":{"saved":true},"~1":"这是字面量键"}
pointer-empty-key|空字符串键|对象允许空字符串键。空 Pointer 表示整个文档，而单个斜杠表示选择空键，这两个路径有不同含义。|{"":{"value":"空键成员"},"name":"根对象"}
numeric-object-keys|数字对象键与数组下标|对象键 "0" 仍是字符串键；数组下标 0 才是位置。树导航必须先识别当前容器类型再解释路径段。|{"lookup":{"0":"zero","01":"leading"},"list":["first","second"]}
nested-array-path|多层数组定位|矩阵用连续的数组下标定位。/matrix/1/0 应得到 3，保留外层行和内层列可以避免将矩阵错误展平成普通列表。|{"matrix":[[1,2],[3,4]],"axisNames":["row","column"]}
mixed-tree|混合容器树|同一对象内可以组合对象、数组与标量。结构视图显示根、子节点与类型，编辑某个叶子不会影响相邻分支。|{"section":{"items":[{"id":"a","flags":[true,false]}]},"total":1}
tree-menu|菜单树|菜单的 children 递归保存同类节点，叶子可省略 children。父节点的 id 是业务标识，不应从显示标题推导。|{"menu":{"id":"file","label":"文件","children":[{"id":"open","label":"打开"},{"id":"recent","label":"最近","children":[]}]}}
adjacency-index|邻接表索引|图或组织结构也可以用节点字典和父子引用表示。引用保存稳定 id，避免相同子节点在多个位置复制后产生不同版本。|{"nodes":{"root":{"children":["a","b"]},"a":{"children":[]},"b":{"children":["a"]}},"start":"root"}
translation-pointer|多语言路径选择|翻译表先按语言再按消息键组织。含点的键仍是一个完整键，JSON Pointer 不会把点自动解释为嵌套访问。|{"zh-CN":{"editor.save":"保存"},"en":{"editor.save":"Save"}}
structure-summary|树节点的类型记录|结构统计需要区分容器和叶子。可以把节点的路径、类型及成员数保存为普通 JSON，供离线检查报告复用。|{"nodes":[{"pointer":"","type":"object","children":2},{"pointer":"/ready","type":"boolean","children":0},{"pointer":"/items","type":"array","children":0}]}
# configuration|离线应用配置
editor-preferences|编辑器偏好设置|缩进宽度是整数，自动保存是布尔值，字体回退是有序数组。分开保存这些类型使设置页能够选择正确的控件。|{"editor":{"indentSize":2,"insertSpaces":true,"wordWrap":"on","fontFamily":["monospace","sans-serif"]}}
workspace-folders|本地多目录工作区|工作区引用多个本地文件夹，并为每个目录保存独立显示名。相对路径让导出的工作区在不同设备沙盒中仍可重定位。|{"folders":[{"name":"应用","path":"./app"},{"name":"资料","path":"./docs"}],"settings":{"restoreExpandedFolders":true}}
feature-flags|离线能力开关|能力开关记录当前设备已启用的功能。显式关闭云同步可供界面判断入口，不能把开关当作联网权限本身。|{"features":{"jsonTools":true,"localTerminal":true,"cloudSync":false},"configurationVersion":2}
keybindings|快捷键绑定|快捷键数组按命令描述操作，条件表达式作为文本保存。使用稳定命令 id 可以在界面语言变化后继续保持绑定。|{"bindings":[{"key":"Ctrl+S","command":"document.save","when":"editorFocused"},{"key":"Ctrl+Shift+F","command":"json.format","when":"jsonDocument"}]}
theme-palette|主题调色板|颜色值是字符串，透明度单独用 0 到 1 的数值。主题配置描述样式，不执行任何代码，适合随离线包共享。|{"name":"Paper","colors":{"background":"#FAFAF8","foreground":"#242424","error":"#B3261E"},"selectionOpacity":0.24}
session-restore|会话恢复数据|恢复记录同时保存打开文件、活动文件和光标位置。路径相对于项目根目录，避免将另一台设备的绝对沙盒路径写入共享资料。|{"openFiles":["src/data.json","README.md"],"activeFile":"src/data.json","cursors":{"src/data.json":{"line":8,"column":3}}}
explorer-state|文件树展开状态|展开目录列表仅保存目录，不保存临时选中状态。版本字段让将来的迁移逻辑能识别旧格式，项目 id 防止不同项目互相覆盖。|{"version":1,"projectId":"local-notes","expandedDirectories":["assets","assets/content","src"],"showHiddenFiles":false}
export-preset|本地导出预设|导出规则用包含和排除两个数组表达，避免用户把生成目录带进备份。配置只描述本地文件操作，无需远程地址。|{"format":"zip","include":["src/**","assets/**"],"exclude":["build/**",".cache/**"],"preserveTimestamps":false}
retention-policy|本地备份保留策略|保留数量与大小限制使用明确单位。达到任一限制时由应用清理最旧备份，配置本身不会删除文件。|{"backup":{"maxCopies":12,"maxTotalBytes":52428800,"minimumIntervalSeconds":300,"directory":".qfli/backups"}}
settings-overrides|配置继承与覆盖|默认值和项目覆盖分开放置，能清楚看到用户实际改了哪些字段。空覆盖对象表示完整采用默认值。|{"defaults":{"indent":2,"newline":"lf"},"projectOverrides":{"indent":4},"fileOverrides":{"data.json":{"indent":2}}}
# records|人物与业务记录
contact-card|通讯录名片|姓名、联系方式与地址有不同结构；电话号码含加号且可能有前导零，应使用字符串。多个邮箱按用途标记而不是拼成一段。|{"name":{"given":"Lin","family":"Chen"},"phones":[{"label":"mobile","value":"+86 13800000000"}],"emails":[{"label":"work","value":"lin@example.invalid"}]}
postal-address|结构化邮寄地址|地址按国家、地区、城市和多行街道拆分，邮编作为字符串。无需为不适用的地区强行填入一个假省份。|{"countryCode":"CN","region":"浙江","city":"杭州","streetLines":["示例路 18 号","3 楼"],"postalCode":"310000"}
user-profile|用户资料与可选字段|公开显示资料与可选生日分开，null 明确表示未提供。不要从年龄反推生日，也不要把未知值写成空日期。|{"id":"u_204","displayName":"小舟","birthday":null,"visibility":{"email":"private","displayName":"public"}}
membership|会员有效期|会员状态、有效区间和权益列表一起表达授权。区间结束时间与当前状态并非同一信息，离线场景仍应保留原始时间。|{"memberId":"m17","tier":"reader","validity":{"from":"2026-01-01","until":"2026-12-31"},"benefits":["offline-library","annotations"]}
consent-record|本地同意记录|协议记录保存版本、时间和明确选择，便于升级协议后判断是否需要重新展示。记录选择不应写入不必要的身份信息。|{"agreementVersion":"3.1","choices":{"essentialStorage":true,"optionalAnalytics":false},"recordedAt":"2026-10-22T08:30:00+08:00"}
emergency-contact|紧急联系人|关系与优先级分别保存，联系人同意状态可为待确认。电话号码继续使用文本，备注说明可联系时段。|{"personId":"p9","emergencyContacts":[{"name":"周先生","relationship":"family","priority":1,"phone":"+86 13900000000","consent":"pending"}],"notes":"白天联系"}
preference-survey|偏好问卷答案|多选答案用数组，单选用字符串，开放题用文本。未作答和用户主动选择空列表需要在业务规则中区别对待。|{"surveyId":"reading-habits","answers":{"formats":["ebook","paper"],"frequency":"weekly","comment":"偏爱历史"},"unanswered":["ageGroup"]}
organization-unit|组织部门记录|部门通过 parentId 建立层级，根部门使用 null。负责人可以独立引用人员 id，避免把完整人员信息重复嵌入每个部门。|{"unitId":"design","name":"设计组","parentId":"product","managerId":"u_204","costCenter":"CC-008"}
availability-calendar|可联系时段|每周时段需要时区和星期编号约定。起止时间使用本地钟表字符串，跨天时段应拆分或用明确日期表示。|{"timeZone":"Asia/Shanghai","weekStartsOn":1,"weekly":[{"weekday":2,"from":"09:00","to":"11:30"},{"weekday":4,"from":"14:00","to":"17:00"}]}
record-provenance|记录来源与修订|来源、修订号和校对人帮助追踪资料变更。内容哈希是完整性线索，不等于数字签名，也不证明来源可信。|{"record":{"title":"历史资料卡"},"provenance":{"sourceFile":"archive/card-17.txt","revision":4,"reviewedBy":"editor-2","digestAlgorithm":"sha256"}}
# commerce|订单与库存
catalog-product|商品规格表|商品的展示名、SKU 和可选规格各司其职。库存跟踪使用 SKU，不能依赖会被修改的商品名称。|{"productId":"p-tea","name":"乌龙茶","variants":[{"sku":"TEA-100","grams":100,"priceMinor":3800},{"sku":"TEA-250","grams":250,"priceMinor":8800}],"currency":"CNY"}
cart-lines|购物车行项目|每行保留单价快照和数量，便于解释小计。数量与金额都是整数，不能让字符串数字绕过业务校验。|{"cartId":"cart-local","lines":[{"sku":"PEN-BLUE","quantity":3,"unitPriceMinor":250}],"subtotalMinor":750,"currency":"CNY"}
purchase-order|采购单审批|采购单将申请人、供应商和审批状态关联起来。审批历史是有序记录，当前状态只是其中最新的可视摘要。|{"poNumber":"PO-2026-18","requesterId":"u12","supplierId":"s3","approval":{"state":"approved","steps":[{"role":"manager","result":"accepted"}]}}
stock-ledger|库存流水|库存变化使用带符号的数量和原因，期末数量可以据此重算。流水比直接覆盖库存更容易发现漏记或重复记账。|{"sku":"BAG-01","openingQuantity":20,"movements":[{"reason":"receipt","delta":8},{"reason":"sale","delta":-3}],"closingQuantity":25}
warehouse-bins|仓库货位|货位由区域、通道和层位描述，容量与占用量可进行本地校验。一个 SKU 可以分散在多个货位，不能只保存一个位置文本。|{"warehouse":"W1","bins":[{"code":"A-02-03","capacity":40,"contents":[{"sku":"BOLT-M6","quantity":18}]}]}
invoice-tax|发票税额明细|含税金额、未税金额和税额分别以最小货币单位保存。税率使用整数基点表示，避免用二进制小数计算财务结果。|{"invoiceNo":"INV-2026-08","currency":"CNY","netMinor":10000,"tax":{"rateBasisPoints":600,"amountMinor":600},"grossMinor":10600}
refund-request|退款分摊|部分退款需要指向具体订单行，并区分商品退款与运费退款。原因码供统计，补充说明保留给人工审核。|{"orderId":"o48","refund":{"lines":[{"lineId":"l2","quantity":1,"amountMinor":1200}],"shippingMinor":0,"reason":"damaged","note":"包装破损"}}
shipment-package|包裹重量与尺寸|重量和尺寸都带明确单位，不能混用克与千克。物流追踪号作为文本保留前导零，运输事件按发生顺序记录。|{"trackingNumber":"0000182037","weight":{"value":750,"unit":"g"},"size":{"length":20,"width":15,"height":8,"unit":"cm"},"events":[{"status":"packed","at":"2026-10-21T15:00:00Z"}]}
coupon-eligibility|优惠条件组合|最低消费、适用分类和不能叠加的优惠明确分开。null 上限表示无上限，不能误写成 0 导致优惠额度被限制为零。|{"coupon":"BOOK10","conditions":{"minimumSpendMinor":5000,"categories":["books"],"exclusiveWith":["CLEARANCE"]},"discount":{"percent":10,"maximumMinor":null}}
reorder-plan|补货计划|补货点、目标库存与交货周期分别表达触发和数量。预计到货日是规划数据，不会由 JSON 本身自动执行采购。|{"sku":"FILTER-A","reorderPoint":6,"targetStock":24,"leadTimeDays":5,"supplier":{"id":"s9","minimumOrderQuantity":12}}
# money|记账与预算
expense-entry|费用报销记录|一笔报销包含付款金额、用途和本地附件路径。附件路径相对项目存储，备注不能替代实际凭证是否存在的检查。|{"expenseId":"e31","amountMinor":8600,"currency":"CNY","category":"transport","occurredOn":"2026-10-20","receipt":"receipts/e31.png"}
split-bill|多人费用分摊|分摊使用整数分避免尾数丢失。每人分配额之和应等于总额，不能通过每项四舍五入后默认它们恰好一致。|{"totalMinor":10000,"shares":[{"person":"A","amountMinor":3334},{"person":"B","amountMinor":3333},{"person":"C","amountMinor":3333}],"currency":"CNY"}
double-entry|复式记账分录|借方和贷方采用相同整数单位，合计需要平衡。账户代码作为字符串以保留会计编码中的前导零。|{"journalId":"J101","currency":"CNY","postings":[{"account":"1001","debitMinor":5000,"creditMinor":0},{"account":"6001","debitMinor":0,"creditMinor":5000}]}
monthly-budget|月度预算与结转|预算按分类保存计划和实际，结转规则独立描述。预算可以超支，负的剩余额不应被自动截断而掩盖问题。|{"period":"2026-10","categories":{"food":{"plannedMinor":120000,"actualMinor":98000},"books":{"plannedMinor":20000,"actualMinor":24000}},"carryOverUnused":true}
savings-goal|储蓄目标进度|目标额和已存额保存为整数，百分比可以在界面计算。完成日期允许为空，表示尚未设置时间限制。|{"goal":"应急资金","targetMinor":3000000,"savedMinor":1250000,"currency":"CNY","deadline":null,"contributions":[{"date":"2026-10-01","amountMinor":50000}]}
recurring-charge|周期费用定义|周期规则与实际扣款分开，防止配置被误认为已付款记录。每月指定日遇到短月份需要明确处理策略。|{"name":"资料订阅","amountMinor":1800,"schedule":{"frequency":"monthly","dayOfMonth":31,"shortMonth":"last-day"},"nextDue":"2026-10-31"}
currency-quote|离线汇率快照|汇率记录来源时间和基准货币，只是离线快照。不能把它称为实时价格，也不要把一个数值的方向反过来使用。|{"base":"CNY","quotes":{"USD":{"numerator":14,"denominator":100},"EUR":{"numerator":13,"denominator":100}},"asOf":"2026-10-01","kind":"illustrative-snapshot"}
loan-schedule|借款还款计划|本金与利息分开使每期总额可核算。这里是演示计划数据，不包含利率推算，也不代表真实金融建议。|{"loanId":"demo-loan","currency":"CNY","installments":[{"due":"2026-11-01","principalMinor":100000,"interestMinor":3000},{"due":"2026-12-01","principalMinor":100000,"interestMinor":2500}]}
reconciliation|账目对账结果|对账将匹配、缺失和差异分别列出，方便人工处理。差异列表应保留双方原值，而不是直接覆盖其中一个来源。|{"statementId":"oct-demo","matchedIds":["t1","t2"],"missingFromLedger":["t3"],"differences":[{"transactionId":"t4","statementMinor":900,"ledgerMinor":800}]}
cash-envelope|现金信封分配|收入按信封分配，用未分配余额反映尚未安排的钱。转移记录是独立事件，避免只看到最终余额而无法解释变化。|{"incomeMinor":500000,"envelopes":{"rent":200000,"food":100000,"travel":50000},"unallocatedMinor":150000,"transfers":[{"from":"travel","to":"food","amountMinor":10000}]}
# schedule|时间与任务
todo-item|任务清单项|状态、截止日期和检查项分别保存。已完成检查项不一定意味着整个任务完成，应用应按自己的规则决定任务状态。|{"id":"t17","title":"整理离线资料","status":"doing","dueDate":"2026-10-25","checklist":[{"text":"校验 JSON","done":true},{"text":"备份项目","done":false}]}
task-dependencies|任务依赖图|前置任务通过 id 引用，依赖数组为空表示可以立即开始。应用还需要检查循环依赖；JSON 语法正确不代表计划逻辑可执行。|{"tasks":[{"id":"draft","dependsOn":[]},{"id":"review","dependsOn":["draft"]},{"id":"publish","dependsOn":["review"]}]}
calendar-event|带时区日程|事件同时保存 UTC 时间和显示时区。绝对时刻适合跨时区同步，全天事件则应单独使用日期表示。|{"title":"文档评审","start":"2026-10-23T01:00:00Z","end":"2026-10-23T02:00:00Z","displayTimeZone":"Asia/Shanghai","allDay":false}
all-day-event|全天事件|全天事件的日期区间不应硬塞进午夜时间戳。结束日期采用不包含边界的规则，可以明确表示一个或多个完整日。|{"title":"资料归档日","dateRange":{"start":"2026-10-24","endExclusive":"2026-10-25"},"allDay":true,"calendar":"personal"}
recurrence-exceptions|重复计划与例外|周期规则不能只保存自然语言。周几重复、何时结束和哪些日期跳过都应显式表示，例外日期按本地日历理解。|{"repeat":{"frequency":"weekly","weekdays":[1,3,5],"until":"2026-12-31"},"excludeDates":["2026-11-02"],"localTime":"08:30","timeZone":"Asia/Shanghai"}
time-tracking|工时片段|每段工时记录起止时间与任务关联，暂停区间单独保存。计算总时长时需要减去暂停，并检查区间是否重叠。|{"taskId":"t17","startedAt":"2026-10-22T09:00:00+08:00","endedAt":"2026-10-22T11:00:00+08:00","breaks":[{"from":"10:00","to":"10:15"}]}
pomodoro-state|专注计时状态|计时状态保存剩余秒数和当前阶段，避免恢复应用后从头开始。已完成次数是统计字段，不能代替正在进行的阶段信息。|{"phase":"focus","remainingSeconds":1020,"durations":{"focus":1500,"shortBreak":300,"longBreak":900},"completedSessions":3,"running":false}
meeting-minutes|会议纪要行动项|参会者、决议和行动项分组使纪要便于检索。行动项拥有负责人和截止日期，减少自然语言任务无法分派的问题。|{"meetingId":"m04","attendees":["u1","u2"],"decisions":["保留本地导出"],"actions":[{"text":"整理样例","owner":"u2","due":"2026-10-26"}]}
reminder-policy|本地提醒规则|提醒偏移量用分钟表示，负值代表提前。免打扰时段是本地钟表范围，应用需要在触发时结合设备时区判断。|{"offsetMinutes":[-30,-5,0],"quietHours":{"from":"22:00","until":"07:00"},"delivery":"local-notification","repeatIfMissed":false}
milestone-plan|里程碑验收|里程碑以可观察的验收项定义完成，而不只是写一个日期。证据路径是本地文档，状态记录尚未通过的检查。|{"milestone":"离线版本候选","targetDate":"2026-10-30","acceptance":[{"check":"全部示例合法","state":"passed","evidence":"reports/catalog.json"},{"check":"设备运行","state":"pending","evidence":null}]}
# documents|文档与知识库
document-metadata|文档元数据|标题、作者、标签和正文文件路径拆开，适合离线索引。创建时间与修改时间分开保存，不能在每次读取时重写创建时间。|{"id":"doc7","title":"JSON 使用手册","authors":["编辑组"],"tags":["json","offline"],"bodyFile":"notes/json.md","createdAt":"2026-09-01T10:00:00Z","modifiedAt":"2026-10-20T08:00:00Z"}
table-of-contents|章节目录|章节目录记录稳定锚点和子章节，顺序表示阅读顺序。标题修改后锚点可以保持不变，避免书签全部失效。|{"chapters":[{"anchor":"intro","title":"开始","children":[{"anchor":"first-file","title":"第一个文件","children":[]}]},{"anchor":"tools","title":"工具","children":[]}]}
note-links|双向笔记引用|引用边使用来源、目标与关系类型，索引器可据此计算反向链接。笔记正文不必嵌入全部目标内容。|{"notes":{"n1":{"file":"intro.md"},"n2":{"file":"pointer.md"}},"links":[{"from":"n1","to":"n2","relation":"explains"}]}
bibliography|参考资料条目|参考条目保留作者数组、出版年份和本地副本路径。原始地址仅为文献标识，示例不会自动访问它。|{"key":"json-note","title":"数据交换格式笔记","authors":[{"family":"Chen","given":"Lin"}],"year":2025,"localCopy":"references/note.pdf","identifier":"local:note-2025"}
annotation-range|文本批注范围|批注范围需要说明偏移量单位，避免中文和表情导致错位。引用原文帮助恢复位置，但不应该替代精确范围。|{"documentId":"doc7","range":{"start":18,"end":26,"unit":"utf16-code-unit"},"quote":"结构化数据","comment":"补充数组示例","resolved":false}
reading-progress|阅读进度书签|阅读位置用章节锚点和页内百分比表示，比屏幕像素更适应字体变化。历史书签仍保存原始标题便于用户识别。|{"documentId":"guide","position":{"anchor":"pointer","fraction":0.35},"bookmarks":[{"anchor":"format","label":"格式化快捷键"}],"finished":false}
revision-diff|文档修订摘要|修订摘要记录变更类别和路径，而不是只保存最后一次文本。旧版本 id 使审阅者能够定位比较基准。|{"baseRevision":"r3","revision":"r4","changes":[{"kind":"insert","path":"/chapters/2","summary":"新增路径章节"},{"kind":"edit","path":"/title","summary":"明确离线范围"}]}
glossary|术语表|一个术语可以有多个别名和一个明确解释。相关术语使用 id 关联，避免把它们嵌入成无限递归的对象。|{"terms":[{"id":"pointer","term":"JSON Pointer","aliases":["JSON 路径指针"],"definition":"用斜杠路径定位 JSON 值","related":["patch"]}]}
local-search-index|本地搜索索引|倒排索引将词映射到文档 id 和位置数组。索引可以重建，因此版本和源文件摘要比人工编辑索引内容更重要。|{"indexVersion":1,"documents":{"d1":"notes/a.md","d2":"notes/b.md"},"terms":{"json":[{"doc":"d1","positions":[0,12]},{"doc":"d2","positions":[3]}]}}
archive-manifest|文档归档清单|归档清单记录相对路径、字节数与摘要算法。读取清单不会证明文件存在，导入工具仍要逐一验证实际条目。|{"archiveVersion":1,"entries":[{"path":"guide.md","bytes":1280,"digest":{"algorithm":"sha256","hex":"0123456789abcdef"}}],"createdBy":"offline-export"}
# education|学习与练习
course-outline|课程大纲|课程按模块组织目标与课时，前置知识是显式列表。把完成标准写成具体能力，能帮助判断学完后是否掌握。|{"course":"JSON 基础","prerequisites":["文本编辑"],"modules":[{"id":"types","minutes":20,"outcomes":["区分六种 JSON 值"]},{"id":"paths","minutes":25,"outcomes":["定位嵌套成员"]}]}
quiz-choice|单选题配置|题目选项有稳定 id，正确答案引用 id，避免调换显示顺序后答案发生变化。解析解释用于学习反馈而不是程序执行。|{"question":"哪个是合法布尔值？","options":[{"id":"a","text":"true"},{"id":"b","text":"True"},{"id":"c","text":"yes"}],"correctOptionId":"a","explanation":"JSON 关键字必须小写。"}
quiz-multiple|多选题评分|多选题保存答案集合和评分规则。数组顺序不代表答案优先级，评分时应按集合比较并明确是否允许部分得分。|{"questionId":"q-types","correctOptionIds":["object","array","null"],"scoring":{"mode":"exact-set","maximumPoints":3,"allowPartial":false}}
flashcard|间隔复习卡|卡片将正面问题、背面答案和复习调度分开，适合离线存储。复习时间是计划，学习记录还应保存实际作答结果。|{"cardId":"json-pointer-escape","front":"斜杠在 Pointer 中如何转义？","back":"~1","review":{"intervalDays":7,"dueOn":"2026-10-29","ease":2.5}}
rubric|项目评分量表|量表条目给出分值和可观察证据，避免只写优秀或一般。所有权重合计应由业务校验检查，JSON 解析不会替你相加。|{"rubric":"数据建模作业","criteria":[{"id":"types","points":40,"evidence":"字段类型准确"},{"id":"units","points":30,"evidence":"计量单位明确"},{"id":"validation","points":30,"evidence":"校验结果无错误"}]}
learning-attempt|练习尝试记录|每次尝试保留提交答案和反馈，不覆盖早先失败记录。耗时使用毫秒，字段名避免让读取方误以为是秒。|{"exerciseId":"pointer-1","attempts":[{"answer":"/items/0","correct":false,"elapsedMilliseconds":18000},{"answer":"/items/0/name","correct":true,"elapsedMilliseconds":9000}]}
lesson-progress|课程完成度|进度表通过课时 id 保存状态，当前章节可以独立定位。百分比应由已完成课时计算，避免两个字段长期不一致。|{"courseId":"json-basics","lessons":{"types":"completed","arrays":"completed","pointer":"in-progress","patch":"not-started"},"currentLesson":"pointer"}
lab-fixtures|实验输入输出夹具|夹具文件名映射到文本内容，方便本地自动测试创建临时项目。嵌套 JSON 文本需要字符串转义，不能把它当作已解析对象混用。|{"labId":"format-01","files":{"data.json":"{\"ok\":true}"},"expected":{"exitCode":0,"formatted":"{\n  \"ok\": true\n}"}}
classroom-roster|小组课程名单|分组名单只保存教学所需的匿名 id 和角色。个人联系方式与成绩不应未经需要直接复制到共享练习文件。|{"classId":"offline-json","groups":[{"id":"g1","members":[{"learnerId":"l01","role":"editor"},{"learnerId":"l02","role":"reviewer"}]}]}
skill-matrix|能力掌握矩阵|每项技能用等级和证据表达，不用一个总分掩盖薄弱点。未知状态单独保留，不能直接当成零分或已掌握。|{"learnerId":"local","skills":{"parse":{"level":"independent","evidence":"lab-01"},"pointer":{"level":"with-help","evidence":"lab-05"},"schema":{"level":"unknown","evidence":null}}}
# diagnostics|日志与诊断
structured-log|结构化日志事件|日志的时间、级别与上下文分开，便于按条件过滤。消息只是面向人的说明，程序筛选应使用稳定事件码。|{"timestamp":"2026-10-22T01:15:30Z","level":"info","event":"json.format.completed","message":"格式化完成","context":{"file":"data.json","durationMilliseconds":4}}
parse-diagnostic|语法错误位置|诊断记录一基行列与零基偏移，两个坐标必须声明约定。错误范围让编辑器能够画波浪线并在问题列表中跳转。|{"severity":"error","code":"json.syntax","message":"缺少冒号","location":{"offset":8,"line":1,"column":9,"length":1},"coordinateSystem":{"lineBase":1,"offsetUnit":"utf16"}}
validation-report|批量校验报告|批量报告保留每个文件的实际结果，而不只是一个成功总数。总数需要从明细计算，防止遗漏失败文件仍显示通过。|{"checkedFiles":3,"results":[{"file":"a.json","valid":true},{"file":"b.json","valid":false,"errors":[{"line":2,"column":4}]},{"file":"c.json","valid":true}]}
operation-timing|离线操作耗时|耗时事件采用单调时钟测量的持续时间，墙上时间用于展示。解析和格式化拆分计时有助于识别性能瓶颈。|{"operation":"json-inspect","documentBytes":4096,"timingsMicroseconds":{"parse":230,"tree":180,"format":120},"clock":"monotonic"}
crash-summary|本地崩溃摘要|崩溃摘要保存组件、异常类型和本地日志路径，避免把完整敏感文档嵌进日志。记录只是静态示例，不会上传数据。|{"applicationVersion":"1.0.0","component":"document-editor","exception":{"type":"FormatException","message":"Unexpected token"},"logFile":"logs/crash-01.txt","uploaded":false}
problem-groups|问题按文件分组|问题面板可以用文件路径分组并保留各诊断严重性。警告与错误分开统计，用户才能判断哪些问题会阻止校验通过。|{"files":{"src/data.json":[{"severity":"error","message":"尾随逗号","line":4}],"assets/index.json":[{"severity":"warning","message":"未使用条目","line":1}]}}
output-record|工具输出记录|输出记录保留操作名、退出状态和实际文本。JSON 格式化不是执行程序，因此状态描述应明确叫校验或格式化。|{"operation":"validate-json","exitCode":0,"stdout":"JSON 有效：object，3 个成员","stderr":"","sourceFile":"data.json"}
audit-trail|本地修改审计|审计事件用前后修订号和操作类型说明变化，避免记录全部敏感正文。操作者可以是本地匿名标识而非真实姓名。|{"events":[{"sequence":1,"actor":"local-user","action":"document.format","document":"data.json","beforeRevision":3,"afterRevision":4}]}
health-checks|离线能力自检|自检逐项报告本地读写、解析和资产加载状态。缺少设备检查应明确 pending，不能把桌面测试当成设备通过。|{"checks":{"assetLoad":"passed","jsonParser":"passed","sandboxWrite":"passed","ohosDeviceExecution":"pending"},"environment":"desktop-test"}
test-evidence|测试证据清单|测试证据区分命令、结果与执行环境。没有实际执行的项目记录为 not-run，便于审阅者识别尚未完成的验证。|{"suite":"offline-json-catalog","commands":[{"command":"flutter test test/json_content_test.dart","environment":"host","status":"passed"},{"command":"device catalog smoke","environment":"ohos","status":"not-run"}]}
# storage|文件与数据存储
file-inventory|本地文件清单|文件清单用相对路径保存文件大小与类型。文件扩展名只是提示，导入后仍需检查真实内容是否符合预期格式。|{"root":"project","files":[{"path":"data.json","bytes":128,"mediaType":"application/json"},{"path":"notes/readme.md","bytes":640,"mediaType":"text/markdown"}]}
backup-manifest|备份版本清单|备份记录源版本、文件摘要和创建时间，恢复前可核对完整性。摘要长度示例并非真实文件计算结果，应按实际文件重算。|{"backupId":"b20261022","sourceRevision":12,"createdAt":"2026-10-22T08:00:00Z","files":[{"path":"src/data.json","sha256":"demo-digest","bytes":88}]}
migration-plan|数据格式迁移|迁移步骤列出源版本和目标版本，便于拒绝不支持的跳跃升级。步骤名称是已实现处理器的 id，不是任意可执行代码。|{"fromVersion":1,"toVersion":3,"steps":[{"id":"rename-display-name","targetVersion":2},{"id":"split-address","targetVersion":3}],"createBackup":true}
local-cache|本地缓存条目|缓存保存内容、写入时间和有效期，过期后可以重建。离线应用的缓存来源可以是本地文件，而无需外部服务。|{"key":"preview:data.json","source":{"path":"data.json","modifiedRevision":8},"cachedAt":"2026-10-22T08:00:00Z","ttlSeconds":600,"value":{"rootType":"object"}}
import-conflicts|导入冲突策略|冲突清单让用户对每个文件选择跳过、替换或另存。所有决定写入计划后再执行，减少半途覆盖导致的数据不一致。|{"importId":"i3","conflicts":[{"path":"data.json","resolution":"rename","newPath":"data-imported.json"},{"path":"notes.md","resolution":"keep-existing"}]}
atomic-save|原子保存状态|安全保存先写临时文件再替换目标，状态记录可以帮助恢复中断操作。这个 JSON 是演示过程，不会自动操作磁盘。|{"target":"data.json","temporary":".data.json.tmp","stage":"temporary-written","checks":{"flushCompleted":true,"validated":true},"nextAction":"replace-target"}
trash-record|回收站记录|删除记录保留原始相对路径和回收位置，使用户能够恢复。永久清理时间单独保存，避免把移入回收站误认为已经彻底删除。|{"itemId":"trash-7","originalPath":"drafts/old.json","storedPath":".trash/7.json","deletedAt":"2026-10-20T12:00:00Z","purgeAfter":"2026-11-20T12:00:00Z"}
file-associations|文件关联规则|文件名模式与语言类型的映射帮助编辑器选择高亮。规则优先级显式排序，避免同一文件匹配多条规则时行为随机。|{"associations":[{"pattern":"*.json","language":"json","priority":10},{"pattern":"*.schema.json","language":"json-schema","priority":20}],"fallbackLanguage":"plain-text"}
document-lock|本地编辑锁|编辑锁用于协调多个本地窗口，记录持有者和令牌。过期时间只用于恢复策略，不应单凭客户端时间就覆盖仍活跃的编辑会话。|{"document":"data.json","ownerWindow":"window-2","token":"local-lock-19","acquiredAt":"2026-10-22T08:00:00Z","leaseSeconds":60}
index-checkpoint|索引构建检查点|长任务检查点保存已经处理的位置，便于中断后继续。源文件列表修订变化时应重新开始，不能盲目沿用旧偏移。|{"job":"local-index","sourceRevision":6,"processedFiles":18,"totalFiles":40,"lastCompleted":"notes/intro.md","state":"paused"}
# patches|补丁与合并
merge-delete|合并补丁删除字段|合并补丁里对象成员值为 null 表示删除该成员。若业务需要把字段设为真正 null，应使用普通编辑或 JSON Patch。|{"target":{"title":"草稿","obsolete":true},"patch":{"title":"定稿","obsolete":null},"expected":{"title":"定稿"}}
merge-array-replace|合并补丁替换数组|RFC 7396 合并补丁对数组整体替换，不逐项合并。示例用两个成员变为一个成员，避免误以为剩余项目会自动保留。|{"target":{"tags":["draft","internal"]},"patch":{"tags":["public"]},"expected":{"tags":["public"]}}
merge-nested|嵌套合并补丁|嵌套对象逐层合并，未出现在补丁中的成员保留。深层字段变化不应丢弃同级的其他设置。|{"target":{"editor":{"indent":2,"wrap":true},"theme":"light"},"patch":{"editor":{"indent":4}},"expected":{"editor":{"indent":4,"wrap":true},"theme":"light"}}
patch-add-member|添加对象成员|JSON Patch 的 add 使用 Pointer 路径。目标父对象必须已存在，操作不会自动创建缺失的整条路径。|{"document":{"name":"note"},"operations":[{"op":"add","path":"/archived","value":false}],"expected":{"name":"note","archived":false}}
patch-append-array|向数组末尾追加|数组追加用路径结尾的 -，它是 add 操作的特殊位置。普通读取路径不能用 - 代表最后一个元素。|{"document":{"items":["a","b"]},"operations":[{"op":"add","path":"/items/-","value":"c"}],"expected":{"items":["a","b","c"]}}
patch-replace|替换现有字段|replace 只用于已经存在的路径，缺少目标时应该报错。相比 add，它适合表达调用方确信旧字段存在的约束。|{"document":{"status":"draft","revision":1},"operations":[{"op":"replace","path":"/status","value":"review"}],"expected":{"status":"review","revision":1}}
patch-remove|移除数组成员|移除数组成员后后续元素下标会变化。批量删除多个下标时必须考虑操作顺序，不能假定下标永久指向同一项。|{"document":{"items":["a","b","c"]},"operations":[{"op":"remove","path":"/items/1"}],"expected":{"items":["a","c"]}}
patch-copy|复制现有值|copy 从现有路径读取值并写入新路径。复制后两处分支应独立，后续修改副本不能反过来改变原始对象。|{"document":{"template":{"enabled":true}},"operations":[{"op":"copy","from":"/template","path":"/instance"}],"expected":{"template":{"enabled":true},"instance":{"enabled":true}}}
patch-move|移动对象成员|move 同时完成读取、删除与添加，可用于字段重命名。源路径和目标路径都按 Pointer 转义，不能把自然语言点路径混入。|{"document":{"oldName":"笔记","count":2},"operations":[{"op":"move","from":"/oldName","path":"/name"}],"expected":{"count":2,"name":"笔记"}}
patch-test|补丁前置条件|test 用于检查当前值是否符合预期，再决定能否执行后续操作。失败时整个文档应保持原样，以免产生部分更新。|{"document":{"version":3,"published":false},"operations":[{"op":"test","path":"/version","value":3},{"op":"replace","path":"/published","value":true}],"expected":{"version":3,"published":true}}
# forms|表单与输入建模
text-field|文本输入字段|字段配置把初始值、必填规则和长度限制分开，便于界面显示与校验复用。提示文本不能代替可访问名称。|{"fieldId":"displayName","widget":"text","label":"显示名称","defaultValue":"","validation":{"required":true,"minimumLength":2,"maximumLength":40}}
number-field|有单位的数字输入|输入框的最小值、最大值和步长是数值约束，单位独立展示。保存的数据应是数值而不是带 cm 的拼接字符串。|{"fieldId":"height","widget":"number","unit":"cm","constraints":{"minimum":1,"maximum":300,"step":0.5},"value":172.5}
choice-field|下拉选项与保存值|选项的 value 是稳定数据，label 是可翻译显示名。变更显示语言时，已保存的 value 无需跟着修改。|{"fieldId":"paperSize","widget":"select","options":[{"value":"a4","label":"A4 纸"},{"value":"letter","label":"Letter 纸"}],"selected":"a4"}
conditional-field|条件显示表单|条件使用结构化字段、运算符和值表达，不把任意脚本塞进配置。隐藏字段是否清空必须显式声明。|{"fieldId":"companyName","visibleWhen":{"field":"accountType","operator":"equals","value":"business"},"clearWhenHidden":true,"value":null}
repeated-group|可重复表单组|收货人可以有多个地址，因此重复组保存为数组。每个组有自己的稳定 id，删除中间一项不会改变其他项的身份。|{"groupId":"addresses","minimumItems":1,"items":[{"id":"addr-home","label":"家","city":"杭州"},{"id":"addr-work","label":"工作","city":"苏州"}]}
validation-messages|字段校验反馈|字段错误按路径组织，可与编辑器问题列表共用定位方式。一个字段可以同时违反多个业务规则，应保留完整消息数组。|{"valid":false,"fieldErrors":{"/email":[{"code":"required","message":"请输入邮箱"}],"/age":[{"code":"range","message":"范围为 0 到 150"}]}}
draft-form|表单草稿恢复|草稿保留原始字符串输入以支持尚未填完的数字。提交时再规范化并校验，避免保存草稿时擅自把无效输入改为零。|{"formId":"expense","draftVersion":2,"rawValues":{"amount":"12.","date":"2026-10-","note":"未完成"},"dirtyFields":["amount","date"],"submitted":false}
field-dependencies|级联选择字段|城市选择依赖地区，依赖变化时下级字段需要重置。可选项从本地字典读取，示例不请求远程地区服务。|{"fields":{"region":"zhejiang","city":"hangzhou"},"dependencies":[{"source":"region","targets":["city"],"onChange":"clear-targets"}],"optionSource":"assets/regions.json"}
input-normalization|输入规范化规则|去除首尾空白、Unicode 规范化和大小写转换是不同步骤。只有明确适用的字段才应该做转换，不能统一改写所有用户文本。|{"field":"tag","pipeline":[{"operation":"trim"},{"operation":"unicode-normalize","form":"NFC"},{"operation":"lowercase","locale":"en"}],"preserveOriginal":true}
form-submission|提交快照与幂等键|提交快照保存经过校验的值和本地请求标识，避免双击按钮产生重复记录。这个标识只用于本地事务，不会发送请求。|{"submissionId":"local-submit-17","formVersion":3,"validatedValues":{"name":"小林","quantity":2},"status":"saved-locally","duplicatePolicy":"ignore-same-id"}
# metrics|统计与图表
categorical-chart|分类柱状图数据|分类轴和系列分别保存，所有系列长度应与分类数量一致。缺失数值使用 null，不用零掩盖没有观测的事实。|{"categories":["周一","周二","周三"],"series":[{"name":"阅读分钟","values":[25,null,40]}],"valueUnit":"min"}
time-series|时间序列观测|每个观测点同时保存时间戳和值，便于识别采样间隔变化。不要用数组下标推断时间，否则丢点后整条序列会错位。|{"metric":"temperature","unit":"C","samples":[{"at":"2026-10-22T08:00:00Z","value":21.2},{"at":"2026-10-22T08:05:00Z","value":21.6}]}
histogram|直方图分箱|分箱边界需要声明包含规则，相邻区间不能重复统计边界值。最后区间可包含上界，以覆盖整个观测范围。|{"measure":"duration","unit":"ms","bins":[{"fromInclusive":0,"toExclusive":10,"count":8},{"fromInclusive":10,"toExclusive":20,"count":3}],"overflowCount":1}
scatter-plot|散点图坐标|散点记录把 x、y 与样本 id 放在一起，避免两个独立数组被错误排序。坐标轴单位帮助解释值之间的关系。|{"axes":{"x":{"label":"时长","unit":"min"},"y":{"label":"完成量","unit":"pages"}},"points":[{"id":"s1","x":20,"y":8},{"id":"s2","x":35,"y":11}]}
summary-statistics|描述统计结果|汇总结果同时给出样本数、缺失数和统计值。均值必须与单位一起解释，不能从没有样本的集合伪造零均值。|{"variable":"readingMinutes","unit":"min","sampleCount":5,"missingCount":1,"statistics":{"minimum":10,"maximum":40,"mean":24,"median":25}}
pivot-table|交叉汇总表|透视表明确行维度、列维度和聚合方式。单元格用坐标引用维度值，便于检查缺少组合或重复组合。|{"rows":["books","tools"],"columns":["Q1","Q2"],"aggregation":"sum-minor-units","cells":[{"row":"books","column":"Q1","value":12000},{"row":"tools","column":"Q2","value":8500}]}
chart-thresholds|阈值与告警区间|正常范围、警告范围和严重范围应避免不明确的重叠。这里只保存演示阈值，具体判断需要应用按明确优先级实现。|{"metric":"diskUsagePercent","thresholds":[{"from":0,"toExclusive":80,"level":"normal"},{"from":80,"toExclusive":95,"level":"warning"},{"from":95,"toInclusive":100,"level":"critical"}]}
moving-window|滑动窗口配置|窗口长度和最少样本数决定是否能计算聚合值。按数量和按时间的窗口语义不同，配置必须明确采用哪一种。|{"aggregation":"moving-average","window":{"kind":"sample-count","size":5,"minimumValidSamples":3},"missingValuePolicy":"skip","centered":false}
dashboard-layout|仪表板布局|组件按网格坐标与尺寸定位，数据源引用本地指标 id。展示布局与指标数据拆开，调整面板不会重写原始观测。|{"grid":{"columns":12,"rowHeight":80},"widgets":[{"id":"summary","kind":"number","metricId":"total","rect":{"x":0,"y":0,"w":4,"h":1}},{"id":"trend","kind":"line","metricId":"daily","rect":{"x":4,"y":0,"w":8,"h":3}}]}
data-quality|数据质量检查|质量报告区分缺失、重复和越界，错误应指向具体记录。总行数和有效行数可以用于核对是否有记录未被处理。|{"dataset":"measurements","rowCount":12,"validRowCount":9,"issues":[{"row":3,"field":"value","code":"missing"},{"row":7,"field":"id","code":"duplicate"},{"row":9,"field":"value","code":"out-of-range"}]}
# science|测量与实验数据
measurement-uncertainty|测量值与不确定度|测量结果同时保存值、单位和不确定度类型。标准不确定度与置信区间不是同一概念，应使用明确字段表达。|{"quantity":"length","value":12.34,"unit":"mm","uncertainty":{"kind":"standard","value":0.02},"instrumentId":"caliper-demo"}
sensor-calibration|传感器校准系数|校准模型通过模型名和系数描述，适用量程独立记录。外推超出校准范围时应给出提示，不能默认仍然精确。|{"sensorId":"temp-01","model":"linear","coefficients":{"slope":1.002,"offset":-0.15},"validRange":{"minimum":0,"maximum":50,"unit":"C"}}
experiment-plan|实验条件与重复次数|实验计划列出受控因素和响应变量，重复次数单独保存。相同条件的多次测量用于估计波动，不能简单覆盖为一个值。|{"experimentId":"paper-test","factors":{"paperType":["A","B"],"humidityPercent":50},"response":{"name":"strength","unit":"N"},"replicates":3}
sample-chain|样品流转记录|样品记录保存批次、容器与交接事件，便于追溯。交接时间与接收人是历史事实，不应仅保留最后持有人。|{"sampleId":"S-014","batch":"B-26","container":"vial-3","custody":[{"at":"2026-10-20T09:00:00Z","from":"collector","to":"lab","condition":"sealed"}]}
unit-conversion|单位换算参数|线性换算可以用比例和偏移描述，但单位必须是明确符号。摄氏度转开尔文有偏移，不能只使用一个乘法因子。|{"conversion":{"from":"C","to":"K","multiplyBy":1,"add":273.15},"input":20,"expectedOutput":293.15}
spectral-series|光谱采样表|光谱的波长与强度成对保存，两个轴单位分别定义。归一化强度没有物理单位时应明确说明它是相对量。|{"wavelengthUnit":"nm","intensityUnit":"relative","points":[[400,0.12],[450,0.34],[500,0.85],[550,1.0]],"normalization":"maximum-equals-one"}
observation-flags|观测值质量标记|观测值和质量标记应同时保留。可疑数据先标记再由分析策略决定是否排除，不要静默修改原始值。|{"station":"demo-1","observations":[{"value":18.2,"flags":[]},{"value":99.9,"flags":["sensor-range-exceeded"]}],"unit":"C"}
coordinate-frame|坐标系定义|坐标值必须与参考系、轴方向和单位一起解释。设备局部坐标不能直接当作地理经纬度使用。|{"frameId":"robot-local","handedness":"right","axes":{"x":"forward","y":"left","z":"up"},"unit":"m","origin":{"description":"base center"}}
uncertainty-budget|不确定度预算表|多个不确定度来源分别记录分布与标准分量。预算表用于解释结果来源，本示例并未自动计算合成不确定度。|{"quantity":"mass","unit":"g","components":[{"source":"resolution","distribution":"rectangular","standardUncertainty":0.003},{"source":"repeatability","distribution":"normal","standardUncertainty":0.005}]}
reproducibility-record|实验复现信息|复现记录需要输入摘要、参数版本与随机种子。仅保存最终结果无法说明如何重新得到同样的结果。|{"runId":"run-017","inputFile":"samples.csv","parameterVersion":"v2","randomSeed":17,"software":{"name":"local-analysis","version":"1.2"},"resultFile":"results/run-017.json"}
# geography|地理与路线数据
geo-point|GeoJSON 点|GeoJSON Point 的坐标顺序是经度在前、纬度在后。坐标数组只是数据，展示地图还需要独立的离线底图资源。|{"type":"Point","coordinates":[120.1551,30.2741]}
geo-line|GeoJSON 线段|LineString 由有序位置组成，表示路线的连接顺序。反转数组会改变行进方向，因此排序工具不应重排坐标点。|{"type":"LineString","coordinates":[[120.15,30.27],[120.16,30.28],[120.17,30.275]]}
geo-polygon|GeoJSON 多边形边界|多边形线性环需要首尾坐标一致。这里用简单矩形演示闭合边界，环内每个位置都是经纬度对。|{"type":"Polygon","coordinates":[[[120.1,30.2],[120.2,30.2],[120.2,30.3],[120.1,30.3],[120.1,30.2]]]}
geo-feature|GeoJSON 要素属性|Feature 将几何与业务属性分开，geometry 负责位置，properties 负责名称等信息。id 是稳定标识，不应与名称绑定。|{"type":"Feature","id":"place-1","geometry":{"type":"Point","coordinates":[120.15,30.27]},"properties":{"name":"示例书屋","category":"library"}}
geo-collection|GeoJSON 要素集合|FeatureCollection 的 features 只能放要素对象。某个要素的位置未知时 geometry 可以为 null，而不是随意使用零坐标。|{"type":"FeatureCollection","features":[{"type":"Feature","geometry":null,"properties":{"name":"待定位资料点"}}]}
bounding-box|地理边界范围|边界框保存西、南、东、北，字段名比匿名四元素数组更容易检查。跨日期变更线的边界需要额外约定，不能盲目比较最小最大。|{"bounds":{"west":119.9,"south":30.1,"east":120.4,"north":30.5},"coordinateReference":"longitude-latitude","crossesAntimeridian":false}
route-waypoints|路线途经点|途经点保留顺序、停留分钟数与备注。预计行程是规划信息，不能把它当成实时导航或实时路况。|{"routeName":"城市步行演示","waypoints":[{"name":"书屋","coordinate":[120.15,30.27],"stayMinutes":30},{"name":"公园","coordinate":[120.16,30.28],"stayMinutes":20}],"mode":"walking"}
offline-map-pack|离线地图包清单|地图包需要范围、缩放级别和本地瓦片位置。清单只是元数据，不下载瓦片，也不保证路径下已经有地图资源。|{"packId":"demo-city","zoomRange":{"minimum":10,"maximum":14},"tilesRoot":"maps/demo/{z}/{x}/{y}.png","tileScheme":"xyz","downloadEnabled":false}
location-accuracy|定位结果与精度|定位点需要观测时间和水平精度，不能只保存经纬度。精度单位为米，演示数据不代表设备正在请求定位权限。|{"position":{"longitude":120.155,"latitude":30.274},"horizontalAccuracyMeters":12,"observedAt":"2026-10-22T08:10:00Z","source":"illustrative-fixture"}
transit-itinerary|离线公交行程|行程分为步行和乘车段，不同段保存各自需要的字段。时刻是离线示例快照，实际出行前不能据此推断当前运营情况。|{"legs":[{"mode":"walk","distanceMeters":300},{"mode":"bus","routeLabel":"示例 1 路","from":"A站","to":"B站","scheduledDeparture":"09:10"}],"dataKind":"demonstration"}
# household|日常物品管理
pantry-item|食品库存批次|同种食品分批保存数量和日期，避免把新旧批次混在一起。最佳食用期与安全期限具有不同语义，应保留标签原文。|{"item":"燕麦片","batches":[{"batch":"A","quantity":2,"unit":"bag","bestBefore":"2026-12-01"},{"batch":"B","quantity":1,"unit":"bag","bestBefore":"2027-02-01"}]}
recipe-ingredients|食谱用料与份数|用料数量与单位分开，便于按份数缩放。少许这类非数值用量用文本字段保留，不能假装可以按同一公式计算。|{"recipe":"番茄面","servings":2,"ingredients":[{"name":"面条","amount":200,"unit":"g"},{"name":"番茄","amount":2,"unit":"piece"},{"name":"盐","amountText":"少许"}]}
meal-plan|一周用餐安排|用餐计划按日期和餐次组织，引用食谱 id 而非复制整个做法。人数单独保存，使采购汇总能够按实际份数计算。|{"days":[{"date":"2026-10-23","meals":{"lunch":{"recipeId":"tomato-noodles","people":2},"dinner":{"recipeId":"vegetable-rice","people":3}}}]}
shopping-list|共享采购清单|采购项保存完成状态和数量，按分类展示更易检查遗漏。同一名称的不同规格应使用独立 id 区分。|{"listId":"weekend","items":[{"id":"milk-1l","name":"牛奶","quantity":2,"unit":"box","category":"dairy","checked":false},{"id":"apple","name":"苹果","quantity":4,"unit":"piece","category":"fruit","checked":true}]}
appliance-maintenance|设备保养计划|家用设备的型号、购置日期与保养周期分开保存。已经完成的保养保留历史，下次日期由业务规则计算。|{"appliance":{"name":"空气净化器","model":"DEMO-A"},"maintenance":{"intervalDays":180,"lastCompletedOn":"2026-08-01","parts":[{"name":"滤芯","quantity":1}]}}
warranty-record|保修信息|保修记录保留期限、凭证路径和序列号，序列号作为文本。不要把凭证图片本身直接塞入清单导致文件过大。|{"itemId":"laptop-demo","serialNumber":"00009-A","purchasedOn":"2026-03-10","warrantyUntil":"2028-03-09","proofFile":"receipts/laptop.pdf"}
home-inventory|家庭物品目录|物品关联房间和收纳位置，估计价值是可选字段。用于备份的清单应避免记录不必要的家庭敏感信息。|{"rooms":{"study":{"items":[{"id":"book-box","name":"资料箱","location":"书架下层","quantity":1,"estimatedValueMinor":null}]}}}
moving-boxes|搬家箱号清单|每个箱子有稳定编号、目的房间和易碎提示。箱内物品列表便于搬迁后查找，重量与是否可叠放分别描述搬运要求。|{"boxId":"BOX-012","destinationRoom":"study","fragile":true,"stackable":false,"weightKg":6.5,"contents":["台灯","相框"]}
plant-care|植物养护记录|浇水记录与计划分开，可以避免仅看周期就重复浇水。土壤状态是观察值，实际养护不能只由日期决定。|{"plantId":"pothos-1","location":"窗边","care":{"checkIntervalDays":5,"lastWateredOn":"2026-10-18"},"observations":[{"date":"2026-10-22","soil":"slightly-moist"}]}
utility-reading|水电表读数|表读数与消费量不同，使用相邻读数差值才能计算用量。更换或归零事件需要单独记录，不能产生负用量后直接忽略。|{"meterId":"electric-demo","unit":"kWh","readings":[{"date":"2026-09-30","value":1250.5},{"date":"2026-10-31","value":1376.2}],"replacementEvents":[]}
# media|媒体与创作资源
image-metadata|图片尺寸与色彩|图片元数据保存像素尺寸、方向和色彩空间。文件扩展名不能证明实际编码格式，需要读取文件头或解码后核实。|{"file":"photos/demo.jpg","dimensions":{"width":1920,"height":1080,"unit":"px"},"orientation":"landscape","colorSpace":"sRGB","hasAlpha":false}
audio-track|音频轨道信息|采样率、声道数和时长分别使用明确单位。曲目标题与文件名分开，可以在不重命名文件的情况下修改展示信息。|{"trackId":"a17","title":"本地录音","file":"audio/note.wav","sampleRateHz":48000,"channels":1,"durationMilliseconds":12500}
video-timeline|视频剪辑时间线|片段的素材区间和时间线起点是不同坐标系，必须分开保存。时间用毫秒整数以减少跨帧换算时的误解。|{"timeUnit":"ms","clips":[{"asset":"intro.mp4","sourceIn":500,"sourceOut":3500,"timelineStart":0},{"asset":"demo.mp4","sourceIn":0,"sourceOut":8000,"timelineStart":3000}]}
subtitle-cues|字幕时间段|字幕块有开始、结束和文本，顺序用于播放。结束时间必须晚于开始时间，是否允许字幕重叠由播放器规则决定。|{"language":"zh-CN","timeUnit":"ms","cues":[{"start":0,"end":1800,"text":"欢迎使用离线工具"},{"start":2000,"end":4200,"text":"先打开一个 JSON 文件"}]}
sprite-atlas|精灵图切片|图集中的每个精灵保存矩形区域和锚点。区域坐标按像素计算，超出纹理边界需要由资源校验器报告。|{"texture":"sprites.png","textureSize":{"width":256,"height":128},"sprites":{"cursor":{"x":0,"y":0,"width":16,"height":24,"pivot":[0,0]},"marker":{"x":16,"y":0,"width":32,"height":32,"pivot":[0.5,1]}}}
animation-keyframes|动画关键帧|关键帧记录时间、属性值和插值方式，时间必须单调。三维位置使用固定长度数组，不能混入不同维数的点。|{"durationMilliseconds":1000,"property":"position","keyframes":[{"time":0,"value":[0,0,0],"easing":"linear"},{"time":1000,"value":[10,5,0],"easing":"ease-out"}]}
font-manifest|本地字体资源|字体文件、字重和样式显式关联，避免用一个文件冒充多个真实字重。资源必须随包提供，不能指向需要联网下载的字体服务。|{"family":"LocalSans","faces":[{"file":"fonts/regular.ttf","weight":400,"style":"normal"},{"file":"fonts/bold.ttf","weight":700,"style":"normal"}],"fallbackFamilies":["sans-serif"]}
color-tokens|设计语义颜色|语义色与原始色板分开，组件引用角色而不是硬编码颜色。颜色字符串只是格式约定，需要额外检查十六进制长度和合法字符。|{"palette":{"blue500":"#2563EB","red600":"#DC2626"},"semantic":{"action.primary":"blue500","feedback.error":"red600"},"mode":"light"}
asset-license|创作资源授权清单|资源授权记录作者、许可标识和是否需要署名。许可字符串是记录信息，不能代替阅读实际授权条款。|{"assets":[{"path":"illustrations/compass.svg","creator":"Demo Artist","license":"CC-BY-4.0","attributionRequired":true,"attributionText":"Compass by Demo Artist"}]}
playlist|本地播放列表|播放列表保存有序轨道引用与循环模式，不把音频内容嵌入 JSON。缺失文件应作为可恢复错误报告，而不是跳过后仍显示全部可用。|{"name":"学习录音","tracks":[{"file":"audio/intro.ogg","resumeMilliseconds":0},{"file":"audio/chapter1.ogg","resumeMilliseconds":32000}],"repeat":"none","shuffle":false}
# accessibility|无障碍与本地化
accessible-controls|控件可访问描述|图标按钮需要独立的可访问名称与提示，不能只依赖图形。状态值使用结构化字段以便辅助技术读取。|{"controlId":"format","role":"button","accessibleName":"格式化 JSON","hint":"按两空格缩进重新排列文档","state":{"disabled":false,"busy":false}}
focus-order|键盘焦点顺序|焦点顺序按稳定控件 id 记录，跳过不可用控件由界面逻辑决定。视觉排列变化后应核对焦点顺序仍符合阅读习惯。|{"scope":"json-tools","tabOrder":["source-editor","validate-button","format-button","result-view"],"initialFocus":"source-editor","trapFocus":false}
screenreader-announcements|辅助提示优先级|通知消息通过礼貌或紧急优先级区分，避免每次输入都打断用户。错误数量变化可以聚合播报，而非逐字朗读整个文档。|{"announcements":[{"message":"校验通过","priority":"polite"},{"message":"保存失败，请检查本地存储空间","priority":"assertive"}],"coalesceMilliseconds":500}
contrast-settings|显示与动效偏好|对比度、缩放和减少动效是不同需求，应可独立设置。用户偏好保存为本地配置，不应强制覆盖系统的辅助设置。|{"contrast":"high","textScale":1.4,"reduceMotion":true,"highlightErrorsWith":{"color":true,"underline":true,"icon":true}}
message-catalog|界面消息目录|消息 id 保持稳定，语言文本单独存储。占位符使用具名参数，方便不同语言调整语序而不改变业务代码。|{"locale":"zh-CN","messages":{"document.saved":"已保存 {fileName}","json.errorLocation":"第 {line} 行，第 {column} 列"},"placeholders":{"line":"integer","column":"integer"}}
plural-message|复数消息分支|复数规则将数字类别映射到消息文本，不能假设所有语言只有单复数两种。这里明确给出 one 和 other 两种英文分支。|{"locale":"en","messageId":"files.count","argument":"count","forms":{"one":"{count} file","other":"{count} files"}}
locale-fallback|语言回退链|回退链先尝试完整地区，再尝试基础语言，最后使用默认语言。链应避免循环，并保留用户主动选择的语言优先级。|{"requestedLocale":"zh-HK","fallbackChain":["zh-HK","zh-Hant","en"],"defaultLocale":"en","missingMessagePolicy":"show-key"}
number-presentation|数字展示配置|小数位数、分组和计量单位属于展示规则，不应改变原始数据。格式化后的字符串适合界面，导出计算数据仍应保留数值。|{"locale":"de-DE","format":{"style":"decimal","minimumFractionDigits":2,"maximumFractionDigits":2,"useGrouping":true},"rawValue":1234.5}
right-to-left-layout|从右到左布局|文本方向与控件顺序可以不同，代码编辑区通常仍需要左到右。配置应允许局部方向覆盖以保持路径与数字易读。|{"locale":"ar","pageDirection":"rtl","overrides":{"codeEditor":"ltr","filePath":"ltr","messageText":"auto"}}
localized-content|本地化内容覆盖|同一内容 id 关联多个语言版本，资料版本可分别维护。缺少某种语言时显示回退标记，不能假称已完整翻译。|{"contentId":"json-guide","variants":{"zh-CN":{"file":"guide.zh.md","revision":4},"en":{"file":"guide.en.md","revision":3}},"translationStatus":{"en":"needs-update"}}
# schemas|本地模式校验
schema-primitive|基本类型模式|type 约束要求值具有指定 JSON 类型。模式本身也是 JSON，解析模式成功与被校验数据符合模式是两项独立检查。|{"schema":{"type":"string"},"validDocument":"hello","invalidDocument":42}
schema-required|对象必填字段|required 只要求字段存在，不自动限制它的类型。properties 与 required 配合才能同时表达存在性和内容约束。|{"schema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]},"validDocument":{"name":"笔记"}}
schema-additional|拒绝额外字段|additionalProperties 为 false 时，未声明成员会被报告。严格结构适合固定合同；需要兼容扩展的资料应谨慎使用。|{"schema":{"type":"object","properties":{"id":{"type":"integer"}},"required":["id"],"additionalProperties":false},"invalidDocument":{"id":1,"extra":true}}
schema-enum|枚举选项约束|enum 使用实际 JSON 值比较，不会把数值与数字字符串视为相同。枚举适合有限状态集合，显示文案仍可独立翻译。|{"schema":{"enum":["draft","review","published"]},"validDocument":"review","invalidDocument":"Review"}
schema-number-range|数值上下界|minimum 和 maximum 表示包含边界的范围。业务还需要约定单位，否则同一个合法数字可能代表完全不同的量。|{"schema":{"type":"integer","minimum":0,"maximum":100},"validDocument":100,"invalidDocument":101,"unit":"percent"}
schema-text-length|字符串长度约束|字符串长度规则限制文本大小，不能用来判断邮箱或文件路径是否可信。表情与组合字符的长度还需要明确实现采用的字符单位。|{"schema":{"type":"string","minLength":2,"maxLength":12},"validDocument":"local-note","invalidDocument":"x"}
schema-array-items|数组成员模式|items 把同一规则应用到每个数组成员，minItems 则要求最低数量。数组合法不代表成员都满足业务类型。|{"schema":{"type":"array","items":{"type":"integer"},"minItems":1},"validDocument":[1,2,3],"invalidDocument":[1,"2"]}
schema-constant|常量版本字段|const 可以固定协议版本，避免旧读取器悄悄接受不认识的新格式。后续版本应通过明确迁移而不是修改校验结果。|{"schema":{"type":"object","properties":{"schemaVersion":{"const":1}},"required":["schemaVersion"]},"validDocument":{"schemaVersion":1}}
schema-local-reference|文档内模式引用|本地引用以 #/ 开头，只解析当前模式文档中的定义。离线校验器不应为了外部引用自动访问网络。|{"schema":{"$defs":{"name":{"type":"string","minLength":1}},"type":"object","properties":{"title":{"$ref":"#/$defs/name"}}},"validDocument":{"title":"离线资料"}}
schema-unsupported|不支持关键字报告|模式支持范围必须明确。遇到当前实现不支持的 format 等关键字时应显示未支持诊断，而不能直接宣称完整校验通过。|{"schema":{"type":"string","format":"email"},"document":"not-an-email","expectedPolicy":"report-unsupported-keyword-without-network"}
# interchange|表格与交换格式
table-records|对象数组表格|表格可用对象数组表示，每行拥有相同字段名。缺失字段与 null 的区别在导出 CSV 时可能丢失，应明确采用的空值规则。|[{"name":"A","score":90,"remark":null},{"name":"B","score":85,"remark":"补充练习"}]
columnar-table|按列存储的表格|列式结构把每个字段的值放在单独数组，适合批量处理。所有列长度必须一致，否则行号无法对应同一条记录。|{"columns":{"id":["a","b","c"],"value":[10,20,30],"valid":[true,false,true]},"rowCount":3}
table-schema|表格列定义|列定义给出字段名、类型与空值规则，数据行只保存值。列顺序属于格式合同，变更顺序时必须同步更新行数据。|{"columns":[{"name":"code","type":"string","nullable":false},{"name":"quantity","type":"integer","nullable":false}],"rows":[["A",2],["B",0]]}
csv-quoted-values|CSV 引号与换行|逗号、双引号和换行都可能出现在 JSON 字符串中。转换到 CSV 时需要按目标格式转义，不能简单用逗号拼接。|[{"name":"a,b","note":"said \"hello\""},{"name":"plain","note":"line one\nline two"}]
json-lines-source|JSON Lines 原始文本|JSON Lines 每行一个独立 JSON 值，不能把多行直接当成单个 JSON 文档。这里把原始行文本放进字符串用于演示转换。|{"lines":"{\"id\":1}\n{\"id\":2}\n","expectedArray":[{"id":1},{"id":2}]}
key-value-pairs|键值对数组|当顺序重要或允许重复键时，使用键值对数组比对象更明确。对象不能安全表达同名成员的多次出现。|{"pairs":[["tag","json"],["tag","offline"],["sort","name"]],"preserveOrder":true,"allowRepeatedKeys":true}
base64-envelope|二进制内容封装|JSON 没有原生二进制类型，少量字节可以用 Base64 字符串包装。编码会增加体积，大文件通常应使用本地文件引用。|{"mediaType":"application/octet-stream","encoding":"base64","data":"SGVsbG8=","decodedBytes":5}
date-envelope|日期文本合同|JSON 没有原生日期类型，日期需要字符串与格式约定。完整日期、本地时刻和 UTC 时刻不能互相无条件替换。|{"date":"2026-10-22","localDateTime":"2026-10-22T16:30:00","utcInstant":"2026-10-22T08:30:00Z","conventions":{"date":"calendar-date","instant":"UTC"}}
decimal-envelope|高精度十进制表示|需要精确保留小数位的数值可用字符串加 scale 表达。解析者应使用相应十进制算法，不要先转为浮点再尝试恢复精度。|{"decimal":{"unscaledValue":"1234567890123456789","scale":4},"display":"123456789012345.6789","representation":"base10-fixed-scale"}
tagged-union|带标签的联合结构|kind 字段决定 value 的结构，使多种记录能够放在一个数组里。读取器应对未知 kind 给出明确诊断而非猜测类型。|{"events":[{"kind":"text","value":{"text":"便笺"}},{"kind":"file","value":{"path":"data.json","bytes":24}},{"kind":"marker","value":null}]}
# tests|测试与边界夹具
test-case|单项测试规格|测试规格明确输入、操作与预期值，便于离线重复执行。实际结果应由测试程序产生，不能直接把预期值打印成通过。|{"caseId":"sort-keys","operation":"sort","input":{"z":1,"a":2},"expected":{"a":2,"z":1},"assertion":"structural-equality"}
parameterized-cases|参数化边界测试|边界测试覆盖空集合、单项和多项，能揭示下标与空值处理问题。场景结构相同是测试策略，不是新增教程数量的填充来源。|{"operation":"array-length","cases":[{"input":[],"expected":0},{"input":[null],"expected":1},{"input":[true,false],"expected":2}]}
invalid-json-fixtures|无效 JSON 文本夹具|无效文档保存为 JSON 字符串，这个外层文档仍合法。测试程序读取字符串后再交给解析器，检查错误确实被捕获。|{"invalidSources":["{\"a\":}","[1,]","{a:1}","True"],"expectedStatus":"syntax-error"}
duplicate-key-fixture|重复键测试夹具|重复键可能被宽松解析器静默覆盖，严格编辑器应报告歧义。为了保存测试内容，重复键文档在此作为原始文本字符串。|{"source":"{\"name\":\"first\",\"name\":\"second\"}","policy":"reject-duplicate-object-members","expectedProblem":"duplicate-key"}
deep-nesting-fixture|嵌套深度边界|深度限制保护编辑器避免过度递归。测试先按指定深度生成文档，再验证临界允许值与超限值，不能只测试普通浅对象。|{"generator":{"container":"array","depths":[1,64,128,129],"leaf":0},"limit":128,"overLimitPolicy":"diagnostic"}
roundtrip-fixture|解析格式化往返测试|往返测试验证格式化前后的结构相等，不要求空白或对象成员顺序完全一致。数组顺序与字符串内容必须保持。|{"source":"{\"b\":[2,1],\"a\":\"line\\ntext\"}","operations":["parse","pretty","parse"],"assertions":["same-structure","same-array-order","same-string-content"]}
mutation-safety|失败操作不修改输入|对补丁或转换的失败测试必须检查原文保持不变。仅验证抛出异常不足以发现先修改再失败的部分写入问题。|{"initial":{"revision":1,"name":"draft"},"operations":[{"op":"replace","path":"/name","value":"changed"},{"op":"test","path":"/revision","value":2}],"expectFailure":true,"expectedAfterFailure":{"revision":1,"name":"draft"}}
missing-versus-null|缺失路径与空值测试|已存在的 null 和不存在路径应该有不同结果。读取接口若只返回 null 会丢失这个区别，应提供状态或抛出明确错误。|{"document":{"present":null},"queries":[{"pointer":"/present","exists":true,"expected":null},{"pointer":"/absent","exists":false,"expectedError":"missing-path"}]}
unicode-fixtures|Unicode 与转义往返|可见文本相似不代表代码点相同，测试应保留原始字符串。格式化不能无授权地做 Unicode 规范化或改变转义后的实际字符。|{"strings":["é","é","🧑‍💻","\u0041","A"],"assertion":"preserve-decoded-string","normalizeUnicode":false}
resource-limits|资源上限测试计划|资源测试覆盖字节数、节点数和深度三种不同限制。报告应说明触发哪一项限制，不能统一显示一个无法解释的失败。|{"limits":{"sourceBytes":2097152,"maximumNodes":50000,"maximumDepth":128},"cases":["exact-limit","one-over-limit","small-valid-document"],"expectedFailureMode":"actionable-diagnostic"}
# workflows|状态与权限建模
state-machine|审批状态机|状态机用明确转换表限制允许操作，每个转换保存触发事件。当前状态是数据，是否允许转移由本地业务逻辑判断。|{"initial":"draft","states":["draft","review","approved","rejected"],"transitions":[{"from":"draft","event":"submit","to":"review"},{"from":"review","event":"accept","to":"approved"},{"from":"review","event":"reject","to":"rejected"}]}
role-permissions|角色权限矩阵|角色映射到明确动作集合，避免用一个管理员布尔值解释所有权限。数据文件只描述策略，不能替代系统沙盒权限。|{"roles":{"reader":["document.read"],"editor":["document.read","document.edit"],"owner":["document.read","document.edit","project.delete"]},"defaultRole":"reader"}
capability-manifest|离线能力声明|应用能力清单明确哪些功能依赖本地实现。禁用外部引用和下载让独立版保持离线，UI 仍需与真实实现保持一致。|{"capabilities":{"jsonValidation":"local","schemaReferences":"document-internal-only","terminal":"sandbox-local","packageDownload":"disabled","cloudProjects":"disabled"}}
approval-history|多步骤审批历史|历史记录按序保存每次决定和当时角色，当前审批人独立指定。撤回与拒绝不是同一种状态，应保留事件原意。|{"requestId":"r18","currentStep":"finance","history":[{"step":"manager","decision":"approved","actor":"u2","sequence":1},{"step":"finance","decision":"returned-for-details","actor":"u8","sequence":2}]}
local-job-queue|本地任务队列|队列任务保存依赖、尝试次数和当前状态。失败重试有上限，不能让损坏输入在后台无限循环占用设备资源。|{"jobs":[{"id":"j1","kind":"index","state":"completed","dependsOn":[],"attempts":1},{"id":"j2","kind":"thumbnail","state":"waiting","dependsOn":["j1"],"attempts":0}],"maximumAttempts":3}
undo-history|撤销记录|撤销命令保存可逆的前后值及目标路径。合并连续输入时需要相同文档和兼容操作，不能跨文件合并撤销记录。|{"document":"data.json","commands":[{"id":"c1","path":"/title","before":"draft","after":"review"},{"id":"c2","path":"/count","before":1,"after":2}],"cursor":2}
transaction-plan|本地事务执行计划|事务将多个文件写入作为一个计划，预检通过后才执行。恢复策略明确回滚来源，避免失败后用户不知道哪些文件已改变。|{"transactionId":"tx3","preflight":{"freeSpaceRequiredBytes":4096,"backupRequired":true},"writes":[{"path":"a.json","temporary":".a.tmp"},{"path":"b.json","temporary":".b.tmp"}],"onFailure":"restore-backups"}
privacy-export|资料导出脱敏规则|导出策略可以按字段路径删除或替换敏感信息。脱敏后的结果仍要重新校验，规则不能仅靠字符串全文替换实现。|{"rules":[{"pointer":"/contact/phone","action":"remove"},{"pointer":"/person/name","action":"replace","value":"anonymous"}],"retainFields":["/recordId"],"writeTo":"exports/redacted.json"}
local-resource-access|本地资源访问白名单|相对资源路径仍需检查目录穿越，不能因为没有网络就认为所有路径安全。访问策略限定项目根并拒绝上级目录引用。|{"root":"project","allowedSubdirectories":["assets","data"],"rejectParentTraversal":true,"followSymbolicLinks":false,"access":"read-only"}
workflow-checkpoint|流程中断与恢复|流程检查点保存已完成步骤和下一步，恢复前应再次确认输入修订。仅有状态文件不证明任务仍在运行，需要实际进程或执行句柄。|{"workflowId":"export-17","inputRevision":8,"completedSteps":["validate","stage-files"],"nextStep":"write-archive","execution":{"state":"stopped","liveHandle":null}}
# structures|算法数据结构
binary-tree|二叉树结构|二叉树节点明确区分左子树和右子树，空分支用 null 表示。对象成员顺序不表达树的左右关系，因此必须使用具名字段。|{"root":{"value":8,"left":{"value":3,"left":null,"right":null},"right":{"value":10,"left":null,"right":null}}}
linked-list|链表引用表|链表可以用节点字典和 next 引用表示，头节点单独保存。遍历器需要检测缺失引用和循环，语法校验不能保证链表完整。|{"head":"n1","nodes":{"n1":{"value":"A","next":"n2"},"n2":{"value":"B","next":"n3"},"n3":{"value":"C","next":null}}}
trie-index|前缀树词典|前缀树将每个字符作为一层，终止标记区别完整词与普通前缀。空 children 对象表示没有后续字符，不等于节点本身不是一个词。|{"root":{"terminal":false,"children":{"c":{"terminal":false,"children":{"a":{"terminal":false,"children":{"t":{"terminal":true,"children":{}}}}}}}}}
sparse-matrix|稀疏矩阵三元组|稀疏矩阵只保存非零元素的行、列和值，并明确下标从零开始。读取器需检查坐标范围和重复坐标的合并策略。|{"shape":[3,4],"indexBase":0,"entries":[{"row":0,"column":2,"value":5},{"row":2,"column":1,"value":-1}],"defaultValue":0}
weighted-graph|带权有向图|边分别保存起点、终点与权重，方向是图的独立属性。存在负权边时不能盲目采用仅支持非负权的最短路算法。|{"directed":true,"vertices":["A","B","C"],"edges":[{"from":"A","to":"B","weight":4},{"from":"B","to":"C","weight":2},{"from":"A","to":"C","weight":9}],"weightUnit":"cost"}
priority-queue|优先队列元素|优先队列保存优先级与稳定入队顺序，二者可共同处理同级任务。数组当前排列只是序列化形态，不能假定一定已经满足堆结构。|{"ordering":"lowest-priority-first","items":[{"id":"scan","priority":2,"sequence":1},{"id":"save","priority":1,"sequence":2},{"id":"preview","priority":2,"sequence":3}]}
interval-set|半开区间集合|半开区间使用包含起点、不包含终点的约定，使相邻区间可无重叠拼接。开始等于结束的区间为空，不能当成一个有效时长。|{"boundaryConvention":"start-inclusive-end-exclusive","intervals":[{"start":0,"end":5},{"start":5,"end":8},{"start":10,"end":12}],"domain":"integer-position"}
disjoint-sets|并查集父节点表|并查集通过父指针表示集合，根节点指向自己。rank 是合并优化元数据，不应被误解为集合内成员数量。|{"parent":{"a":"a","b":"a","c":"c","d":"c"},"rank":{"a":1,"b":0,"c":1,"d":0},"elements":["a","b","c","d"]}
finite-automaton|有限状态自动机|自动机定义字母表、转移表与接受状态，未定义转移需要明确拒绝。状态名称只是标识，不包含可执行脚本。|{"alphabet":["0","1"],"startState":"even","acceptStates":["even"],"transitions":{"even":{"0":"even","1":"odd"},"odd":{"0":"odd","1":"even"}}}
bipartite-assignment|双部图匹配数据|两类节点分别保存，并通过允许匹配边连接。边只表示可分配关系，求得的匹配还需要检查每个节点的容量约束。|{"leftNodes":["workerA","workerB"],"rightNodes":["task1","task2","task3"],"allowedPairs":[["workerA","task1"],["workerA","task2"],["workerB","task2"],["workerB","task3"]],"capacityPerLeftNode":1}
'''


def pretty(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def leaf(value: object, pointer: str = "") -> tuple[str, object]:
    """Choose a real, deterministic leaf for a machine-checkable exercise."""
    if isinstance(value, dict) and value:
        key = list(value)[-1]
        token = key.replace("~", "~0").replace("/", "~1")
        return leaf(value[key], pointer + "/" + token)
    if isinstance(value, list) and value:
        index = len(value) - 1
        return leaf(value[index], pointer + "/" + str(index))
    return pointer, value


def inherited() -> tuple[list[dict], list[dict], dict]:
    tutorials = [
        e for e in json.loads((CORE_CONTENT / "tutorials.json").read_text(encoding="utf-8"))["entries"]
        if e["type"] == "json"
    ]
    examples = [
        e for e in json.loads((CORE_CONTENT / "examples.json").read_text(encoding="utf-8"))["entries"]
        if e["type"] == "json"
    ]
    tutorials, examples = copy.deepcopy(tutorials), copy.deepcopy(examples)
    audit = {
        "schemaVersion": 1,
        "baseline": "qfli_studio_core/assets/content at curriculum migration",
        "inheritedExampleCount": len(examples),
        "inheritedTutorialCount": len(tutorials),
        "inheritedCodeSha256": {},
        "corrections": {"exampleOutputs": 0, "lessonOutputs": 0, "proseExerciseAnswers": 0, "exampleFixtures": 0},
        "correctionDetails": [],
    }
    for entry in examples:
        audit["inheritedCodeSha256"][entry["id"]] = hashlib.sha256(entry["code"].encode()).hexdigest()
        expected = pretty(json.loads(entry["code"]))
        audit["corrections"]["exampleOutputs"] += entry["expectedOutput"] != expected
        if entry["expectedOutput"] != expected:
            audit["correctionDetails"].append({
                "id": entry["id"], "field": "expectedOutput",
                "previousValue": entry["expectedOutput"],
                "reason": "Replace fabricated runtime output with actual formatted JSON",
            })
        entry["expectedOutput"] = expected
        # Legacy fixtures were labels ("fixture-1"), not input documents.
        audit["corrections"]["exampleFixtures"] += 1
        audit["correctionDetails"].append({
            "id": entry["id"], "field": "inputFixtures",
            "previousValue": entry["inputFixtures"],
            "reason": "Replace fixture labels with the actual importable JSON document",
        })
        entry["inputFixtures"] = {"data.json": entry["code"]}
    for entry in tutorials:
        for lesson in entry["lessons"]:
            audit["inheritedCodeSha256"][lesson["id"]] = hashlib.sha256(lesson["code"].encode()).hexdigest()
            expected = pretty(json.loads(lesson["code"]))
            audit["corrections"]["lessonOutputs"] += lesson["output"] != expected
            if lesson["output"] != expected:
                audit["correctionDetails"].append({
                    "id": lesson["id"], "field": "output",
                    "previousValue": lesson["output"],
                    "reason": "Replace fabricated runtime output with actual formatted JSON",
                })
            lesson["output"] = expected
            lesson["explain"] += "\n\n离线验证说明：JSON 是数据格式。此处结果是本应用对文档实际解析并格式化后的内容，不是程序控制台输出。示例数据保留原有编号，新增实际场景请参阅后续分类。"
            for index, exercise in enumerate(lesson["exercises"]):
                try:
                    json.loads(exercise["answer"])
                except json.JSONDecodeError:
                    audit["correctionDetails"].append({
                        "id": lesson["id"], "field": f"exercises/{index}/answer",
                        "previousValue": exercise["answer"],
                        "reason": "Preserve prose answer in a valid JSON explanation object",
                    })
                    exercise["answer"] = pretty({"explanation": exercise["answer"]})
                    audit["corrections"]["proseExerciseAnswers"] += 1
    return tutorials, examples, audit


def build() -> dict[str, str]:
    tutorials, examples, audit = inherited()
    category, category_name = "", ""
    added = 0
    category_counts: dict[str, int] = {}
    for line in RECORDS.splitlines():
        if not line.strip():
            continue
        if line.startswith("# "):
            category, category_name = line[2:].split("|", 1)
            continue
        slug, title, explanation, document = line.split("|", 3)
        try:
            value = json.loads(document)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid authored JSON: {category}/{slug}: {error}") from error
        code = pretty(value)
        pointer, answer = leaf(value)
        lesson_id = f"json-practical-{slug}-lesson"
        metadata = {
            "language": "json", "type": "json", "locale": "zh-CN",
            "level": "beginner" if category == "foundations" else "intermediate",
            "title": f"{category_name}：{title}", "summary": explanation,
            "concepts": [category_name, title, "离线校验", "JSON Pointer"],
            "source": "Original QFLIJson offline curriculum",
            "license": "CC BY 4.0", "updatedAt": UPDATED,
        }
        examples.append({
            **metadata, "id": f"json-practical-{slug}", "code": code,
            "expectedOutput": code, "inputFixtures": {"data.json": code},
            "templateType": "json", "sourceLessonId": lesson_id,
        })
        tutorials.append({
            **metadata, "id": f"json-practical-{slug}-tutorial",
            "lessons": [{
                "id": lesson_id, "title": title, "summary": explanation,
                "concepts": metadata["concepts"],
                "explain": explanation + "\n\n操作：先校验并观察根类型，再格式化，最后用结构树定位字段。格式化只改变空白，不证明业务约束成立。所有示例均为离线演示数据；其中地址、路径与标识符不会自动触发网络请求或文件操作。",
                "objective": f"能够解释“{title}”的数据结构，并准确定位其成员。",
                "prerequisites": ["基础 JSON 值类型"] if category != "foundations" else [],
                "pitfalls": ["JSON 语法有效不等于业务规则正确。", "数组顺序具有含义；对象字段顺序不应用作业务条件。"],
                "code": code, "output": code,
                "exercises": [{
                    "prompt": f"使用 JSON Pointer {json.dumps(pointer, ensure_ascii=False)} 选择当前值，以合法 JSON 写出答案。",
                    "hint": "空路径表示根；路径中的 ~0 表示波浪号，~1 表示斜杠；数组从 0 开始计数。",
                    "answer": pretty(answer),
                }],
            }],
        })
        added += 1
        category_counts[category] = category_counts.get(category, 0) + 1
    assert added >= 220, f"Expected 220+ authored scenarios, got {added}"
    assert len({e["id"] for e in examples}) == len(examples)
    assert len({e["code"] for e in examples}) == len(examples)
    audit.update({"newExampleCount": added, "newTutorialCount": added, "categories": category_counts})
    for name, entries in (("tutorials", tutorials), ("examples", examples)):
        audit[f"total{name.title()}"] = len(entries)
    return {
        "tutorials.json": pretty({"schemaVersion": 1, "entries": tutorials}) + "\n",
        "examples.json": pretty({"schemaVersion": 1, "entries": examples}) + "\n",
        "catalog_audit.json": pretty(audit) + "\n",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify checked-in assets without writing")
    args = parser.parse_args()
    documents = build()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, contents in documents.items():
        path = OUTPUT / name
        if args.check:
            assert path.read_text(encoding="utf-8") == contents, f"Stale asset: {path}"
        else:
            path.write_text(contents, encoding="utf-8", newline="\n")
    print(f"{'Verified' if args.check else 'Built'} {len(documents)} offline JSON curriculum assets")


if __name__ == "__main__":
    main()
