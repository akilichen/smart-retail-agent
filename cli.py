"""
商超购物助手 - CLI 交互入口
在终端中与 Agent 进行多轮对话。
"""

import sys
import os
import traceback
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_graph
from config import MAX_RECURSION_LIMIT


# ============================================================
# 终端颜色工具
# ============================================================

class Colors:
    """终端 ANSI 颜色码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"


def print_banner():
    """打印欢迎横幅"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════╗
║     🛒 鲜选生活超市 - 智能购物助手            ║
╚══════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)
    print(f"{Colors.DIM}  输入你的购物需求，我会帮你找商品、查促销、推荐搭配。{Colors.RESET}")
    print(f"{Colors.DIM}  输入 /quit 或 /exit 退出，输入 /help 查看帮助。{Colors.RESET}")
    print(f"{Colors.DIM}  按 Ctrl+C 随时退出。{Colors.RESET}\n")


def print_help():
    """打印帮助信息"""
    help_text = f"""
{Colors.YELLOW}{Colors.BOLD}可用命令：{Colors.RESET}
  {Colors.GREEN}/help{Colors.RESET}      显示此帮助信息
  {Colors.GREEN}/quit{Colors.RESET}      退出对话
  {Colors.GREEN}/exit{Colors.RESET}      退出对话
  {Colors.GREEN}/clear{Colors.RESET}     清空对话历史，重新开始
  {Colors.GREEN}/debug{Colors.RESET}     切换调试模式（显示工具调用详情）

{Colors.YELLOW}{Colors.BOLD}使用示例：{Colors.RESET}
  "帮我找找无糖饮料"
  "有什么在打折的零食吗"
  "酸奶和什么搭配比较好"
  "你们几点关门"
  "怎么退货"
"""
    print(help_text)


