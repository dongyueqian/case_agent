import json
from agents.agent5_prd import parse_prd_to_structured_text
from agents.agent1_feature import parse_feature_points
from agents.agent2_scene import plan_test_scene
from agents.agent3_generator import generate_full_test_case
from agents.agent4_check import mix_self_check
from parse_prd import ParsePRD


def input_multi_require():
    print("\n👉 输入业务需求，连续两次回车提交，输入q退出")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().lower() == "q":
                return "quit"
            if not line.strip() and lines:
                break
            lines.append(line)
        except EOFError:
            return "quit"
    return "\n".join(lines).strip()

def run_total_flow(require_text: str):
    print("\n===== 开始四层Agent流水线执行 =====")
    # 第一层
    print("\n[1/4] 解析提取功能点")
    feature_data = parse_feature_points(require_text)
    if not feature_data:
        print("❌ 第一层功能点解析失败")
        return

    # 第二层
    print("\n[2/4] 规划测试场景")
    scene_data = plan_test_scene(feature_data)
    if not scene_data:
        print("❌ 第二层场景规划失败")
        return

    # 第三层
    print("\n[3/4] 自动生成标准测试用例")
    raw_case = generate_full_test_case(feature_data, scene_data)
    if not raw_case:
        print("❌ 第三层用例生成失败")
        return

    # 第四层
    print("\n[4/4] 混合自检优化补齐")
    final_case_json = mix_self_check(raw_case, feature_data)

    # 结果输出保存
    print("\n===== 🎯 最终生成测试用例 =====")
    try:
        result_data = json.loads(final_case_json)
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
        with open("final_test_cases.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 成功生成 {len(result_data)} 条用例，已保存本地")
    except Exception as e:
        print(f"解析异常：{e}\n原始数据：\n{final_case_json}")

if __name__ == "__main__":
    print("===== 四层模块化智能用例生成工具 =====")
    while True:  # 这里加循环，实现多轮对话
        select = input("\n请选择模式：1 手动输入需求   2 读取docx   q 退出：")

        if select.strip().lower() == "q":
            print("👋 程序退出")
            break

        if select == "1":
            while True:  # 手动输入无限循环
                content = input_multi_require()
                if content == "quit":
                    print("\n🔙 返回主菜单...")
                    break
                if content:
                    run_total_flow(content)

        elif select == "2":
            doc_path = input("请输入docx文件完整路径：")
            prd_raw = ParsePRD.parse_doc_file(doc_path)
            structured_req = parse_prd_to_structured_text(prd_raw)
            run_total_flow(structured_req)

        else:
            print("⚠️ 输入错误，请输入 1、2 或 q")