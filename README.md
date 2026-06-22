# astrbot_plugin_share_forward

> 自动识别群聊/私聊里发出的 **抖音 / 哔哩哔哩 / 小红书** 分享链接，
> 解析其内容（标题、作者、正文、视频、图集、高赞评论），并打包成一条
> **QQ 合并转发** 消息发送回去。

## ✨ 功能特性

- 支持平台：
  - 抖音（`v.douyin.com` / `iesdouyin.com` / `douyin.com`）
    - 视频（含无水印直链）
    - 图集（多张图片）
    - 纯文字动态
    - 高赞评论 Top 3（需配置 Cookie）
  - 哔哩哔哩 B 站（`b23.tv` / `bilibili.com/video/BVxxx`）
    - 视频标题、UP 主、封面、简介
    - 原视频流（优先音视频合一 `durl`，失败兜底 `dash.video`）
    - 高赞评论 Top 3（匿名可获取）
  - 小红书（`xhslink.com` / `xiaohongshu.com/explore/...`）
    - 图文、视频笔记
    - 高赞评论 Top 3
- 合并转发节点可自定义：
  - 标题 + 作者 + 平台标签
  - 封面图 / 图集
  - 视频文件直发（受 QQ 文件大小限制）
  - 原始链接 + 无水印直链
  - 高赞评论 Top 3
  - 正文/动态描述
- 仅 QQ 平台（`aiocqhttp`）使用合并转发，其他平台自动降级为多条普通消息。
- 支持 QQ 卡片消息解析：如果分享链接被平台包装成 JSON 卡片，也会尝试从卡片中提取真实链接。
- 默认识别到可解析链接后先发送 `解析bot为您服务 ٩( 'ω' )و`，便于判断插件是否触发。
- 合并转发默认按内容分类展示：📌解析信息、📝正文内容、🖼️图片内容、🎬视频内容、💬热门评论、🔗链接信息。
- 支持同链接防抖、解析重试、代理、群/会话白名单、私聊开关。
- 支持视频发送模式：
  - `direct_url`：直接把视频直链交给 QQ 协议端发送，速度快
  - `download`：先下载到本地再发送，兼容性更强但更慢
  - `off`：不发送视频文件，只保留直链
- B 站视频默认不放入伪造合并转发的视频节点，只保留视频直链，避免 NapCat 拉取 `bilivideo.com` 视频失败导致整条合并转发发送失败。
- `v1.0.2` 修复抖音分享页不返回旧 `_ROUTER_DATA` 时的解析失败问题，增加移动端 UA、括号配平提取、`douyin.com/video/{id}` 页面兜底和旧 `iteminfo` 接口兜底。
- `v1.0.3` 参考 `drdon1234/astrbot_plugin_douyin_bot` 的可用路径：短链优先 `HEAD` 跟随、宽松提取数字 ID、优先从 `loaderData -> videoInfoRes -> item_list[0]` 解析抖音内容，并补充触发提示消息。
- `v1.0.4` 新增合并转发分组模式，默认按内容分类插入标题节点；同时去掉解析信息里的平台标签，只保留内容类型、标题、作者。
- `v1.0.5` 去掉解析信息里的“类型”字段，并为分类标题、标题、作者、点赞、链接等信息加入轻量 emoji，让合并转发更清晰。
- `v1.0.6` 精简热门评论格式：去掉用户名、点赞数和数字序号，改用 🥇🥈🥉 奖牌展示前三条评论。
- `v1.0.7` 修复 B 站原视频不出现的问题，新增 `x/player/playurl` 播放流获取逻辑。
- `v1.0.8` 修复 NapCat 发送 B 站视频合并转发时报 `handleOb11FileLikeMessage terminated` 的问题：默认不把 B站 CDN 视频 URL 放进伪造合并转发视频节点，只在链接信息里保留视频直链。

## 🔧 安装

把本目录放进 `AstrBot/data/plugins/`，然后在 WebUI 的「插件管理」里点击重载即可。

## ⚙️ 配置项

