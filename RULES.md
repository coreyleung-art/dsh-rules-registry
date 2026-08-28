# 规则账本（完整规则本）

> v1.0.0 | 8 条 | 所有总线设备必须服从

## R001 ✅ 红绿灯互斥协议
- 分类: 协作 | 范围: all-bus-devices | 状态: enforced
- 摘要: 同源操作（同文件/后台/任务）前必须 agent_light 查询 → agent_lock 独占 → 操作完 agent_unlock
- 详情: 红灯=被占用；共享读锁可并行；写锁互斥；不要绕过锁直接操作

## R002 ✅ 通道分级纪律
- 分类: 协作 | 范围: all-bus-devices | 状态: enforced
- 摘要: STATUS/ACK→黑板；TASK→p2p；COLLAB→线程；EVENT→事件总线；BATCH→邮箱
- 详情: 非紧急只发「看黑板 <key>」最短提示（≤200 字目标）；纯确认不回（防刷屏）

## R003 ✅ 黑板消息发送规范
- 分类: 工程 | 范围: all-bus-devices | 状态: enforced
- 摘要: 写黑板消息必须用 python json.dumps 生成 JSON 文件再 curl 发送（--data-binary @file）
- 详情: 禁止 heredoc -d 和 printf（转义坑导致 value 空）；写入后立即回读验证 value 非空

## R004 ✅ central-inbox 注入目标显式配置
- 分类: 工程 | 范围: all-bus-devices | 状态: enforced
- 摘要: 每台设备 central-inbox 必须显式设 CENTRAL_AGENT=<本机中枢会话id>，禁止依赖自动找第一个会话
- 详情: 自动找第一个会话会注入错目标导致双向不通（i9→mac 根因）

## R005 ✅ 永续通讯协议 CCEP
- 分类: 架构 | 范围: all-bus-devices | 状态: enforced
- 摘要: 通道迭代必须用旧通道投递新通道，验证可行才切换；除死机外永续通讯
- 详情: 五步：准备→投递→端侧验证→就绪确认→切换；沙箱先行（任何重启/测试前先沙箱验证）

## R006 ✅ 插件化工具化标准（8 项）
- 分类: 工程 | 范围: all-bus-devices | 状态: enforced
- 摘要: 凡插件化/工具化默认按 8 项：dsh 插件形态/TCC 检测/CLD 自适应/dsh 版本自适应/文档化/版本管理/统一日志/自动落链
- 详情: 新插件/工具必须 8 项全达标才交付

## R007 ✅ 删前考古纪律
- 分类: 数据 | 范围: all-bus-devices | 状态: enforced
- 摘要: 删除/清理共享资源前先跑 pre-delete-archaeology.py 考古评估
- 详情: 三态判定：safe_delete/archive_meta/sediment_first；与 sedimentation 一进一出闭环

## R008 ✅ 规则治理流程
- 分类: 治理 | 范围: all-bus-devices | 状态: enforced
- 摘要: 新规则提交流程：提交→总线审核→裁决评估→吸收→同步泛化所有侧
- 详情: 所有总线设备服从完整规则本（rules-registry/rules.json）；规则变更走账本版本管理
