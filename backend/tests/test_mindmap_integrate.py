"""思维导图导航整合测试"""
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
    assert response.data.get("aligned_with_navigation") == True
    mock_nav_agent.handle_request.assert_called_once()


@pytest.mark.asyncio
async def test_integrate_action_no_nav_agent():
    """测试当导航Agent不可用时的降级处理"""
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_user.username = "admin"
    mock_user.roles = ["admin"]
    
    agent = MindMapAgent(mock_session, mock_user)
    
    with patch('app.agents.mindmap_agent.agent.get_registry') as mock_registry:
        mock_registry.return_value.get_agent.return_value = None
        
        with patch.object(agent, 'llm') as mock_llm:
            mock_llm.generate_mindmap.return_value = '{"name": "降级导图"}'
            
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


@pytest.mark.asyncio
async def test_generate_with_navigation_param():
    """测试generate action的use_navigation参数"""
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_user.username = "admin"
    mock_user.roles = ["admin"]
    
    agent = MindMapAgent(mock_session, mock_user)
    
    with patch.object(agent, 'llm') as mock_llm:
        mock_llm.generate_mindmap.return_value = '{"name": "测试导图"}'
        
        request = MagicMock()
        request.params = {
            "action": "generate",
            "text": "测试内容",
            "format": "json",
            "depth": 2,
            "use_navigation": False
        }
        
        response = await agent.handle_request(request)
    
    assert response.success == True