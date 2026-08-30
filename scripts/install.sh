#!/bin/sh
# ainovel-cli Script cài đặt một dòng
#
#   curl -fsSL https://raw.githubusercontent.com/voocel/ainovel-cli/main/scripts/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/voocel/ainovel-cli/main/scripts/install.sh | sh -s -- v1.2.3
#
# Thư mục cài đặt tùy chỉnh: AINOVEL_INSTALL_DIR=~/.local/bin curl -fsSL ... | sh
# Chỉ định phiên bản: AINOVEL_VERSION=v1.2.3 curl -fsSL ... | sh
set -e

REPO="voocel/ainovel-cli"
BIN="ainovel-cli"
DEST="${AINOVEL_INSTALL_DIR:-/usr/local/bin}"
VERSION="${AINOVEL_VERSION:-${1:-latest}}"

for cmd in curl tar; do
	command -v "$cmd" >/dev/null 2>&1 || { echo "Cần có $cmd, vui lòng cài đặt trước rồi thử lại"; exit 1; }
done

case "$(uname -s)" in
	Darwin) OS="Darwin" ;;
	Linux)  OS="Linux" ;;
	*) echo "Hệ điều hành không hỗ trợ: $(uname -s); Windows vui lòng tải thủ công tại https://github.com/$REPO/releases"; exit 1 ;;
esac

case "$(uname -m)" in
	x86_64|amd64)  ARCH="x86_64" ;;
	arm64|aarch64) ARCH="arm64" ;;
	*) echo "Kiến trúc không hỗ trợ: $(uname -m)"; exit 1 ;;
esac

if [ "$VERSION" = "latest" ] || [ -z "$VERSION" ]; then
	API="https://api.github.com/repos/$REPO/releases/latest"
	echo "Đang tìm phiên bản mới nhất..."
else
	case "$VERSION" in
		v*) TAG="$VERSION" ;;
		*) TAG="v$VERSION" ;;
	esac
	API="https://api.github.com/repos/$REPO/releases/tags/$TAG"
	echo "Đang tìm phiên bản $TAG..."
fi

RELEASE=$(curl -fsSL "$API")
TAG=$(printf '%s\n' "$RELEASE" | grep '"tag_name"' | head -1 | cut -d '"' -f 4)
URL=$(printf '%s\n' "$RELEASE" \
	| grep "browser_download_url" \
	| grep "_${OS}_${ARCH}.tar.gz" \
	| head -1 | cut -d '"' -f 4)
[ -n "$URL" ] || { echo "Không tìm thấy gói cài đặt ${OS}_${ARCH}, vui lòng tải thủ công tại https://github.com/$REPO/releases"; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Đang tải $URL"
curl -fsSL -o "$TMP/pkg.tar.gz" "$URL"
tar -xzf "$TMP/pkg.tar.gz" -C "$TMP"

echo "Đang cài đặt vào $DEST"
[ -d "$DEST" ] || mkdir -p "$DEST" 2>/dev/null || sudo mkdir -p "$DEST"
if [ -w "$DEST" ]; then
	mv "$TMP/$BIN" "$DEST/$BIN"
else
	echo "Cần quyền quản trị để ghi vào $DEST"
	sudo mv "$TMP/$BIN" "$DEST/$BIN"
fi
chmod +x "$DEST/$BIN"

# Binary chưa ký, macOS chạy lần đầu sẽ bị Gatekeeper chặn, gỡ cách ly
[ "$OS" = "Darwin" ] && xattr -d com.apple.quarantine "$DEST/$BIN" 2>/dev/null || true

echo "✓ Cài đặt hoàn tất: $DEST/$BIN"
[ -n "$TAG" ] && echo "Phiên bản: $TAG"
command -v "$BIN" >/dev/null 2>&1 || echo "Gợi ý: $DEST chưa có trong PATH, vui lòng thêm vào PATH"
echo "Chạy $BIN để bắt đầu sử dụng"
