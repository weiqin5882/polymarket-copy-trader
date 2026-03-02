# 🚀 服务器部署指南

将 Polymarket 跟单策略部署到服务器，实现 24/7 自动运行。

## 📋 系统要求

| 配置 | 最低要求 | 推荐 |
|-----|---------|-----|
| CPU | 1核 | 2核 |
| 内存 | 512MB | 1GB |
| 磁盘 | 5GB | 10GB |
| 系统 | Ubuntu 20.04+ / CentOS 8+ | Ubuntu 22.04 LTS |
| 网络 | 稳定连接 | 推荐海外服务器 |

## 🛠️ 部署方式

### 方式一：一键脚本部署（推荐）

```bash
# 1. 登录你的服务器
ssh root@your-server-ip

# 2. 下载部署脚本
curl -fsSL https://raw.githubusercontent.com/weiqin5882/polymarket-copy-trader/master/deploy.sh -o deploy.sh

# 3. 运行部署脚本
chmod +x deploy.sh
sudo ./deploy.sh

# 4. 编辑配置
nano /opt/polymarket-copy-trader/config.json
nano /opt/polymarket-copy-trader/.env

# 5. 启动服务
sudo systemctl start polymarket-copy-trader

# 6. 查看日志
sudo tail -f /opt/polymarket-copy-trader/logs/output.log
```

### 方式二：手动部署

```bash
# 1. 克隆代码
git clone https://github.com/weiqin5882/polymarket-copy-trader.git

# 2. 安装依赖
cd polymarket-copy-trader
pip install -r requirements.txt

# 3. 配置
cp config.json config.json.bak
# 编辑 config.json

# 4. 运行
python copy_trader.py
```

### 方式三：Docker 部署

```bash
# 1. 克隆代码
git clone https://github.com/weiqin5882/polymarket-copy-trader.git
cd polymarket-copy-trader

# 2. 编辑配置
nano config.json
nano .env

# 3. 启动
sudo docker-compose up -d

# 4. 查看日志
sudo docker-compose logs -f copy-trader
```

## ⚙️ 配置说明

### 配置文件位置

```
/opt/polymarket-copy-trader/
├── config.json          # 策略配置
├── .env                 # 环境变量（API密钥等）
├── logs/                # 日志目录
│   ├── output.log      # 标准输出
│   └── error.log       # 错误日志
└── data/               # 数据目录
```

### 配置 API 密钥（如需实际交易）

```bash
nano /opt/polymarket-copy-trader/.env
```

填入：
```
POLY_PRIVATE_KEY=0x你的私钥
POLY_API_KEY=你的API密钥
POLY_API_SECRET=你的API密钥
POLY_API_PASSPHRASE=你的密码
```

**⚠️ 安全提醒：**
- 私钥只保存在服务器上
- 设置文件权限：`chmod 600 .env`
- 定期备份但不要上传到 Git

## 🎮 管理命令

### 系统服务管理

```bash
# 启动
sudo systemctl start polymarket-copy-trader

# 停止
sudo systemctl stop polymarket-copy-trader

# 重启
sudo systemctl restart polymarket-copy-trader

# 查看状态
sudo systemctl status polymarket-copy-trader

# 开机启动
sudo systemctl enable polymarket-copy-trader

# 取消开机启动
sudo systemctl disable polymarket-copy-trader
```

### 快捷命令

```bash
cd /opt/polymarket-copy-trader

# 查看状态
./check_status.sh

# 启动
./start.sh

# 停止
./stop.sh

# 重启
./restart.sh

# 查看日志
./logs.sh
```

### 日志管理

```bash
# 查看实时日志
sudo tail -f /opt/polymarket-copy-trader/logs/output.log

# 查看错误日志
sudo tail -f /opt/polymarket-copy-trader/logs/error.log

# 查看最近100行
sudo tail -n 100 /opt/polymarket-copy-trader/logs/output.log

# 搜索关键词
sudo grep "交易信号" /opt/polymarket-copy-trader/logs/output.log
```

## 📊 监控设置

### 查看运行状态

```bash
/opt/polymarket-copy-trader/check_status.sh
```

