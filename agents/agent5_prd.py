from llm_client import llm_call
from config import MAX_REQ_TEXT_LEN
import json

def parse_prd_to_structured_text(prd_text: str) -> str:
    """第五层Agent：PRD文档结构化解析，提取6大类需求"""
    prompt = """
        你是专业的PRD结构化解析专家，精准识别6类核心信息：
        1.功能点 2.业务规则 3.校验规则 4.页面元素 5.接口约束 6.性能规则
        
        关键词锚定：
        功能点：新增、查询、筛选、分页、重置、菜单、tab
        业务规则：仅记录、自动生成、不生成、默认保留、归档
        校验规则：不能晚于、最大不超过、格式错误、非空、提示
        页面元素：按钮、输入框、表格、分页、空状态、选择器
        接口约束：GET、POST、参数、必填、page、page_size、响应
        性能规则：响应耗时、数据量、存储时长、保留期限
        
        处理要求：
        1. 优先提取表格内所有规则
        2. 忽略版本记录、术语表、附录、后续扩展、无关背景
        3. 输出严格JSON格式，不要多余文字
        
        输出JSON结构：
        {
          "功能点": [],
          "业务规则": [],
          "校验规则": [],
          "页面元素": [],
          "接口约束": [],
          "性能规则": []
        }
        """ + f"\nPRD全文：{prd_text}"

    json_str = llm_call(prompt)
    try:
        data = json.loads(json_str)
        res = []
        for k, v in data.items():
            res.append(f"【{k}】：{'；'.join(v)}")
        return "\n".join(res)[:MAX_REQ_TEXT_LEN]
    except:
        return json_str[:MAX_REQ_TEXT_LEN] if json_str else ""