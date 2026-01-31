"""Command-line interface for SecondMe SDK."""

import argparse
import sys

from . import __version__

HELP_TEXT = """
SecondMe Python SDK (seme-sdk) v{version}
==========================================

一个用于与 SecondMe API 交互的 Python SDK。

安装
----
  pip install seme-sdk

快速开始
--------
  from seme import SecondMeClient

  # 使用 API Key
  client = SecondMeClient(api_key="lba_ak_xxxxx...")

  # 获取用户信息
  user = client.get_user_info()
  print(f"Hello, {{user.name}}!")

  # 流式聊天
  for chunk in client.chat_stream("你好"):
      print(chunk.delta, end="", flush=True)

主要类
------
  SecondMeClient    主客户端，提供所有 API 方法
  OAuth2Client      OAuth2 认证客户端

用户 API
--------
  client.get_user_info()           获取用户基本信息
  client.get_user_shades()         获取用户兴趣标签
  client.get_user_softmemory()     获取用户软记忆（支持分页和关键词过滤）

笔记 API
--------
  client.add_note(content, title, urls, memory_type)
      添加笔记，content 和 urls 至少提供一个

聊天 API
--------
  client.chat_stream(message, session_id, app_id, system_prompt)
      流式聊天，返回 ChatChunk 迭代器

  client.get_session_list(app_id)
      获取会话列表

  client.get_session_messages(session_id)
      获取指定会话的消息历史

OAuth2 认证
-----------
  from seme import OAuth2Client, SecondMeClient

  oauth = OAuth2Client(
      client_id="your_client_id",
      client_secret="your_client_secret",
      redirect_uri="https://your-app.com/callback"
  )

  # 生成授权 URL
  url = oauth.get_authorization_url(scopes=["user.info", "chat"])

  # 用授权码换取 Token
  tokens = oauth.exchange_code(code="lba_ac_xxxxx...")

  # 创建带自动刷新的客户端
  client = SecondMeClient.from_oauth(oauth, tokens)

可用权限范围 (Scopes)
--------------------
  user.info            用户基本信息
  user.info.shades     用户兴趣标签
  user.info.softmemory 用户软记忆
  note.add             添加笔记
  chat                 聊天和会话管理

异常类
------
  SecondMeError          基础异常
  AuthenticationError    认证失败 (401)
  PermissionDeniedError  权限不足 (403)
  NotFoundError          资源不存在 (404)
  InvalidParameterError  参数无效 (400)
  RateLimitError         请求过于频繁 (429)
  ServerError            服务器错误 (5xx)
  TokenExpiredError      Token 已过期

数据模型
--------
  UserInfo        用户信息
  Shade           兴趣标签
  SoftMemory      软记忆
  ChatChunk       流式聊天块
  ChatMessage     聊天消息
  Session         会话
  TokenResponse   Token 响应

更多信息
--------
  PyPI:   https://pypi.org/project/seme-sdk/
  GitHub: https://github.com/secondme/seme-sdk

使用 --api 查看详细的 API 参考文档
使用 --examples 查看更多示例代码
"""

