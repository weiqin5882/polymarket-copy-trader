#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polymarket 智能跟单策略
自动跟随顶级交易者的操作
"""

import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TraderProfile:
    """被跟随交易者档案"""
    address: str
    name: str = ""
    
    # 历史表现
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss: float = 0.0
    avg_return: float = 0.0
    
    # 风险控制
    max_position_size: float = 0.0  # 该交易者的最大单笔仓位
    avg_holding_time: float = 0.0   # 平均持仓时间（小时）
    
    # 评分
    score: float = 0.0  # 综合评分 0-100
    
    # 跟随配置
    follow_ratio: float = 0.1  # 跟随比例（0.1 = 对方买100，你跟10）
    max_follow_amount: float = 1000  # 最大跟随金额（USDC）
    enabled: bool = True


@dataclass
class Trade:
    """交易记录"""
    trader_address: str
    market_id: str
    token_id: str
    side: str  # BUY or SELL
    price: float
    size: float
    timestamp: datetime
    transaction_hash: str = ""
    
    # 市场信息
    market_question: str = ""


@dataclass
class CopyTradeConfig:
    """跟单配置"""
    # 风险控制
    max_total_exposure: float = 5000  # 总最大敞口（USDC）
    max_single_trade: float = 500     # 单笔最大跟随金额
    max_open_positions: int = 10      # 最大同时持仓数
    
    # 跟单延迟（秒）
    follow_delay: float = 3.0  # 检测到交易后等待3秒再跟
    
    # 筛选条件
    min_trader_score: float = 70.0      # 最小交易者评分
    min_trader_win_rate: float = 0.55   # 最小胜率 55%
    min_trader_trades: int = 20         # 最小交易次数
    
    # 不跟的市场类型
    excluded_markets: List[str] = field(default_factory=list)  # 市场关键词黑名单
    max_market_price: float = 0.95      # 不跟价格 >95% 的市场（几乎确定）
    min_market_price: float = 0.05      # 不跟价格 <5% 的市场（几乎不可能）
    
    # 止损设置
    stop_loss_pct: float = 0.15  # 15% 止损
    take_profit_pct: float = 0.30  # 30% 止盈


class TraderAnalyzer:
    """交易者分析器"""
    
    def __init__(self):
        self.api_base = "https://data-api.polymarket.com"
    
    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        """获取交易排行榜"""
        try:
            response = requests.get(
                f"{self.api_base}/leaderboard",
                params={"limit": limit, "timeframe": "30d"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"获取排行榜失败: {e}")
        return []
    
    def analyze_trader(self, address: str) -> Optional[TraderProfile]:
        """分析单个交易者的历史表现"""
        try:
            # 获取交易历史
            trades_response = requests.get(
                f"{self.api_base}/trades",
                params={"user": address, "limit": 100},
                timeout=10
            )
            
            if trades_response.status_code != 200:
                return None
            
            trades_data = trades_response.json()
            
            if not trades_data or len(trades_data) < 5:
                return None  # 交易次数太少
            
            # 计算指标
            total_trades = len(trades_data)
            winning_trades = sum(1 for t in trades_data if t.get('profit', 0) > 0)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_pnl = sum(t.get('profit', 0) for t in trades_data)
            avg_return = total_pnl / total_trades if total_trades > 0 else 0
            
            # 计算最大仓位
            position_sizes = [t.get('size', 0) * t.get('price', 0) for t in trades_data]
            max_position = max(position_sizes) if position_sizes else 0
            
            # 计算评分 (0-100)
            score = self._calculate_score(win_rate, total_pnl, total_trades, avg_return)
            
            return TraderProfile(
                address=address,
                total_trades=total_trades,
                win_rate=win_rate,
                profit_loss=total_pnl,
                avg_return=avg_return,
                max_position_size=max_position,
                score=score
            )
            
        except Exception as e:
            print(f"分析交易者 {address} 失败: {e}")
            return None
    
    def _calculate_score(self, win_rate: float, pnl: float, trades: int, avg_return: float) -> float:
        """计算交易者综合评分"""
        # 胜率权重 30%
        win_rate_score = min(win_rate * 100, 50) * 0.3
        
        # 盈亏权重 40%
        pnl_score = min(max(pnl / 1000, 0), 40) * 0.4  # 假设1000USDC为满分
        
        # 活跃度权重 20%
        activity_score = min(trades / 50, 20) * 0.2  # 50笔交易为满分
        
        # 平均收益权重 10%
        avg_return_score = min(max(avg_return / 10, 0), 10) * 0.1
        
        return win_rate_score + pnl_score + activity_score + avg_return_score
    
    def discover_top_traders(self, min_score: float = 70.0, limit: int = 20) -> List[TraderProfile]:
        """发现顶级交易者"""
        print("🔍 正在发现顶级交易者...")
        
        # 获取排行榜
        leaderboard = self.get_leaderboard(limit=limit * 2)
        
        top_traders = []
        for entry in leaderboard:
            address = entry.get('address')
            if not address:
                continue
            
            # 分析交易者
            profile = self.analyze_trader(address)
            
            if profile and profile.score >= min_score:
                top_traders.append(profile)
                print(f"  ✅ {address[:15]}... | 评分: {profile.score:.1f} | "
                      f"胜率: {profile.win_rate:.1%} | 盈亏: ${profile.profit_loss:.0f}")
        
        # 按评分排序
        top_traders.sort(key=lambda x: x.score, reverse=True)
        
        print(f"\n📊 发现 {len(top_traders)} 位符合条件的顶级交易者")
        return top_traders[:limit]


class TradeMonitor:
    """交易监控器"""
    
    def __init__(self, traders: List[TraderProfile]):
        self.traders = {t.address: t for t in traders}
        self.last_trade_times: Dict[str, datetime] = {}
        self.api_base = "https://data-api.polymarket.com"
    
    def get_recent_trades(self, trader_address: str, since: datetime) -> List[Trade]:
        """获取交易者的最新交易"""
        trades = []
        
        try:
            response = requests.get(
                f"{self.api_base}/trades",
                params={
                    "user": trader_address,
                    "limit": 10,
                    "after": since.isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for t in data:
                    trade = Trade(
                        trader_address=trader_address,
                        market_id=t.get('marketId', ''),
                        token_id=t.get('tokenId', ''),
                        side="BUY" if t.get('side') == 0 else "SELL",
                        price=float(t.get('price', 0)),
                        size=float(t.get('size', 0)),
                        timestamp=datetime.fromisoformat(t.get('timestamp', '').replace('Z', '+00:00')),
                        transaction_hash=t.get('transactionHash', ''),
                        market_question=t.get('marketQuestion', '')
                    )
                    trades.append(trade)
                    
        except Exception as e:
            print(f"获取 {trader_address} 的交易失败: {e}")
        
        return trades
    
    async def monitor_loop(self, callback, interval: float = 5.0):
        """监控循环"""
        print(f"\n👀 开始监控 {len(self.traders)} 位交易者...")
        print(f"   检查间隔: {interval}秒")
        
        # 初始化最后检查时间
        for addr in self.traders:
            self.last_trade_times[addr] = datetime.now() - timedelta(minutes=5)
        
        while True:
            for address, profile in self.traders.items():
                if not profile.enabled:
                    continue
                
                # 获取新交易
                since = self.last_trade_times[address]
                trades = self.get_recent_trades(address, since)
                
                for trade in trades:
                    print(f"\n📢 检测到交易!")
                    print(f"   交易者: {address[:15]}...")
                    print(f"   市场: {trade.market_question[:50]}")
                    print(f"   方向: {trade.side}")
                    print(f"   价格: {trade.price:.2%}")
                    print(f"   数量: {trade.size}")
                    
                    # 调用回调处理
                    await callback(trade, profile)
                
                if trades:
                    self.last_trade_times[address] = datetime.now()
            
            await asyncio.sleep(interval)


class CopyTrader:
    """跟单执行器"""
    
    def __init__(self, config: CopyTradeConfig):
        self.config = config
        self.positions: Dict[str, Dict] = {}  # 当前持仓
        self.trade_history: List[Dict] = []
        
        # 初始化 Polymarket 客户端（如果需要实际交易）
        self.client = None  # 这里应该初始化 ClobClient
    
    async def on_new_trade(self, trade: Trade, profile: TraderProfile):
        """处理新交易信号"""
        
        # 1. 检查筛选条件
        if not self._should_follow(trade, profile):
            return
        
        # 2. 等待延迟（避免抢跑）
        print(f"   ⏱️ 等待 {self.config.follow_delay}秒...")
        await asyncio.sleep(self.config.follow_delay)
        
        # 3. 计算跟单参数
        follow_size = self._calculate_follow_size(trade, profile)
        
        if follow_size <= 0:
            print("   ❌ 计算后的跟单数量为0，跳过")
            return
        
        # 4. 检查风险控制
        if not self._check_risk_limits(trade, follow_size):
            return
        
        # 5. 执行跟单
        await self._execute_copy_trade(trade, follow_size, profile)
    
    def _should_follow(self, trade: Trade, profile: TraderProfile) -> bool:
        """检查是否应该跟随这笔交易"""
        
        # 检查价格范围
        if trade.price > self.config.max_market_price:
            print(f"   ⚠️ 价格 {trade.price:.2%} 超过上限，不跟")
            return False
        
        if trade.price < self.config.min_market_price:
            print(f"   ⚠️ 价格 {trade.price:.2%} 低于下限，不跟")
            return False
        
        # 检查市场黑名单
        market_lower = trade.market_question.lower()
        for keyword in self.config.excluded_markets:
            if keyword.lower() in market_lower:
                print(f"   ⚠️ 市场在黑名单中 ({keyword})，不跟")
                return False
        
        # 检查交易者条件
        if profile.score < self.config.min_trader_score:
            print(f"   ⚠️ 交易者评分 {profile.score:.1f} 过低，不跟")
            return False
        
        if profile.win_rate < self.config.min_trader_win_rate:
            print(f"   ⚠️ 交易者胜率 {profile.win_rate:.1%} 过低，不跟")
            return False
        
        return True
    
    def _calculate_follow_size(self, trade: Trade, profile: TraderProfile) -> float:
        """计算跟单数量"""
        # 原始交易金额
        original_amount = trade.price * trade.size
        
        # 按比例跟随
        follow_amount = original_amount * profile.follow_ratio
        
        # 限制最大金额
        follow_amount = min(follow_amount, profile.max_follow_amount)
        follow_amount = min(follow_amount, self.config.max_single_trade)
        
        # 计算数量
        follow_size = follow_amount / trade.price if trade.price > 0 else 0
        
        return follow_size
    
    def _check_risk_limits(self, trade: Trade, follow_size: float) -> bool:
        """检查风险限制"""
        
        # 检查持仓数量
        if len(self.positions) >= self.config.max_open_positions:
            print(f"   ⚠️ 已达到最大持仓数 {self.config.max_open_positions}，不跟")
            return False
        
        # 检查总敞口
        total_exposure = sum(p['amount'] for p in self.positions.values())
        follow_amount = trade.price * follow_size
        
        if total_exposure + follow_amount > self.config.max_total_exposure:
            print(f"   ⚠️ 总敞口将超过限制，不跟")
            return False
        
        # 检查是否已在该市场有持仓
        if trade.market_id in self.positions:
            print(f"   ⚠️ 已在该市场有持仓，不跟")
            return False
        
        return True
    
    async def _execute_copy_trade(self, trade: Trade, follow_size: float, profile: TraderProfile):
        """执行跟单交易"""
        
        follow_amount = trade.price * follow_size
        
        print(f"\n🚀 执行跟单:")
        print(f"   市场: {trade.market_question[:50]}")
        print(f"   方向: {trade.side}")
        print(f"   价格: {trade.price:.2%}")
        print(f"   数量: {follow_size:.2f}")
        print(f"   金额: ${follow_amount:.2f} USDC")
        print(f"   跟随交易者: {profile.address[:15]}...")
        
        # 这里应该调用实际的交易 API
        # 示例：
        # order = self.client.create_and_post_order(...)
        
        # 记录持仓
        self.positions[trade.market_id] = {
            'token_id': trade.token_id,
            'side': trade.side,
            'entry_price': trade.price,
            'size': follow_size,
            'amount': follow_amount,
            'trader': profile.address,
            'timestamp': datetime.now()
        }
        
        # 记录历史
        self.trade_history.append({
            'type': 'COPY',
            'original_trade': trade,
            'follow_size': follow_size,
            'follow_amount': follow_amount,
            'timestamp': datetime.now()
        })
        
        print(f"   ✅ 跟单成功! (模拟模式)")
    
    def check_positions(self):
        """检查持仓，执行止损止盈"""
        # 获取当前价格
        # 检查是否达到止损/止盈条件
        # 如果达到，平仓
        pass
    
    def get_stats(self) -> Dict:
        """获取跟单统计"""
        return {
            'total_trades': len(self.trade_history),
            'open_positions': len(self.positions),
            'total_exposure': sum(p['amount'] for p in self.positions.values()),
            'positions': self.positions
        }


async def main():
    """主程序"""
    print("=" * 60)
    print("🎯 Polymarket 智能跟单系统")
    print("=" * 60)
    
    # 1. 配置
    config = CopyTradeConfig(
        max_total_exposure=5000,
        max_single_trade=500,
        follow_delay=3.0,
        min_trader_score=70.0,
        excluded_markets=['test', 'demo']  # 排除测试市场
    )
    
    # 2. 发现顶级交易者
    analyzer = TraderAnalyzer()
    top_traders = analyzer.discover_top_traders(min_score=70.0, limit=10)
    
    if not top_traders:
        print("❌ 未发现符合条件的交易者")
        return
    
    # 3. 设置跟随比例
    for i, trader in enumerate(top_traders):
        trader.follow_ratio = 0.1  # 10% 跟随
        trader.max_follow_amount = 500
        trader.name = f"TopTrader_{i+1}"
    
    # 4. 创建监控器和跟单器
    monitor = TradeMonitor(top_traders)
    copy_trader = CopyTrader(config)
    
    # 5. 启动监控循环
    try:
        await monitor.monitor_loop(
            callback=copy_trader.on_new_trade,
            interval=5.0
        )
    except KeyboardInterrupt:
        print("\n\n👋 停止跟单")
        
        # 输出统计
        stats = copy_trader.get_stats()
        print(f"\n📊 跟单统计:")
        print(f"   总跟单次数: {stats['total_trades']}")
        print(f"   当前持仓: {stats['open_positions']}")
        print(f"   总敞口: ${stats['total_exposure']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
