# Code Knowledge Graph

代码知识图谱分析工具，支持 MCP (Model Context Protocol) 集成，帮助 AI 理解项目结构和代码依赖关系。

## 安装

```bash
# 使用 uv
uv sync

# 或使用 pip
pip install -e .
```

## 启动方式

### MCP 服务器模式

```bash
# 直接运行
python -m mcp_server.run

# 或使用 uv
uv run python -m mcp_server.run

# 或通过 main.py
python main.py mcp
```

### Kiro 配置

在 `~/.kiro/settings/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "code-knowledge-graph": {
      "command": "D:/Python313/Scripts/uv.exe",
      "args": ["--directory", "D:/PythonProjectAll/ast-test", "run", "python", "-m", "mcp_server.run"]
    }
  }
}
```

### CLI 命令

```bash
# 启动 Web 可视化界面
python main.py serve --port 8000

# 生成目录树
python main.py tree /path/to/project

# 生成依赖图
python main.py graph /path/to/project
```

---

## MCP 工具文档

### 项目管理工具

#### `scan_project`
扫描并分析项目代码依赖。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |
| incremental | boolean | ❌ | true | 是否增量更新 |
| include_external | boolean | ❌ | false | 是否包含第三方依赖 |

**返回示例：**
```json
{
  "success": true,
  "project_id": 1,
  "project_path": "D:/Projects/my-app",
  "project_name": "my-app",
  "file_count": 42,
  "file_types": {"python": 30, "javascript": 12},
  "scan_mode": "incremental"
}
```

---

#### `get_project_tree`
获取项目目录树结构。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |
| directories_only | boolean | ❌ | false | 是否只返回文件夹（不含文件） |
| max_depth | integer | ❌ | -1 | 最大深度限制，-1 表示无限制 |
| output_format | string | ❌ | "json" | 输出格式："json" 或 "ascii" |

**返回示例（directories_only=true）：**
```json
{
  "success": true,
  "project_path": "D:/Projects/my-app",
  "directories_only": true,
  "max_depth": -1,
  "format": "json",
  "tree": {
    "name": "my-app",
    "path": "",
    "type": "directory",
    "children": [
      {"name": "src", "path": "src", "type": "directory", "children": [...]},
      {"name": "tests", "path": "tests", "type": "directory", "children": [...]}
    ]
  }
}
```

---

#### `list_projects`
获取所有已扫描的项目列表。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| paths_only | boolean | ❌ | false | 是否只返回路径列表 |

**返回示例（paths_only=true）：**
```json
{
  "success": true,
  "paths": ["D:/Projects/my-app", "D:/Projects/another-project"],
  "total": 2
}
```

**返回示例（paths_only=false）：**
```json
{
  "success": true,
  "projects": [
    {
      "id": 1,
      "name": "my-app",
      "path": "D:/Projects/my-app",
      "file_count": 42,
      "last_scanned": "2026-01-19T10:30:00"
    }
  ],
  "total": 1
}
```

---

#### `get_project_info`
获取项目详细信息。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |

---

#### `delete_project`
删除已扫描的项目。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |

---

### 统计分析工具

#### `get_file_stats`
获取项目文件类型统计。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |
| subdirectory | string | ❌ | null | 子目录过滤 |

**返回示例：**
```json
{
  "project_path": "D:/Projects/my-app",
  "subdirectory": null,
  "total_files": 42,
  "stats": [
    {"type": "python", "count": 30, "percentage": 71.4, "total_size": 125000},
    {"type": "javascript", "count": 12, "percentage": 28.6, "total_size": 45000}
  ]
}
```

---

#### `get_reference_ranking`
获取被引用最多的文件排名。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |
| limit | integer | ❌ | 20 | 返回结果数量限制 |
| file_type | string | ❌ | null | 文件类型过滤 |
| include_external | boolean | ❌ | false | 是否包含第三方依赖 |

**返回示例：**
```json
{
  "project_path": "D:/Projects/my-app",
  "limit": 20,
  "file_type_filter": null,
  "include_external": false,
  "total_results": 5,
  "results": [
    {
      "file": "src/utils/helpers.py",
      "count": 15,
      "references": ["src/api/routes.py", "src/services/user.py", "..."]
    }
  ]
}
```

---

#### `get_depth_analysis`
获取目录和文件层级分析。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | ✅ | - | 项目路径 |
| subdirectory | string | ❌ | null | 子目录过滤 |

**返回示例：**
```json
{
  "project_path": "D:/Projects/my-app",
  "subdirectory": null,
  "directory_depth": {"max": 5, "avg": 2.3},
  "file_depth": {"max": 6, "avg": 3.1}
}
```

---

#### `get_function_relations`
获取指定文件间的函数调用关系（最多10个文件）。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| files | array[string] | ✅ | - | 要分析的文件路径列表（最多10个） |
| include_external | boolean | ❌ | false | 是否包含第三方依赖调用 |

**返回示例：**
```json
{
  "files": ["src/api/routes.py", "src/services/user.py"],
  "functions": [
    {"name": "get_user", "file": "src/services/user.py", "line": 15},
    {"name": "user_endpoint", "file": "src/api/routes.py", "line": 8}
  ],
  "calls": [
    {"from": "user_endpoint", "to": "get_user", "line": 12}
  ]
}
```

---

### 上下文工具

#### `get_related_code_context`
获取文件的关联代码上下文（Repo Map），包含目标文件及其依赖文件的签名和摘要。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| project_path | string | ✅ | - | 项目路径 |
| file_path | string | ✅ | - | 目标文件相对路径 |
| hops | integer | ❌ | 1 | 依赖跳数（1-3） |
| include_external | boolean | ❌ | false | 是否包含第三方依赖 |

**返回示例：**
```json
{
  "target_file": "src/api/routes.py",
  "hops": 1,
  "related_files": [
    {
      "path": "src/services/user.py",
      "signatures": [
        "def get_user(user_id: int) -> User",
        "def create_user(data: UserCreate) -> User"
      ]
    }
  ]
}
```

---

### 其他工具

#### `open_web_ui`
打开 Code Knowledge Graph Web 可视化界面。

无参数。

**返回示例：**
```json
{
  "success": true,
  "url": "http://127.0.0.1:18000",
  "message": "Web UI opened in browser"
}
```

---

## 使用场景

### 1. AI 编码前了解项目结构

```
1. 调用 get_project_tree(path, directories_only=true) 获取目录结构
2. 调用 scan_project(path) 建立依赖索引
3. 调用 get_reference_ranking(path) 找出核心文件
4. 根据结构决定新代码放置位置
```

### 2. 修改代码前了解影响范围

```
1. 调用 get_related_code_context(project_path, file_path, hops=2) 
2. 查看哪些文件依赖当前文件
3. 评估修改的影响范围
```

### 3. 理解函数调用关系

```
1. 调用 get_function_relations(files) 
2. 查看函数之间的调用关系
3. 理解代码执行流程
```