API_REFERENCE = """
SecondMe SDK API 参考
=====================

SecondMeClient
--------------
主客户端类，提供所有 SecondMe API 的访问方法。

构造函数:
    SecondMeClient(
        api_key: str = None,           # API Key (lba_ak_xxx...)
        access_token: str = None,      # OAuth2 Access Token (lba_at_xxx...)
        base_url: str = "https://app.mindos.com/gate/lab",
        oauth_client: OAuth2Client = None,  # 用于自动刷新
        refresh_token: str = None,     # 刷新令牌
        expires_in: int = 7200,        # Token 有效期（秒）
        on_token_refresh: Callable = None  # Token 刷新回调
    )

类方法:
    SecondMeClient.from_oauth(oauth_client, token_response, on_token_refresh=None)
        从 OAuth2 Token 响应创建客户端，自动启用 Token 刷新

实例方法:

  get_user_info() -> UserInfo
      获取当前用户信息
      权限: user.info

  get_user_shades() -> List[Shade]
      获取用户兴趣标签列表
      权限: user.info.shades

  get_user_softmemory(keyword=None, page_no=1, page_size=20) -> SoftMemoryResponse
      获取用户软记忆
      参数:
        - keyword: 可选，过滤关键词
        - page_no: 页码（从1开始）
        - page_size: 每页数量
      权限: user.info.softmemory

  add_note(content=None, title=None, urls=None, memory_type="TEXT") -> str
      添加笔记
      参数:
        - content: 笔记内容（与 urls 至少提供一个）
        - title: 可选，笔记标题
        - urls: 可选，URL 列表
        - memory_type: 类型，默认 "TEXT"
      返回: 笔记 ID
      权限: note.add

  chat_stream(message, session_id=None, app_id=None, system_prompt=None) -> Iterator[ChatChunk]
      流式聊天
      参数:
        - message: 用户消息
        - session_id: 可选，会话 ID（用于连续对话）
        - app_id: 可选，应用 ID
        - system_prompt: 可选，系统提示词
      返回: ChatChunk 迭代器
      权限: chat

  get_session_list(app_id=None) -> List[Session]
      获取会话列表
      参数:
        - app_id: 可选，按应用 ID 过滤
      权限: chat

  get_session_messages(session_id) -> List[ChatMessage]
      获取会话消息历史
      参数:
        - session_id: 会话 ID
      权限: chat

  close()
      关闭客户端，释放资源


OAuth2Client
------------
OAuth2 认证客户端。

构造函数:
    OAuth2Client(
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: str = "https://app.mindos.com/gate/lab"
    )

实例方法:

  get_authorization_url(scopes, state=None) -> str
      生成授权 URL
      参数:
        - scopes: 权限范围列表，如 ["user.info", "chat"]
        - state: 可选，CSRF 防护状态参数

  exchange_code(code) -> TokenResponse
      用授权码换取 Token
      参数:
        - code: 授权回调中的 code 参数

  refresh_token(refresh_token) -> TokenResponse
      刷新 Access Token
      参数:
        - refresh_token: 刷新令牌


数据模型
--------

UserInfo:
    name: str                  # 用户名
    email: str                 # 邮箱
    avatar: str                # 头像 URL
    bio: str                   # 简介
    self_introduction: str     # 自我介绍
    voice_id: str              # 语音 ID
    profile_completeness: float  # 资料完整度 (0-1)

Shade:
    id: str                    # 标签 ID
    shade_name: str            # 标签名称
    confidence_level: float    # 置信度 (0-1)
    public_content: str        # 公开内容
    private_content: str       # 私有内容

SoftMemory:
    id: str                    # 记忆 ID
    content: str               # 内容
    created_at: datetime       # 创建时间
    memory_type: str           # 类型

SoftMemoryResponse:
    items: List[SoftMemory]    # 记忆列表
    total: int                 # 总数
    page_no: int               # 当前页
    page_size: int             # 每页数量
    has_more: bool             # 是否有更多

ChatChunk:
    content: str               # 累积内容
    delta: str                 # 本次增量
    done: bool                 # 是否结束
    session_id: str            # 会话 ID
    message_id: str            # 消息 ID

ChatMessage:
    message_id: str            # 消息 ID
    role: str                  # 角色 ("user" 或 "assistant")
    content: str               # 内容
    timestamp: datetime        # 时间戳

Session:
    session_id: str            # 会话 ID
    app_id: str                # 应用 ID
    last_message: str          # 最后一条消息
    last_update_time: datetime # 最后更新时间
    message_count: int         # 消息数量

TokenResponse:
    access_token: str          # 访问令牌
    refresh_token: str         # 刷新令牌
    token_type: str            # 令牌类型 ("Bearer")
    expires_in: int            # 有效期（秒）
    scope: str                 # 权限范围
"""

