# 混合模式改造说明

## 改造目标

参考 `typescript/PPT生成` 项目，将图片高清放大 MCP 从纯异步模式改造为混合模式：
- **2分40秒内同步返回结果**
- **超时则返回任务ID，切换为后台异步执行**

## 核心改动

### 1. `submit_super_resolution_task` 函数改造

#### 原实现（纯异步）
- 提交任务后立即返回 `job_id`
- 用户需要手动调用 `query_task_status` 查询结果
- 依赖推送通知

#### 新实现（混合模式）
- 提交任务后自动开始轮询查询
- 每 3 秒查询一次任务状态
- 2分40秒（160秒）超时限制
- **成功时**：直接返回完整结果（包括 `output_url`、`elapsed_seconds` 等）
- **超时时**：返回任务ID，提示后台异步执行
- **失败时**：立即返回错误信息

### 2. 关键代码逻辑

```python
# 混合模式：轮询查询任务状态（2分40秒超时）
start_time = time.time()
timeout = 160  # 2分40秒
viapi_client = get_viapi_client()

while time.time() - start_time < timeout:
    # 等待3秒后再查询
    time.sleep(3)
    
    # 查询任务状态
    query_response = viapi_client.get_async_job_result_with_options(...)
    status = query_response.body.data.status
    
    if status in ["SUCCESS", "PROCESS_SUCCESS"]:
        # 返回成功结果
        return {
            "status": "success",
            "output_url": result_url,
            "elapsed_seconds": elapsed_seconds,
            ...
        }
    elif status in ["FAILED", "PROCESS_FAILED"]:
        # 返回失败信息
        return CallToolResult(..., isError=True)
    # status=PROCESSING 继续等待

# 超时，返回任务ID
return {
    "status": "async",
    "job_id": job_id,
    "tip": "Task will execute in background...",
}
```

### 3. 返回结果格式变化

#### 同步模式（任务快速完成）
```json
{
  "status": "success",
  "message": "✅ Image super-resolution completed",
  "job_id": "ABC123-DEF456-GHI789",
  "scale": 3,
  "output_url": "https://viapi-cn-shanghai.oss-cn-shanghai.aliyuncs.com/...",
  "output_format": "jpg",
  "elapsed_seconds": 8
}
```

#### 异步模式（任务超时）
```json
{
  "status": "async",
  "message": "Image processing takes longer time, switched to background async execution",
  "job_id": "ABC123-DEF456-GHI789",
  "scale": 3,
  "tip": "Task will execute in background, push notification will be sent when completed."
}
```

### 4. 工具描述更新

- `submit_super_resolution_task`：更新为"混合模式"说明
- `query_task_status`：标注为"可选"，说明大多数情况下不需要手动查询

## 用户体验提升

### 改造前
1. 用户提交任务 → 获得 job_id
2. 用户手动查询状态（或等待推送通知）
3. 查询多次直到获得结果

### 改造后
1. 用户提交任务 → 自动等待（最多2分40秒）
2. **快速任务**：直接获得结果和下载链接 ✅
3. **慢速任务**：获得任务ID，后台继续处理，完成后推送通知

## 技术细节

### 轮询策略
- 间隔：3秒
- 超时：160秒（2分40秒）
- 状态检查：SUCCESS / PROCESS_SUCCESS / FAILED / PROCESS_FAILED / PROCESSING

### 错误处理
- 查询失败时继续轮询（不中断）
- 任务失败时立即返回错误（使用 `CallToolResult` 的 `isError=True`）
- 超时时返回正常结果（status="async"）

### 性能考虑
- 大多数图片处理在 3-10 秒内完成
- 2分40秒的超时设置覆盖了绝大多数场景
- 避免无限等待导致的用户体验问题

## 参考实现

完整参考了 `typescript/PPT生成/src/index.ts` 中的 `handlePptBuild` 函数实现：
- 相同的超时时间（160秒）
- 相同的轮询间隔（3秒）
- 相同的返回结果结构（status、message、elapsed_seconds 等）
- 相同的错误处理逻辑

## 文档更新

- ✅ README.md：更新核心特性、使用指南、注意事项
- ✅ 工具描述：更新 docstring 说明混合模式
- ✅ 示例代码：提供同步和异步两种返回结果示例
