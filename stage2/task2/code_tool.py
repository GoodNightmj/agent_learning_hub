import  subprocess
import sys
def execute_python(
    code: str,
    timeout: int = 5,
    max_output_chars: int = 5000
) -> dict:
    if not code or not code.strip():
        return {"success": False, "error": "code 不能为空字符串"}
    if not isinstance(timeout, (float, int)) or timeout <= 0:
        return {"success": False, "error": "timeout 必须是大于 0 的数字"}
    if not isinstance(max_output_chars, int) or max_output_chars <= 0:
        return {"success": False, "error": "max_output_chars 必须是大于 0 的整数"}
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if len(result.stdout) > max_output_chars or len(result.stderr) > max_output_chars:
            print(f"警告: 输出被截断，stdout 长度: {len(result.stdout)}, stderr 长度: {len(result.stderr)}")
        stdout = result.stdout[:max_output_chars]
        stderr = result.stderr[:max_output_chars]
        if result.returncode != 0:
            return {"success": False, "stdout":"", "stderr": stderr, "exit_code": 1}
        return {"success": True, "stdout": stdout, "stderr": "","exit_code": 0}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout":"", "stderr": f"执行超时，超过 {timeout} 秒", "exit_code": -1}
if __name__ == "__main__":
    code = """
for i in range(10000):
    print(i)"""
    result = execute_python(code)
    print(result)