EXAMPLES = """
SecondMe SDK 使用示例
=====================

1. 基础使用 - API Key 认证
--------------------------

from seme import SecondMeClient

# 创建客户端
client = SecondMeClient(api_key="lba_ak_your_api_key")

# 获取用户信息
user = client.get_user_info()
print(f"用户名: {user.name}")
print(f"邮箱: {user.email}")
print(f"简介: {user.bio}")

# 获取兴趣标签
shades = client.get_user_shades()
for shade in shades:
    print(f"- {shade.shade_name}: {shade.confidence_level:.0%}")

# 获取软记忆
memories = client.get_user_softmemory(page_size=10)
print(f"共 {memories.total} 条记忆")
for mem in memories.items:
    print(f"- {mem.content[:50]}...")

# 关闭客户端
client.close()


2. 流式聊天
-----------

from seme import SecondMeClient

client = SecondMeClient(api_key="lba_ak_your_api_key")

# 简单聊天
print("AI: ", end="")
for chunk in client.chat_stream("你好，介绍一下你自己"):
    print(chunk.delta, end="", flush=True)
print()

# 连续对话（保持会话）
session_id = None

# 第一轮
for chunk in client.chat_stream("我叫张三"):
    if chunk.session_id:
        session_id = chunk.session_id
    print(chunk.delta, end="", flush=True)
print()

# 第二轮（AI 会记住你的名字）
for chunk in client.chat_stream("你还记得我叫什么吗？", session_id=session_id):
    print(chunk.delta, end="", flush=True)
print()

# 自定义系统提示
for chunk in client.chat_stream(
    "讲个笑话",
    system_prompt="你是一个幽默的脱口秀演员，善于用反转和双关语"
):
    print(chunk.delta, end="", flush=True)
print()

client.close()


3. 添加笔记
-----------

from seme import SecondMeClient

client = SecondMeClient(api_key="lba_ak_your_api_key")

# 添加文本笔记
note_id = client.add_note(
    content="今天学习了 Python SDK 的开发",
    title="学习笔记"
)
print(f"笔记已创建: {note_id}")

# 添加 URL 笔记
note_id = client.add_note(
    urls=["https://docs.python.org/3/"],
    memory_type="URL"
)
print(f"URL 笔记已创建: {note_id}")

client.close()


4. 会话管理
-----------

from seme import SecondMeClient

client = SecondMeClient(api_key="lba_ak_your_api_key")

# 获取所有会话
sessions = client.get_session_list()
print(f"共 {len(sessions)} 个会话")

for session in sessions[:5]:
    print(f"会话 {session.session_id}:")
    print(f"  消息数: {session.message_count}")
    print(f"  最后消息: {session.last_message[:30] if session.last_message else '无'}...")

# 获取某个会话的消息历史
if sessions:
    messages = client.get_session_messages(sessions[0].session_id)
    for msg in messages:
        role = "用户" if msg.role == "user" else "AI"
        print(f"{role}: {msg.content[:50]}...")

client.close()


5. OAuth2 认证流程
------------------

from seme import OAuth2Client, SecondMeClient

# 第一步：创建 OAuth2 客户端
oauth = OAuth2Client(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://your-app.com/callback"
)

# 第二步：生成授权 URL，引导用户访问
auth_url = oauth.get_authorization_url(
    scopes=["user.info", "user.info.shades", "chat", "note.add"],
    state="random_csrf_token"
)
print(f"请访问: {auth_url}")

# 第三步：用户授权后，获取回调中的 code
code = input("请输入授权码: ")

# 第四步：用授权码换取 Token
tokens = oauth.exchange_code(code)
print(f"Access Token: {tokens.access_token[:20]}...")
print(f"有效期: {tokens.expires_in} 秒")

# 第五步：创建带自动刷新的客户端
def on_refresh(new_tokens):
    print("Token 已自动刷新")
    # 这里可以保存新的 Token 到数据库

client = SecondMeClient.from_oauth(
    oauth_client=oauth,
    token_response=tokens,
    on_token_refresh=on_refresh
)

# 正常使用
user = client.get_user_info()
print(f"欢迎, {user.name}!")

client.close()


6. 错误处理
-----------

from seme import (
    SecondMeClient,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    SecondMeError
)

client = SecondMeClient(api_key="lba_ak_your_api_key")

try:
    user = client.get_user_info()
except AuthenticationError as e:
    print(f"认证失败: {e}")
    # 检查 API Key 是否正确
except PermissionDeniedError as e:
    print(f"权限不足: {e}")
    # 需要申请相应的权限范围
except RateLimitError as e:
    print(f"请求过于频繁: {e}")
    # 稍后重试
except SecondMeError as e:
    print(f"API 错误: {e}")
finally:
    client.close()


7. 使用上下文管理器
-------------------

from seme import SecondMeClient

# 使用 with 语句，自动关闭客户端
with SecondMeClient(api_key="lba_ak_your_api_key") as client:
    user = client.get_user_info()
    print(f"Hello, {user.name}!")

    for chunk in client.chat_stream("你好"):
        print(chunk.delta, end="")
    print()

# 客户端已自动关闭
"""


def main():
    parser = argparse.ArgumentParser(
        description="SecondMe Python SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"seme-sdk {__version__}"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="显示详细的 API 参考文档"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="显示使用示例"
    )

    args = parser.parse_args()

    if args.api:
        print(API_REFERENCE)
    elif args.examples:
        print(EXAMPLES)
    else:
        print(HELP_TEXT.format(version=__version__))


if __name__ == "__main__":
    main()
