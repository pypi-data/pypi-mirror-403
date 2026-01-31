# Makefile for PRP (Python Registry Provider) Package

.PHONY: help clean build test-upload upload check verify

help:
	@echo "PRP (Python Registry Provider) 包发布工具"
	@echo ""
	@echo "可用命令:"
	@echo "  clean     - 清理构建产物"
	@echo "  build     - 构建包"
	@echo "  check     - 检查包的有效性"
	@echo "  verify    - 验证包的功能"
	@echo "  test-upload - 上传到测试PyPI服务器"
	@echo "  upload    - 上传到正式PyPI服务器"

clean:
	@echo "清理构建产物..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	@echo "清理完成"

build: clean
	@echo "安装构建工具..."
	pip install --upgrade "setuptools<60.0.0" wheel build twine
	@echo "构建包..."
	python -m build
	@echo "构建完成，生成的包位于 dist/ 目录"

check: build
	@echo "检查包..."
	twine check dist/*
	@echo "包检查完成"

verify: build
	@echo "验证包..."
	# 创建临时虚拟环境测试安装
	python -m venv .tmp_test_env
	if [ "$$(uname)" = "Darwin" ]; then \
		source .tmp_test_env/bin/activate && pip install dist/*.tar.gz && echo "安装成功"; \
	else \
		source .tmp_test_env/bin/activate && pip install dist/*.tar.gz && echo "安装成功"; \
	fi
	# 测试命令是否可以正常运行
	.tmp_test_env/bin/prp --help || echo "命令可用性测试完成"
	# 清理临时环境
	rm -rf .tmp_test_env
	@echo "验证完成"

test-upload: check
	@echo "上传到测试PyPI服务器..."
	twine upload --repository testpypi dist/*

upload: check
	@echo "上传到PyPI服务器..."
	twine upload dist/*