打开 WebUI → 插件管理 → 找到 `astrbot_plugin_share_forward` → 配置：

| 配置 | 说明 |
| --- | --- |
| `enabled` | 总开关 |
| `notify_when_triggered` | 识别到可解析链接后先发送触发提示 |
| `forward_grouping_mode` | 合并转发分组模式：`sectioned` 分类模式 / `flat` 旧版平铺模式 |
| `platforms` | 启用哪些平台（抖音 / B 站 / 小红书） |
| `forward_content` | 合并转发节点包含哪些内容 |
| `use_forward_message` | 是否使用 QQ 合并转发，不稳定时可关闭 |
| `video_send_mode` | 视频发送模式：`direct_url` / `download` / `off` |
| `skip_bilibili_video_in_forward` | B 站视频默认不放入合并转发视频节点，避免 NapCat 拉流失败 |
| `video_max_size_mb` | 视频文件直发的最大体积（MB） |
| `max_images_per_forward` | 图集最多发送图片数量 |
| `request_timeout` | 单次请求超时（秒） |
| `retry_count` | 解析失败重试次数 |
| `debounce_interval` | 同一会话内同链接防抖秒数 |
| `proxy` | 请求代理地址 |
| `enable_in_private` | 是否允许私聊触发 |
| `group_whitelist` | 群号白名单，留空表示不限 |
| `id_whitelist` | 统一会话白名单，适合精确限制触发范围 |
| `douyin_cookie` | 抖音 Cookie（拉取评论用，可选） |
| `xiaohongshu_cookie` | 小红书 Cookie（**必填**，至少含 `a1=...`） |
| `stop_event_after_match` | 命中后阻断后续 LLM 处理 |
| `reply_when_fail` | 解析失败时给用户反馈 |
| `debug_log` | 调试日志 |

### Cookie 怎么获取

1. 浏览器登录对应平台
2. F12 → Application / 应用 → Cookies → 选中域名
3. 复制完整 Cookie 字符串（格式：`key1=value1; key2=value2; ...`）
4. 粘贴到对应配置项

## 🧩 工作原理

1. 监听所有消息（`@filter.regex`，无需 at 机器人即可触发）
2. 从纯文本和 QQ JSON 卡片中提取出可能的 URL
3. 先检查白名单、私聊开关、同链接防抖
4. 依次让各平台解析器判定能否处理，并按配置做失败重试
5. 解析器返回 `ParsedItem`（含标题/作者/视频/图集/评论等）
6. 主流程根据配置组装合并转发的 `Node` 列表
7. 通过 `event.chain_result([Comp.Nodes(...)])` 发出，或降级为普通消息

## 🧪 参考与取舍

开发时参考了 AstrBot 插件市场中同类解析插件的工程设计，例如：

- `astrbot_plugin_link_resolver`：吸收了平台独立配置、重试、防抖、错误处理、合并转发开关等思路。
- `astrbot_plugin_parser`：吸收了卡片消息解析、白名单/黑名单、同会话防抖、多解析器注册等思路。
- `douyin_bot`：吸收了 `iesdouyin.com/share/video/{id}` + `_ROUTER_DATA` 的轻量解析路径。

没有照搬的部分：

- 不依赖第三方解析 API，避免接口失效或隐私问题。
- 不把天气、热搜等无关功能塞进同一个插件。
- 不使用 `template_list` 做复杂平台配置，避免 AstrBot 4.25.2 WebUI 的兼容性坑。
- 不在 Node 内嵌套 Node，图集统一按“一张图片一个节点”发送，兼容性更稳。

## ⚠️ 风险与限制

- 三大平台的反爬策略时常变化，本插件采用尽量"无签名/弱签名"的解析路径，
  **可能在风控更新后失效**，请关注仓库 issues。
- 抖音评论需要 Cookie；不带 Cookie 时仅返回视频/图集/正文。
- 小红书必须配置 Cookie，否则会被风控直接拒绝。
- 视频文件直发受 QQ Bot 协议端文件大小限制（NapCat / Lagrange 一般 ≤100MB）。

## 📜 License

MIT
