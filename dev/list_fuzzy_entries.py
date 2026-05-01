#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
List all fuzzy entries for manual review
"""
import polib

po_file = 'ContestKeeper/locale/uk/LC_MESSAGES/django.po'
po = polib.pofile(po_file)

fuzzy_entries = [e for e in po if e.flags and 'fuzzy' in e.flags]

print("=" * 100)
print("ВСІХ НЕЧІТКИХ ЗАПИСІВ ДЛЯ РУЧНОЇ ПЕРЕВІРКИ")
print("=" * 100)
print(f"\nКількість: {len(fuzzy_entries)}\n")

for i, entry in enumerate(fuzzy_entries, 1):
    print(f"{i}. [{entry.location}]")
    print(f"   msgid: {entry.msgid}")
    print(f"   msgstr: {entry.msgstr}")
    if entry.previous_msgid:
        print(f"   previous_msgid: {entry.previous_msgid}")
    print()

print("\n" + "=" * 100)
print("РЕКОМЕНДАЦІЇ ДЛЯ ВИПРАВЛЕННЯ:")
print("=" * 100)

# Group by issue type
issues = {
    'opposite_meaning': [],
    'wrong_plural': [],
    'incomplete': [],
    'wrong_context': [],
    'other': [],
}

for entry in fuzzy_entries:
    msgid = entry.msgid
    msgstr = entry.msgstr
    prev = entry.previous_msgid
    
    if 'Closed' in msgid and 'відкрита' in msgstr.lower():
        issues['opposite_meaning'].append((msgid, msgstr, prev))
    elif msgid.endswith('s') and prev and prev.endswith(''):
        issues['wrong_plural'].append((msgid, msgstr, prev))
    elif len(msgstr) < len(msgid) * 0.5:
        issues['incomplete'].append((msgid, msgstr, prev))
    else:
        issues['other'].append((msgid, msgstr, prev))

print("\n1. ПРОТИЛЕЖНІ ЗНАЧЕННЯ (2 записи):")
for msgid, msgstr, prev in issues['opposite_meaning']:
    print(f"   ❌ {msgid} → {msgstr} (було: {prev})")

print("\n2. НЕПРАВИЛЬНА МНОЖИНА:")
for msgid, msgstr, prev in issues['wrong_plural'][:5]:
    print(f"   ❌ {msgid} → {msgstr} (було: {prev})")

print("\n3. НЕПОВНІ ПЕРЕКЛАДИ:")
for msgid, msgstr, prev in issues['incomplete'][:5]:
    print(f"   ⚠️  {msgid} → {msgstr}")

print(f"\n4. ІНШІ ПРОБЛЕМИ ({len(issues['other'])} записів)")
