from llm_client import llm_call

def parse_feature_points(user_require: str) -> str | None:
    """第一层Agent：把需求拆解为独立可测试原子功能点"""
    prompt = f"""
    请将以下产品需求拆解为多条独立可测试功能点，简洁直白，不编造额外功能。
    需求内容：
    {user_require}
    """
    return llm_call(prompt)