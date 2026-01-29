import pytest

from ddtols import JSEnv, init

@pytest.fixture(autouse=True)
def setup_module():
    init()

def test_js_eval():
    """测试简单的 JS 代码执行"""
    with JSEnv() as js:
        result = js.eval("1 + 1")
        assert result == 2

def test_js_call():
    """测试调用 JS 函数"""
    with JSEnv() as js:
        # 定义一个函数，显式挂载到 globalThis，并返回 true
        js.eval("""
            globalThis.add = function(a, b) {
                return a + b;
            };
            true;
        """)
        # 调用
        result = js.call("add", 10, 20)
        assert result == 30

def test_js_compile():
    """测试 compile 方法"""
    with JSEnv() as js:
        # 使用 compile 定义函数
        js.compile("""
            globalThis.sub = function(a, b) {
                return a - b;
            };
            true;
        """)
        # 调用
        result = js.call("sub", 50, 20)
        assert result == 30

def test_js_file(tmp_path):
    """测试加载 JS 文件"""
    # 创建一个临时的 js 文件
    js_file = tmp_path / "test.js"
    js_file.write_text("""
        globalThis.multiply = function(a, b) {
            return a * b;
        };
        true;
    """, encoding="utf-8")
    
    with JSEnv() as js:
        js.load_file(str(js_file))
        result = js.call("multiply", 5, 6)
        assert result == 30

def test_js_error():
    """测试 JS 错误捕获"""
    with JSEnv() as js:
        with pytest.raises(Exception):
            js.eval("throw new Error('Something went wrong')")
