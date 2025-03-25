import json
import httpx
import logging
from typing import Any, List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
required_env_vars = ["OPENAI_API_KEY", "BASE_URL", "MODEL"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
    raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# 初始化 FastAPI 应用
app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 MCP 服务器
mcp = FastMCP("WeatherServer")

# Open-Meteo API 配置
OPEN_METEO_API_BASE = "https://api.open-meteo.com/v1/forecast"

# 存储对话历史
message_history: List[Dict] = []

class Query(BaseModel):
    query: str

async def fetch_weather(latitude: float, longitude: float) -> dict[str, Any] | None:
    """
    从 Open-Meteo API 获取天气信息。
    :param latitude: 纬度
    :param longitude: 经度
    :return: 天气数据字典；若出错返回包含 error 信息的字典
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",  # 获取当前天气
        "timezone": "auto",  # 自动时区
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_METEO_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()  # 返回字典类型
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

def format_weather(data: dict[str, Any] | str) -> str:
    """
    将天气数据格式化为易读文本。
    :param data: 天气数据（可以是字典或 JSON 字符串）
    :return: 格式化后的天气信息字符串
    """
    # 如果传入的是字符串，则先转换为字典
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            return f"无法解析天气数据: {e}"

    # 如果数据中包含错误信息，直接返回错误提示
    if "error" in data:
        return f"⚠ {data['error']}"

    # 提取数据时做容错处理
    temperature = data.get("current_weather", {}).get("temperature", "N/A")
    wind_speed = data.get("current_weather", {}).get("windspeed", "N/A")
    weather_code = data.get("current_weather", {}).get("weathercode", "N/A")

    # 根据天气代码转换为天气描述
    weather_description = {
        0: "晴",
        1: "大部分晴",
        2: "局部多云",
        3: "多云",
        45: "雾",
        51: "小雨",
        61: "中雨",
        80: "阵雨",
    }.get(weather_code, "未知")

    return (
        f"● 当前天气\n"
        f"  温度: {temperature}°C\n"
        f"● 风速: {wind_speed} km/h\n"
        f"  天气: {weather_description}\n"
    )

@mcp.tool()
async def query_weather(latitude: float, longitude: float) -> str:
    """
    输入指定位置的纬度和经度，返回当前天气查询结果。
    :param latitude: 纬度
    :param longitude: 经度
    :return: 格式化后的天气信息
    """
    data = await fetch_weather(latitude, longitude)
    return format_weather(data)

@app.post("/query")
async def process_query(query: Query):
    """处理用户查询"""
    try:
        logger.info(f"收到查询: {query.query}")
        
        # 添加用户查询到历史记录
        message_history.append({"role": "user", "content": query.query})
        
        # 构建系统提示词，指导模型使用天气查询工具
        system_prompt = """你是一个智能助手，可以帮助用户查询天气信息。
当用户询问天气时，你需要：
1. 首先识别用户查询的城市名称
2. 使用 query_weather 工具查询该城市的天气，需要提供城市的经纬度坐标
3. 根据返回的天气数据生成友好的回复

请确保在回复中包含温度、天气描述等详细信息。如果用户质疑天气数据的准确性，你应该重新查询并解释可能的原因。"""

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ] + message_history

        # 定义可用工具
        tools = [{
            "type": "function",
            "function": {
                "name": "query_weather",
                "description": "查询指定位置的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "纬度"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "经度"
                        }
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }]

        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        # 处理返回的内容
        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            # 解析工具调用
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # 如果是天气查询工具
            if tool_name == "query_weather":
                # 获取天气数据
                weather_data = await query_weather(
                    tool_args["latitude"],
                    tool_args["longitude"]
                )
                
                # 将工具调用结果添加到消息历史
                message_history.append(content.message.model_dump())
                message_history.append({
                    "role": "tool",
                    "content": weather_data,
                    "tool_call_id": tool_call.id,
                })

                # 让模型根据天气数据生成最终回复
                response = client.chat.completions.create(
                    model=os.getenv("MODEL"),
                    messages=message_history,
                )
                final_response = response.choices[0].message.content
                message_history.append({"role": "assistant", "content": final_response})
                return {"response": final_response}

        # 如果没有工具调用，直接返回模型回复
        final_response = content.message.content
        message_history.append({"role": "assistant", "content": final_response})
        return {"response": final_response}

    except Exception as e:
        logger.error(f"处理查询时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理查询失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("启动 MCP 服务器...")
    uvicorn.run(app, host="0.0.0.0", port=5000) 