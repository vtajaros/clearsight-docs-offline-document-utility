import pytest
from services.bionic_service import BionicService
import random

def test_bionic_column_sort():
    svc = BionicService()
    
    blocks = [
        {"id": "heading", "bbox": [50, 50, 550, 80]},
        {"id": "col1_y100", "bbox": [50, 100, 280, 150]},
        {"id": "col2_y100", "bbox": [320, 100, 550, 150]},
        {"id": "col1_y200", "bbox": [50, 200, 280, 250]},
        {"id": "col2_y200", "bbox": [320, 200, 550, 250]},
    ]
    
    scrambled = blocks.copy()
    random.shuffle(scrambled)
    
    sorted_blocks = svc._sort_blocks_multi_column(scrambled, 600)
    result_ids = [b["id"] for b in sorted_blocks]
    
    assert result_ids == ["heading", "col1_y100", "col1_y200", "col2_y100", "col2_y200"]
    print("Test passed successfully!")

if __name__ == "__main__":
    test_bionic_column_sort()
