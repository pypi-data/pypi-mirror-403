# 混合模式对比：PPT生成 vs 图片高清放大

## 核心实现对比

### PPT生成 (TypeScript)

```typescript
async function handlePptBuild(text: string) {
    // 1. 提交任务
    const response = await fetch(url, {...});
    const data = await response.json() as PptBuildResponse;
    const taskId = data.data.id;
    
    // 2. 轮询查询（2分40秒超时）
    const startTime = Date.now();
    const timeout = 160 * 1000; // 2分40秒
    
    while (Date.now() - startTime < timeout) {
        await new Promise(resolve => setTimeout(resolve, 3000)); // 等待3秒
        
        const queryResponse = await fetch(queryUrl, {...});
        const queryData = await queryResponse.json() as PptQueryResponse;
        
        if (queryData.data.status === 2) {
            // 成功：返回完整结果
            return {
                status: "success",
                message: "✅ PPT生成完成",
                id: taskId,
                preview_url: queryData.data.preview_url,
                ppt_url: pptUrl,
                elapsedSeconds: elapsedSeconds
            };
        } else if (queryData.data.status === 3) {
            // 失败：返回错误
            return { isError: true };
        }
        // status=1 继续等待
    }
    
    // 3. 超时：返回任务ID
    return {
        status: "async",
        message: "PPT生成时间较长，已切换为后台异步执行",
        id: taskId,
        tip: "任务会在后台异步执行，完成后会在右上角弹出通知。"
    };
}
```

### 图片高清放大 (Python)

```python
def submit_super_resolution_task(image_url: str, scale: int, ...) -> dict:
    # 1. 提交任务
    response = client.generate_super_resolution_image_advance(request, runtime)
    job_id = response.body.request_id
    
    # 2. 轮询查询（2分40秒超时）
    start_time = time.time()
    timeout = 160  # 2分40秒
    viapi_client = get_viapi_client()
    
    while time.time() - start_time < timeout:
        time.sleep(3)  # 等待3秒
        
        query_response = viapi_client.get_async_job_result_with_options(...)
        status = query_response.body.data.status
        
        if status in ["SUCCESS", "PROCESS_SUCCESS"]:
            # 成功：返回完整结果
            return {
                "status": "success",
                "message": "✅ Image super-resolution completed",
                "job_id": job_id,
                "output_url": result_url,
                "elapsed_seconds": elapsed_seconds,
            }
        elif status in ["FAILED", "PROCESS_FAILED"]:
            # 失败：返回错误
            return CallToolResult(..., isError=True)
        # status=PROCESSING 继续等待
    
    # 3. 超时：返回任务ID
    return {
        "status": "async",
        "message": "Image processing takes longer time, switched to background async execution",
        "job_id": job_id,
        "tip": "Task will execute in background, push notification will be sent when completed.",
    }
```

## 关键参数对比

| 参数 | PPT生成 | 图片高清放大 | 说明 |
|------|---------|--------------|------|
| **超时时间** | 160秒 (2分40秒) | 160秒 (2分40秒) | ✅ 完全一致 |
| **轮询间隔** | 3秒 | 3秒 | ✅ 完全一致 |
| **成功状态** | status=2 | SUCCESS / PROCESS_SUCCESS | 不同API的状态码 |
| **失败状态** | status=3 | FAILED / PROCESS_FAILED | 不同API的状态码 |
| **处理中状态** | status=1 | PROCESSING | 不同API的状态码 |

## 返回结果对比

### 成功时（同步模式）

**PPT生成：**
```json
{
  "status": "success",
  "message": "✅ PPT生成完成",
  "id": "task-123",
  "ppt_title": "...",
  "preview_url": "...",
  "ppt_url": "...",
  "elapsedSeconds": 8
}
```

**图片高清放大：**
```json
{
  "status": "success",
  "message": "✅ Image super-resolution completed",
  "job_id": "task-123",
  "output_url": "...",
  "output_format": "jpg",
  "elapsed_seconds": 8
}
```

### 超时时（异步模式）

**PPT生成：**
```json
{
  "status": "async",
  "message": "PPT生成时间较长，已切换为后台异步执行",
  "id": "task-123",
  "tip": "任务会在后台异步执行，完成后会在右上角弹出通知。"
}
```

**图片高清放大：**
```json
{
  "status": "async",
  "message": "Image processing takes longer time, switched to background async execution",
  "job_id": "task-123",
  "tip": "Task will execute in background, push notification will be sent when completed."
}
```

## 实现差异

| 方面 | PPT生成 | 图片高清放大 |
|------|---------|--------------|
| **语言** | TypeScript | Python |
| **异步方式** | async/await | time.sleep() |
| **时间计算** | Date.now() | time.time() |
| **错误处理** | try-catch | try-except |
| **API调用** | fetch (HTTP) | SDK Client |

## 用户体验一致性

两个实现在用户体验上完全一致：

1. ✅ **快速任务**：直接返回结果，无需等待
2. ✅ **慢速任务**：自动切换异步，推送通知
3. ✅ **超时设置**：2分40秒覆盖大多数场景
4. ✅ **轮询策略**：3秒间隔，平衡性能和体验
5. ✅ **错误提示**：清晰的状态和错误信息

## 优势总结

### 相比纯异步模式

- ❌ **纯异步**：提交 → 等待通知 → 手动查询
- ✅ **混合模式**：提交 → 自动等待 → 直接获得结果

### 用户操作步骤

**改造前（纯异步）：**
1. 提交任务
2. 获得 job_id
3. 等待通知或手动查询
4. 多次查询直到完成

**改造后（混合模式）：**
1. 提交任务
2. **快速任务**：直接获得结果 ✅
3. **慢速任务**：获得 job_id，等待通知

### 性能影响

- 轮询开销：每3秒一次，最多53次（160秒 / 3秒）
- 大多数任务在 3-10 秒内完成，实际轮询次数 1-3 次
- 对服务器压力影响极小
- 用户体验提升显著

## 总结

通过参考 PPT生成 的混合模式实现，成功将图片高清放大 MCP 改造为：
- ✅ 保持相同的超时和轮询策略
- ✅ 提供一致的用户体验
- ✅ 兼容原有的异步推送通知机制
- ✅ 代码结构清晰，易于维护
