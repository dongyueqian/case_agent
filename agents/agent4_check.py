import json
from llm_client import llm_call
from local_check import local_fix_cases
from config import CASE_MIN_NUM, CASE_MAX_NUM

def mix_self_check(raw_case_json: str, feature_info: str) -> str:
    """第四层Agent：本地优先校验，不足条数再调用大模型补充"""
    print("  → 执行本地字段修复、去重、格式化")
    case_list = local_fix_cases(raw_case_json)
    now_num = len(case_list)
    print(f"  → 本地处理完成，当前共 {now_num} 条用例")

    # 数量达标直接返回
    if CASE_MIN_NUM <= now_num <= CASE_MAX_NUM:
        print("  ✅ 用例数量合规，无需LLM补充")
        return json.dumps(case_list, ensure_ascii=False, indent=2)

    # 超出上限截断
    if now_num > CASE_MAX_NUM:
        print(f"  ⚠️ 超出最大数量，截断至{CASE_MAX_NUM}条")
        return json.dumps(case_list[:CASE_MAX_NUM], ensure_ascii=False, indent=2)

    # 数量不足调用LLM补齐
    print(f"  ⚠️ 用例不足{CASE_MIN_NUM}条，调用大模型补充场景")
    supplement_prompt = f"""
        当前已有{now_num}条测试用例，请补充完善至{CASE_MIN_NUM}~{CASE_MAX_NUM}条。
        保留原有所有用例不变，补充缺失的正常流程、异常流程、边界校验场景。
        每条必须包含完整五字段，仅输出标准JSON数组。
        
        参考业务功能：
        {feature_info}
        现有用例：
        {json.dumps(case_list, ensure_ascii=False, indent=2)}
        """
    supplement_res = llm_call(supplement_prompt)
    if not supplement_res:
        return json.dumps(case_list, ensure_ascii=False, indent=2)

    final_cases = local_fix_cases(supplement_res)
    if len(final_cases) > CASE_MAX_NUM:
        final_cases = final_cases[:CASE_MAX_NUM]
    print(f"  ✅ 补充完成，最终生成 {len(final_cases)} 条用例")
    return json.dumps(final_cases, ensure_ascii=False, indent=2)