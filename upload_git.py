#!/usr/bin/env python3
"""
一键上传项目到Git
"""
import os
import subprocess
import sys


def run_command(cmd, cwd=None):
    """运行命令并打印输出"""
    print(f"🚀 执行: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd,
                                capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️  {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主函数"""
    project_path = "/Users/dongyueqian/PycharmProjects/case_agent"

    print("=" * 50)
    print("🚀 开始上传项目到Git")
    print("=" * 50)

    # 1. 初始化Git
    if not os.path.exists(os.path.join(project_path, ".git")):
        print("\n1. 初始化Git仓库...")
        run_command("git init", project_path)
    else:
        print("\n1. Git仓库已初始化")

    # 2. 添加文件
    print("\n2. 添加文件到暂存区...")
    run_command("git add .", project_path)

    # 3. 提交
    print("\n3. 提交到本地仓库...")
    commit_message = input("请输入提交信息 (默认: Initial commit): ") or "Initial commit"
    run_command(f'git commit -m "{commit_message}"', project_path)

    # 4. 询问是否推送到远程
    push_remote = input("\n是否推送到远程仓库？(y/n, 默认n): ").strip().lower()

    if push_remote == 'y':
        remote_url = input("https://github.com/dongyueqian/case_agent.git").strip()

        if remote_url:
            print("\n4. 推送到远程仓库...")
            run_command(f"git remote add origin {remote_url}", project_path)
            run_command("git branch -M main", project_path)
            run_command("git push -u origin main", project_path)
            print("✅ 推送完成！")
        else:
            print("⚠️  未提供远程URL，跳过推送")
    else:
        print("✅ 本地提交完成！")

    print("\n" + "=" * 50)
    print("📊 Git状态:")
    run_command("git status", project_path)
    print("=" * 50)


if __name__ == "__main__":
    main()
