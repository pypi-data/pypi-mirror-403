#!/usr/bin/env python3
"""
Capture and analyze actual Sphinx build output
Run: python capture_and_analyze.py
"""
import subprocess
import sys
import re

print("="*70)
print("📸 CAPTURING SPHINX BUILD OUTPUT")
print("="*70)

# Run make html and capture output
print("\n🔨 Running: make html")
print("Please wait...\n")

try:
    result = subprocess.run(
        ['make', 'html'],
        capture_output=True,
        text=True,
        cwd='.',
        timeout=120
    )
    
    stdout = result.stdout
    stderr = result.stderr
    combined = stdout + stderr
    
except subprocess.TimeoutExpired:
    print("❌ Build timed out!")
    sys.exit(1)
except Exception as e:
    print(f"❌ Build failed: {e}")
    sys.exit(1)

# Save to file
with open('build_output.txt', 'w', encoding='utf-8') as f:
    f.write(combined)

print(f"✅ Output saved to: build_output.txt")
print(f"   Total lines: {len(combined.splitlines())}")

# Analyze WARNING lines
print("\n" + "="*70)
print("📊 ANALYZING WARNING LINES")
print("="*70)

warning_lines = [line for line in combined.splitlines() if 'WARNING:' in line]
print(f"\n📍 Total WARNING lines: {len(warning_lines)}")

if warning_lines:
    # Check first few warnings
    print("\n🔍 First 3 WARNING lines:")
    for i, line in enumerate(warning_lines[:3], 1):
        has_ansi = '\033[' in line or '\x1b[' in line
        print(f"\n   [{i}] Has ANSI codes: {has_ansi}")
        print(f"       Length: {len(line)}")
        print(f"       Preview: {line[:100]}...")
        
        if has_ansi:
            print(f"       ✅ COLORED!")
        else:
            print(f"       ❌ PLAIN TEXT")
    
    # Check last few warnings
    print("\n🔍 Last 3 WARNING lines:")
    for i, line in enumerate(warning_lines[-3:], len(warning_lines)-2):
        has_ansi = '\033[' in line or '\x1b[' in line
        print(f"\n   [{i}] Has ANSI codes: {has_ansi}")
        print(f"       Length: {len(line)}")
        print(f"       Preview: {line[:100]}...")
        
        if has_ansi:
            print(f"       ✅ COLORED!")
        else:
            print(f"       ❌ PLAIN TEXT")
    
    # Statistics
    colored_count = sum(1 for line in warning_lines if '\033[' in line or '\x1b[' in line)
    plain_count = len(warning_lines) - colored_count
    
    print("\n" + "="*70)
    print("📊 STATISTICS")
    print("="*70)
    print(f"   Total WARNINGs: {len(warning_lines)}")
    print(f"   ✅ Colored:     {colored_count} ({colored_count/len(warning_lines)*100:.1f}%)")
    print(f"   ❌ Plain:       {plain_count} ({plain_count/len(warning_lines)*100:.1f}%)")
    
    if colored_count == len(warning_lines):
        print("\n   🎉 100% COLORED! Extension working perfectly!")
    elif colored_count == 0:
        print("\n   ❌ 0% COLORED! Extension NOT working!")
    else:
        print(f"\n   ⚠️  Partial coloring! {colored_count}/{len(warning_lines)} colored")
        
        # Find transition point
        print("\n   🔍 Finding transition point...")
        for i, line in enumerate(warning_lines, 1):
            has_ansi = '\033[' in line or '\x1b[' in line
            if has_ansi:
                print(f"      First colored WARNING at line #{i}")
                break
    
    # Check for extension loading message
    print("\n" + "="*70)
    print("🔍 CHECKING EXTENSION LOADING")
    print("="*70)
    
    if 'sphinxcolor' in combined.lower():
        # Find lines mentioning sphinxcolor
        sphinx_lines = [line for line in combined.splitlines() if 'sphinxcolor' in line.lower()]
        print(f"\n   Found {len(sphinx_lines)} lines mentioning sphinxcolor:")
        for line in sphinx_lines[:5]:
            print(f"      {line[:100]}")
    else:
        print("\n   ⚠️  No mention of 'sphinxcolor' in output!")
        print("      → Extension might not be loading!")

else:
    print("\n   ℹ️  No WARNING lines found in output")

print("\n" + "="*70)
print("💡 RECOMMENDATIONS")
print("="*70)

if colored_count == 0:
    print("""
   Extension is NOT working! Try:
   
   1. Check extension loads:
      python deep_debug.py
   
   2. Check conf.py:
      grep sphinxcolor conf.py
   
   3. Reinstall:
      pip uninstall sphinxcolor -y
      pip install -e /path/to/sphinxcolor
   
   4. Check for errors:
      make html 2>&1 | grep -i error
""")
elif colored_count < len(warning_lines):
    print(f"""
   Extension partially working ({colored_count}/{len(warning_lines)})!
   
   → First ~{len(warning_lines) - colored_count} warnings are NOT colored
   → This means extension loads TOO LATE
   
   Current approach (monkey-patch) should fix this.
   
   Check:
   1. Is extension.py using latest VERSION? (monkey-patch version)
   2. Run: python deep_debug.py
   3. Check if TestWrapper.__new__() is called
""")
else:
    print("""
   🎉 Extension working 100%! All warnings colored!
   
   You're done! Enjoy your colorful Sphinx output! 🎨
""")

print("="*70)
print(f"\n📄 Full output saved to: build_output.txt")
print(f"📄 Analyze it: cat build_output.txt | less -R")
print("="*70)