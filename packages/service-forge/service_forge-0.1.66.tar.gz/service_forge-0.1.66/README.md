# Service Forge

Automated service creation and maintenance tool.

## Install

```bash
pip install -e .
```

## CLI Usage (sft)

Service Forge 提供了命令行工具 `sft` 用于服务管理。

### 服务上传和部署

```bash
# 上传服务（打包并上传到服务器）
sft upload [project_path]

# 列出本地已打包的服务包
sft list

# 部署服务（只在服务器上使用）
sft deploy <name> <version>
```

### 配置管理

```bash
# 列出所有配置项
sft config list

# 获取指定配置项的值
sft config get <key>

# 设置配置项的值
sft config set <key> <value>
```

### 服务管理

```bash
# 列出所有服务
sft service list

# 删除服务（只在服务器上使用）
sft service delete <service_name> [--force, -f]

# 查看服务日志（只在服务器上使用）
sft service logs <service_name> [--container, -c] [--tail, -n] [--follow, -f] [--previous, -p]
```

## TODO

- [x] 数据库中自动添加trace_id
- [ ] BaseModel管理和注入
- [ ] Workflow相关更加精确的报错信息
- [ ] 完善通用节点
- [ ] 服务之间的相互调用
- [ ] 节点自动生成
- [ ] 服务存活心跳包
- [ ] 各种类型的测试