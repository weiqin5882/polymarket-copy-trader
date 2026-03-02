#!/bin/bash
# Polymarket 跟单策略 - 服务器部署脚本
# 支持 Ubuntu/Debian/CentOS

set -e

echo "🚀 Polymarket 跟单策略 - 服务器部署"
echo "======================================"

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 sudo 运行"
    exit 1
fi

# 获取项目目录
PROJECT_DIR="/opt/polymarket-copy-trader"
SERVICE_NAME="polymarket-copy-trader"
USER="polymarket"

echo ""
echo "📋 部署配置:"
echo "  项目目录: $PROJECT_DIR"
echo "  服务名: $SERVICE_NAME"
echo "  运行用户: $USER"
echo ""

# 1. 安装依赖
echo "📦 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv git curl
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip git curl
elif command -v dnf &> /dev/null; then
    dnf install -y python3 python3-pip git curl
else
    echo "❌ 不支持的系统"
    exit 1
fi

echo "✅ 系统依赖安装完成"

# 2. 创建用户
echo ""
echo "👤 创建运行用户..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$PROJECT_DIR" "$USER"
    echo "✅ 用户 $USER 已创建"
else
    echo "✅ 用户 $USER 已存在"
fi

# 3. 克隆代码
echo ""
echo "📥 下载项目代码..."
if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  目录已存在，更新代码..."
    cd "$PROJECT_DIR"
    git pull
else
    git clone https://github.com/weiqin5882/polymarket-copy-trader.git "$PROJECT_DIR"
    chown -R "$USER:$USER" "$PROJECT_DIR"
fi
echo "✅ 代码下载完成"

# 4. 创建虚拟环境
echo ""
echo "🐍 创建 Python 虚拟环境..."
cd "$PROJECT_DIR"
sudo -u "$USER" python3 -m venv venv
sudo -u "$USER" venv/bin/pip install -q --upgrade pip
sudo -u "$USER" venv/bin/pip install -q -r requirements.txt
echo "✅ 虚拟环境创建完成"

# 5. 创建配置目录
echo ""
echo "⚙️  创建配置..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"
chown -R "$USER:$USER" "$PROJECT_DIR/logs"
chown -R "$USER:$USER" "$PROJECT_DIR/data"

# 6. 创建环境变量文件
echo ""
echo "🔐 配置环境变量..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Polymarket API 配置（如需实际交易）
# POLY_PRIVATE_KEY=0x...
# POLY_API_KEY=...
# POLY_API_SECRET=...
# POLY_API_PASSPHRASE=...

# 通知配置（可选）
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
# DISCORD_WEBHOOK=...

# 日志级别
LOG_LEVEL=INFO
EOF
    chown "$USER:$USER" "$PROJECT_DIR/.env"
    echo "✅ 环境变量文件已创建: $PROJECT_DIR/.env"
    echo "⚠️  请编辑该文件，填入你的 API 凭证"
else
    echo "✅ 环境变量文件已存在"
fi

# 7. 复制配置文件
echo ""
if [ ! -f "$PROJECT_DIR/config.json" ]; then
    sudo -u "$USER" cp "$PROJECT_DIR/config.json.example" "$PROJECT_DIR/config.json" 2>/dev/null || \
    sudo -u "$USER" cp "$PROJECT_DIR/config.json" "$PROJECT_DIR/config.json"
    echo "✅ 配置文件已创建"
fi

# 8. 创建 systemd 服务
echo ""
echo "🔧 创建系统服务..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Polymarket Copy Trader
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/copy_trader.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/output.log
StandardError=append:$PROJECT_DIR/logs/error.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR/logs $PROJECT_DIR/data

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ 系统服务已创建"

# 9. 创建日志轮转
echo ""
echo "📝 配置日志轮转..."
cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
$PROJECT_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
echo "✅ 日志轮转已配置"

# 10. 创建监控脚本
echo ""
echo "📊 创建监控脚本..."
cat > "$PROJECT_DIR/check_status.sh" << 'EOF'
#!/bin/bash
# 状态检查脚本

