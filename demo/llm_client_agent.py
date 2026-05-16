import json
import re
import time
import logging
from zhipuai import ZhipuAI
from parse_prd import ParsePRD

# ==================== 配置 ====================
API_KEY = "911378a9afab4588853e4158eeeacc89.ZWPYdOeqx0ln9Q0n"
MODEL_NAME = "glm-4-flash"
TEMPERATURE = 0.1
TIMEOUT = 180
client = ZhipuAI(api_key=API_KEY)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
conversation_memory = []


# ==================== 通用LLM调用（带重试） ====================
def llm_call(prompt, model=MODEL_NAME, temperature=TEMPERATURE, max_retries=3):
    """带重试的LLM调用"""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                timeout=TIMEOUT,
                messages=[{"role": "user", "content": prompt}]
            )
            content = resp.choices[0].message.content.strip()
            content = content.replace("'", '"')
            content = content.strip().strip("```json").strip("```").strip()
            return content
        except Exception as e:
            logging.warning(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logging.error(f"LLM调用最终失败: {str(e)}")
                return None
            time.sleep(2)
    return None


# ==================== 本地自检函数 ====================
def extract_cases_from_broken_json(broken_str):
    """从破损的JSON中尝试提取用例"""
    cases = []
    # 正则匹配每个用例对象
    pattern = r'\{\s*"用例编号"\s*:\s*"[^"]*"\s*,\s*"用例标题"\s*:\s*"[^"]*"\s*,\s*"前置条件"\s*:\s*"[^"]*"\s*,\s*"操作步骤"\s*:\s*"[^"]*"\s*,\s*"预期结果"\s*:\s*"[^"]*"\s*\}'
    matches = re.findall(pattern, broken_str, re.DOTALL)

    for match in matches:
        try:
            case = json.loads(match)
            cases.append(case)
        except:
            continue
    return cases


def generate_default_value(field, idx, case):
    """为缺失字段生成默认值"""
    defaults = {
        "用例编号": f"TC{idx + 1:03d}",
        "用例标题": f"测试用例_{idx + 1}",
        "前置条件": "系统已启动，用户已登录",
        "操作步骤": "1. 执行测试操作",
        "预期结果": "系统正常响应"
    }
    return defaults.get(field, "")


def agent_self_check_local(case_json_str, feature_points):
    """
    本地自检：补齐缺失字段、去重、格式校验
    不调用LLM，避免超时
    """
    # 1. 解析 JSON
    try:
        cases = json.loads(case_json_str)
    except json.JSONDecodeError:
        # 尝试修复常见格式问题
        try:
            cases = extract_cases_from_broken_json(case_json_str)
        except:
            logging.error("JSON解析失败，返回空数组")
            return []

    # 确保是列表
    if not isinstance(cases, list):
        cases = [cases] if cases else []

    # 2. 必需字段列表
    required_fields = ["用例编号", "用例标题", "前置条件", "操作步骤", "预期结果"]

    # 3. 补齐缺失字段
    fixed_cases = []
    seen_titles = set()

    for idx, case in enumerate(cases):
        # 跳过无效用例
        if not isinstance(case, dict):
            continue

        # 补齐缺失字段
        for field in required_fields:
            if field not in case or not case[field]:
                case[field] = generate_default_value(field, idx, case)

        # 去重：基于"用例标题"去重
        title = case.get("用例标题", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        # 确保操作步骤是字符串，如果是列表则转换
        if isinstance(case.get("操作步骤"), list):
            case["操作步骤"] = "\n".join(case["操作步骤"])

        fixed_cases.append(case)

    # 4. 标准化编号（TC001, TC002...）
    for idx, case in enumerate(fixed_cases, 1):
        case["用例编号"] = f"TC{idx:03d}"

    return fixed_cases


def agent_self_check_with_fallback(case_json, feature_points):
    """
    混合自检：先本地快速处理，用例不足8条时用LLM补充
    """
    print("  → 执行本地自检（补齐字段、去重、格式化）...")
    local_cases = agent_self_check_local(case_json, feature_points)
    local_count = len(local_cases)
    print(f"  → 本地处理完成，共 {local_count} 条用例")

    # 如果用例数量在8-15条之间，直接返回
    if 8 <= local_count <= 15:
        print("  ✅ 用例数量符合要求（8-15条），无需LLM补充")
        return json.dumps(local_cases, ensure_ascii=False, indent=2)

    # 用例不足8条，调用LLM补充
    if local_count < 8:
        print(f"  ⚠️ 用例数量不足（{local_count}条），调用LLM补充到8-12条...")

        # 构建补充提示词
        supplement_prompt = f"""
        你是测试用例补充专家。当前已有 {local_count} 条测试用例，请补充到 8-12 条。
        
        要求：
        1. 保留原有用例的全部内容
        2. 补充缺失的测试场景（如：正常流程、异常流程、边界值）
        3. 每条用例必须包含：用例编号、用例标题、前置条件、操作步骤、预期结果
        4. 只输出标准JSON数组，不要其他解释
        
        功能点参考：
        {feature_points}
        
        现有用例：
        {json.dumps(local_cases, ensure_ascii=False, indent=2)}
        
        请输出补充后的完整用例集（JSON数组）：
        """
        llm_result = llm_call(supplement_prompt)

        if llm_result:
            # 再次用本地逻辑处理LLM返回的结果
            print("  → LLM补充完成，再次执行本地格式化...")
            merged_cases = agent_self_check_local(llm_result, feature_points)

            # 控制数量不超过15条
            if len(merged_cases) > 15:
                merged_cases = merged_cases[:15]

            print(f"  ✅ LLM补充完成，最终 {len(merged_cases)} 条用例")
            return json.dumps(merged_cases, ensure_ascii=False, indent=2)
        else:
            print("  ⚠️ LLM补充失败，使用本地已有用例")
            return json.dumps(local_cases, ensure_ascii=False, indent=2)

    # 用例超过15条，截断并提示
    if local_count > 15:
        print(f"  ⚠️ 用例数量超出（{local_count}条），截断至前15条")
        local_cases = local_cases[:15]
        return json.dumps(local_cases, ensure_ascii=False, indent=2)

    return json.dumps(local_cases, ensure_ascii=False, indent=2)


# ==================== 1.需求解析Agent ====================
def agent_parse_requirement(user_input):
    prompt = f"""
    请把下面产品需求拆解为独立可测试的原子功能点：
    1. 只提炼真实需求，不额外编造功能
    2. 每条功能点简洁明确

    用户需求：
    {user_input}
    """
    return llm_call(prompt)


# ==================== 2.场景规划Agent ====================
def agent_test_plan(feature_points):
    prompt = f"""
    基于给出的功能点，规划测试场景，要求：
    1. 只做核心场景：正常流程、空输入、格式非法、业务异常
    2. 不扩展冷门边界、不增加多余场景
    3. 场景数量控制在8~15个，不重复

    功能点：
    {feature_points}
    """
    return llm_call(prompt)


# ==================== 3.用例生成Agent ====================
def agent_gen_test_case(feature_points, scene_plan):
    prompt = f"""
    你是专业测试工程师，必须生成【完整字段】的测试用例，严格遵守：

    1. 每条用例必须包含【全部5个字段】，缺一不可：
       - 用例编号
       - 用例标题
       - 前置条件
       - 操作步骤
       - 预期结果

    2. 操作步骤必须具体、可执行，分步骤写。
    3. 预期结果必须明确、可验证。
    4. 用例数量 8~12 条。
    5. 只输出标准双引号 JSON 数组，绝对不要省略字段！
    6. 禁止只输出标题，禁止缺字段！

    功能点：
    {feature_points}
    测试场景：
    {scene_plan}
    """
    return llm_call(prompt)


# ==================== 4.提炼PRD Agent ====================
def agent_parse_prd(prd_text):
    prompt = f"""
    你是专业的PRD结构化解析专家，目标是从产品需求文档（含大量段落、表格）中，精准识别并分类6类核心信息：
    1. 功能点：可独立使用的功能、菜单、按钮、页面能力
    2. 业务规则：系统必须遵守的业务逻辑、数据处理规则
    3. 校验规则：输入限制、格式校验、范围限制、报错提示
    4. 页面元素：按钮、输入框、表格、分页、提示文案、样式
    5. 接口约束：请求方式、参数、必填项、响应结构、限制
    6. 性能规则：响应时间、数据量限制、存储、时效规则

    【关键词锚定（必须严格匹配）】
    - 功能点：新增、查询、筛选、分页、重置、菜单、tab、展示、加载
    - 业务规则：仅记录、必须触发、自动生成、不生成、默认、保留、归档
    - 校验规则：不能晚于、最大不超过、格式不正确、不能为空、提示
    - 页面元素：按钮、输入框、表格、分页、斑马纹、空状态、选择器
    - 接口约束：GET、POST、参数、必填、page、page_size、响应
    - 性能规则：1秒、10万条、6个月、日均、查询耗时

    【处理要求】
    1. 保留所有表格内容，表格里的规则优先提取
    2. 忽略：版本记录、术语表、附录、后续扩展、背景介绍
    3. 每一条信息必须归到上面6类之一，不能遗漏
    4. 输出严格JSON格式，不要解释、不要markdown、不要多余文字

    【输出JSON结构】
    {{
      "功能点": [],
      "业务规则": [],
      "校验规则": [],
      "页面元素": [],
      "接口约束": [],
      "性能规则": []
    }}

    下面是PRD全文：
    {prd_text}
    """
    json_str = llm_call(prompt)
    try:
        structured = json.loads(json_str)
        lines = []
        for k, v in structured.items():
            lines.append(f"【{k}】：" + "；".join(v))
        return "\n".join(lines)
    except:
        return json_str


# ==================== 多行输入 ====================
def get_multiline_input():
    print("\n👉 输入需求（可多行，连按2次回车提交），输入 q 退出程序：")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().lower() == "q":
                return "quit"
            if line.strip() == "" and len(lines) > 0:
                break
            lines.append(line)
        except EOFError:
            return "quit"
    return "\n".join(lines).strip()


# ==================== 主流程 ====================
def run_agent_workflow(user_req):
    global conversation_memory
    conversation_memory.append(f"用户需求：{user_req}")

    print("\n[1/4] 解析需求，拆解功能点...")
    feature = agent_parse_requirement(user_req)
    if not feature:
        print("❌ 需求解析失败")
        return
    print(f"  ✅ 功能点：{feature[:200]}...")

    print("\n[2/4] 规划测试场景维度...")
    plan = agent_test_plan(feature)
    if not plan:
        print("❌ 场景规划失败")
        return
    print(f"  ✅ 场景规划：{plan[:200]}...")

    print("\n[3/4] 生成JSON测试用例...")
    case_res = agent_gen_test_case(feature, plan)
    if not case_res:
        print("❌ 用例生成失败")
        return
    print("  ✅ 用例生成完成")

    print("\n[4/4] 混合自检（本地 + LLM降级补充）...")
    final_case = agent_self_check_with_fallback(case_res, feature)

    print("\n===== 🎯 Agent 最终测试用例 =====")
    try:
        parsed = json.loads(final_case)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))

        # 保存到文件
        with open("../test_cases.json", "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存 {len(parsed)} 条用例到 test_cases.json")

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print("原始输出:")
        print(final_case)


# ==================== 入口 ====================
if __name__ == "__main__":
    print("===== 混合自检版 测试用例智能Agent =====")
    print("说明：优先本地处理，仅在用例不足8条时调用LLM补充\n")

    model = input("输入 1 手动输入需求，输入 2 读取docx：")
    if model == "1":
        user_content = get_multiline_input()
        if user_content and user_content != "quit":
            run_agent_workflow(user_content)
    elif model == "2":
        file_path = input("输入docx文件路径：")
        prd_text = ParsePRD.parse_doc_file(file_path)
        clean_req = agent_parse_prd(prd_text)
        run_agent_workflow(clean_req)