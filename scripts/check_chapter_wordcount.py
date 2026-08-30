#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra số từ của chương
Kiểm tra số từ của tệp chương chỉ định, thông báo mở rộng nếu dưới 3000 từ
"""

import re
import sys
from pathlib import Path

# Sửa lỗi encoding console trên Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def count_words(text: str) -> int:
    """Đếm số từ (hỗ trợ cả tiếng Việt/phương Tây và ký tự chữ Hán, loại trừ markdown)"""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # Đếm ký tự chữ Hán (nếu có)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Loại bỏ ký tự chữ Hán trước khi đếm từ tiếng Việt / phương Tây
    non_cjk_text = re.sub(r'[\u4e00-\u9fff]', ' ', text)
    words = len(re.findall(r'\b\w+\b', non_cjk_text))
    return words + chinese_chars


def extract_content_from_chapter(file_path: Path) -> str:
    """Trích xuất phần nội dung chính từ file chương (loại bỏ tiêu đề và metadata)"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    content_start = 0
    for i, line in enumerate(lines):
        if line.startswith('#') and ('chương' in line.lower() or 'ch' in line.lower() or '章' in line):
            content_start = i + 1
            break

    return '\n'.join(lines[content_start:])


def check_chapter(file_path: str, min_words: int = 3000) -> dict:
    """Kiểm tra số từ của một chương đơn lẻ"""
    path = Path(file_path)
    if not path.exists():
        return {
            'file': str(path),
            'exists': False,
            'word_count': 0,
            'status': 'error',
            'message': f'Tệp không tồn tại: {file_path}',
        }

    main_content = extract_content_from_chapter(path)
    word_count = count_words(main_content)
    status = 'pass' if word_count >= min_words else 'fail'
    message = f'Số từ: {word_count}'
    if word_count >= min_words:
        message += ' (✓ Đạt chuẩn)'
    else:
        message += f' (✗ Chưa đủ, cần tối thiểu {min_words} từ)'

    return {
        'file': str(path),
        'exists': True,
        'word_count': word_count,
        'status': status,
        'message': message,
    }


def check_all_chapters(directory: str, pattern: str = '*.md', min_words: int = 3000) -> list:
    """Kiểm tra tất cả các tệp chương phù hợp trong thư mục"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f'Lỗi: Thư mục không tồn tại - {directory}')
        return []

    chapter_files = sorted([f for f in dir_path.glob(pattern) if not f.name.startswith('.') and not f.name.endswith(('.plan.json', '.json'))])
    return [check_chapter(str(chapter_file), min_words) for chapter_file in chapter_files]


def print_results(results: list, min_words: int = 3000) -> None:
    """In kết quả kiểm tra"""
    if not results:
        print('Không tìm thấy tệp chương nào')
        return

    total_words = 0
    passed = 0
    failed = 0

    print('\n' + '=' * 60)
    print('BÁO CÁO KIỂM TRA SỐ TỪ CÁC CHƯƠNG')
    print('=' * 60)

    for result in results:
        if not result['exists']:
            print(f'\n❌ {result["file"]}')
            print(f'   {result["message"]}')
            continue

        total_words += result['word_count']
        if result['status'] == 'pass':
            passed += 1
            icon = '✅'
        else:
            failed += 1
            icon = '⚠️ '

        print(f'\n{icon} {Path(result["file"]).name}')
        print(f'   {result["message"]}')

    print('\n' + '-' * 60)
    print(f'Tổng cộng: {len(results)} chương | {passed} chương đạt | {failed} chương chưa đủ | Tổng số từ: {total_words:,}')
    print('-' * 60)

    if failed > 0:
        print(f'\n⚠️  Có {failed} chương chưa đạt {min_words} từ, gợi ý mở rộng:')
        print('   - Thêm miêu tả chi tiết (bối cảnh, tâm lý, hành động)')
        print('   - Tăng thêm phân cảnh đối thoại')
        print('   - Mở rộng hoạt động nội tâm của nhân vật')
        print('   - Bổ sung câu chuyện bối cảnh')
        print('\n   Tham khảo: references/content-expansion.md')


def main() -> None:
    """Hàm chính"""
    if len(sys.argv) < 2:
        print('Cách dùng:')
        print('  Kiểm tra 1 chương:  python check_chapter_wordcount.py <đường_dẫn_tệp> [số_từ_tối_thiểu]')
        print('  Kiểm tra cả thư mục: python check_chapter_wordcount.py --all <thư_mục> [số_từ_tối_thiểu]')
        print('')
        print('Ví dụ:')
        print('  python check_chapter_wordcount.py workspace/output/novel/chapters/01.md')
        print('  python check_chapter_wordcount.py workspace/output/novel/chapters/01.md 3500')
        print('  python check_chapter_wordcount.py --all workspace/output/novel/chapters')
        print('  python check_chapter_wordcount.py --all workspace/output/novel/chapters 3500')
        return

    if sys.argv[1] == '--all':
        if len(sys.argv) < 3:
            print('Lỗi: Cần chỉ định đường dẫn thư mục khi dùng --all')
            return
        directory = sys.argv[2]
        min_words = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
        results = check_all_chapters(directory, min_words=min_words)
        print_results(results, min_words)
        return

    file_path = sys.argv[1]
    min_words = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    result = check_chapter(file_path, min_words)
    print_results([result], min_words)


if __name__ == '__main__':
    main()
