#!/usr/bin/env python3
"""
CVM Dify MCP Server
提供4个Dify工作流调用工具：
1. cvm_price_query - CVM机型价格查询
2. cvm_purchase - CVM机型购买
3. automation_test - 自动化测试
4. shutdown_monitor - 自动化关停机监控
"""

import os
import logging
import requests
from mcp.server.fastmcp import FastMCP

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dify API 基础URL
DIFY_BASE_URL = "http://idify.woa.com/v1"

# 从环境变量获取各工作流的API密钥
CVM_PRICE_QUERY_API_KEY = os.environ.get("CVM_PRICE_QUERY_API_KEY", "")
CVM_PURCHASE_API_KEY = os.environ.get("CVM_PURCHASE_API_KEY", "")
AUTOMATION_TEST_API_KEY = os.environ.get("AUTOMATION_TEST_API_KEY", "")
SHUTDOWN_MONITOR_API_KEY = os.environ.get("SHUTDOWN_MONITOR_API_KEY", "")

# 创建MCP服务器实例
mcp = FastMCP("cvm-dify")


def run_dify_workflow(api_key: str, lan: str, user_id: str = "mcp_user") -> str:
    """
    调用Dify工作流的通用函数
    :param api_key: Dify工作流的API密钥
    :param lan: 自然语言输入
    :param user_id: 用户标识
    :return: 工作流执行结果
    """
    if not api_key:
        return "错误：API密钥未配置，请在MCP配置文件的env中设置对应的API密钥"
    
    url = f"{DIFY_BASE_URL}/workflows/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"lan": lan},
        "response_mode": "blocking",
        "user": user_id
    }
    
    try:
        logger.info(f"Running Dify workflow: {url} with user: {user_id}, lan: {lan}")
        response = requests.post(url, headers=headers, json=payload, timeout=1000)
        
        if response.status_code != 200:
            logger.error(f"Dify API Error: {response.status_code} - {response.text}")
            return f"工作流调用失败 ({response.status_code}): {response.text}"
        
        result = response.json()
        # Dify工作流输出通常在 data.outputs 中
        outputs = result.get('data', {}).get('outputs', {})
        # 获取result字段，如果不存在则返回整个outputs的字符串形式
        return outputs.get('result', str(outputs))
        
    except requests.exceptions.Timeout:
        logger.error("Dify workflow timeout")
        return "工作流执行超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return f"网络请求失败: {str(e)}"
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        return f"工作流执行失败: {str(e)}"


@mcp.tool()
def cvm_price_query(lan: str) -> str:
    """
    CVM机型价格查询工作流
    
    功能说明：
    - 查询腾讯云CVM云服务器各机型的价格信息
    - 支持自然语言查询，如"查询S5.MEDIUM4机型的价格"、"北京地区8核16G的机型多少钱"等
    - 可以查询按量付费、包年包月等不同计费模式的价格
    - 支持查询不同地域、不同规格的机型价格对比
    
    使用场景：
    - 当用户需要了解CVM机型的价格时
    - 当用户需要对比不同机型或地域的价格时
    - 当用户进行成本预估时
    
    :param lan: 自然语言查询内容，描述你想查询的机型价格信息
    :return: 查询结果，包含机型价格等详细信息
    
    示例输入：
    - "查询S5.MEDIUM4机型在广州的价格"
    - "8核16G的机型有哪些，分别多少钱"
    - "对比SA2和S5系列的价格"
    """
    logger.info(f"[cvm_price_query] 收到查询请求: {lan}")
    result = run_dify_workflow(CVM_PRICE_QUERY_API_KEY, lan)
    logger.info(f"[cvm_price_query] 查询完成")
    return result


@mcp.tool()
def cvm_purchase(lan: str) -> str:
    """
    CVM机型购买工作流
    
    功能说明：
    - 执行腾讯云CVM云服务器的购买操作
    - 支持自然语言描述购买需求，如"购买一台S5.MEDIUM4机型"、"在北京地区创建一台8核16G的实例"等
    - 可以指定地域、可用区、机型、镜像、网络配置等参数
    - 支持按量付费和包年包月等计费模式
    
    使用场景：
    - 当用户需要创建新的CVM实例时
    - 当用户需要批量购买云服务器时
    - 当用户描述了具体的配置需求需要下单时
    
    注意事项：
    - 购买操作会产生费用，请确认用户已明确表达购买意图
    - 建议在购买前先使用价格查询工具确认费用
    
    :param lan: 自然语言描述的购买需求，包含机型、地域、数量等信息
    :return: 购买操作结果，包含实例ID等信息
    
    示例输入：
    - "在广州地区购买一台S5.MEDIUM4机型，系统盘50G"
    - "创建2台8核16G的实例，使用CentOS 7.6系统"
    - "按量付费购买一台SA2.MEDIUM4机型"
    """
    logger.info(f"[cvm_purchase] 收到购买请求: {lan}")
    result = run_dify_workflow(CVM_PURCHASE_API_KEY, lan)
    logger.info(f"[cvm_purchase] 购买操作完成")
    return result


@mcp.tool()
def automation_test(lan: str) -> str:
    """
    自动化测试工作流
    
    功能说明：
    - 执行CVM相关的自动化测试任务
    - 支持自然语言描述测试需求，如"测试S5机型的网络性能"、"执行磁盘IO压测"等
    - 可以进行性能测试、压力测试、功能验证等多种测试类型
    - 自动生成测试报告和结果分析
    
    使用场景：
    - 当用户需要对CVM实例进行性能测试时
    - 当用户需要验证某个配置或功能时
    - 当用户需要进行自动化回归测试时
    - 当用户需要生成测试报告时
    
    :param lan: 自然语言描述的测试需求，包含测试对象、测试类型、测试参数等
    :return: 测试执行结果，包含测试报告、性能数据等信息
    
    示例输入：
    - "对实例i-xxx执行CPU压力测试"
    - "测试广州地区S5机型的网络延迟"
    - "执行磁盘读写性能测试，持续5分钟"
    - "验证实例的内存是否正常"
    """
    logger.info(f"[automation_test] 收到测试请求: {lan}")
    result = run_dify_workflow(AUTOMATION_TEST_API_KEY, lan)
    logger.info(f"[automation_test] 测试执行完成")
    return result


@mcp.tool()
def shutdown_monitor(lan: str) -> str:
    """
    自动化关停机监控工作流
    
    功能说明：
    - 监控和管理CVM实例的关停机状态
    - 支持自然语言描述监控需求，如"检查哪些实例已关机"、"监控实例的运行状态"等
    - 可以设置关机告警、自动重启等策略
    - 提供实例状态的实时监控和历史记录
    
    使用场景：
    - 当用户需要监控实例是否正常运行时
    - 当用户需要查询已关机的实例时
    - 当用户需要设置关机自动告警时
    - 当用户需要管理实例的开关机策略时
    
    :param lan: 自然语言描述的监控需求，包含监控对象、监控类型、告警设置等
    :return: 监控结果，包含实例状态、告警信息等
    
    示例输入：
    - "检查所有实例的运行状态"
    - "查询最近24小时内关机的实例"
    - "监控实例i-xxx的状态，关机时发送告警"
    - "设置自动重启策略，实例关机后5分钟自动重启"
    """
    logger.info(f"[shutdown_monitor] 收到监控请求: {lan}")
    result = run_dify_workflow(SHUTDOWN_MONITOR_API_KEY, lan)
    logger.info(f"[shutdown_monitor] 监控操作完成")
    return result


def main():
    # 运行MCP服务器
    mcp.run()


if __name__ == "__main__":
    main()
