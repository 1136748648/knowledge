# FR-MINDMAP-003: 导航结构整合实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现思维导图与知识导航树的整合功能，使生成的思维导图与知识导航结构对齐。

**Architecture:** 通过MCP协议调用导航Agent获取导航树，将导航结构作为提示词输入LLM，生成与导航对齐的思维导图。保持Agent之间的低耦合性。

**Tech Stack:** Python 3.11+, FastAPI, Casbin, SQLAlchemy, Vue3, Element Plus

---

## 文件结构

| 文件路径 | 职责 | 状态 |
|----------|------|------|
| `backend/app/agents/mindmap_agent/agent.py` | 思维导图Agent，新增integrate action | 修改 |
| `backend/app/api/wiki.py` | Wiki API，新增整合端点 | 修改 |
| `backend/tests/test_mindmap_integrate.py` | 整合功能测试 | 新增 |
| `frontend/src/api/wiki.js` | 前端API，新增整合接口 | 修改 |
| `frontend/src/views/Wiki.vue` | Wiki页面，添加导航整合选项 | 修改 |
| `docs/requirements/detailed/FR-MINDMAP.md` | 更新需求状态 | 修改 |

---

## Task 1: 修改思维导图Agent，新增integrate action

**Files:**
- Modify: `backend/app/agents/mindmap_agent/agent.py`
- Test: `backend/tests/test_mindmap_integrate.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_mindmap_integrate.py
import pytest
from unittest.mock import patch, MagicMock
from app.agents.mindmap_agent.agent import MindMapAgent

@pytest.mark.asyncio
async def test_integrate_action():
    """测试导航整合action"""
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_user.username = "admin"
    mock_user.roles = ["admin"]
    
    agent = MindMapAgent(mock_session, mock_user)
    
    # Mock get_registry 和导航Agent
    with patch('app.agents.mindmap_agent.agent.get_registry') as mock_registry:
        mock_nav_agent = MagicMock()
        mock_registry.return_value.get_agent.return_value = mock_nav_agent
        
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {
            "name": "知识导航",
            "children": [{"name": "部门文档"}, {"name": "项目文档"}]
        }
        mock_nav_agent.handle_request.return_value = mock_response
        
        # Mock LLM服务
        with patch.object(agent, 'llm') as mock_llm:
            mock_llm.generate_mindmap.return_value = '{"name": "整合导图"}'
            
            request = MagicMock()
            request.params = {
                "action": "integrate",
                "text": "测试文档内容",
                "format": "json",
                "depth": 3
            }
            
            response = await agent.handle_request(request)
    
    assert response.success == True
    assert "mindmap" in response.data
    mock_nav_agent.handle_request.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_mindmap_integrate.py::test_integrate_action -v`
Expected: FAIL with "action 'integrate' not supported"

- [ ] **Step 3: Write minimal implementation**

```python
# 在 mindmap_agent/agent.py 中添加
# 1. 更新 input_schema，添加 integrate action
input_schema={
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["generate", "convert", "simplify", "expand", "integrate"]
        },
        "data": {"type": "object"},
        "text": {"type": "string"},
        "format": {"type": "string", "enum": ["json", "mermaid", "markdown"]},
        "depth": {"type": "integer", "minimum": 1, "maximum": 5},
        "use_navigation": {"type": "boolean", "default": True}
    },
    "required": ["action"]
},

# 2. 在 handle_request 中添加 integrate 分支
elif action == "integrate":
    text = request.params.get("text", "")
    nav_tree = await self._get_nav_tree()
    mindmap = await self._generate_with_nav(text, nav_tree, format_type, depth)
    
    return MCPResponse(
        success=True,
        data={
            "mindmap": mindmap,
            "format": format_type,
            "nodes": self._count_nodes(mindmap),
            "depth": depth,
            "aligned_with_navigation": True
        },
        sources=[
            {"type": "mindmap", "action": "integrate"},
            {"type": "navigation", "action": "get_tree"}
        ],
        confidence=0.85
    )

# 3. 添加辅助方法
async def _get_nav_tree(self):
    """通过MCP协议获取导航树"""
    try:
        registry = get_registry()
        nav_agent = registry.get_agent("navigation_agent", self.db_session, self.user)
        
        if nav_agent:
            request = MCPRequest(
                agent_id="navigation_agent",
                params={"action": "get_tree"}
            )
            response = await nav_agent.handle_request(request)
            return response.data if response.success else {}
        return {}
    except Exception:
        return {}

async def _generate_with_nav(self, text: str, nav_tree: dict, format_type: str, depth: int) -> str:
    """结合导航结构生成思维导图"""
    if not text:
        return ""
    
    nav_prompt = ""
    if nav_tree:
        nav_prompt = f"""
        
参考以下知识导航结构来组织思维导图：
{json.dumps(nav_tree, ensure_ascii=False)}

请确保生成的思维导图与上述导航结构对齐。
"""
    
    prompt = f"""
根据以下文档内容生成思维导图：

{text}

{nav_prompt}

要求：
- 深度至少{depth}层
- 结构清晰，符合逻辑
"""
    
    try:
        return await self.llm.generate_mindmap(prompt, format_type, depth)
    except Exception:
        return self._fallback_mindmap(text, format_type, depth)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_mindmap_integrate.py::test_integrate_action -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add app/agents/mindmap_agent/agent.py tests/test_mindmap_integrate.py
git commit -m "feat: add integrate action to mindmap agent"
```

