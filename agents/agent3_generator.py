from llm_client import llm_call

def generate_full_test_case(feature: str, scene: str) -> str | None:
    """第三层Agent：生成带完整5字段标准测试用例"""
    prompt = f"""
你是专业测试工程师，严格按照要求生成测试用例：
1. 每条用例**只使用中文字段名**，必须包含五个字段：
用例编号、用例标题、前置条件、操作步骤、预期结果
2. 禁止使用case_id、case_title等英文字段
3. 操作步骤清晰可执行，预期结果明确可验证
4. 用例数量控制在8~12条
5. 只输出标准双引号JSON数组，禁止缺失字段、禁止输出代码与解释

已有功能点：
{feature}
规划测试场景：
{scene}
"""
    return llm_call(prompt)