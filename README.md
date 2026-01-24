# Binance Square

2026.01.22

## 一、用到的项目

### 1、浏览器

[https://github.com/ungoogled-software/ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)

ungoogled-chromium 是一个基于 Google Chromium 的浏览器项目，主要目标是去除所有与 Google 服务相关的依赖，增强隐私和用户对浏览器的控制权，同时尽量保持原生 Chromium 的使用体验。

## 二、项目部署

我是在 Mac 上进行部署，如果是 Windows ，操作类似。

### 1、打开终端命令行

点击“启动台”，输入“终端”，打开终端

默认是在当前用户的目录下

在命令行输入下面的命名，显示当前所在目录

```bash
pwd
```

### 2、从 github 代码仓库把代码克隆到本地

```bash
# 如果没有安装 git，先安装一下
git clone https://github.com/hunterlarcuad/bn-square.git
```

### 3、代码部署

```bash
# 进入到代码目录
cd bn-square
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
source venv/bin/activate
# 在虚拟环境中安装依赖包
pip install -r requirements.txt
# 拷贝默认配置
cp conf.py.sample conf.py
```

### 4、使用记事本编辑 conf.py

设置 ungoogled-chromium 执行文件所在的路径

DEF_PATH_BROWSER = '/Applications/Chromium.app/Contents/MacOS/Chromium’

智普大模型，用来自动回复，新用户注册，白嫖资源包，有3个月的有效期

通过我的邀请链接注册即可获得 2000万Tokens 大礼包，期待和你一起在BigModel上体验最新顶尖模型能力；链接：[https://www.bigmodel.cn/invite?icode=qauKhTeA%2BAzmE%2Ba3pjZTEHHEaazDlIZGj9HxftzTbt4%3D](https://www.bigmodel.cn/invite?icode=qauKhTeA%2BAzmE%2Ba3pjZTEHHEaazDlIZGj9HxftzTbt4%3D)

免费的如果用完，实名认证一下，还能再赠送一个资源包

```bash
# 图形验证码
DEF_CAPTCHA_KEY = 'your_key'

# Cloudflare 人机验证
DEF_CAPMONSTER_KEY = 'your_key'

# GLM API Key
DEF_LLM_ZHIPUAI = 'set_your_secretkey'
# 用哪个模型，如果赠送的资源包指定了模型，在这里设置
DEF_MODEL_ZHIPUAI = 'glm-7'

# 设置浏览器路径
DEF_PATH_BROWSER = '/Applications/Chromium.app/Contents/MacOS/Chromium'
```

如何查看智普赠送的资源包是哪个模型？

打开”资源包管理”

[https://www.bigmodel.cn/finance-center/resource-package/package-mgmt](https://www.bigmodel.cn/finance-center/resource-package/package-mgmt)

在”我的资源包”，适用场景，如果是适用所有按 tokens 计费，就是通用的；如果是指定了适用于 xx 模型，就在配置里设置对应的模型。

## 三、运行

```bash
cd bn-square/
# 激活虚拟环境
source venv/bin/activate
# 启动
python bn_square.py

# 发长文如果需要上传封面图，指定 --upload_image 参数，会暂停，手动上传图片后，在命令行敲回车，继续
python bn_square.py --upload_image
```
