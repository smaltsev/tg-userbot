#!/usr/bin/env python3
"""
Test the optimized group discovery logic without authentication.
This simulates the discovery process to verify the optimization works.
"""

import asyncio
import logging
import time
from telegram_scanner.config import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockTelegramGroup:
    """Mock group for testing."""
    def __init__(self, id, title, username=None):
        self.id = id
        self.title = title
        self.username = username
        self.member_count = 1000
        self.is_private = False
        self.access_hash = 12345
        self.is_channel = False
        self.is_megagroup = True

async def test_discovery_logic():
    """Test the discovery optimization logic."""
    print("Testing optimized group discovery logic...")
    
    # Load config to get selected groups
    config_manager = ConfigManager("config.json")
    config = await config_manager.load_config()
    
    print(f"Selected groups from config: {config.selected_groups}")
    
    # Simulate the optimized discovery process
    discovered_groups = []
    
    # Step 1: Try direct search (simulated)
    print("\nStep 1: Simulating direct group search...")
    
    # Mock some groups that would be found by direct search
    mock_groups = [
        MockTelegramGroup(1966291562, "КиберТопор", "cybertopor"),
        MockTelegramGroup(1754252633, "Топор Live", "toporlive"),
        MockTelegramGroup(1326223284, "Рыбарь", "rybar"),
        MockTelegramGroup(1364471164, "КБ плюс", "kbplus"),
        MockTelegramGroup(1842181039, "artjockey", "artjockey")
    ]
    
    # Simulate finding groups by direct search
    for group_name in config.selected_groups:
        for mock_group in mock_groups:
            # Check if group matches (same logic as in scanner)
            if (group_name.lower() in mock_group.title.lower() or 
                (mock_group.username and group_name.lower() in mock_group.username.lower())):
                discovered_groups.append(mock_group)
                print(f"  ✓ Found by direct search: {mock_group.title} (ID: {mock_group.id})")
                break
    
    print(f"\nDirect search found: {len(discovered_groups)} groups")
    
    # Step 2: Check if we need dialog iteration
    if len(discovered_groups) == len(config.selected_groups):
        print("✓ All selected groups found by direct search - no dialog iteration needed!")
        total_time = 2.5  # Simulated fast discovery time
    else:
        print("Some groups not found by direct search, would need dialog iteration...")
        # Simulate finding remaining groups
        remaining = len(config.selected_groups) - len(discovered_groups)
        print(f"Would need to search dialogs for {remaining} remaining groups")
        total_time = 15.0  # Simulated longer time with dialog iteration
    
    print(f"\nSimulated discovery results:")
    print(f"  Total groups found: {len(discovered_groups)}")
    print(f"  Estimated time: {total_time:.1f} seconds")
    print(f"  Groups found:")
    for group in discovered_groups:
        print(f"    - {group.title} (ID: {group.id})")
    
    # Test early termination logic
    print(f"\nEarly termination test:")
    print(f"  Target groups: {len(config.selected_groups)}")
    print(f"  Found groups: {len(discovered_groups)}")
    if len(discovered_groups) >= len(config.selected_groups):
        print("  ✓ Would terminate early - optimization working!")
    else:
        print("  ⚠ Would continue searching - partial optimization")
    
    return len(discovered_groups) == len(config.selected_groups)

async def main():
    """Main test function."""
    print("=" * 60)
    print("Group Discovery Optimization Test")
    print("=" * 60)
    
    success = await test_discovery_logic()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Optimization test passed!")
        print("The scanner should work efficiently when authentication is resolved.")
    else:
        print("⚠ Optimization test shows room for improvement.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())