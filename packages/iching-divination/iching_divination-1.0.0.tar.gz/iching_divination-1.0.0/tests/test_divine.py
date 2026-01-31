#!/usr/bin/env python3
"""
Test suite for iching-divination
Tests the core calculation logic for accuracy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from iching_divination.divine import calculate_hexagram


class TestHexagramCalculation:
    """Test hexagram calculation with known examples"""
    
    def test_user_case_687766(self):
        """
        Test case: 687766
        - Lower: 6,8,7 = ⚋⚋⚊ = 艮 (Mountain)
        - Upper: 7,6,6 = ⚊⚋⚋ = 震 (Thunder)
        - Result: 雷山小过 (Small Excess)
        - Moving: 初爻, 五爻, 上爻
        """
        result = calculate_hexagram([6, 8, 7, 7, 6, 6])
        
        assert result['ben_gua'] == "雷山小过"
        assert result['lower_trigram'] == "艮"
        assert result['upper_trigram'] == "震"
        assert result['bian_gua'] == "天火同人"
        assert result['moving_yaos'] == ["初爻", "五爻", "上爻"]
        assert result['has_moving'] is True
    
    def test_qian_wei_tian(self):
        """
        Test: 乾为天 (The Creative)
        All yang, no moving
        777777 = ⚊⚊⚊⚊⚊⚊
        """
        result = calculate_hexagram([7, 7, 7, 7, 7, 7])
        
        assert result['ben_gua'] == "乾为天"
        assert result['lower_trigram'] == "乾"
        assert result['upper_trigram'] == "乾"
        assert result['bian_gua'] is None
        assert result['moving_yaos'] == []
        assert result['has_moving'] is False
    
    def test_kun_wei_di(self):
        """
        Test: 坤为地 (The Receptive)
        All yin, no moving
        888888 = ⚋⚋⚋⚋⚋⚋
        """
        result = calculate_hexagram([8, 8, 8, 8, 8, 8])
        
        assert result['ben_gua'] == "坤为地"
        assert result['lower_trigram'] == "坤"
        assert result['upper_trigram'] == "坤"
        assert result['bian_gua'] is None
    
    def test_tai_hexagram(self):
        """
        Test: 地天泰 (Peace)
        Lower: 777 = ⚊⚊⚊ = 乾 (Heaven)
        Upper: 888 = ⚋⚋⚋ = 坤 (Earth)
        777888
        """
        result = calculate_hexagram([7, 7, 7, 8, 8, 8])
        
        assert result['ben_gua'] == "地天泰"
        assert result['lower_trigram'] == "乾"
        assert result['upper_trigram'] == "坤"
    
    def test_pi_hexagram(self):
        """
        Test: 天地否 (Stagnation)
        Lower: 888 = ⚋⚋⚋ = 坤 (Earth)
        Upper: 777 = ⚊⚊⚊ = 乾 (Heaven)
        888777
        """
        result = calculate_hexagram([8, 8, 8, 7, 7, 7])
        
        assert result['ben_gua'] == "天地否"
        assert result['lower_trigram'] == "坤"
        assert result['upper_trigram'] == "乾"
    
    def test_single_moving_yao(self):
        """Test with only one moving yao"""
        # 9 in second position only
        # 7,9,7,8,8,8
        result = calculate_hexagram([7, 9, 7, 8, 8, 8])
        
        assert result['moving_yaos'] == ["二爻"]
        assert result['has_moving'] is True
    
    def test_all_moving_yaos(self):
        """Test with all moving yaos"""
        # Alternating 6 and 9
        result = calculate_hexagram([6, 9, 6, 9, 6, 9])
        
        assert len(result['moving_yaos']) == 6
        assert result['has_moving'] is True
    
    def test_ben_gua_consistency(self):
        """Test that the same input always produces the same output"""
        result1 = calculate_hexagram([6, 8, 7, 7, 6, 6])
        result2 = calculate_hexagram([6, 8, 7, 7, 6, 6])
        
        assert result1 == result2


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_length_short(self):
        """Test with less than 6 numbers"""
        with pytest.raises(ValueError, match="需要6个数字"):
            calculate_hexagram([6, 7, 8])
    
    def test_invalid_length_long(self):
        """Test with more than 6 numbers"""
        with pytest.raises(ValueError, match="需要6个数字"):
            calculate_hexagram([6, 7, 8, 7, 6, 6, 7])
    
    def test_invalid_number_5(self):
        """Test with invalid number 5"""
        with pytest.raises(ValueError, match="无效数字"):
            calculate_hexagram([6, 7, 5, 7, 6, 6])
    
    def test_invalid_number_0(self):
        """Test with invalid number 0"""
        with pytest.raises(ValueError, match="无效数字"):
            calculate_hexagram([6, 7, 0, 7, 6, 6])
    
    def test_invalid_number_10(self):
        """Test with invalid number 10"""
        with pytest.raises(ValueError, match="无效数字"):
            calculate_hexagram([6, 7, 10, 7, 6, 6])


class TestTrigramMapping:
    """Test that trigram mappings are correct"""
    
    def test_zhen_trigram(self):
        """
        震 (Zhen/Thunder): One yang at bottom
        少阳+少阴+少阴 = 7,8,8 = ⚊⚋⚋
        """
        result = calculate_hexagram([7, 8, 8, 8, 8, 8])
        # Lower trigram should be 震
        assert result['lower_trigram'] == "震"
    
    def test_gen_trigram(self):
        """
        艮 (Gen/Mountain): One yang at top
        少阴+少阴+少阳 = 8,8,7 = ⚋⚋⚊
        """
        result = calculate_hexagram([8, 8, 7, 8, 8, 8])
        # Lower trigram should be 艮
        assert result['lower_trigram'] == "艮"
    
    def test_kan_trigram(self):
        """
        坎 (Kan/Water): One yang in middle
        少阴+少阳+少阴 = 8,7,8 = ⚋⚊⚋
        """
        result = calculate_hexagram([8, 7, 8, 8, 8, 8])
        assert result['lower_trigram'] == "坎"
    
    def test_li_trigram(self):
        """
        离 (Li/Fire): One yin in middle
        少阳+少阴+少阳 = 7,8,7 = ⚊⚋⚊
        """
        result = calculate_hexagram([7, 8, 7, 8, 8, 8])
        assert result['lower_trigram'] == "离"


class TestChangedHexagram:
    """Test changed hexagram (变卦) calculation"""
    
    def test_simple_change(self):
        """Test simple yin-yang flip"""
        # 6 (yin) should become yang
        # 9 (yang) should become yin
        result = calculate_hexagram([6, 9, 8, 8, 8, 8])
        
        # Original lower: 6,9,8 = ⚋⚊⚋ = 坎
        # Changed lower:  ⚊⚋⚋ = 震
        assert result['lower_trigram'] == "坎"
        assert result['changed_lower'] == "震"
    
    def test_no_change_for_78(self):
        """Test that 7 and 8 don't change"""
        result = calculate_hexagram([7, 8, 7, 8, 8, 8])
        
        # No moving yaos
        assert result['changed_lower'] == result['lower_trigram']
        assert result['changed_upper'] == result['upper_trigram']


if __name__ == "__main__":
    # Run with: python3 tests/test_divine.py
    pytest.main([__file__, "-v"])
