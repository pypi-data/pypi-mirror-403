import pytest
import sys
import os

# 添加项目根目录到Python路径，以便正确导入prp模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from prp.main import PRP

def test_add_registry():
    """
    测试添加镜像源
    """
    prp = PRP()
    # 修复测试：添加有效的镜像源
    prp.add_registry("test_registry", "https://test.registry.com/simple/", "https://test.registry.com/")
    # 检查镜像源是否被正确添加
    assert "test_registry" in prp.registries

def test_delete_registry():
    """
    测试删除镜像源
    """
    prp = PRP()
    # 先添加一个镜像源
    prp.add_registry("temp_registry", "https://temp.registry.com/simple/", "https://temp.registry.com/")
    # 确认镜像源存在
    assert "temp_registry" in prp.registries
    # 删除镜像源
    prp.delete_registry("temp_registry")
    # 检查镜像源是否被删除
    assert "temp_registry" not in prp.registries

def test_use_registry():
    """
    测试使用镜像源
    """
    prp = PRP()
    # 添加一个镜像源用于测试
    prp.add_registry("test_registry", "https://test.registry.com/simple/", "https://test.registry.com/")
    # 切换到该镜像源
    result = prp.use_registry("test_registry")
    # 检查是否切换成功
    assert result is True
    assert prp.current_registry == "test_registry"

def test_list_registries(capsys):
    """
    测试列出所有镜像源
    """
    prp = PRP()
    # 调用list_registries方法
    prp.list_registries()
    # 捕获输出
    captured = capsys.readouterr()
    # 检查输出是否包含镜像源列表
    assert "Available Registries:" in captured.out

def test_current_registry_info(capsys):
    """
    测试显示当前镜像源信息
    """
    prp = PRP()
    # 调用current_registry_info方法
    prp.current_registry_info()
    # 捕获输出
    captured = capsys.readouterr()
    # 检查输出是否包含当前镜像源信息
    assert "Current registry:" in captured.out

def test_add_multiple_registries():
    """
    测试批量添加镜像源
    Testing adding multiple registries
    """
    prp = PRP()
    # 添加多个镜像源
    prp.add_registry(
        "multi_test1", "https://multi1.test.com/simple/", "https://multi1.test.com/",
        "multi_test2", "https://multi2.test.com/simple/", "https://multi2.test.com/"
    )
    # 检查镜像源是否被正确添加
    assert "multi_test1" in prp.registries
    assert "multi_test2" in prp.registries
    assert prp.registries["multi_test1"]["url"] == "https://multi1.test.com/simple/"
    assert prp.registries["multi_test2"]["url"] == "https://multi2.test.com/simple/"

def test_delete_multiple_registries():
    """
    测试批量删除镜像源
    Testing deleting multiple registries
    """
    prp = PRP()
    # 先添加多个镜像源
    prp.add_registry(
        "multi_del1", "https://multidel1.test.com/simple/", "https://multidel1.test.com/",
        "multi_del2", "https://multidel2.test.com/simple/", "https://multidel2.test.com/",
        "multi_del3", "https://multidel3.test.com/simple/", "https://multidel3.test.com/"
    )
    
    # 确认镜像源存在
    assert "multi_del1" in prp.registries
    assert "multi_del2" in prp.registries
    assert "multi_del3" in prp.registries
    
    # 删除多个镜像源
    prp.delete_registry("multi_del1", "multi_del2")
    
    # 检查镜像源是否被删除
    assert "multi_del1" not in prp.registries
    assert "multi_del2" not in prp.registries
    assert "multi_del3" in prp.registries  # multi_del3 应该仍然存在

def test_use_multiple_registries():
    """
    测试使用多个镜像源（主要源+额外源）
    Testing using multiple registries (primary + additional)
    """
    prp = PRP()
    # 添加多个镜像源用于测试
    prp.add_registry(
        "primary_registry", "https://primary.test.com/simple/", "https://primary.test.com/",
        "secondary_registry", "https://secondary.test.com/simple/", "https://secondary.test.com/",
        "tertiary_registry", "https://tertiary.test.com/simple/", "https://tertiary.test.com/"
    )
    
    # 切换到多个镜像源（第一个为主要，其余为额外源）
    result = prp.use_registry("primary_registry", "secondary_registry", "tertiary_registry")
    
    # 检查是否切换成功
    assert result is True
    assert prp.current_registry == "primary_registry"
    assert hasattr(prp, 'extra_registries')
    assert "secondary_registry" in getattr(prp, 'extra_registries', [])
    assert "tertiary_registry" in getattr(prp, 'extra_registries', [])

def test_protect_default_registries():
    """
    测试默认镜像源不能被删除
    Testing that default registries cannot be deleted
    """
    prp = PRP()
    initial_count = len(prp.registries)
    
    # 尝试删除默认镜像源（应该失败）
    prp.delete_registry("pypi")
    
    # 检查默认镜像源是否仍然存在
    assert "pypi" in prp.registries
    assert len(prp.registries) == initial_count  # 镜像源数量应该不变

def test_reset_to_defaults():
    """
    测试恢复默认配置
    Testing reset to default configuration
    """
    prp = PRP()
    
    # 添加一个自定义镜像源
    prp.add_registry("custom_registry", "https://custom.test.com/simple/", "https://custom.test.com/")
    assert "custom_registry" in prp.registries
    
    # 记录当前镜像源数量
    current_count = len(prp.registries)
    
    # 恢复默认配置
    result = prp.reset_to_defaults()
    
    # 检查是否成功恢复
    assert result is True
    assert "pypi" in prp.registries
    assert "tuna" in prp.registries
    assert "aliyun" in prp.registries
    assert "custom_registry" not in prp.registries  # 自定义镜像源应该被移除
    assert prp.current_registry == "pypi"  # 当前镜像源应该恢复为pypi