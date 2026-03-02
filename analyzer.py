#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跟单分析工具
分析历史跟单表现，优化跟随策略
"""

import json
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class CopyTradeResult:
    """跟单结果"""
    original_trader: str
    market_id: str
    market_question: str
    entry_price: float
    exit_price: float
    size: float
    side: str
    pnl: float
    pnl_pct: float
    holding_time_hours: float
    followed_at: datetime


class CopyTradeAnalyzer:
    """跟单分析器"""
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file
        self.trades: List[CopyTradeResult] = []
    
    def add_trade(self, trade: CopyTradeResult):
        """添加交易记录"""
        self.trades.append(trade)
    
    def analyze_by_trader(self) -> Dict:
        """按交易者分析表现"""
        trader_stats = {}
        
        for trade in self.trades:
            addr = trade.original_trader
            if addr not in trader_stats:
                trader_stats[addr] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0,
                    'avg_holding_time': 0
                }
            
            stats = trader_stats[addr]
            stats['total_trades'] += 1
            if trade.pnl > 0:
                stats['winning_trades'] += 1
            stats['total_pnl'] += trade.pnl
            stats['avg_holding_time'] += trade.holding_time_hours
        
        # 计算平均值
        for addr, stats in trader_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['winning_trades'] / stats['total_trades']
                stats['avg_holding_time'] /= stats['total_trades']
        
        return trader_stats
    
    def analyze_by_market_type(self) -> Dict:
        """按市场类型分析"""
        # 可以根据市场关键词分类
        pass
    
    def get_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        trader_stats = self.analyze_by_trader()
        
        # 识别表现最好的交易者
        sorted_traders = sorted(
            trader_stats.items(),
            key=lambda x: x[1]['total_pnl'],
            reverse=True
        )
        
        print("\n🏆 顶级跟单对象:")
        for addr, stats in sorted_traders[:5]:
            print(f"  {addr[:15]}... | "
                  f"盈亏: ${stats['total_pnl']:.0f} | "
                  f"胜率: {stats['win_rate']:.1%} | "
                  f"交易数: {stats['total_trades']}")
        
        # 识别表现差的交易者
        poor_performers = [
            (addr, stats) for addr, stats in trader_stats.items()
            if stats['total_pnl'] < 0
        ]
        
        if poor_performers:
            print("\n⚠️  建议停止跟随:")
            for addr, stats in poor_performers:
                print(f"  {addr[:15]}... | 亏损: ${stats['total_pnl']:.0f}")
        
        return recommendations
    
    def generate_report(self) -> str:
        """生成完整报告"""
        if not self.trades:
            return "暂无交易记录"
        
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        total_pnl = sum(t.pnl for t in self.trades)
        avg_holding = sum(t.holding_time_hours for t in self.trades) / total_trades
        
        report = f"""
{'='*60}
📊 跟单分析报告
{'='*60}

总交易次数: {total_trades}
胜率: {winning_trades/total_trades:.1%}
总盈亏: ${total_pnl:.2f}
平均持仓时间: {avg_holding:.1f}小时

按交易者表现:
"""
        
        trader_stats = self.analyze_by_trader()
        for addr, stats in sorted(trader_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
            report += f"  {addr[:20]}... | PnL: ${stats['total_pnl']:.0f} | 胜率: {stats['win_rate']:.1%}\n"
        
        return report
    
    def save_to_file(self, filepath: str):
        """保存分析结果"""
        data = {
            'trades': [
                {
                    'original_trader': t.original_trader,
                    'market_id': t.market_id,
                    'market_question': t.market_question,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'size': t.size,
                    'side': t.side,
                    'pnl': t.pnl,
                    'pnl_pct': t.pnl_pct,
                    'holding_time_hours': t.holding_time_hours,
                    'followed_at': t.followed_at.isoformat()
                }
                for t in self.trades
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 交易历史已保存到 {filepath}")


def analyze_demo():
    """分析演示"""
    analyzer = CopyTradeAnalyzer()
    
    # 模拟一些交易记录
    demo_trades = [
        CopyTradeResult(
            original_trader="0x1234...",
            market_id="market1",
            market_question="BTC > 100k?",
            entry_price=0.45,
            exit_price=0.62,
            size=100,
            side="BUY",
            pnl=170,
            pnl_pct=0.378,
            holding_time_hours=48,
            followed_at=datetime.now()
        ),
        CopyTradeResult(
            original_trader="0x1234...",
            market_id="market2",
            market_question="Election winner?",
            entry_price=0.55,
            exit_price=0.48,
            size=100,
            side="BUY",
            pnl=-70,
            pnl_pct=-0.127,
            holding_time_hours=24,
            followed_at=datetime.now()
        ),
        CopyTradeResult(
            original_trader="0x5678...",
            market_id="market3",
            market_question="Fed rate cut?",
            entry_price=0.30,
            exit_price=0.45,
            size=150,
            side="BUY",
            pnl=225,
            pnl_pct=0.50,
            holding_time_hours=72,
            followed_at=datetime.now()
        )
    ]
    
    for trade in demo_trades:
        analyzer.add_trade(trade)
    
    # 生成报告
    print(analyzer.generate_report())
    
    # 获取建议
    analyzer.get_recommendations()


if __name__ == "__main__":
    analyze_demo()