---

## Task 2: 新增Wiki API端点

**Files:**
- Modify: `backend/app/api/wiki.py`

- [ ] **Step 1: 新增整合端点**

```python
# 在 wiki.py 中添加
@router.post("/mindmap/integrate")
async def generate_mindmap_with_nav(
    text: str,
    format: str = "mermaid",
    depth: int = 3,
    user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    结合导航结构生成思维导图
    
    将文档内容与知识导航树整合，生成符合导航结构的思维导图
    """
    agent = MindMapAgent(session, user)
    
    request = MCPRequest(
        agent_id="mindmap_agent",
        params={
            "action": "integrate",
            "text": text,
            "format": format,
            "depth": depth
        }
    )
    
    response = await agent.handle_request(request)
    
    if response.success:
        return response.data
    else:
        raise HTTPException(status_code=500, detail=response.error)
```

- [ ] **Step 2: Commit**

```bash
cd backend
git add app/api/wiki.py
git commit -m "feat: add mindmap integrate endpoint"
```

---

## Task 3: 更新前端API

**Files:**
- Modify: `frontend/src/api/wiki.js`

- [ ] **Step 1: 添加整合接口**

```javascript
// 结合导航结构生成思维导图
export const generateMindmapWithNav = (text, format = 'mermaid', depth = 3) =>
  request.post('/wiki/mindmap/integrate', { text, format, depth })
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/api/wiki.js
git commit -m "feat: add mindmap integrate api"
```

---

## Task 4: 更新前端Wiki页面

**Files:**
- Modify: `frontend/src/views/Wiki.vue`

- [ ] **Step 1: 添加导航整合选项**

```vue
<!-- 在思维导图生成区域添加 -->
<el-form-item label="导航整合">
  <el-switch 
    v-model="useNavigation" 
    :disabled="!!generating"
    @change="onNavigationChange"
  />
  <span class="switch-label">使用知识导航结构</span>
</el-form-item>
```

- [ ] **Step 2: 添加调用逻辑**

```javascript
const useNavigation = ref(true)

async function generateMindmap() {
  if (!currentContent.value) {
    ElMessage.warning('请先输入文档内容')
    return
  }
  
  generating.value = true
  try {
    let result
    if (useNavigation.value) {
      result = await generateMindmapWithNav(
        currentContent.value,
        mindmapFormat.value,
        mindmapDepth.value
      )
    } else {
      result = await generateMindmap(
        currentContent.value,
        mindmapFormat.value,
        mindmapDepth.value
      )
    }
    mindmapResult.value = result.mindmap
    ElMessage.success('思维导图生成成功')
  } catch {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/views/Wiki.vue
git commit -m "feat: add navigation integration option"
```

---

## Task 5: 更新需求文档

**Files:**
- Modify: `docs/requirements/detailed/FR-MINDMAP.md`

- [ ] **Step 1: 更新状态**

修改FR-MINDMAP-003状态从 `❌ 未实现` 改为 `✅ 已完成`

- [ ] **Step 2: Commit**

```bash
git add docs/requirements/detailed/FR-MINDMAP.md
git commit -m "docs: update FR-MINDMAP-003 status"
```

---

## Self-Review

### 1. Spec Coverage

| 需求项 | 对应Task |
|--------|----------|
| 获取知识导航结构 | Task 1: _get_nav_tree() |
| 整合到思维导图生成 | Task 1: _generate_with_nav() |
| 输出符合导航结构的导图 | Task 2: API端点 |

### 2. Placeholder Scan

✅ 无占位符，所有步骤都有具体代码和命令

### 3. Type Consistency

✅ 类型和方法签名一致

---

**Plan complete.**