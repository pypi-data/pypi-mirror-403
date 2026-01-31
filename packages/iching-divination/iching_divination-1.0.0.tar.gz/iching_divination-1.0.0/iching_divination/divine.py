#!/usr/bin/env python3
"""
IChing Divination Calculator - 易经解卦计算

A robust implementation of the Three-Coin Divination method (三硬币起卦法).
All calculations are performed by this script to ensure accuracy.

Usage:
    python divine.py <6 numbers>
    Example: python divine.py 687766

Note for AI assistants: Always use this script for calculations.
Do not calculate hexagrams manually as AI is prone to errors in:
- Trigram mapping (e.g., confusing 震 vs 艮)
- Yao order (bottom vs top)
- Hexagram naming
"""

import sys
from typing import List, Tuple, Dict, Optional, Final


# ============ Constants ============

YAO_SYMBOLS: Final[Dict[int, Tuple[str, bool, str]]] = {
    6: ("⚋", True, "老阴 (Old Yin)"),      # Moving
    7: ("⚊", False, "少阳 (Young Yang)"),  # Static
    8: ("⚋", False, "少阴 (Young Yin)"),   # Static
    9: ("⚊", True, "老阳 (Old Yang)"),     # Moving
}

# Trigram mapping: (初爻, 二爻, 三爻) -> (name, symbol, natural)
# Order is from bottom (初爻) to top (三爻)
TRIGRAMS: Final[Dict[Tuple[str, str, str], Tuple[str, str, str]]] = {
    ("⚊", "⚊", "⚊"): ("乾", "☰", "天 (Heaven)"),
    ("⚊", "⚊", "⚋"): ("兑", "☱", "泽 (Lake)"),
    ("⚊", "⚋", "⚊"): ("离", "☲", "火 (Fire)"),
    ("⚊", "⚋", "⚋"): ("震", "☳", "雷 (Thunder)"),   # Yang at bottom
    ("⚋", "⚊", "⚊"): ("巽", "☴", "风 (Wind)"),
    ("⚋", "⚊", "⚋"): ("坎", "☵", "水 (Water)"),     # Yang at middle
    ("⚋", "⚋", "⚊"): ("艮", "☶", "山 (Mountain)"),  # Yang at top
    ("⚋", "⚋", "⚋"): ("坤", "☷", "地 (Earth)"),
}

