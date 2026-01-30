"""
AI 测试助手 MCP Server
支持 VS Code Copilot、Cursor、Cherry Studio 等 MCP 客户端
"""

import os
import json
import warnings
from typing import Any

import httpx
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

# 抑制警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# 创建 MCP Server
mcp = FastMCP("AI Test Assistant")

# -------------------------------------------------------------
# LLM 配置
# -------------------------------------------------------------
DEFAULT_LLM_TIMEOUT = 120

def get_provider_priority():
    return ["zhipu", "qwen", "deepseek", "kimi"]

provider_name_map = {
    "zhipu": "智谱 GLM",
    "qwen": "通义千问",
    "deepseek": "DeepSeek",
    "kimi": "Kimi",
}

def build_client(provider: str):
    try:
        if provider == "zhipu":
            api_key = os.getenv("ZHIPU_API_KEY")
            base_url = "https://open.bigmodel.cn/api/paas/v4"
            model = os.getenv("ZHIPU_MODEL_NAME", "glm-4-flash")
        elif provider == "qwen":
            api_key = os.getenv("QWEN_API_KEY")
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            model = os.getenv("QWEN_MODEL_NAME", "qwen-turbo")
        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com/v1"
            model = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
        elif provider == "kimi":
            api_key = os.getenv("KIMI_API_KEY")
            base_url = "https://api.moonshot.cn/v1"
            model = os.getenv("KIMI_MODEL_NAME", "moonshot-v1-8k")
        else:
            return None, None

        if not api_key:
            return None, None

        http_client = httpx.Client(verify=False, timeout=DEFAULT_LLM_TIMEOUT)
        client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        return client, model
    except Exception:
        return None, None


def call_llm(prompt: str, sys_prompt: str = "", temperature: float = 0.2, max_tokens: int = 2000) -> str:
    errors = []
    for provider in get_provider_priority():
        client, model = build_client(provider)
        if client is None or not model:
            continue
        try:
            messages = []
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})

            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content.strip()
            return f"[{provider_name_map.get(provider, provider)}] {content}"
        except Exception as exc:
            errors.append(f"{provider}: {exc}")
            continue

    return f"生成失败: {'; '.join(errors)}" if errors else "未配置 API Key"


SYSTEM_PROMPT = "You are a senior QA architect. Respond in Chinese."


# -------------------------------------------------------------
# MCP Tools (技能)
# -------------------------------------------------------------

@mcp.tool()
def generate_ac(user_story: str) -> str:
    """
    根据用户故事生成验收标准(AC)，采用 BDD Given-When-Then 格式。
    
    Args:
        user_story: 用户故事描述，例如"作为用户，我希望能够搜索商品"
    
    Returns:
        BDD 格式的验收标准列表
    """
    prompt = f"""
基于以下用户故事生成验收标准 (AC)，严格要求：

1) **必须**采用标准 BDD 的 Given-When-Then 三段式格式，每条 AC 格式如下：
   AC-<编号>: <简短标题>
   Given: <前置条件/上下文>
   When: <用户执行的动作>
   Then: <系统应产生的可验证结果>

2) AC 需遵循 INVEST 原则；
3) 生成 5-8 条 AC，覆盖正向场景、异常场景和边界场景；
4) 请保持中文输出。

用户故事: {user_story}
""".strip()
    return call_llm(prompt, SYSTEM_PROMPT)


@mcp.tool()
def generate_test_cases(user_story: str) -> str:
    """
    根据用户故事生成测试用例，使用等价类划分和边界值分析方法，包含优先级标注。
    
    Args:
        user_story: 用户故事描述
    
    Returns:
        Markdown 表格格式的测试用例，包含 ID、优先级(P0/P1/P2)、标题、前置条件、测试步骤、预期结果
    """
    prompt = f"""
为下述用户故事生成 8-15 条测试用例，要求：

1) 使用等价类划分和边界值分析方法
2) 用 Markdown 表格呈现，必须包含以下列：
   | ID | 优先级 | 标题 | 前置条件 | 测试步骤 | 预期结果 |
   
3) 优先级标注规则：
   - P0: 核心功能/阻塞性问题
   - P1: 重要功能
   - P2: 次要功能/边界场景

4) 请保持中文输出。

用户故事: {user_story}
""".strip()
    return call_llm(prompt, SYSTEM_PROMPT)


@mcp.tool()
def generate_ui_automation(user_story: str) -> str:
    """
    根据用户故事生成 UI 自动化测试代码，使用 Python + Selenium + POM 设计模式。
    
    Args:
        user_story: 用户故事描述
    
    Returns:
        Python Selenium 自动化测试代码
    """
    prompt = f"""
生成基于 Python + Selenium 的 UI 自动化测试脚本，用于验证下述用户故事。

**代码结构要求**：
1. 使用 Page Object Model (POM) 设计模式
2. 包含 BasePage 基类和具体页面类
3. 使用 webdriver-manager 自动管理浏览器驱动
4. 使用显式等待 WebDriverWait
5. 至少包含 2-3 个测试方法（正向+异常）
6. 每个测试方法有 Given-When-Then 注释

用户故事: {user_story}
""".strip()
    return call_llm(prompt, SYSTEM_PROMPT, max_tokens=3000)


@mcp.tool()
def generate_api_automation(user_story: str) -> str:
    """
    根据用户故事生成接口自动化测试代码，使用 Python + requests + pytest。
    
    Args:
        user_story: 用户故事描述
    
    Returns:
        Python pytest 接口自动化测试代码
    """
    prompt = f"""
生成基于 Python requests + pytest 的接口自动化测试代码，用于验证下述用户故事。

**代码结构要求**：
1. 配置层：base_url, headers, token 等配置
2. 工具层：封装通用的 HTTP 请求方法
3. 测试层：pytest 测试用例

**测试用例要求**：
- 至少 5 个测试用例，覆盖正向、反向、边界、权限场景
- 每个用例使用 Given-When-Then 注释
- 使用清晰的断言消息

用户故事: {user_story}
""".strip()
    return call_llm(prompt, SYSTEM_PROMPT, max_tokens=3000)


@mcp.tool()
def generate_all(user_story: str) -> str:
    """
    一键生成所有测试资产：AC验收标准、测试用例、UI自动化代码、接口自动化代码。
    
    Args:
        user_story: 用户故事描述
    
    Returns:
        包含所有生成内容的完整报告
    """
    results = []
    
    results.append("# 🎯 AC 验收标准\n")
    results.append(generate_ac(user_story))
    
    results.append("\n\n# 📝 测试用例\n")
    results.append(generate_test_cases(user_story))
    
    results.append("\n\n# 🖥️ UI 自动化代码\n")
    results.append(generate_ui_automation(user_story))
    
    results.append("\n\n# 🔌 接口自动化代码\n")
    results.append(generate_api_automation(user_story))
    
    return "\n".join(results)


# -------------------------------------------------------------
# 启动 MCP Server
# -------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
