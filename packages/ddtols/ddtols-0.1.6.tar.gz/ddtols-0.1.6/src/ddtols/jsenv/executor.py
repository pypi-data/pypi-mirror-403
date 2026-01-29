from __future__ import annotations

import os
from typing import Any, Literal

import never_jscore

from ..decorators import log_execution
from ..diary import get_logger

logger = get_logger("jsenv")

class JSEnv:
    """
    JavaScript 执行环境封装类。
    基于 never_jscore (Deno Core/V8) 实现。
    """

    @log_execution
    def __init__(self) -> None:
        """
        初始化 JS 环境。
        """
        try:
            self.ctx = never_jscore.Context()
            logger.debug("JSEnv initialized successfully")
        except Exception:
            logger.exception("Failed to initialize JSEnv")
            raise

    @log_execution
    def eval(self, code: str) -> Any:
        """
        执行一段 JS 代码并返回结果。
        
        参数：
        code (str): JS 代码字符串。
        
        返回：
        Any: 执行结果。
        """
        try:
            return self.ctx.evaluate(code)
        except Exception:
            logger.exception("JS evaluation failed")
            raise

    @log_execution
    def compile(self, code: str) -> None:
        """
        加载 JS 代码到上下文（不关注返回值，仅用于定义函数或变量）。
        
        参数：
        code (str): JS 代码字符串。
        """
        try:
            # 必须使用 compile 来确保正确注册到全局上下文
            # 注意：compile 仅编译不执行，必须手动 evaluate 返回的 script
            # 追加 ;true; 以防止 JSON 解析错误（当代码返回 undefined 时）
            script = self.ctx.compile(f"{code}")
            
            # 编译后立即执行，使函数/变量在上下文中生效
            # 如果不执行，函数定义将不会注册到全局
            if script:
                script.evaluate()
            
            logger.debug("JS code compiled and evaluated successfully")
        except Exception:
            logger.exception("JS compilation failed")
            raise

    @log_execution
    def load_file(self, file_path: str) -> None:
        """
        加载并执行一个 JS 文件。
        
        参数：
        file_path (str): JS 文件路径。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JS file not found: {file_path}")
            
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
            
        try:
            self.compile(code)
            logger.debug(f"Loaded JS file: {file_path}")
        except Exception:
            logger.exception("Failed to load JS file %s", file_path)
            raise

    @log_execution
    def call(self, func_name: str, *args: Any) -> Any:
        """
        调用已定义的 JS 函数。
        
        参数：
        func_name (str): JS 函数名。
        *args: 传递给函数的参数。
        
        返回：
        Any: 函数执行结果。
        """
        try:
            try:
                return self.ctx.call(func_name, list(args))
            except TypeError:
                return self.ctx.call(func_name, *args)
        except Exception:
            logger.exception("Failed to call JS function '%s'", func_name)
            raise

    def __enter__(self) -> "JSEnv":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:
        """显式关闭 Context 以释放 V8 资源"""
        ctx = getattr(self, "ctx", None)
        if ctx is None:
            return
        del ctx
        self.ctx = None
        logger.debug("JSEnv context closed")
