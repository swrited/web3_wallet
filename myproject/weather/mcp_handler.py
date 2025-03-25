import os
import json
import httpx
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

class MCPHandler:
    def __init__(self):
        """初始化 MCP 处理器"""
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")
        
        if not self.openai_api_key:
            raise ValueError("未找到 OpenAI API Key，请在 .env 文件中设置 OPENAI_API_KEY")
        
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        self.message_history = []
        
        # Open-Meteo API 配置
        self.weather_api_base = "https://api.open-meteo.com/v1/forecast"

    async def fetch_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """从 Open-Meteo API 获取天气信息"""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "timezone": "auto",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.weather_api_base, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": f"获取天气数据失败: {str(e)}"}

    def format_weather(self, weather_data: Dict[str, Any]) -> str:
        """格式化天气数据"""
        if "error" in weather_data:
            return f"错误: {weather_data['error']}"

        try:
            current = weather_data.get("current_weather", {})
            temperature = current.get("temperature")
            wind_speed = current.get("windspeed")
            weather_code = current.get("weathercode")

            # 天气代码映射
            weather_descriptions = {
                0: "晴朗", 1: "多云", 2: "阴天", 3: "阴天",
                45: "雾", 48: "霾",
                51: "小雨", 53: "中雨", 55: "大雨",
                61: "小雨", 63: "中雨", 65: "大雨",
                71: "小雪", 73: "中雪", 75: "大雪",
                77: "雪粒",
                80: "阵雨", 81: "阵雨", 82: "暴雨",
                85: "阵雪", 86: "暴雪",
                95: "雷雨", 96: "雷阵雨", 99: "雷阵雨"
            }

            weather_description = weather_descriptions.get(weather_code, "未知天气")

            return (
                f"● 当前天气\n"
                f"  温度: {temperature}°C\n"
                f"  风速: {wind_speed} km/h\n"
                f"  天气: {weather_description}\n"
            )
        except Exception as e:
            return f"格式化天气数据时出错: {str(e)}"

    async def process_query(self, query: str) -> str:
        """异步处理用户查询"""
        try:
            # 添加用户查询到历史记录
            self.message_history.append({"role": "user", "content": query})
            
            # 构建系统提示词
            system_prompt = """你是一个智能天气助手，可以帮助用户查询天气信息。
当用户询问天气时，你需要：
1. 首先识别用户查询的位置信息（经纬度）
2. 使用提供的天气查询工具获取天气数据
3. 根据返回的天气数据生成友好的回复

请确保在回复中包含温度、天气描述等详细信息。"""

            # 定义天气查询工具
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

            # 调用 API 进行对话
            messages = [{"role": "system", "content": system_prompt}] + self.message_history
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            # 处理响应
            content = response.choices[0]
            if content.finish_reason == "tool_calls":
                tool_call = content.message.tool_calls[0]
                tool_args = json.loads(tool_call.function.arguments)
                
                # 获取天气数据
                weather_data = await self.fetch_weather(
                    tool_args["latitude"],
                    tool_args["longitude"]
                )
                
                # 格式化天气数据
                weather_info = self.format_weather(weather_data)
                
                # 将工具调用结果添加到消息历史
                self.message_history.append(content.message.model_dump())
                self.message_history.append({
                    "role": "tool",
                    "content": weather_info,
                    "tool_call_id": tool_call.id,
                })

                # 让模型生成最终回复
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.message_history,
                )
                reply = final_response.choices[0].message.content
            else:
                reply = content.message.content

            # 保存助手回复到历史记录
            self.message_history.append({"role": "assistant", "content": reply})
            return reply

        except Exception as e:
            raise Exception(f"处理查询时出错: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        self.message_history = []


