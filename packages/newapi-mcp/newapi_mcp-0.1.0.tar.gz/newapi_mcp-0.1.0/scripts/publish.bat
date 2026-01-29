@echo off
REM MCP 发布脚本 (Windows)

setlocal enabledelayedexpansion

echo 🚀 New API MCP 发布脚本
echo ========================

where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python 未安装
    exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
    echo ❌ Git 未安装
    exit /b 1
)

for /f "tokens=2 delims== " %%i in ('findstr /R "version = " pyproject.toml ^| findstr /v "^REM"') do (
    set VERSION=%%i
    set VERSION=!VERSION:"=!
    goto :version_found
)
:version_found

echo 📦 版本: %VERSION%

echo.
echo 1️⃣  检查 Git 状态...
git status --porcelain >nul 2>nul
if not errorlevel 1 (
    for /f %%i in ('git status --porcelain') do (
        echo ⚠️  工作目录有未提交的更改
        git status --short
        set /p CONTINUE="继续? (y/n): "
        if /i not "!CONTINUE!"=="y" exit /b 1
        goto :git_check_done
    )
)
:git_check_done

echo.
echo 2️⃣  运行测试...
if exist "tests" (
    python -m pytest tests/ -v
    if errorlevel 1 (
        echo ❌ 测试失败
        exit /b 1
    )
) else (
    echo ⚠️  未找到测试目录
)

echo.
echo 3️⃣  代码质量检查...

where black >nul 2>nul
if not errorlevel 1 (
    echo   - 检查代码格式...
    black --check src/
    if errorlevel 1 (
        echo ❌ 代码格式不符合要求，运行: black src/
        exit /b 1
    )
)

where ruff >nul 2>nul
if not errorlevel 1 (
    echo   - 运行 Lint...
    ruff check src/
    if errorlevel 1 (
        echo ❌ Lint 检查失败
        exit /b 1
    )
)

where mypy >nul 2>nul
if not errorlevel 1 (
    echo   - 类型检查...
    mypy src/
    if errorlevel 1 (
        echo ⚠️  类型检查有警告（非致命）
    )
)

echo.
echo 4️⃣  构建发行包...
if exist "dist" (
    rmdir /s /q dist
)

python -m build
if errorlevel 1 (
    echo ❌ 构建失败
    exit /b 1
)

echo ✅ 构建成功
dir dist\

echo.
echo 5️⃣  验证包...
where twine >nul 2>nul
if not errorlevel 1 (
    twine check dist\*
    if errorlevel 1 (
        echo ❌ 包验证失败
        exit /b 1
    )
) else (
    echo ⚠️  twine 未安装，跳过验证
)

echo.
echo 6️⃣  创建 Git 标签...
set TAG=v%VERSION%
git rev-parse %TAG% >nul 2>nul
if not errorlevel 1 (
    echo ⚠️  标签 %TAG% 已存在
) else (
    git tag -a %TAG% -m "Release version %VERSION%"
    echo ✅ 标签 %TAG% 已创建
)

echo.
echo 7️⃣  上传到 PyPI...
echo 选项:
echo   1. 上传到 PyPI（生产）
echo   2. 上传到 TestPyPI（测试）
echo   3. 跳过上传
set /p CHOICE="选择 (1-3): "

if "%CHOICE%"=="1" (
    echo 上传到 PyPI...
    where twine >nul 2>nul
    if errorlevel 1 (
        echo ❌ twine 未安装
        exit /b 1
    )
    twine upload dist\*
    echo ✅ 上传成功
) else if "%CHOICE%"=="2" (
    echo 上传到 TestPyPI...
    where twine >nul 2>nul
    if errorlevel 1 (
        echo ❌ twine 未安装
        exit /b 1
    )
    twine upload --repository testpypi dist\*
    echo ✅ 上传成功
) else if "%CHOICE%"=="3" (
    echo ⏭️  跳过上传
) else (
    echo ❌ 无效选择
    exit /b 1
)

echo.
echo ✅ 发布流程完成！
echo.
echo 后续步骤:
echo   1. 推送标签: git push origin %TAG%
echo   2. 推送代码: git push origin main
echo   3. 在 GitHub 创建 Release
echo.
echo 验证发布:
echo   pip install newapi-mcp==%VERSION%
