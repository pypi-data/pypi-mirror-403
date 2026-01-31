import os
import asyncio
import openai
from typing import Union, List, Dict, Any, Optional
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm  # 引入标准 tqdm 用于串行进度条
import nest_asyncio

# 解决 Jupyter/Colab 环境下的事件循环嵌套问题
try:
    nest_asyncio.apply()
except Exception:
    pass

# ==========================================
# 1. 成本统计 (Cost Manager) - 保持不变
# ==========================================
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "default": {"input": 0., "output": 0.}
}


class CostManager:
    def __init__(self):
        self.stats = {"api_calls": 0, "input_tokens": 0, "output_tokens": 0, "errors": 0}

    def update(self, response: Any = None, error: bool = False):
        if error:
            self.stats["errors"] += 1
        elif response and hasattr(response, "usage") and response.usage:
            self.stats["api_calls"] += 1
            self.stats["input_tokens"] += response.usage.prompt_tokens
            self.stats["output_tokens"] += response.usage.completion_tokens

    def print_usage(self, model_name: str):
        pricing = MODEL_PRICING.get(model_name, MODEL_PRICING.get("default"))

        # 获取各项数据
        in_tok = self.stats["input_tokens"]
        out_tok = self.stats["output_tokens"]
        total_tok = in_tok + out_tok

        # 计算成本
        input_cost = (in_tok / 1_000_000) * pricing["input"]
        output_cost = (out_tok / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        # 打印详细报表
        print(f"\n====== [Cost Report: {model_name}] ======")
        print(f"  Calls:        {self.stats['api_calls']} (Errors: {self.stats['errors']})")
        print(f"  Input Tokens: {in_tok:,}")
        print(f"  Output Tokens:{out_tok:,}")
        print(f"  Total Tokens: {total_tok:,}")
        print(f"  Total Cost:   ${total_cost:.5f}")
        print("=========================================\n")


# ==========================================
# 2. 核心类 OpenAIChat
# ==========================================

class OpenAIChat:
    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            model_name: str = "gpt-4o-mini",
            max_tokens: int = 1024,
            temperature: float = 0.7,
            max_concurrency: int = 20,
            max_retries: int = 3,
            timeout: float = 60.0,
            **kwargs
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing. Please provide it or set OPENAI_API_KEY env var.")

        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")

        self.aclient = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=max_retries,
            timeout=timeout
        )

        self.model_name = model_name
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.cost_manager = CostManager()

        self.default_params = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

    # ------------------------------------------------------------------
    #  内部工具
    # ------------------------------------------------------------------

    def _merge_params(self, **kwargs) -> Dict[str, Any]:
        params = self.default_params.copy()
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v
        return params

    def _to_message(self, content: Union[str, List[Dict]]) -> List[Dict]:
        if isinstance(content, str):
            return [{"role": "user", "content": content}]
        return content

    def _normalize_inputs(self, inputs) -> tuple[List[List[Dict]], bool]:
        """
        标准化输入
        Returns:
            formatted_inputs: List[List[Dict]]
            is_list_input: bool (标记原始输入是否是列表结构，决定返回值类型)
        """
        # 1. 字符串 -> 单条
        if isinstance(inputs, str):
            return [self._to_message(inputs)], False

        # 2. 列表处理
        if isinstance(inputs, list):
            if not inputs:
                return [], True
            # ["Q1", "Q2"]
            if isinstance(inputs[0], str):
                return [self._to_message(i) for i in inputs], True
            # [{"role":...}] -> 单条复杂对话
            if isinstance(inputs[0], dict):
                return [inputs], False
            # [[{"role":...}], [...]]
            if isinstance(inputs[0], list):
                return inputs, True

        raise ValueError(f"Unsupported input type: {type(inputs)}")

    # ------------------------------------------------------------------
    #  核心执行逻辑
    # ------------------------------------------------------------------

    async def _generate_single_task(self, messages: List[Dict], **kwargs) -> str:
        """执行单个LLM请求"""
        params = self._merge_params(**kwargs)

        # 如果是串行执行，这里其实不需要 semaphore，但留着也没坏处
        async with self.semaphore:
            try:
                response = await self.aclient.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **params
                )
                self.cost_manager.update(response)
                return response.choices[0].message.content.strip()
            except Exception as e:
                self.cost_manager.update(error=True)
                return f"[ERROR: {str(e)}]"

    async def _run_scheduler(self, formatted_inputs: List[List[Dict]], is_batch: bool, **kwargs) -> List[str]:
        """
        调度器：决定是并发执行还是串行执行
        """
        if not formatted_inputs:
            return []

        # 模式 1: 并发 (Concurrent)
        if is_batch:
            tasks = [self._generate_single_task(msgs, **kwargs) for msgs in formatted_inputs]
            if len(tasks) > 1:
                return await tqdm_asyncio.gather(*tasks, desc=f"Concurrent ({self.model_name})")
            else:
                return await asyncio.gather(*tasks)

        # 模式 2: 串行 (Sequential) - 逐个执行
        else:
            results = []
            # 只有当数量 > 1 时才显示串行进度条
            iterator = tqdm(formatted_inputs, desc=f"Sequential ({self.model_name})") if len(formatted_inputs) > 1 else formatted_inputs

            for msgs in iterator:
                res = await self._generate_single_task(msgs, **kwargs)
                results.append(res)
            return results

    def _run_async(self, coro):
        """环境自适应执行器"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return loop.run_until_complete(coro)
        else:
            return asyncio.run(coro)

    # ------------------------------------------------------------------
    #  统一公开入口
    # ------------------------------------------------------------------

    def generate(self, inputs: Union[str, List[str], List[Dict], List[List[Dict]]], is_batch: bool = True, **kwargs) -> Union[str, List[str]]:
        """
        :param inputs: 输入数据 (str 或 List)
        :param is_batch:
            True (默认): 开启并发加速 (Concurrent)
            False: 强制串行执行 (Sequential), 适合调试或严格顺序
        :param kwargs: 动态参数 (temperature, etc.)
        :return: str 或 List[str] (取决于输入格式)
        """
        # 1. 格式化输入，并获取原始形状
        formatted_inputs, is_list_input = self._normalize_inputs(inputs)

        # 2. 如果输入本身就是单条 (is_list_input=False)，强制 is_batch=True 以便复用逻辑，但结果会解包
        #    或者直接传进去，反正只有一个任务，并发和串行没区别。

        # 3. 构造协程 (传入 is_batch 参数)
        coroutine = self._run_scheduler(formatted_inputs, is_batch=is_batch, **kwargs)

        # 4. 执行
        results = self._run_async(coroutine)

        # 5. 根据原始输入形状返回
        return results if is_list_input else results[0]

    def print_usage(self):
        self.cost_manager.print_usage(self.model_name)


# ==========================================
# 测试代码
# ==========================================
if __name__ == "__main__":
    llm = OpenAIChat(model_name="gpt-4o-mini", max_concurrency=10)

    # 模拟一些问题
    prompts = [f"What is {i}+{i}?" for i in range(5)]

    print("--- 1. 默认模式: is_batch=True (并发/快) ---")
    # 进度条会显示 "Concurrent", 速度很快
    res_fast = llm.generate(prompts, is_batch=True)
    print(f"Sample: {res_fast[0]}")

    print("\n--- 2. 调试模式: is_batch=False (串行/慢) ---")
    # 进度条会显示 "Sequential", 一个个走
    res_slow = llm.generate(prompts, is_batch=False)
    print(f"Sample: {res_slow[0]}")

    print("\n--- 3. 单条输入 (自动忽略 is_batch) ---")
    res_single = llm.generate("Hi", is_batch=False)
    print(f"Result: {res_single}")

    llm.print_usage()
