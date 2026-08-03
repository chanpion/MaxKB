#!/usr/bin/env bash
#
# MaxKB 前端打包脚本（在「构建机」上执行）
#
# 职责：安装依赖 → 构建 Next.js standalone → 组装可直接部署的 tar.gz。
#       Node 运行时由目标机另行准备，本脚本不把开发用 node_modules / 源码打进包。
#
# 用法：
#   ./scripts/package.sh                 # 使用 package.json 中的 version
#   ./scripts/package.sh --version 1.2.3 # 显式指定版本
#   ./scripts/package.sh --out-dir dist  # 指定输出目录（默认 frontend/dist）
#
# 前置条件：
#   - Node.js >= 18.17（Next.js 14.2 要求）
#   - npm（需支持 `npm ci`，故必须有 package-lock.json）
#   - 从 frontend/ 项目根目录运行（脚本会自动定位项目根）

set -euo pipefail

# ---------- 定位项目根目录 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------- 解析参数 ----------
VERSION=""
OUT_DIR="${PROJECT_DIR}/dist"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    -h|--help)  sed -n '8,18p' "$0"; exit 0 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

cd "${PROJECT_DIR}"

# 读取版本（优先参数，其次 package.json）
if [[ -z "${VERSION}" ]]; then
  VERSION="$(node -p "require('./package.json').version" 2>/dev/null || echo "0.0.0")"
fi

echo "==> [package] 前端版本: ${VERSION}"
echo "==> [package] 项目目录: ${PROJECT_DIR}"

# ---------- 检查前置依赖 ----------
command -v node >/dev/null 2>&1 || { echo "ERROR: 未检测到 node，请先安装 Node.js (>=18.17)" >&2; exit 1; }
command -v npm  >/dev/null 2>&1 || { echo "ERROR: 未检测到 npm" >&2; exit 1; }
[[ -f package-lock.json ]] || { echo "ERROR: 缺少 package-lock.json，无法使用 npm ci" >&2; exit 1; }

echo "==> [package] node: $(node -v)  npm: $(npm -v)"

# ---------- 安装依赖并构建 ----------
echo "==> [package] 安装依赖 (npm ci) ..."
npm ci

echo "==> [package] 构建 (npm run build) ..."
npm run build

# ---------- 组装部署包 ----------
STAGE="${PROJECT_DIR}/.pkg_stage"
PKG_NAME="maxkb-frontend-${VERSION}"
PKG_DIR="${STAGE}/${PKG_NAME}"
rm -rf "${STAGE}"
mkdir -p "${PKG_DIR}"

echo "==> [package] 组装部署目录 ..."

# 1) standalone 运行时（server.js + 精简 node_modules）
cp -R ".next/standalone/." "${PKG_DIR}/"

# 2) 静态资源必须放进 standalone 内部，server.js 才能正确托管
mkdir -p "${PKG_DIR}/.next"
cp -R ".next/static" "${PKG_DIR}/.next/static"
cp -R "public"       "${PKG_DIR}/public"

# 3) 配置与启动辅助文件
cp ".env.example"                       "${PKG_DIR}/.env.example"
cp "${PROJECT_DIR}/deploy.sh"           "${PKG_DIR}/deploy.sh"
mkdir -p "${PKG_DIR}/config/systemd"
cp "${PROJECT_DIR}/config/systemd/maxkb-frontend.service" "${PKG_DIR}/config/systemd/"
[[ -f DEPLOY.md ]] && cp DEPLOY.md "${PKG_DIR}/DEPLOY.md"

# 4) 版本号
echo "${VERSION}" > "${PKG_DIR}/VERSION"

# ---------- 生成 tar ----------
mkdir -p "${OUT_DIR}"
TAR_PATH="${OUT_DIR}/${PKG_NAME}.tar.gz"
tar -C "${STAGE}" -czf "${TAR_PATH}" "${PKG_NAME}"

# ---------- 清理临时目录 ----------
rm -rf "${STAGE}"

echo "==> [package] 完成: ${TAR_PATH}"
echo "==> [package] 体积: $(du -h "${TAR_PATH}" | cut -f1)"
