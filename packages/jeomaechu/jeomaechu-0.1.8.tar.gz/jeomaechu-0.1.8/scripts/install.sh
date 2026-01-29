#!/bin/bash
# jeomaechu (점메추) Quick Installer
set -e

echo "🍱 점메추(jeomaechu) 설치를 시작합니다..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 에러: python3가 설치되어 있지 않습니다."
    exit 1
fi

# Install via Pip
echo "📦 최신 버전을 GitHub에서 설치합니다..."
python3 -m pip install "git+https://github.com/hslcrb/pypack_jeomaechu.git"

echo "✅ 설치가 완료되었습니다!"
echo "🚀 이제 터미널에 'jeomaechu' 또는 'j'를 입력하여 실행해보세요!"
echo ""
jeomaechu --version || echo "💡 점심 메뉴 추천을 받으려면 'jeomaechu'를 입력하세요."
