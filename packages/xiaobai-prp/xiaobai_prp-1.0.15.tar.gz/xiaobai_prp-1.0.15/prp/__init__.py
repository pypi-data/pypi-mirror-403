"""PRP (Python Registry Provider) - A tool for managing Python package index sources."""

__version__ = "1.0.15"


# 在包被导入时尝试自动配置最快镜像源（仅在首次使用时）
def _auto_configure_on_import():
    import os
    import atexit
    
    config_file = os.path.expanduser("~/.prp/config.json")
    flag_file = os.path.expanduser("~/.prp/.first_run_completed")
    
    # 检查是否已经完成首次运行配置
    if not os.path.exists(os.path.dirname(config_file)):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    if not os.path.exists(flag_file):
        try:
            from .main import PRP
            prp_instance = PRP()
            # 使用 atexit 确保在进程结束前执行
            def _configure_fastest():
                print("正在自动配置最快的镜像源...")
                fastest = prp_instance.find_fastest_registry()
                if fastest:
                    print(f"检测到最快的镜像源是: {fastest}")
                    prp_instance.use_registry(fastest)
                    print(f"已将 pip 配置更新为使用 {fastest} 镜像源")
                    print("安装完成！现在 pip 将默认使用最快的镜像源。")
                    
                    # 创建标志文件，表示首次运行已完成
                    config_dir = os.path.dirname(prp_instance.config_file)
                    flag_file = os.path.join(config_dir, ".first_run_completed")
                    with open(flag_file, 'w') as f:
                        f.write("completed")
                else:
                    print("未能检测到任何可用的镜像源")
            
            atexit.register(_configure_fastest)
        except ImportError:
            pass  # 如果导入失败，不执行自动配置
        except Exception:
            pass  # 忽略配置过程中的任何错误，不影响正常使用


# 在模块加载时尝试自动配置
_auto_configure_on_import()