# 64 Hexagrams mapping: (upper, lower) -> name
HEXAGRAM_NAMES: Final[Dict[Tuple[str, str], str]] = {
    # Qian (Heaven) upper
    ("乾", "乾"): "乾为天 (The Creative)",
    ("乾", "兑"): "天泽履 (Treading)",
    ("乾", "离"): "天火同人 (Fellowship)",
    ("乾", "震"): "天雷无妄 (Innocence)",
    ("乾", "巽"): "天风姤 (Coming to Meet)",
    ("乾", "坎"): "天水讼 (Conflict)",
    ("乾", "艮"): "天山遁 (Retreat)",
    ("乾", "坤"): "天地否 (Stagnation)",
    # Dui (Lake) upper
    ("兑", "乾"): "泽天夬 (Breakthrough)",
    ("兑", "兑"): "兑为泽 (The Joyous)",
    ("兑", "离"): "泽火革 (Revolution)",
    ("兑", "震"): "泽雷随 (Following)",
    ("兑", "巽"): "泽风大过 (Preponderance of the Great)",
    ("兑", "坎"): "泽水困 (Exhaustion)",
    ("兑", "艮"): "泽山咸 (Influence)",
    ("兑", "坤"): "泽地萃 (Gathering Together)",
    # Li (Fire) upper
    ("离", "乾"): "火天大有 (Possession in Great Measure)",
    ("离", "兑"): "火泽睽 (Opposition)",
    ("离", "离"): "离为火 (The Clinging)",
    ("离", "震"): "火雷噬嗑 (Biting Through)",
    ("离", "巽"): "火风鼎 (The Cauldron)",
    ("离", "坎"): "火水未济 (Before Completion)",
    ("离", "艮"): "火山旅 (The Wanderer)",
    ("离", "坤"): "火地晋 (Progress)",
    # Zhen (Thunder) upper
    ("震", "乾"): "雷天大壮 (The Power of the Great)",
    ("震", "兑"): "雷泽归妹 (The Marrying Maiden)",
    ("震", "离"): "雷火丰 (Abundance)",
    ("震", "震"): "震为雷 (The Arousing)",
    ("震", "巽"): "雷风恒 (Duration)",
    ("震", "坎"): "雷水解 (Deliverance)",
    ("震", "艮"): "雷山小过 (Small Excess)",
    ("震", "坤"): "雷地豫 (Enthusiasm)",
    # Xun (Wind) upper
    ("巽", "乾"): "风天小畜 (The Taming Power of the Small)",
    ("巽", "兑"): "风泽中孚 (Inner Truth)",
    ("巽", "离"): "风火家人 (The Family)",
    ("巽", "震"): "风雷益 (Increase)",
    ("巽", "巽"): "巽为风 (The Gentle)",
    ("巽", "坎"): "风水涣 (Dispersion)",
    ("巽", "艮"): "风山渐 (Development)",
    ("巽", "坤"): "风地观 (Contemplation)",
    # Kan (Water) upper
    ("坎", "乾"): "水天需 (Waiting)",
    ("坎", "兑"): "水泽节 (Limitation)",
    ("坎", "离"): "水火既济 (After Completion)",
    ("坎", "震"): "水雷屯 (Difficulty at the Beginning)",
    ("坎", "巽"): "水风井 (The Well)",
    ("坎", "坎"): "坎为水 (The Abysmal)",
    ("坎", "艮"): "水山蹇 (Obstruction)",
    ("坎", "坤"): "水地比 (Holding Together)",
    # Gen (Mountain) upper
    ("艮", "乾"): "山天大畜 (The Taming Power of the Great)",
    ("艮", "兑"): "山泽损 (Decrease)",
    ("艮", "离"): "山火贲 (Grace)",
    ("艮", "震"): "山雷颐 (The Corners of the Mouth)",
    ("艮", "巽"): "山风蛊 (Work on What Has Been Spoiled)",
    ("艮", "坎"): "山水蒙 (Youthful Folly)",
    ("艮", "艮"): "艮为山 (Keeping Still)",
    ("艮", "坤"): "山地剥 (Splitting Apart)",
    # Kun (Earth) upper
    ("坤", "乾"): "地天泰 (Peace)",
    ("坤", "兑"): "地泽临 (Approach)",
    ("坤", "离"): "地火明夷 (Darkening of the Light)",
    ("坤", "震"): "地雷复 (Return)",
    ("坤", "巽"): "地风升 (Pushing Upward)",
    ("坤", "坎"): "地水师 (The Army)",
    ("坤", "艮"): "地山谦 (Modesty)",
    ("坤", "坤"): "坤为地 (The Receptive)",
}

YAO_POSITIONS: Final[List[str]] = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]


# ============ Core Functions ============

def calculate_hexagram(numbers: List[int]) -> Dict:
    """
    Calculate hexagram from 6 numbers.
    
    This is the main entry point for all divination calculations.
    AI assistants MUST use this function - do not calculate manually!
    
    Args:
        numbers: List of 6 integers (6, 7, 8, or 9) representing yaos
                from bottom (1st) to top (6th)
    
    Returns:
        Dictionary containing:
        - numbers: Original input
        - yao_symbols: List of yao symbols (⚋ or ⚊)
        - ben_gua: Original hexagram name (本卦)
        - bian_gua: Changed hexagram name (变卦), or None
        - lower_trigram: Lower trigram name
        - upper_trigram: Upper trigram name
        - changed_lower: Changed lower trigram (for 变卦)
        - changed_upper: Changed upper trigram (for 变卦)
        - moving_yaos: List of moving yao positions
        - has_moving: Boolean indicating if there are moving yaos
    
    Raises:
        ValueError: If input is not 6 numbers or contains invalid numbers
    
    Example:
        >>> result = calculate_hexagram([6, 8, 7, 7, 6, 6])
        >>> result['ben_gua']
        '雷山小过 (Small Excess)'
    """
    if len(numbers) != 6:
        raise ValueError(f"需要6个数字，实际得到{len(numbers)}个 (Expected 6 numbers, got {len(numbers)})")
    
    for n in numbers:
        if n not in (6, 7, 8, 9):
            raise ValueError(f"无效数字: {n}，必须是6,7,8,9 (Invalid number: {n}, must be 6,7,8,9)")
    
    # Convert to yao symbols and track moving status
    symbols: List[str] = []
    movings: List[bool] = []
    
    for n in numbers:
        symbol, is_moving, _ = YAO_SYMBOLS[n]
        symbols.append(symbol)
        movings.append(is_moving)
    
    # Find moving yao positions
    moving_positions = [
        YAO_POSITIONS[i] for i, is_moving in enumerate(movings) if is_moving
    ]
    
    # Form original trigrams
    # Lower: positions 1-3 (index 0-2)
    # Upper: positions 4-6 (index 3-5)
    lower = tuple(symbols[0:3])
    upper = tuple(symbols[3:6])
    
    lower_info = TRIGRAMS[lower]
    upper_info = TRIGRAMS[upper]
    
    lower_name = lower_info[0]
    upper_name = upper_info[0]
    
    ben_gua = HEXAGRAM_NAMES.get((upper_name, lower_name), f"{upper_name}上{lower_name}")
    
    # Calculate changed hexagram
    changed_symbols = symbols.copy()
    for i, is_moving in enumerate(movings):
        if is_moving:
            # Flip yin/yang
            changed_symbols[i] = "⚊" if symbols[i] == "⚋" else "⚋"
    
    changed_lower = tuple(changed_symbols[0:3])
    changed_upper = tuple(changed_symbols[3:6])
    
    changed_lower_name = TRIGRAMS[changed_lower][0]
    changed_upper_name = TRIGRAMS[changed_upper][0]
    
    bian_gua: Optional[str] = None
    if moving_positions:
        bian_gua = HEXAGRAM_NAMES.get(
            (changed_upper_name, changed_lower_name),
            f"{changed_upper_name}上{changed_lower_name}"
        )
    
    return {
        "numbers": numbers,
        "yao_symbols": symbols,
        "ben_gua": ben_gua,
        "bian_gua": bian_gua,
        "lower_trigram": lower_name,
        "upper_trigram": upper_name,
        "changed_lower": changed_lower_name if moving_positions else lower_name,
        "changed_upper": changed_upper_name if moving_positions else upper_name,
        "moving_yaos": moving_positions,
        "has_moving": len(moving_positions) > 0,
    }


