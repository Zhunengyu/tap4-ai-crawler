import os
import json
import requests
from logging import getLogger

logger = getLogger(__name__)

class LLMUtil:
    def __init__(self):
        # DeepSeek API 配置
        self.api_key = os.getenv('DEEPSEEK_API_KEY', '')  # 从环境变量获取 API 密钥
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API 端点
        self.model = "deepseek-chat"  # 或者您想使用的其他 DeepSeek 模型
    
    def _call_deepseek_api(self, prompt):
        """调用 DeepSeek API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # 检查请求是否成功
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
            # 返回一个简单的备用响应
            return "无法获取详细描述。请稍后再试。"
    
    def process_detail(self, content):
        """处理网页内容，生成详细描述"""
        # 提取一部分内容（避免超过 API 限制）
        truncated_content = content[:4000] if len(content) > 4000 else content
        
        prompt = f"""
        请根据以下网页内容，生成一个详细的 Markdown 格式描述，包括：
        1. 一级标题（网站名称）
        2. 简短介绍（2-3句话）
        3. 主要功能（列表形式）
        4. 使用场景（列表形式）
        5. 简短结论

        网页内容:
        {truncated_content}
        """
        
        return self._call_deepseek_api(prompt)
    
    def process_tags(self, text):
        """根据内容生成标签"""
        prompt = f"""
        根据以下文本，生成5个最相关的标签词（单个词或短语）。
        格式要求：返回一个 JSON 数组，如 ["tag1", "tag2", "tag3", "tag4", "tag5"]

        文本: {text}
        """
        
        try:
            result = self._call_deepseek_api(prompt)
            # 尝试解析 JSON 数组
            tags = json.loads(result)
            if isinstance(tags, list):
                return tags[:5]  # 确保最多返回5个标签
        except:
            # 如果解析失败，返回默认标签
            logger.error("标签解析失败，返回默认标签")
        
        return ["website", "online", "ai", "tool"]
    
    def process_language(self, language, text):
        """将文本翻译成指定语言"""
        prompt = f"""
        请将以下文本翻译成{language}语言:

        {text}
        """
        
        result = self._call_deepseek_api(prompt)
        return result
