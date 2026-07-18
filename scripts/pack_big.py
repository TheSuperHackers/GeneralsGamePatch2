#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""
pack_big.py - Create Command & Conquer Generals / Zero Hour .BIG Archive Files.

Functions Overview:
-------------------
- parse_multi_str(filepath: Path):
    Parses a multi-language .str text file containing language prefixes (US:, DE:, FR:,
    ES:, IT:, KO:, ZH:, BP:, PL:) and returns a dictionary mapping each language prefix
    to a list of (label, text) string pairs.

- compile_csf(entries, lang_id):
    Compiles a list of (label, text) string pairs into a binary .csf (Client String File)
    byte buffer. Formats the binary header (magic ' FSC', version 3, label/value counts, 
    and language ID) and encodes wide characters in UTF-16LE bitwise-NOT representation.

- create_big_archive(input_dir: str, output_big: str):
    Packs an input directory into a .BIG archive file. Performs recursive file collection,
    on-the-fly compilation of generals.str into 9 localized binary .csf files (omitting raw 
    generals.str), dynamic generation of 35 empty root INI dummy files, EA-compliant index 
    sorting (root files before subdirectory contents), header offset calculations, and binary 
    writing.

- main():
    CLI entry point that parses command-line arguments (--input/-i and --output/-o)
    and invokes create_big_archive.