def print_ai_response(content: str):
    """格式化打印 AI 回复"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}🤖 助手：{Colors.RESET}")
    # 逐行打印，保持格式
    for line in content.split("\n"):
        print(f"  {line}")
    print()


def print_tool_call(tool_name: str, tool_args: dict):
    """打印工具调用信息（调试模式）"""
    print(f"\n{Colors.MAGENTA}  ⚙️  调用工具: {tool_name}{Colors.RESET}")
    if tool_args:
        args_str = ", ".join(f"{k}={v!r}" for k, v in tool_args.items() if v)
        if args_str:
            print(f"{Colors.DIM}     参数: {args_str}{Colors.RESET}")


def print_tool_result(tool_name: str, content: str):
    """打印工具返回结果（调试模式）"""
    # 截取前200字符展示
    preview = content[:200] + "..." if len(content) > 200 else content
    print(f"{Colors.DIM}  📋 {tool_name} 返回: {preview}{Colors.RESET}\n")


def print_error(error_msg: str):
    """打印错误信息"""
    print(f"\n{Colors.RED}❌ 错误：{error_msg}{Colors.RESET}\n")


# ============================================================
# 对话循环
# ============================================================

def run_conversation(debug: bool = False):
    """
    运行多轮对话循环。

    Args:
        debug: 是否开启调试模式，显示工具调用详情
    """
    print_banner()

    # 构建 Graph
    try:
        graph = build_graph()
    except Exception as e:
        print_error(f"Graph 构建失败：{str(e)}")
        print(f"{Colors.DIM}{traceback.format_exc()}{Colors.RESET}")
        return

    # 对话历史（用于多轮上下文）
    conversation_history = []

    print(f"{Colors.CYAN}准备好了吗？告诉我你想买什么吧！{Colors.RESET}\n")

    while True:
        # === 获取用户输入 ===
        try:
            user_input = input(f"{Colors.BLUE}{Colors.BOLD}你：{Colors.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{Colors.YELLOW}👋 再见，欢迎下次光临！{Colors.RESET}\n")
            break

        # 跳过空输入
        if not user_input:
            continue

        # === 处理命令 ===
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print(f"\n{Colors.YELLOW}👋 再见，欢迎下次光临！{Colors.RESET}\n")
            break

        if user_input.lower() == "/help":
            print_help()
            continue

        if user_input.lower() == "/clear":
            conversation_history = []
            print(f"\n{Colors.YELLOW}🔄 对话历史已清空，重新开始吧！{Colors.RESET}\n")
            continue

        if user_input.lower() == "/debug":
            debug = not debug
            status = "开启" if debug else "关闭"
            print(f"\n{Colors.YELLOW}🔧 调试模式已{status}{Colors.RESET}\n")
            continue

        # === 添加到对话历史 ===
        conversation_history.append(HumanMessage(content=user_input))

        # === 调用 Graph ===
        try:
            # 构建输入状态
            input_state = {
                "messages": conversation_history.copy(),
                "intent": None,
                "cart": [],
                "recommendation_triggered": False,
            }

            # 执行 Graph
            result = graph.invoke(
                input_state,
                config={"recursion_limit": MAX_RECURSION_LIMIT},
            )

            # === 解析结果 ===
            result_messages = result.get("messages", [])

            if debug:
                # 调试模式：展示完整的消息流转
                print(f"\n{Colors.DIM}{'─' * 50}")
                print(f"  意图: {result.get('intent', 'unknown')}")
                print(f"  消息数: {len(result_messages)}")
                print(f"{'─' * 50}{Colors.RESET}\n")

                for msg in result_messages:
                    if isinstance(msg, AIMessage):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                print_tool_call(tc["name"], tc["args"])
                        elif msg.content:
                            print_ai_response(msg.content)
                    elif isinstance(msg, type) and msg.__name__ == "ToolMessage":
                        print_tool_result(msg.name, msg.content)

            else:
                # 正常模式：只展示最终 AI 回复
                # 从结果消息中找到最后一条 AIMessage（非工具调用）
                final_response = None
                for msg in reversed(result_messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        # 跳过纯工具调用的消息（没有content或content为空）
                        if not (hasattr(msg, "tool_calls") and msg.tool_calls and not msg.content):
                            final_response = msg.content
                            break

                if final_response:
                    print_ai_response(final_response)
                else:
                    print_ai_response("抱歉，我暂时无法回答这个问题。请稍后再试。")

            # === 更新对话历史 ===
            # 只保留用户消息和最终的 AI 回复，精简历史
            conversation_history = []
            for msg in result_messages:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    # 只保留有实际内容的消息
                    if msg.content:
                        conversation_history.append(msg)

        except Exception as e:
            error_msg = str(e)
            # 友好提示常见错误
            if "recursion_limit" in error_msg.lower() or "recursion" in error_msg.lower():
                print_error("对话轮次超限，请尝试简化你的问题或清空对话历史（/clear）。")
            elif "api" in error_msg.lower() or "openai" in error_msg.lower():
                print_error(f"API 调用失败，请检查网络连接和 API 配置。详情：{error_msg}")
            elif "chroma" in error_msg.lower() or "vector" in error_msg.lower():
                print_error("向量数据库异常，请确认已运行 python knowledge/build_vectorstore.py 构建知识库。")
            else:
                print_error(f"发生未知错误：{error_msg}")
                if debug:
                    print(f"{Colors.DIM}{traceback.format_exc()}{Colors.RESET}")


# ============================================================
# 入口
# ============================================================

def main():
    """主入口"""
    # 检查命令行参数
    debug = "--debug" in sys.argv or "-d" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"""
{Colors.BOLD}鲜选生活超市 - 智能购物助手 CLI{Colors.RESET}

用法: python cli.py [选项]

选项:
  -d, --debug    开启调试模式，显示工具调用详情
  -h, --help     显示此帮助信息

示例:
  python cli.py              # 正常模式
  python cli.py --debug      # 调试模式
""")
        return

    run_conversation(debug=debug)


if __name__ == "__main__":
    main()