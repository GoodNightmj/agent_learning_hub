import urllib
import requests
from bs4 import BeautifulSoup
def fetch_webpage(
    url: str,
    max_chars: int = 10000,
    timeout: int = 10
) -> dict:
    if not url or not url.strip():
        return {"success": False, "error": "url 不能为空字符串"}
    if not isinstance(max_chars, int) or max_chars <= 0:
        return {"success": False, "error": "max_chars 必须是大于 0 的整数"}
    if not isinstance(timeout, (int,float)) or timeout <= 0:
        return {"success": False, "error": "timeout 必须是大于 0 的数字"}
    parsed_url=urllib.parse.urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        return {"success": False, "error": "只允许 http 或 https 协议的 URL"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout,allow_redirects=True)
        response.raise_for_status()
        if response.encoding is None or response.encoding=='ISO-8859-1':
            response.encoding = response.apparent_encoding
    except requests.exceptions.Timeout:
        return {"success": False, "error": f"请求超时: {timeout} 秒"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP 错误: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"请求错误: {str(e)}"}
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "noscript","footer","nav" ]):
            element.decompose()
        title=soup.title.string if soup.title else ""
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        cleaned_text = "\n".join(line for line in lines if line)
        if len(cleaned_text) > max_chars:
            cleaned_text = cleaned_text[:max_chars]
        return {"success": True, "url": url, "title": title, "content": cleaned_text}
    except Exception as e:
        return {"success": False, "error": f"解析网页内容失败: {str(e)}"}
if __name__ == "__main__":
    test_url = "file:///etc/passwd"
    result = fetch_webpage(test_url, max_chars=500)
    if result["success"]:
        print("网页标题:", result["title"])
        print("网页内容:", result["content"])
    else:
        print("错误:", result["error"])

            