"""

import os
import sys
import struct
import argparse
import codecs
from pathlib import Path

DUMMY_FILES = [
    'airforcegeneral.ini', 'americaair.ini', 'americacineunit.ini', 'americainfantry.ini', 'americamiscunit.ini',
    'americavehicle.ini', 'bossgeneral.ini', 'chemicalgeneral.ini', 'chinaair.ini', 'chinacineunit.ini',
    'chinainfantry.ini', 'chinamiscunit.ini', 'chinavehicle.ini', 'demogeneral.ini', 'gc_chem_glabuildings.ini',
    'gc_chem_glasystem.ini', 'gc_chem_glaunits.ini', 'gc_slth_glabuildings.ini', 'gc_slth_glasystem.ini',
    'gc_slth_glaunits.ini', 'glaair.ini', 'glacineunit.ini', 'glainfantry.ini', 'glamiscunit.ini', 'glavehicle.ini',
    'hulk.ini', 'infantrygeneral.ini', 'lasergeneral.ini', 'nukegeneral.ini', 'specialpowerobjects.ini',
    'stealthgeneral.ini', 'superweapongeneral.ini', 'tankgeneral.ini', 'techbuildings.ini', 'weaponobjects.ini'
]

LANGUAGE_MAP = {
    'US:': ('English', 0),
    'DE:': ('German', 2),
    'FR:': ('French', 3),
    'ES:': ('Spanish', 4),
    'IT:': ('Italian', 5),
    'KO:': ('Korean', 7),
    'ZH:': ('Chinese', 8),
    'BP:': ('Brazilian', 9),
    'PL:': ('Polish', 10),
}

def parse_multi_str(filepath: Path):
    with open(filepath, 'r', encoding='latin-1') as f:
        lines = f.readlines()
        
    lang_data = {prefix: [] for prefix in LANGUAGE_MAP}
    current_label = None
    for line in lines:
        l = line.strip()
        if not l or l.startswith('//'):
            continue
        if l == 'END':
            current_label = None
            continue
        if current_label is None and not any(l.startswith(p) for p in LANGUAGE_MAP):
            current_label = l
            continue
            
        for prefix in LANGUAGE_MAP:
            if l.startswith(prefix):
                idx = line.find('"')
                if idx != -1:
                    last_q = line.rfind('"')
                    text = line[idx+1:last_q] if last_q > idx else line[idx+1:]
                else:
                    text = ''
                lang_data[prefix].append((current_label, text))
                break
    return lang_data

def compile_csf(entries, lang_id):
    num_labels = len(entries)
    num_strings = len(entries)
    buf = bytearray()
    buf.extend(struct.pack('<IIIIII', 0x43534620, 3, num_labels, num_strings, 0, lang_id))
    for label, text in entries:
        label_bytes = label.encode('latin-1')
        buf.extend(struct.pack('<III', 0x4c424c20, 1, len(label_bytes)))
        buf.extend(label_bytes)
        wide_chars = text.replace('\\n', '\n').replace('\\t', '\t')
        encoded_wchars = bytearray()
        for char in wide_chars:
            w = ord(char) & 0xFFFF
            w_inv = (~w) & 0xFFFF
            encoded_wchars.extend(struct.pack('<H', w_inv))
        buf.extend(struct.pack('<II', 0x53545220, len(wide_chars)))
        buf.extend(encoded_wchars)
    return bytes(buf)

def create_big_archive(input_dir: str, output_big: str):
    input_path = Path(input_dir).resolve()
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory '{input_dir}' does not exist or is not a directory.")
        sys.exit(1)

    file_entries = []
    # Collect all files recursively
    for root, _, files in os.walk(input_path):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(input_path)
            # Use backslashes in BIG archive relative path
            archive_rel_path = str(rel_path).replace('/', '\\')
            
            # Intercept generals.str to compile into 9 localized CSF files
            if archive_rel_path.lower() == 'data\\generals.str':
                lang_data = parse_multi_str(full_path)
                for prefix, (lang_folder, lang_id) in LANGUAGE_MAP.items():
                    entries = lang_data[prefix]
                    csf_bytes = compile_csf(entries, lang_id)
                    csf_rel_path = f"Data\\{lang_folder}\\generals.csf"
                    file_entries.append({
                        'full_path': None,
                        'rel_path': csf_rel_path,
                        'rel_path_bytes': csf_rel_path.encode('latin-1') + b'\x00',
                        'size': len(csf_bytes),
                        'payload_bytes': csf_bytes
                    })
                continue
            else:
                file_size = full_path.stat().st_size
                file_entries.append({
                    'full_path': full_path,
                    'rel_path': rel_path,
                    'rel_path_bytes': archive_rel_path.encode('latin-1') + b'\x00',
                    'size': file_size,
                    'payload_bytes': None
                })

    # Add dummy empty root INI files to prevent premature vanilla loading
    existing_archive_paths = {entry['rel_path_bytes'].decode('latin-1').rstrip('\x00').lower() for entry in file_entries}
    
    for dummy in DUMMY_FILES:
        dummy_rel_path = f"Data\\INI\\Object\\{dummy}"
        if dummy_rel_path.lower() not in existing_archive_paths:
            file_entries.append({
                'full_path': None,
                'rel_path': dummy_rel_path,
                'rel_path_bytes': dummy_rel_path.encode('latin-1') + b'\x00',
                'size': 0,
                'payload_bytes': b''
            })

    # Sort files matching EA's BIG archive order:
    # Files directly inside a directory sort BEFORE any subdirectories of that directory.
    def big_sort_key(entry):
        parts = str(entry['rel_path']).replace('/', '\\').split('\\')
        key = []
        for i, p in enumerate(parts):
            # 0 for file component, 1 for directory component
            is_dir = 0 if i == len(parts) - 1 else 1
            key.append((is_dir, p.lower()))
        return key

    file_entries.sort(key=big_sort_key)

    num_files = len(file_entries)

    # Calculate header size:
    # 16 bytes for main header (BIGF, total_size, num_files, header_size)
    # For each file entry: 4 bytes offset + 4 bytes size + len(rel_path_bytes)
    header_size = 16 + sum(8 + len(entry['rel_path_bytes']) for entry in file_entries)

    # Calculate offsets for each file
    current_offset = header_size
    for entry in file_entries:
        entry['offset'] = current_offset
        current_offset += entry['size']

    total_archive_size = current_offset

    # Ensure target output directory exists
    output_path = Path(output_big).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as out_f:
        # 1. Write main header
        # Signature "BIGF"
        out_f.write(b'BIGF')
        # Total archive size (Little Endian uint32)
        out_f.write(struct.pack('<I', total_archive_size))
        # Number of files (Big Endian uint32)
        out_f.write(struct.pack('>I', num_files))
        # Header size / Offset to first file data (Big Endian uint32)
        out_f.write(struct.pack('>I', header_size))

        # 2. Write file index entries
        for entry in file_entries:
            # File offset (Big Endian uint32)
            out_f.write(struct.pack('>I', entry['offset']))
            # File size (Big Endian uint32)
            out_f.write(struct.pack('>I', entry['size']))
            # Filename null-terminated string
            out_f.write(entry['rel_path_bytes'])

        # 3. Write file data payloads
        for entry in file_entries:
            if entry['payload_bytes'] is not None:
                out_f.write(entry['payload_bytes'])
            else:
                with open(entry['full_path'], 'rb') as in_f:
                    while chunk := in_f.read(64 * 1024):
                        out_f.write(chunk)

    print(f"Successfully created '{output_big}' ({total_archive_size} bytes, {num_files} files).")

def main():
    parser = argparse.ArgumentParser(description="Pack a directory into a C&C Generals .BIG archive.")
    parser.add_argument('--input', '-i', required=True, help="Input directory path to pack.")
    parser.add_argument('--output', '-o', required=True, help="Output .big file path.")

    args = parser.parse_args()
    create_big_archive(args.input, args.output)

if __name__ == '__main__':
    main()
