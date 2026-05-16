import sys
from zhipuai import ZhipuAI
import logging

# 配置基本日志
logging.basicConfig(level=logging.INFO)

client = ZhipuAI(api_key="911378a9afab4588853e4158eeeacc89.ZWPYdOeqx0ln9Q0n")

def get_multiline_input():
    """获取多行输入，连续两次回车结束"""
    print("===== 请输入功能描述（可多行，输完连续按2次回车结束） =====")
    lines = []
    while True:
        line = input()
        # 连续空两行就结束
        if not line and len(lines) > 0:
            break
        lines.append(line)
    return "\n".join(lines).strip()

def generate_test_cases(function_desc, model = "glm-4-flash"):
    prompt = f"""你是一名专业的测试工程师。
请根据下面的功能描述，生成**标准、可执行、完整覆盖**的测试用例。

要求：
1. 每条用例包含：用例编号、用例标题、前置条件、操作步骤、预期结果
2. **只返回 JSON 数组，不要解释、不要前言、不要后记**
3. 格式严格如下：
[
  {{
    "用例编号": "001",
    "用例标题": "...",
    "前置条件": "...",
    "操作步骤": "...",
    "预期结果": "..."
  }}
]
        功能描述：{function_desc}
            """.strip()
    # 创建聊天完成请求
    try:
        response = client.chat.completions.create(
            model= model,
            temperature=0.2, # 越低越稳定、越精准
            messages=[{"role": "user", "content": prompt}]
        )
        # 获取回复
        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"测试用例生成失败：{str(e)}")
        return None

"""
1、输入11位手机号，发送验证码登
2、输入11位手机号和密码登录
"""
if __name__ == "__main__":
    # 获取多行输入
    desc = get_multiline_input()
    if not desc:
        print("输入不能为空，程序退出")
        sys.exit()

    print("\n正在调用大模型生成测试用例，请稍候...")
    result = generate_test_cases(desc)

    if result:
        print("\n===== 生成完成 测试用例JSON =====")
        print(result)
    else:
        print("生成失败，请检查网络或API密钥")
