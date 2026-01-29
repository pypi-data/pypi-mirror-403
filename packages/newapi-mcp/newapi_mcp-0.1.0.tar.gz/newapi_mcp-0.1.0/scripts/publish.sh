#!/bin/bash
# MCP 发布脚本

set -e

echo "🚀 New API MCP 发布脚本"
echo "========================"

# 检查必要工具
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    exit 1
fi

# 获取版本号
VERSION=$(grep 'version = ' pyproject.toml | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')
echo "📦 版本: $VERSION"

# 步骤 1: 检查 Git 状态
echo ""
echo "1️⃣  检查 Git 状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  工作目录有未提交的更改"
    git status --short
    read -p "继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 步骤 2: 运行测试
echo ""
echo "2️⃣  运行测试..."
if [ -d "tests" ]; then
    python -m pytest tests/ -v || {
        echo "❌ 测试失败"
        exit 1
    }
else
    echo "⚠️  未找到测试目录"
fi

# 步骤 3: 代码质量检查
echo ""
echo "3️⃣  代码质量检查..."

if command -v black &> /dev/null; then
    echo "  - 检查代码格式..."
    black --check src/ || {
        echo "❌ 代码格式不符合要求，运行: black src/"
        exit 1
    }
fi

if command -v ruff &> /dev/null; then
    echo "  - 运行 Lint..."
    ruff check src/ || {
        echo "❌ Lint 检查失败"
        exit 1
    }
fi

if command -v mypy &> /dev/null; then
    echo "  - 类型检查..."
    mypy src/ || {
        echo "⚠️  类型检查有警告（非致命）"
    }
fi

# 步骤 4: 构建包
echo ""
echo "4️⃣  构建发行包..."
if [ -d "dist" ]; then
    rm -rf dist/
fi

python -m build || {
    echo "❌ 构建失败"
    exit 1
}

echo "✅ 构建成功"
ls -lh dist/

# 步骤 5: 验证包
echo ""
echo "5️⃣  验证包..."
if command -v twine &> /dev/null; then
    twine check dist/* || {
        echo "❌ 包验证失败"
        exit 1
    }
else
    echo "⚠️  twine 未安装，跳过验证"
fi

# 步骤 6: 创建 Git 标签
echo ""
echo "6️⃣  创建 Git 标签..."
TAG="v$VERSION"
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "⚠️  标签 $TAG 已存在"
else
    git tag -a "$TAG" -m "Release version $VERSION"
    echo "✅ 标签 $TAG 已创建"
fi

# 步骤 7: 上传到 PyPI
echo ""
echo "7️⃣  上传到 PyPI..."
echo "选项:"
echo "  1. 上传到 PyPI（生产）"
echo "  2. 上传到 TestPyPI（测试）"
echo "  3. 跳过上传"
read -p "选择 (1-3): " choice

case $choice in
    1)
        echo "上传到 PyPI..."
        if command -v twine &> /dev/null; then
            twine upload dist/*
            echo "✅ 上传成功"
        else
            echo "❌ twine 未安装"
            exit 1
        fi
        ;;
    2)
        echo "上传到 TestPyPI..."
        if command -v twine &> /dev/null; then
            twine upload --repository testpypi dist/*
            echo "✅ 上传成功"
        else
            echo "❌ twine 未安装"
            exit 1
        fi
        ;;
    3)
        echo "⏭️  跳过上传"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 发布流程完成！"
echo ""
echo "后续步骤:"
echo "  1. 推送标签: git push origin $TAG"
echo "  2. 推送代码: git push origin main"
echo "  3. 在 GitHub 创建 Release"
echo ""
echo "验证发布:"
echo "  pip install newapi-mcp==$VERSION"
