在生产环境中，Django 应用通常需要搭配 **Nginx**（反向代理服务器）和 **uWSGI**（WSGI 应用服务器）运行。Nginx 负责处理静态文件（CSS/JS/图片）、接收客户端请求并转发给 uWSGI，uWSGI 则负责运行 Django 应用代码，两者配合实现高效、稳定的服务部署。


### 一、环境准备  
假设服务器系统为 **Ubuntu 20.04**，已安装 Python 3.8+，并准备好一个 Django 项目（例如 `/home/ubuntu/myproject`）。  


#### 1. 安装依赖包  
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 Python 虚拟环境、编译工具（uWSGI 需编译）
sudo apt install -y python3-pip python3-venv build-essential python3-dev
```  


#### 2. 配置 Django 项目  
进入项目目录，创建并激活虚拟环境，安装项目依赖（包括 Django、uWSGI）：  

```bash
# 进入项目目录
cd /home/ubuntu/myproject

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装项目依赖（确保 requirements.txt 包含 django、uwsgi）
pip install -r requirements.txt  # 若没有，直接安装：pip install django uwsgi
```  


#### 3. 配置 Django 生产环境参数  
修改项目的 `settings.py`，确保生产环境配置正确：  

```python
# myproject/settings.py
DEBUG = False  # 关闭调试模式（生产环境必须）
ALLOWED_HOSTS = ["你的域名或服务器IP"]  # 允许访问的主机

# 静态文件配置（Nginx 会直接处理静态文件）
STATIC_URL = '/static/'
STATIC_ROOT = '/home/ubuntu/myproject/staticfiles'  # 静态文件收集目录

# 媒体文件配置（用户上传的文件）
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/ubuntu/myproject/media'
```  

收集静态文件（将项目中所有静态文件集中到 `STATIC_ROOT`）：  
```bash
python manage.py collectstatic  # 按提示输入 yes 确认
```  


### 二、安装并配置 uWSGI  
uWSGI 是连接 Django 和 Nginx 的中间件，负责运行 Django 应用并处理 Nginx 转发的请求。  


#### 1. 安装 uWSGI  
在虚拟环境中已通过 `pip install uwsgi` 安装，若未安装，执行：  
```bash
pip install uwsgi
```  


#### 2. 创建 uWSGI 配置文件  
在项目目录中创建 `uwsgi.ini` 配置文件，定义 uWSGI 运行参数：  

```ini
# /home/ubuntu/myproject/uwsgi.ini
[uwsgi]
# Django 项目目录（包含 manage.py 的目录）
chdir           = /home/ubuntu/myproject

# Django 的 wsgi 模块路径（项目名.wsgi:application）
module          = myproject.wsgi:application

# 虚拟环境路径
home            = /home/ubuntu/myproject/venv

# 运行方式：使用 Unix Socket（比 TCP 更高效，仅本地通信）
socket          = /home/ubuntu/myproject/uwsgi.sock

# 权限设置（Nginx 需要读写权限）
chmod-socket    = 666
chown-socket    = ubuntu:www-data  # 用户名:nginx用户（www-data 是 Nginx 默认用户）

# 进程和线程配置（根据服务器性能调整）
master          = true  # 主进程
processes       = 4     # 工作进程数（建议 = CPU核心数 * 2）
threads         = 2     # 每个进程的线程数

# 日志配置
logto           = /home/ubuntu/myproject/uwsgi.log  # 日志文件路径
log-reopen      = true  # 日志轮转时自动重新打开

# 退出时清理文件
vacuum          = true
```  


#### 3. 测试 uWSGI 是否正常运行  
通过配置文件启动 uWSGI，测试是否能加载 Django 应用：  
```bash
# 在虚拟环境中执行
uwsgi --ini uwsgi.ini
```  

若启动成功，会在项目目录生成 `uwsgi.sock` 和 `uwsgi.log` 文件。可通过日志排查错误：  
```bash
cat /home/ubuntu/myproject/uwsgi.log
```  


#### 4. 配置 uWSGI 为系统服务（开机自启）  
为避免手动启动 uWSGI，将其配置为 systemd 服务：  

1. 创建服务文件：  
```bash
sudo nano /etc/systemd/system/myproject.service
```  

2. 写入以下内容（注意路径替换为实际项目路径）：  
```ini
[Unit]
Description=uWSGI service for myproject
After=network.target