def format_result(result: Dict) -> str:
    """
    Format calculation result for display.
    
    Args:
        result: Dictionary from calculate_hexagram()
    
    Returns:
        Formatted string for terminal display
    """
    lines = []
    lines.append("\n" + "="*50)
    lines.append("☯ IChing Divination Result | 易经解卦结果")
    lines.append("="*50)
    
    lines.append(f"\n📊 Input | 输入: {result['numbers']}")
    
    lines.append("\nYao Analysis | 爻象分析:")
    for i, pos in enumerate(YAO_POSITIONS):
        symbol = result['yao_symbols'][i]
        number = result['numbers'][i]
        _, is_moving, name = YAO_SYMBOLS[number]
        marker = " 🔥 Moving" if pos in result['moving_yaos'] else ""
        lines.append(f"  {pos}: {number} → {symbol} ({name}){marker}")
    
    lines.append("\n" + "-"*50)
    lines.append("📜 Original Hexagram | 本卦")
    lines.append("-"*50)
    lines.append(f"  Lower Trigram | 下卦: {result['lower_trigram']}")
    lines.append(f"  Upper Trigram | 上卦: {result['upper_trigram']}")
    lines.append(f"  Name | 卦名: {result['ben_gua']}")
    
    if result['bian_gua']:
        lines.append("\n" + "-"*50)
        lines.append("🔄 Changed Hexagram | 变卦")
        lines.append("-"*50)
        lines.append(f"  Lower Trigram | 下卦: {result['changed_lower']}")
        lines.append(f"  Upper Trigram | 上卦: {result['changed_upper']}")
        lines.append(f"  Name | 卦名: {result['bian_gua']}")
        lines.append(f"\n  Moving Yaos | 动爻: {', '.join(result['moving_yaos'])}")
    else:
        lines.append("\n  (No moving yaos | 无动爻，本卦即变卦)")
    
    lines.append("\n" + "="*50)
    return "\n".join(lines)


def main() -> None:
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("☯ IChing Divination | 易经解卦")
        print("="*50)
        print("\nUsage | 用法: python divine.py <6 numbers>")
        print("Example | 示例: python divine.py 687766")
        print("\nNumber Meanings | 数字含义:")
        print("  6 = 老阴 (Old Yin) - Moving | 动爻")
        print("  7 = 少阳 (Young Yang) - Static")
        print("  8 = 少阴 (Young Yin) - Static")
        print("  9 = 老阳 (Old Yang) - Moving | 动爻")
        print("\n⚠️  AI Assistants: Always use this script - never calculate manually!")
        print("    AI助手：必须使用此脚本计算，禁止口算！")
        sys.exit(1)
    
    input_str = sys.argv[1]
    numbers = [int(c) for c in input_str if c.isdigit() and c in "6789"]
    
    try:
        result = calculate_hexagram(numbers)
        print(format_result(result))
    except ValueError as e:
        print(f"❌ Error | 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
