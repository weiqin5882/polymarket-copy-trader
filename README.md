# 🎯 Polymarket 智能跟单策略

自动发现顶级交易者并跟随其交易，实现"站在巨人肩膀上"盈利。

## 🧠 策略逻辑

```
1. 发现顶级交易者
   ├── 分析交易历史
   ├── 计算胜率、盈亏比
   └── 生成综合评分

2. 实时监控
   ├── 监控目标交易者的每笔交易
   ├── 延迟3秒（避免抢跑）
   └── 评估是否符合跟单条件

3. 智能跟单
   ├── 按比例跟随（如10%）
   ├── 自动风险控制
   └── 记录所有操作

4. 止损止盈
   ├── 15% 自动止损
   ├── 30% 自动止盈
   └── 跟踪交易者平仓信号
```

## 📦 文件结构

```
polymarket-copy-trader/
├── copy_trader.py      # 主程序（跟单执行）
├── analyzer.py         # 分析工具（历史回测）
├── config.json         # 配置文件
├── requirements.txt    # 依赖
└── README.md          # 本文件
```

## 🚀 快速开始

### 方式一：服务器部署（推荐）

```bash
# 一键部署到服务器
curl -fsSL https://raw.githubusercontent.com/weiqin5882/polymarket-copy-trader/master/deploy.sh | sudo bash

# 查看部署指南
cat DEPLOY.md
```

[📖 完整部署指南](DEPLOY.md)

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install requests python-dotenv

# 2. 运行
python copy_trader.py
```

### 2. 配置策略

编辑 `config.json`：

```json
{
  "mode": "analyze",  // 先使用 analyze 模式测试
  "risk": {
    "max_total_exposure": 5000,  // 最多投入5000 USDC
    "max_single_trade": 500,     // 单笔最多500 USDC
    "max_open_positions": 10
  },
  "copy": {
    "follow_delay": 3,           // 延迟3秒跟随
    "default_follow_ratio": 0.1  // 跟随比例10%
  }
}
```

### 3. 运行分析模式（推荐先测试）

```bash
python copy_trader.py
```

输出示例：
```
🔍 正在发现顶级交易者...
  ✅ 0x1234... | 评分: 85.3 | 胜率: 68% | 盈亏: $12,450
  ✅ 0x5678... | 评分: 78.1 | 胜率: 61% | 盈亏: $8,320
  ✅ 0x9abc... | 评分: 72.5 | 胜率: 58% | 盈亏: $5,100

📊 发现 3 位符合条件的顶级交易者

👀 开始监控 3 位交易者...
   检查间隔: 5秒

📢 检测到交易!
   交易者: 0x1234...
   市场: Will Bitcoin reach $100k?
   方向: BUY
   价格: 45%
   数量: 1000
   
   ⏱️ 等待 3秒...
   ✅ 通过所有筛选条件
   🚀 执行跟单:
      市场: Will Bitcoin reach $100k?
      方向: BUY
      价格: 45%
      数量: 100
      金额: $450 USDC
      ✅ 跟单成功! (模拟模式)
```

### 4. 分析历史表现

```bash
python analyzer.py
```

生成报告：
```
============================================================
📊 跟单分析报告
============================================================

总交易次数: 15
胜率: 66.7%
总盈亏: $1,250.50
平均持仓时间: 36.5小时

按交易者表现:
  0x1234... | PnL: $890 | 胜率: 75%
  0x5678... | PnL: $360 | 胜率: 60%

🏆 顶级跟单对象:
  0x1234... | 盈亏: $890 | 胜率: 75.0% | 交易数: 8
  0x5678... | 盈亏: $360 | 胜率: 60.0% | 交易数: 7

⚠️  建议停止跟随:
  (无)
