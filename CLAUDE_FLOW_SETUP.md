# Claude Flow 设置完成

## 已安装的文件
- `.claude/` - Claude Code 配置和斜杠命令
- `.roo/` - SPARC 方法论配置和工作流
- `.roomodes` - 开发模式定义文件
- `claude-flow` - 本地执行脚本
- `CLAUDE.md` - 项目指导文档 (如果存在)
- `coordination.md` - 多智能体协调说明 (如果存在)
- `memory-bank.md` - 内存系统配置 (如果存在)
- `memory/` - 内存数据存储目录 (如果存在)

## 验证安装
```bash
# 测试 claude-flow 是否正常工作
./claude-flow --help

# 检查配置文件
ls -la .claude .roo .roomodes
```

## 快速开始

### SPARC 方法论
```bash
# TDD 模式开发
./claude-flow sparc --mode=tdd "你的任务描述"

# 架构设计
./claude-flow sparc --mode=architect "设计系统架构"

# 代码实现
./claude-flow sparc --mode=coder "实现具体功能"

# 规范定义
./claude-flow sparc --mode=spec-pseudocode "定义功能需求"
```

### Swarm 多智能体协作
```bash
# 研究阶段
./claude-flow swarm --strategy=research "技术调研"

# 开发阶段
./claude-flow swarm --strategy=development "功能开发"

# 测试阶段
./claude-flow swarm --strategy=testing "测试优化"
```

### 内存管理
```bash
# 查询存储信息
./claude-flow memory query "搜索内容"

# 查看内存统计
./claude-flow memory stats

# 导出内存数据
./claude-flow memory export backup.json
```

## 下一步
1. 阅读 `CLAUDE.md` 了解项目架构和命令
2. 查看 `.roo/README.md` 了解 SPARC 方法论
3. 检查 `.roomodes` 文件了解可用的开发模式
4. 根据项目需要定制配置文件

## 问题排查
如果遇到问题，请检查：
- `claude-flow` 脚本是否有执行权限: `chmod +x claude-flow`
- 是否在项目根目录执行命令
- 网络连接是否正常（首次运行需要下载）
- 配置文件是否完整：`.claude/config.json`、`.roomodes`

## 相关文档
- `CLAUDE.md` - 完整的项目指导和架构说明
- `coordination.md` - 多智能体协调系统说明
- `memory-bank.md` - 内存系统配置详情
- `.roo/README.md` - SPARC 方法论详细说明
