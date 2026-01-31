#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云图像超分辨率 MCP 服务器
提供图像超分辨率增强功能
"""

import io
import json
import logging
import os
from typing import Literal
from urllib.request import urlopen

from alibabacloud_imageenhan20190930.client import Client as ImageEnhanClient
from alibabacloud_imageenhan20190930.models import GenerateSuperResolutionImageAdvanceRequest
from alibabacloud_viapi20230117.client import Client as ViapiClient
from alibabacloud_viapi20230117.models import GetAsyncJobResultRequest
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, CallToolResult

# 配置日志
logging.basicConfig(
    level=logging.INFO if os.getenv("MCP_DEBUG") == "1" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("阿里云图像超分辨率")


def get_imageenhan_client() -> ImageEnhanClient:
    """获取图像增强客户端实例"""
    config = Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        endpoint="imageenhan.cn-shanghai.aliyuncs.com",
        region_id="cn-shanghai",
    )
    return ImageEnhanClient(config)


def get_viapi_client() -> ViapiClient:
    """获取 VIAPI 客户端实例（用于查询任务状态）"""
    config = Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        endpoint="viapi.cn-shanghai.aliyuncs.com",
        region_id="cn-shanghai",
    )
    return ViapiClient(config)


def verify_credentials():
    """验证环境变量是否配置"""
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"):
        raise ValueError("未设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID")
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        raise ValueError("未设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET")


@mcp.tool()
def submit_super_resolution_task(
    image_url: str,
    scale: Literal[2, 3, 4] = 2,
    output_format: Literal["jpg", "png"] = "jpg",
    output_quality: int = 100,
) -> dict:
    """
    Submit image super-resolution processing task (Hybrid mode: returns result within 2m40s, or returns task ID on timeout)

    Supports any accessible image URL, not limited to Alibaba Cloud OSS

    Args:
        image_url: Image URL address (supports any accessible HTTP/HTTPS URL)
        scale: Upscale factor, options: 2, 3, 4
        output_format: Output format, options: jpg or png
        output_quality: Output quality (1-100)

    Returns:
        Sync mode: Returns result directly (without job_id) if completed within 2m40s
        Async mode: Returns task ID (job_id) only if timeout, push notification will be sent when completed

    Raises:
        ValueError: Parameter validation failed
        RuntimeError: API call failed
    """
    import time
    
    verify_credentials()

    # 验证参数
    if output_quality < 1 or output_quality > 100:
        raise ValueError("output_quality 必须在 1-100 之间")

    client = get_imageenhan_client()

    # 使用 Advance 方法支持任意 URL
    # 下载图片内容到内存
    logger.info(f"下载图片: {image_url}")
    try:
        img_data = urlopen(image_url).read()
        img_stream = io.BytesIO(img_data)
        logger.info(f"图片下载成功，大小: {len(img_data)} 字节")
    except Exception as e:
        raise RuntimeError(f"无法下载图片: {e}")

    # 创建 AdvanceRequest
    request = GenerateSuperResolutionImageAdvanceRequest(
        image_url_object=img_stream,
        scale=scale,
        output_format=output_format,
        output_quality=output_quality,
    )

    runtime = RuntimeOptions()

    # 调用 Advance API
    response = client.generate_super_resolution_image_advance(request, runtime)

    # 检查响应数据
    if not response.body:
        raise RuntimeError("API 返回的响应体为空")

    # 记录完整响应用于调试
    logger.info(f"API 响应: {response.body}")

    # 获取 job_id
    job_id = None
    
    # 异步模式处理（data 为 None 但有 message）
    if not response.body.data:
        message = getattr(response.body, 'message', '')
        if '异步调用' in message or '任务已提交' in message:
            job_id = response.body.request_id  # request_id is job_id
        else:
            # API 错误
            error_details = {
                "request_id": response.body.request_id,
                "code": getattr(response.body, 'code', None),
                "message": message,
            }
            raise RuntimeError(f"API 未返回处理结果。RequestId: {response.body.request_id}, 详细信息: {error_details}")
    # 如果 data 中包含 job_id
    elif hasattr(response.body.data, 'job_id'):
        job_id = response.body.data.job_id
    else:
        # 其他未知情况
        raise RuntimeError(f"API 返回格式异常，响应内容: {response.body}")

    # 混合模式：轮询查询任务状态（2分40秒超时）
    start_time = time.time()
    timeout = 160  # 2分40秒
    viapi_client = get_viapi_client()
    
    logger.info(f"开始轮询任务状态，job_id: {job_id}")
    
    while time.time() - start_time < timeout:
        # 等待3秒后再查询
        time.sleep(3)
        
        try:
            query_request = GetAsyncJobResultRequest(job_id=job_id)
            query_runtime = RuntimeOptions()
            query_response = viapi_client.get_async_job_result_with_options(query_request, query_runtime)
            
            status = query_response.body.data.status
            logger.info(f"任务状态: {status}")
            
            # 任务成功完成
            if status in ["SUCCESS", "PROCESS_SUCCESS"]:
                result_url = getattr(query_response.body.data, "result", None) or \
                             getattr(query_response.body.data, "Result", None)
                
                elapsed_seconds = int(time.time() - start_time)
                
                if result_url:
                    return {
                        "status": "success",
                        "message": "✅ Image super-resolution completed",
                        "request_id": response.body.request_id,
                        "scale": scale,
                        "output_url": result_url,
                        "output_format": output_format,
                        "elapsed_seconds": elapsed_seconds,
                    }
                else:
                    return {
                        "status": "success",
                        "message": "Task completed but no result URL returned",
                        "request_id": response.body.request_id,
                        "elapsed_seconds": elapsed_seconds,
                    }
            
            # 任务失败
            elif status in ["FAILED", "PROCESS_FAILED"]:
                error_msg = getattr(query_response.body.data, "error_message", None) or \
                            getattr(query_response.body.data, "ErrorMessage", "Unknown error")
                error_code = getattr(query_response.body.data, "error_code", None) or \
                             getattr(query_response.body.data, "ErrorCode", "UNKNOWN")
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "failed",
                            "message": f"Image processing failed [{error_code}]: {error_msg}",
                            "error_code": error_code,
                            "error_message": error_msg,
                        }, ensure_ascii=False)
                    )],
                    isError=True
                )
            
            # status=PROCESSING 继续等待
            
        except Exception as e:
            logger.error(f"查询任务状态出错: {e}")
            # 继续轮询
    
    # 超时，返回任务ID
    logger.info(f"任务处理超时，切换为异步模式")
    return {
        "status": "async",
        "message": "Image processing takes longer time, switched to background async execution",
        "job_id": job_id,
        "request_id": response.body.request_id,
        "scale": scale,
        "tip": "Task will execute in background, push notification will be sent when completed.",
    }


@mcp.tool()
def query_task_status(job_id: str) -> dict:
    """
    Query async task processing status and results (optional)
    
    Note: In hybrid mode, most tasks complete within 2m40s and return results directly.
    This tool is only needed when:
    1. Task switched to async mode due to timeout
    2. User manually requests status check
    Push notification will be sent automatically when async task completes.
    
    Args:
        job_id: Task ID
    
    Returns:
        Dictionary containing task status and results
        - status: PROCESSING(processing) / SUCCESS(success) / FAILED(failed)
        - output_url: Image URL after successful processing (returned only on success)
    """
    verify_credentials()

    client = get_viapi_client()

    # 创建查询请求
    request = GetAsyncJobResultRequest(job_id=job_id)

    runtime = RuntimeOptions()

    # 调用查询API（如果失败会抛出异常）
    response = client.get_async_job_result_with_options(request, runtime)

    # 解析状态
    status = response.body.data.status
    result = {
        "success": True,
        "job_id": job_id,
        "status": status,
        "request_id": response.body.request_id,
    }

    # 如果任务完成，添加结果URL
    if status in ["SUCCESS", "PROCESS_SUCCESS"]:
        # 支持两种成功状态：SUCCESS 和 PROCESS_SUCCESS
        result_url = getattr(response.body.data, "result", None) or \
                     getattr(response.body.data, "Result", None)
        if result_url:
            result["output_url"] = result_url
            result["message"] = "Task processing successful"
        else:
            result["message"] = "Task completed but no result URL returned"
    elif status == "PROCESSING":
        result["message"] = "Task processing, push notification will be sent automatically when completed"
    elif status in ["FAILED", "PROCESS_FAILED"]:
        # Handle failure status (FAILED or PROCESS_FAILED)
        # Note: Attribute names are capitalized ErrorCode and ErrorMessage
        error_msg = getattr(response.body.data, "error_message", None) or \
                    getattr(response.body.data, "ErrorMessage", "Unknown error")
        error_code = getattr(response.body.data, "error_code", None) or \
                     getattr(response.body.data, "ErrorCode", "UNKNOWN")
        result["status"] = "PROCESS_FAILED"
        result["message"] = f"Task processing failed [{error_code}]: {error_msg}"
        result["error_message"] = error_msg
        result["error_code"] = error_code
        # Return CallToolResult with isError=True
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
            isError=True
        )
    else:
        # Unknown status
        result["message"] = f"Unknown status: {status}"

    return result


def main():
    """主函数入口"""
    logger.info("启动阿里云图像超分辨率 MCP 服务器...")
    mcp.run()


if __name__ == "__main__":
    main()
