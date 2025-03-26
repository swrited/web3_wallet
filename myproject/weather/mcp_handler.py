import os
import json
import httpx
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

class MCPHandler:
    # 类级别的对话历史存储
    _conversation_histories = {}

    def __init__(self, session_id: str = "default"):
        """初始化 MCP 处理器"""
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")
        self.weather_api_base = "https://api.open-meteo.com/v1/forecast"
        self.session_id = session_id
        
        if not self.openai_api_key:
            raise ValueError("未找到 OpenAI API Key")
        
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        
        # 如果会话ID不存在，创建新的历史记录
        if session_id not in self._conversation_histories:
            self._conversation_histories[session_id] = []
        
        self.conversation_history = self._conversation_histories[session_id]

    async def fetch_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """从 Open-Meteo API 获取天气信息"""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
            "hourly": "precipitation_probability,relativehumidity_2m",
            "timezone": "auto",
            "forecast_days": 7  # 获取未来7天的预报
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
            daily = weather_data.get("daily", {})
            hourly = weather_data.get("hourly", {})

            # 获取当前天气信息
            temperature = current.get("temperature")
            wind_speed = current.get("windspeed")
            weather_code = current.get("weathercode")

            # 获取未来天气预报
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip_probs = daily.get("precipitation_probability_max", [])
            weather_codes = daily.get("weathercode", [])

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

            current_weather = weather_descriptions.get(weather_code, "未知天气")

            # 构建当前天气信息
            current_weather_info = (
                f"● 当前天气\n"
                f"  温度: {temperature}°C\n"
                f"  风速: {wind_speed} km/h\n"
                f"  天气: {current_weather}\n"
            )

            # 构建未来天气预报
            forecast_info = "\n● 未来天气预报\n"
            for i in range(len(dates)):
                date = dates[i]
                max_temp = max_temps[i]
                min_temp = min_temps[i]
                precip_prob = precip_probs[i]
                weather_code = weather_codes[i]
                weather_desc = weather_descriptions.get(weather_code, "未知天气")
                
                forecast_info += (
                    f"  {date}\n"
                    f"    温度: {min_temp}°C ~ {max_temp}°C\n"
                    f"    天气: {weather_desc}\n"
                    f"    降雨概率: {precip_prob}%\n"
                )

            return current_weather_info + forecast_info

        except Exception as e:
            return f"格式化天气数据时出错: {str(e)}"

    async def process_query(self, query: str) -> str:
        """处理用户查询"""
        try:
            # 将用户查询添加到历史记录
            self.conversation_history.append({"role": "user", "content": query})

            # 定义天气查询工具
            tools = [{
                "type": "function",
                "function": {
                    "name": "query_weather",
                    "description": "查询指定位置的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number", "description": "纬度"},
                            "longitude": {"type": "number", "description": "经度"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            }]

            # 调用 API 进行对话，使用完整的对话历史
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=tools,
                tool_choice="auto"
            )

            # 处理响应
            content = response.choices[0]
            if content.finish_reason == "tool_calls":
                # 如果需要使用工具，就解析工具调用
                tool_call = content.message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 执行工具调用
                if tool_name == "query_weather":
                    weather_data = await self.fetch_weather(
                        tool_args["latitude"],
                        tool_args["longitude"]
                    )
                    result = self.format_weather(weather_data)
                else:
                    result = f"未知的工具调用: {tool_name}"

                # 将工具调用结果添加到历史记录
                self.conversation_history.append(content.message.model_dump())
                self.conversation_history.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id,
                })

                # 让模型根据工具调用结果生成最终回复
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                )
                final_response = response.choices[0].message.content
                # 将最终回复添加到历史记录
                self.conversation_history.append({"role": "assistant", "content": final_response})
                return final_response

            # 如果没有工具调用，直接返回模型回复
            final_response = content.message.content
            # 将回复添加到历史记录
            self.conversation_history.append({"role": "assistant", "content": final_response})
            return final_response

        except Exception as e:
            return f"处理查询时出错: {str(e)}"

    def clear_history(self):
        """清除当前会话的对话历史记录"""
        if self.session_id in self._conversation_histories:
            self._conversation_histories[self.session_id] = []
        self.conversation_history = []

    @classmethod
    def clear_all_histories(cls):
        """清除所有会话的对话历史记录"""
        cls._conversation_histories = {}