```

## ⚙️ 配置详解

### 发现顶级交易者

```json
"discovery": {
  "enabled": true,           // 自动发现
  "min_score": 70,           // 最小评分70
  "min_win_rate": 0.55,      // 最小胜率55%
  "min_trades": 20,          // 最少20笔交易
  "limit": 10                // 最多跟踪10人
}
```

### 风险控制

| 参数 | 说明 | 建议值 |
|-----|------|-------|
| `max_total_exposure` | 总最大敞口 | 本金的50% |
| `max_single_trade` | 单笔最大金额 | 总资金的10% |
| `max_open_positions` | 最大持仓数 | 5-10 |
| `stop_loss_pct` | 止损比例 | 10-20% |
| `take_profit_pct` | 止盈比例 | 20-50% |

### 跟单设置

| 参数 | 说明 | 建议值 |
|-----|------|-------|
| `follow_delay` | 延迟跟随（秒） | 3-10秒 |
| `follow_ratio` | 跟随比例 | 5-20% |
| `min_market_price` | 最小价格 | 5% |
| `max_market_price` | 最大价格 | 95% |

## 📊 交易者评分算法

```
综合评分 = 胜率×30 + 盈亏×40 + 活跃度×20 + 平均收益×10

各项满分:
- 胜率: 50% → 50分
- 盈亏: $1000 → 40分
- 活跃度: 50笔交易 → 20分
- 平均收益: $10/笔 → 10分
```

## 🎯 筛选逻辑

跟单前会检查以下条件：

1. ✅ 交易者在白名单中
2. ✅ 交易者评分 ≥ 阈值
3. ✅ 市场不在黑名单
4. ✅ 价格在 5%-95% 之间
5. ✅ 未超过最大持仓数
6. ✅ 未超过总敞口限制

## 💡 进阶用法

### 指定跟随特定交易者

编辑 `config.json`：

```json
"follow_traders": [
  {
    "address": "0x1234567890abcdef...",
    "name": "WhaleTrader",
    "follow_ratio": 0.05,    // 只跟5%
    "max_amount": 200        // 最多200 USDC
  }
]
```

### 手动输入交易者地址

修改 `copy_trader.py`：

```python
# 在 main() 函数中
specific_traders = [
    TraderProfile(
        address="0x...",
        name="MyTarget",
        follow_ratio=0.1,
        max_follow_amount=500
    )
]
monitor = TradeMonitor(specific_traders)
```

### 自定义筛选条件

修改 `CopyTrader._should_follow()`：

```python
def _should_follow(self, trade: Trade, profile: TraderProfile) -> bool:
    # 添加自定义条件
    if trade.size < 100:  # 不跟小额交易
        return False
    if "politics" in trade.market_question.lower():  # 不跟政治市场
        return False
    return True
```

## ⚠️ 风险提示

1. **过去表现不代表未来** - 顶级交易者也可能连续亏损
2. **滑点风险** - 延迟跟随可能导致价格变化
3. **流动性风险** - 小市场可能无法成交
4. **策略失效风险** - 当太多人跟单时，策略可能失效
5. **黑天鹅事件** - 极端市场情况下可能全军覆没

## 📈 预期表现

基于回测（假设）：

| 指标 | 预期值 |
|-----|-------|
| 胜率 | 55-65% |
| 盈亏比 | 1.3:1 |
| 月收益率 | 3-8% |
| 最大回撤 | <25% |

## 🔧 实际交易接入

当前程序是**模拟模式**，如需实际交易：

1. 安装 Polymarket SDK：
```bash
pip install py-clob-client
```

2. 配置 API 凭证（`.env`）：
```
POLY_PRIVATE_KEY=0x...
POLY_API_KEY=...
POLY_API_SECRET=...
POLY_API_PASSPHRASE=...
```

3. 修改 `CopyTrader._execute_copy_trade()`：
```python
from py_clob_client.client import ClobClient

# 初始化客户端
client = ClobClient(
    host="https://clob.polymarket.com",
    key=os.getenv("POLY_PRIVATE_KEY"),
    chain_id=137,
    creds=api_creds
)

# 实际下单
order = client.create_and_post_order(...)
```

## 📚 相关资源

- [Polymarket Data API](https://docs.polymarket.com)
- [Leaderboard API](https://data-api.polymarket.com/leaderboard)
- [Trades API](https://data-api.polymarket.com/trades)

---

*跟单策略适合不想自己分析市场、只想跟随成功交易者的用户。请务必先用模拟模式测试！*