[Service]
User=ubuntu  # 运行用户（项目目录的所有者）
Group=www-data
WorkingDirectory=/home/ubuntu/myproject
ExecStart=/home/ubuntu/myproject/venv/bin/uwsgi --ini uwsgi.ini  # uWSGI 执行路径
Restart=always  # 进程意外退出时自动重启

[Install]
WantedBy=multi-user.target
```  

3. 启动并设置开机自启：  
```bash
# 重新加载系统服务
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start myproject

# 设置开机自启
sudo systemctl enable myproject

# 查看服务状态（确认是否运行正常）
sudo systemctl status myproject
```  


### 三、安装并配置 Nginx  
Nginx 作为反向代理，负责：  
- 接收客户端的 HTTP 请求；  
- 直接返回静态文件（`STATIC_ROOT` 和 `MEDIA_ROOT` 中的文件）；  
- 将动态请求（如 API、页面渲染）转发给 uWSGI 处理。  


#### 1. 安装 Nginx  
```bash
sudo apt install -y nginx
```  

启动 Nginx 并设置开机自启：  
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```  


#### 2. 创建 Nginx 站点配置  
为 Django 项目创建 Nginx 配置文件（而非修改默认配置）：  

1. 创建配置文件：  
```bash
sudo nano /etc/nginx/sites-available/myproject
```  

2. 写入以下内容（替换路径和域名）：  
```nginx
server {
    listen 80;  # 监听 80 端口（HTTP）
    server_name 你的域名或服务器IP;  # 例如：example.com 或 1.2.3.4

    # 访问日志和错误日志
    access_log /var/log/nginx/myproject_access.log;
    error_log /var/log/nginx/myproject_error.log;

    # 静态文件配置（Nginx 直接处理）
    location /static/ {
        alias /home/ubuntu/myproject/staticfiles/;  # 指向 STATIC_ROOT
        expires 30d;  # 静态文件缓存 30 天
    }

    # 媒体文件配置（用户上传的文件）
    location /media/ {
        alias /home/ubuntu/myproject/media/;  # 指向 MEDIA_ROOT
    }

    # 动态请求转发给 uWSGI（通过 Unix Socket）
    location / {
        # 转发到 uWSGI 的 socket
        uwsgi_pass unix:/home/ubuntu/myproject/uwsgi.sock;
        
        # 包含 uWSGI 必备参数（Nginx 提供的模板）
        include /etc/nginx/uwsgi_params;
    }
}
```  


#### 3. 启用站点配置并测试 Nginx  
```bash
# 建立软链接（将 sites-available 中的配置链接到 sites-enabled）
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/

# 检查 Nginx 配置是否有语法错误
sudo nginx -t  # 若显示 "ok" 和 "successful" 则正常

# 重启 Nginx 使配置生效
sudo systemctl restart nginx
```  


#### 4. 配置防火墙（可选）  
若服务器启用了防火墙（如 ufw），需允许 80 端口（HTTP）和 443 端口（HTTPS，后续可配置 SSL）：  
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```  


### 四、验证部署  
打开浏览器，访问服务器的 IP 或域名：  
- 若能正常显示 Django 项目页面，且静态文件（CSS/JS）加载正常，说明部署成功。  
- 若出现错误，可通过以下日志排查：  
  - uWSGI 错误：`/home/ubuntu/myproject/uwsgi.log`  
  - Nginx 错误：`/var/log/nginx/myproject_error.log`  


### 五、进阶：配置 HTTPS（可选）  
为提升安全性，推荐通过 Let’s Encrypt 配置免费 SSL 证书（HTTPS）：  

1. 安装 Certbot：  
```bash
sudo apt install -y certbot python3-certbot-nginx
```  

2. 自动配置 SSL 并更新 Nginx：  
```bash
sudo certbot --nginx -d 你的域名  # 替换为实际域名
```  

按照提示操作，Certbot 会自动配置 HTTPS 并设置证书自动续期。  


### 总结  
Nginx + uWSGI 部署 Django 的核心流程：  
1. uWSGI 运行 Django 应用，通过 Unix Socket 与 Nginx 通信；  
2. Nginx 处理静态文件，并将动态请求转发给 uWSGI；  
3. 配置系统服务确保 uWSGI 和 Nginx 开机自启。  

这种架构兼顾了性能（静态文件由 Nginx 高效处理）和稳定性（uWSGI 管理 Django 进程），是 Django 生产环境的标准部署方案。