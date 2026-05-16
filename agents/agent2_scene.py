from llm_client import llm_call

def plan_test_scene(feature_text: str) -> str | None:
    """第二层Agent：基于功能点规划测试场景"""
    prompt = f"""
根据给出的功能点规划测试场景，只覆盖：正常流程、空输入、格式非法、业务异常四类核心场景。
场景数量控制8~15个，不写冷门边界场景，不重复。
功能点：
{feature_text}
"""
    return llm_call(prompt)