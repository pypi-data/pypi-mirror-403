#!/bin/bash

# Python Registry Provider (PRP) - 发布脚本
# 用于构建和上传PRP包到PyPI服务器

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_message() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# 默认参数
TEST_PYPI=false
VERIFY_BEFORE_UPLOAD=true
CLEAN_ONLY=false

# 显示帮助信息
show_help() {
    cat << EOF
PRP (Python Registry Provider) 发布脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -t, --test              上传到测试PyPI服务器
    -s, --skip-verify       跳过上传前验证
    -c, --clean-only        只清理旧的构建产物

示例:
    $0                      # 构建并上传到PyPI
    $0 -t                   # 构建并上传到测试PyPI
    $0 -t -s                # 构建并上传到测试PyPI，跳过验证
    $0 -c                   # 只清理构建产物
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test)
            TEST_PYPI=true
            shift
            ;;
        -s|--skip-verify)
            VERIFY_BEFORE_UPLOAD=false
            shift
            ;;
        -c|--clean-only)
            CLEAN_ONLY=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主程序
main() {
    if [ "$CLEAN_ONLY" = true ]; then
        print_message "清理旧的构建产物..."
        rm -rf build/ dist/ *.egg-info/
        print_message "清理完成"
        exit 0
    fi

    print_message "开始构建和发布PRP包到PyPI..."

    # 检查Python和pip
    if ! command -v python3 &> /dev/null; then
        print_error "错误: 未找到python3"
        exit 1
    fi

    if ! command -v pip &> /dev/null; then
        print_error "错误: 未找到pip"
        exit 1
    fi

    # 安装构建工具
    print_message "安装/升级构建工具..."
    pip install --upgrade "setuptools<60.0.0" "wheel" "build" "twine"

    # 清理之前的构建产物
    print_message "清理旧的构建产物..."
    rm -rf build/ dist/ *.egg-info/

    # 构建包
    print_message "构建包..."
    python3 -m build

    # xiaobai-prp-*.tar.gz 改为 xiaobai_prp-*.tar.gz
    for file in dist/*.tar.gz; do
        mv "$file" "$(echo "$file" | sed 's/xiaobai-prp-/xiaobai_prp-/')"
    done

    # 检查包
    print_message "检查包..."
    twine check dist/*

    # 可选：验证包
    if [ "$VERIFY_BEFORE_UPLOAD" = true ]; then
        print_message "验证包功能..."
        
        # 创建临时虚拟环境
        VENV_NAME=".tmp_prp_test_env"
        python3 -m venv "$VENV_NAME"
        
        # 激活虚拟环境并安装包
        source "$VENV_NAME/bin/activate"
        pip install dist/*.tar.gz
        
        # 测试prp命令
        print_message "测试prp命令..."
        prp --help
        
        # 清理虚拟环境
        deactivate
        rm -rf "$VENV_NAME"
        
        print_message "验证完成"
    fi

    # 上传到PyPI
    if [ "$TEST_PYPI" = true ]; then
        print_message "上传到测试PyPI服务器..."
        twine upload --repository testpypi dist/*
    else
        print_message "上传到PyPI服务器..."
        twine upload dist/*
    fi

    print_message "发布完成！"
}

main "$@"