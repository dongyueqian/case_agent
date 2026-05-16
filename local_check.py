import re
import json
from config import CASE_MAX_NUM

def extract_cases_from_broken_json(broken_str: str) -> list:
    pattern = r'\{\s*"用例编号"\s*:\s*"[^"]*"\s*,\s*"用例标题"\s*:\s*"[^"]*"\s*,\s*"前置条件"\s*:\s*"[^"]*"\s*,\s*"操作步骤"\s*:\s*"[^"]*"\s*,\s*"预期结果"\s*:\s*"[^"]*"\s*\}'
    matches = re.findall(pattern, broken_str, re.DOTALL)
    cases = []
    for m in matches:
        try:
            cases.append(json.loads(m))
        except:
            continue
    return cases

def get_default_field(field: str, idx: int) -> str:
    defaults = {
        "用例编号": f"TC{idx+1:03d}",
        "用例标题": f"测试用例_{idx+1}",
        "前置条件": "系统已启动，用户已登录",
        "操作步骤": "1. 执行测试操作",
        "预期结果": "系统正常响应"
    }
    return defaults.get(field, "")


def local_fix_cases(case_json_str: str) -> list:
    try:
        cases = json.loads(case_json_str)
    except json.JSONDecodeError:
        cases = extract_cases_from_broken_json(case_json_str)

    if not isinstance(cases, list):
        cases = [cases] if cases else []

    # 统一标准中文字段
    std_fields = ["用例编号", "用例标题", "前置条件", "操作步骤", "预期结果"]
    fixed = []
    title_set = set()

    for idx, item in enumerate(cases):
        if not isinstance(item, dict):
            continue

        # 字段映射：兼容模型输出英文key，统一转为中文
        field_map = {
            "case_id": "用例编号",
            "case_title": "用例标题",
            "pre_condition": "前置条件",
            "operation_steps": "操作步骤",
            "expected_result": "预期结果"
        }

        new_case = {}
        # 先把英文key转成中文
        for old_k, v in item.items():
            new_k = field_map.get(old_k, old_k)
            new_case[new_k] = v
        item = new_case

        # 补齐缺失标准中文字段
        for f in std_fields:
            if f not in item or not str(item[f]).strip():
                item[f] = get_default_field(f, idx)

        # 标题去重
        title = item["用例标题"]
        if title in title_set:
            continue
        title_set.add(title)

        # 步骤格式统一
        if isinstance(item["操作步骤"], list):
            item["操作步骤"] = "\n".join(item["操作步骤"])

        # 只保留标准5个中文字段，剔除所有多余字段
        clean_item = {k: item[k] for k in std_fields}
        fixed.append(clean_item)

    # 统一重编编号
    for i, val in enumerate(fixed, 1):
        val["用例编号"] = f"TC{i:03d}"
    return fixed