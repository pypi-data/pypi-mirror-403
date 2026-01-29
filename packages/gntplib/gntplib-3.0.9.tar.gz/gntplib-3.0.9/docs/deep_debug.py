#!/usr/bin/env python3
"""
Deep Debug Script - Find out EXACTLY what's happening
Run this from your docs folder: python deep_debug.py
"""
import sys
import os
import logging

print("="*70)
print("🔍 DEEP DEBUG - sphinxcolor")
print("="*70)

# Step 1: Check imports
print("\n1️⃣ Testing imports...")
try:
    from sphinxcolor import Config
    from sphinxcolor.extension import RichFormatter, setup
    print("   ✅ sphinxcolor imports OK")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Step 2: Check Sphinx
print("\n2️⃣ Checking Sphinx...")
try:
    import sphinx
    from sphinx.util import logging as sphinx_logging
    print(f"   ✅ Sphinx version: {sphinx.__version__}")
    print(f"   ✅ sphinx.util.logging imported")
except ImportError as e:
    print(f"   ❌ Sphinx import failed: {e}")
    sys.exit(1)

# Step 3: Check ColorizeFormatter BEFORE monkey-patch
print("\n3️⃣ Checking ColorizeFormatter BEFORE monkey-patch...")
try:
    original_class = sphinx_logging.ColorizeFormatter
    print(f"   📍 Original class: {original_class}")
    print(f"   📍 Module: {original_class.__module__}")
    print(f"   📍 Location: {original_class.__module__}:{original_class.__name__}")
except Exception as e:
    print(f"   ❌ Cannot get ColorizeFormatter: {e}")

# Step 4: Test monkey-patch manually
print("\n4️⃣ Testing monkey-patch manually...")
try:
    # Save original
    _original = sphinx_logging.ColorizeFormatter
    
    # Create wrapper
    class TestWrapper:
        def __new__(cls):
            print("   🎉 TestWrapper.__new__() called!")
            return RichFormatter(Config())
    
    # Apply patch
    sphinx_logging.ColorizeFormatter = TestWrapper
    
    print(f"   ✅ Patched: {sphinx_logging.ColorizeFormatter}")
    
    # Test if it works
    print("\n   Testing instantiation...")
    formatter = sphinx_logging.ColorizeFormatter()
    print(f"   📍 Got instance: {formatter.__class__.__name__}")
    print(f"   📍 Is RichFormatter? {isinstance(formatter, RichFormatter)}")
    
except Exception as e:
    print(f"   ❌ Monkey-patch test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Check if conf.py loads sphinxcolor
print("\n5️⃣ Checking conf.py...")
if os.path.exists('conf.py'):
    with open('conf.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'sphinxcolor' in content:
        print("   ✅ 'sphinxcolor' found in conf.py")
        
        # Find extensions list
        import re
        ext_match = re.search(r'extensions\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if ext_match:
            extensions = ext_match.group(1)
            print(f"   📍 Extensions: {extensions[:200]}...")
            
            if "'sphinxcolor'" in extensions or '"sphinxcolor"' in extensions:
                print("   ✅ sphinxcolor in extensions list")
            else:
                print("   ⚠️  sphinxcolor NOT in extensions list!")
    else:
        print("   ⚠️  'sphinxcolor' NOT found in conf.py")
else:
    print("   ❌ conf.py not found! Run from docs folder!")

# Step 6: Check Sphinx logger state
print("\n6️⃣ Checking Sphinx logger state...")
logger = logging.getLogger('sphinx')
print(f"   📍 Logger level: {logger.level}")
print(f"   📍 Handlers count: {len(logger.handlers)}")

for i, handler in enumerate(logger.handlers):
    print(f"\n   Handler [{i}]:")
    print(f"      Class: {handler.__class__.__name__}")
    print(f"      Module: {handler.__class__.__module__}")
    if hasattr(handler, 'formatter') and handler.formatter:
        fmt = handler.formatter
        print(f"      Formatter: {fmt.__class__.__name__}")
        print(f"      Formatter module: {fmt.__class__.__module__}")
        print(f"      Is RichFormatter? {isinstance(fmt, RichFormatter)}")
    else:
        print(f"      Formatter: None")

# Step 7: Test actual formatting
print("\n7️⃣ Testing actual formatting...")
if logger.handlers:
    test_record = logging.LogRecord(
        name='sphinx',
        level=logging.WARNING,
        pathname='test.py',
        lineno=1,
        msg=r'C:\PROJECTS\test\file.py:docstring of test:1: WARNING: test message use :no-index: for one',
        args=(),
        exc_info=None
    )
    
    for i, handler in enumerate(logger.handlers):
        if handler.formatter:
            print(f"\n   Handler [{i}] formatting test:")
            try:
                formatted = handler.formatter.format(test_record)
                print(f"      Output length: {len(formatted)}")
                print(f"      Has ANSI codes: {chr(27) in formatted}")
                print(f"      Preview: {formatted[:100]}...")
            except Exception as e:
                print(f"      ❌ Format failed: {e}")

# Summary
print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)
print("\n❓ Questions to answer:")
print("   1. Did monkey-patch work? (TestWrapper called?)")
print("   2. Are handlers using RichFormatter?")
print("   3. Does formatting produce ANSI codes?")
print("\n💡 If monkey-patch NOT called:")
print("   → sphinxcolor extension not loading correctly")
print("\n💡 If handlers NOT using RichFormatter:")
print("   → Sphinx created handlers BEFORE monkey-patch")
print("\n💡 If no ANSI codes in output:")
print("   → RichFormatter not working correctly")
print("\n🐛 Next: Run 'make html' and compare with output above")
print("="*70)