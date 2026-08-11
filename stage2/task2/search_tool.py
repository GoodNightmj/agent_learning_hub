import os
from dotenv import load_dotenv  
load_dotenv()
from tavily import TavilyClient
from tavily import InvalidAPIKeyError, UsageLimitExceededError
def web_search(
    query: str,
    api_key: str,
    max_results: int = 5
) -> dict:
    if not query or not query.strip():
        return {"success": False, "error": "query 不能为空字符串"}
    if not api_key or not api_key.strip():
        return {"success": False, "error": "api_key 不能为空字符串"}
    if not isinstance(max_results, int) or max_results <= 0:
        return {"success": False, "error": "max_results 必须是大于 0 的整数"}
    try:
        client = TavilyClient(api_key=api_key)
        search_results = client.search(query, search_depth="basic",include_answer=False,include_raw_content=False,max_results=max_results)
        results = [{"title": result.get("title", ""), "url": result.get("url", ""), "content": result.get("content", ""), "score": result.get("score", 0.0)} for result in search_results.get("results", [])]
        return {"success": True, "query": query, "results": results}
    except InvalidAPIKeyError as e:
        return {"success": False, "error": f"API Key 错误或无效: {str(e)}"}

    # 2. 额度不足 / Rate Limit
    except UsageLimitExceededError as e:
        return {"success": False, "error": f"Tavily API 额度耗尽或请求频率超限: {str(e)}"}

    # 3. 网络错误 / 第三方接口异常保底处理
    except Exception as e:
        return {"success": False, "error": f"网络错误或第三方接口异常: {str(e)}"}