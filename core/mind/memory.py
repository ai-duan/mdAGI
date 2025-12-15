"""记忆管理器"""
from typing import List
from .llm import LLMClient

# 配置常量
MEMORY_LIMIT = 100
KEEP_COUNT = 3


class MemoryManager:
    """记忆管理 - 包含记忆存储和知识蒸馏"""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
    
    def summarize_action(
        self,
        task: str,
        thought: str,
        action: str,
        result: str
    ) -> str:
        """生成行动摘要"""
        text = f"任务:{task} 思考:{thought} 行动:{action} 结果:{result[:200]}"
        return self.llm.summarize(text, max_length=100)
    
    def should_distill(self, memory_count: int) -> bool:
        """判断是否需要蒸馏"""
        return memory_count > MEMORY_LIMIT
    
    def distill(self, memories: List[str]) -> tuple[List[str], List[str]]:
        """
        蒸馏记忆为知识
        返回: (新知识列表, 保留的记忆列表)
        """
        if len(memories) <= KEEP_COUNT:
            return [], memories
        
        memories_to_distill = memories[:-KEEP_COUNT]
        active_memory = memories[-KEEP_COUNT:]
        
        print(f"\n[Memory] 蒸馏 {len(memories_to_distill)} 条记忆...")
        
        # 调用 LLM 提取知识
        memory_text = "\n".join(memories_to_distill)
        prompt = f"""从以下记忆中提取关键洞察（每行一条）：
{memory_text}

洞察："""
        
        messages = [
            {"role": "system", "content": "你是知识提取专家。提取可复用的规则和洞察。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm.chat(messages, max_tokens=512)
        
        if result:
            content = result["choices"][0]["message"]["content"]
            insights = [
                f"[经验] {line.strip('- *').strip()}"
                for line in content.split("\n")
                if line.strip()
            ]
            print(f"[Memory] 提炼出 {len(insights)} 条知识")
            return insights, active_memory
        
        return [], active_memory