输出示例：
```
================================
📊 Polymarket 跟单策略状态
================================

🔧 服务状态:
  ✅ 运行中
  ✅ 已启用开机启动

🖥️  进程信息:
  ✅ 进程存在

📜 最新日志 (最近10行):
  [2026-03-02 16:30:15] 发现顶级交易者: 3位
  [2026-03-02 16:30:20] 开始监控...
  ...

💾 磁盘空间:
  已用: 12% 可用: 45G

🧠 内存使用:
  已用: 234M 总共: 1G
```

### 设置告警（可选）

创建告警脚本 `alert.sh`：

```bash
#!/bin/bash
# 检查服务状态，异常时发送通知

SERVICE="polymarket-copy-trader"
LOG_FILE="/opt/polymarket-copy-trader/logs/output.log"

# 检查服务是否运行
if ! systemctl is-active --quiet $SERVICE; then
    # 发送 Telegram 通知
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=🚨 Polymarket跟单策略已停止运行！"
fi

# 检查是否有错误
if grep -q "ERROR" "$LOG_FILE" | tail -1; then
    ERROR_MSG=$(grep "ERROR" "$LOG_FILE" | tail -1)
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=⚠️ 策略错误: $ERROR_MSG"
fi
```

添加到 crontab：

```bash
# 每5分钟检查一次
crontab -e
*/5 * * * * /opt/polymarket-copy-trader/alert.sh
```

## 🔒 安全加固

### 1. 防火墙设置

```bash
# 只开放必要的端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### 2. 文件权限

```bash
# 设置正确的权限
sudo chown -R polymarket:polymarket /opt/polymarket-copy-trader
sudo chmod 600 /opt/polymarket-copy-trader/.env
sudo chmod 644 /opt/polymarket-copy-trader/config.json
```

### 3. 禁用 root 登录（可选）

```bash
# 创建普通用户
sudo adduser trader
sudo usermod -aG sudo trader

# 禁用 root SSH 登录
sudo nano /etc/ssh/sshd_config
# 设置 PermitRootLogin no
sudo systemctl restart sshd
```

## 🔄 更新代码

```bash
cd /opt/polymarket-copy-trader

# 拉取最新代码
sudo -u polymarket git pull

# 更新依赖
sudo -u polymarket venv/bin/pip install -r requirements.txt

# 重启服务
sudo systemctl restart polymarket-copy-trader
```

## 🗑️ 卸载

```bash
# 停止服务
sudo systemctl stop polymarket-copy-trader
sudo systemctl disable polymarket-copy-trader

# 删除服务文件
sudo rm /etc/systemd/system/polymarket-copy-trader.service
sudo rm /etc/logrotate.d/polymarket-copy-trader

# 删除项目（⚠️ 会删除所有数据！）
sudo rm -rf /opt/polymarket-copy-trader

# 删除用户（可选）
sudo userdel polymarket
```

## 🐛 故障排查

### 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u polymarket-copy-trader -n 50

# 检查配置文件语法
python3 -m json.tool /opt/polymarket-copy-trader/config.json

# 手动运行测试
sudo -u polymarket /opt/polymarket-copy-trader/venv/bin/python \
    /opt/polymarket-copy-trader/copy_trader.py --once
```

### 网络连接问题

```bash
# 测试 Polymarket API
ping data-api.polymarket.com

# 测试网络连通性
python3 -c "import requests; print(requests.get('https://data-api.polymarket.com', timeout=5).status_code)"
```

### 内存/CPU 占用高

```bash
# 查看资源使用
sudo systemctl status polymarket-copy-trader
top -p $(pgrep -f "python.*copy_trader")

# 重启服务
sudo systemctl restart polymarket-copy-trader
```

## 📞 获取帮助

如有问题：
1. 查看日志：`sudo tail -f /opt/polymarket-copy-trader/logs/error.log`
2. 检查状态：`/opt/polymarket-copy-trader/check_status.sh`
3. 提交 Issue：https://github.com/weiqin5882/polymarket-copy-trader/issues

---

**⚠️ 重要提醒：**
- 部署后先用 `analyze` 模式测试几天
- 确认策略有效后再切换到 `copy` 模式
- 定期检查服务器状态和资源使用
- 做好日志备份和监控告警
