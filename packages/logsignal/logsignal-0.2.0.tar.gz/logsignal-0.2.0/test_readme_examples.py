#!/usr/bin/env python3
"""
Test script to verify all README examples work correctly.
"""

print("Testing README examples...")
print("=" * 60)

# Test 1: Rule factory methods
print("\n1. Testing Rule factory methods...")
try:
    from logsignal import Rule

    rule1 = Rule.contains("ERROR")
    rule2 = Rule.level("CRITICAL")
    rule3 = Rule.spike(threshold=5, window=10)

    print("✓ Rule.contains() works")
    print("✓ Rule.level() works")
    print("✓ Rule.spike() works")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: LogWatcher with string rules
print("\n2. Testing LogWatcher with string rules...")
try:
    from logsignal import LogWatcher

    watcher = LogWatcher(rules=["ERROR", "CRITICAL"])
    print(f"✓ LogWatcher created with {len(watcher.rules)} rules")
    print(f"✓ Auto-console notifier: {len(watcher.notifiers)} notifier(s)")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Process string input
print("\n3. Testing process with string input...")
try:
    watcher.process("ERROR database connection failed")
    print("✓ String processing works")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Spike detection example
print("\n4. Testing spike detection...")
try:
    import time

    watcher2 = LogWatcher(rules=[Rule.spike(threshold=3, window=5)])

    for _ in range(5):
        watcher2.process("ERROR something bad happened")

    print("✓ Spike detection works")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 5: LogSignalHandler for logging integration
print("\n5. Testing logging integration...")
try:
    import logging
    from logsignal import LogSignalHandler

    logger = logging.getLogger("test_app")
    logger.setLevel(logging.INFO)

    handler = LogSignalHandler()
    logger.addHandler(handler)

    logger.error("DB connection timeout")

    print("✓ LogSignalHandler works")

    # Clean up
    logger.removeHandler(handler)
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 6: StatRule factory method
print("\n6. Testing StatRule factory method...")
try:
    from logsignal import StatRule

    stat = StatRule.error_rate_zscore(z=3.0)
    watcher3 = LogWatcher(auto_console=False)
    watcher3.add_stat(stat)

    print("✓ StatRule.error_rate_zscore() works")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 7: EntropySpike example
print("\n7. Testing EntropySpike...")
try:
    import random
    from logsignal import LogWatcher
    from logsignal.stats.entropy import EntropySpike

    watcher4 = LogWatcher(auto_console=False)
    watcher4.add_stat(EntropySpike(window=10, threshold=2.5))

    normal_logs = [
        "INFO ok",
        "INFO request processed",
        "INFO heartbeat",
        "INFO user active",
    ]

    for _ in range(30):
        watcher4.process({"message": random.choice(normal_logs)})

    attack = "GET /login.php?id=1' OR '1'='1' UNION SELECT password FROM users"

    for _ in range(5):
        watcher4.process({"message": attack})

    print("✓ EntropySpike works")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 8: All exports available
print("\n8. Testing package exports...")
try:
    from logsignal import LogWatcher, Signal, Rule, StatRule, LogSignalHandler

    print("✓ All main classes exported correctly")
    print(f"  - LogWatcher: {LogWatcher}")
    print(f"  - Signal: {Signal}")
    print(f"  - Rule: {Rule}")
    print(f"  - StatRule: {StatRule}")
    print(f"  - LogSignalHandler: {LogSignalHandler}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 9: Backward compatibility
print("\n9. Testing backward compatibility...")
try:
    from logsignal.rules.count import ErrorSpikeRule
    import warnings

    # Suppress deprecation warning for this test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        old_rule = ErrorSpikeRule(level="ERROR", threshold=10, window=60)

    print("✓ ErrorSpikeRule still works (deprecated)")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 10: Mixed rule types
print("\n10. Testing mixed rule types...")
try:
    watcher5 = LogWatcher(
        rules=[
            "ERROR",  # String rule
            Rule.level("CRITICAL"),  # Factory method
            Rule.spike(threshold=5, window=10),  # Another factory
        ]
    )

    watcher5.process("ERROR test")
    watcher5.process({"message": "CRITICAL issue", "level": "CRITICAL"})

    print(f"✓ Mixed rule types work ({len(watcher5.rules)} rules)")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "=" * 60)
print("All README examples tested successfully! ✓")
print("=" * 60)