SERVICE="polymarket-copy-trader"
PROJECT_DIR="/opt/polymarket-copy-trader"

echo "================================"
echo "📊 Polymarket 跟单策略状态"
echo "================================"
echo ""

# 检查服务状态
echo "🔧 服务状态:"
systemctl is-active $SERVICE > /dev/null 2>&1 && echo "  ✅ 运行中" || echo "  ❌ 未运行"
systemctl is-enabled $SERVICE > /dev/null 2>&1 && echo "  ✅ 已启用开机启动" || echo "  ❌ 未启用"
echo ""

# 检查进程
echo "🖥️  进程信息:"
pgrep -f "python.*copy_trader" > /dev/null && echo "  ✅ 进程存在" || echo "  ❌ 进程不存在"
echo ""

# 检查日志
echo "📜 最新日志 (最近10行):"
if [ -f "$PROJECT_DIR/logs/output.log" ]; then
    tail -n 10 "$PROJECT_DIR/logs/output.log"
else
    echo "  暂无日志"
fi
echo ""

# 检查磁盘空间
echo "💾 磁盘空间:"
df -h "$PROJECT_DIR" | tail -1 | awk '{print "  已用: "$5 " 可用: "$4}'
echo ""

# 检查内存使用
echo "🧠 内存使用:"
free -h | grep "Mem:" | awk '{print "  已用: "$3 " 总共: "$2}'
echo ""

echo "================================"
echo "使用命令:"
echo "  启动: sudo systemctl start $SERVICE"
echo "  停止: sudo systemctl stop $SERVICE"
echo "  重启: sudo systemctl restart $SERVICE"
echo "  查看日志: sudo tail -f $PROJECT_DIR/logs/output.log"
echo "================================"
EOF

chmod +x "$PROJECT_DIR/check_status.sh"
echo "✅ 监控脚本已创建"

# 11. 创建启动脚本
echo ""
echo "🚀 创建快捷脚本..."
cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
sudo systemctl start polymarket-copy-trader
echo "✅ 服务已启动"
echo "查看日志: sudo tail -f /opt/polymarket-copy-trader/logs/output.log"
EOF

cat > "$PROJECT_DIR/stop.sh" << 'EOF'
#!/bin/bash
sudo systemctl stop polymarket-copy-trader
echo "✅ 服务已停止"
EOF

cat > "$PROJECT_DIR/restart.sh" << 'EOF'
#!/bin/bash
sudo systemctl restart polymarket-copy-trader
echo "✅ 服务已重启"
EOF

cat > "$PROJECT_DIR/logs.sh" << 'EOF'
#!/bin/bash
sudo tail -f /opt/polymarket-copy-trader/logs/output.log
EOF

chmod +x "$PROJECT_DIR"/*.sh
chown "$USER:$USER" "$PROJECT_DIR"/*.sh

# 12. 完成提示
echo ""
echo "======================================"
echo "✅ 部署完成！"
echo "======================================"
echo ""
echo "📁 项目位置: $PROJECT_DIR"
echo ""
echo "🚀 启动服务:"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "📊 查看状态:"
echo "  sudo $PROJECT_DIR/check_status.sh"
echo ""
echo "📜 查看日志:"
echo "  sudo tail -f $PROJECT_DIR/logs/output.log"
echo ""
echo "⚙️  配置文件:"
echo "  $PROJECT_DIR/config.json"
echo "  $PROJECT_DIR/.env"
echo ""
echo "🔧 快捷命令:"
echo "  $PROJECT_DIR/start.sh    # 启动"
echo "  $PROJECT_DIR/stop.sh     # 停止"
echo "  $PROJECT_DIR/restart.sh  # 重启"
echo "  $PROJECT_DIR/logs.sh     # 查看日志"
echo ""
echo "⚠️  重要提醒:"
echo "  1. 请先编辑 config.json 配置参数"
echo "  2. 如需实际交易，请编辑 .env 填入 API 凭证"
echo "  3. 建议先用 analyze 模式测试几天"
echo "  4. 使用 'sudo systemctl enable $SERVICE_NAME' 设置开机启动"
echo ""
echo "======================================"
