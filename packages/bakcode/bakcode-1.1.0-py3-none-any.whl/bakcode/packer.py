# -*- coding: utf-8 -*-
"""Handles packing: directory → .tar.gz → HEX parts"""

import os, math, tarfile, binascii
from .utils import info, die, safe_remove, parse_size


def make_tgz(dirname, workdir):
    base = os.path.basename(dirname.rstrip(os.sep))
    tgz_path = os.path.join(workdir, base + ".tar.gz")
    info(f"TGZ 생성: {dirname} -> {tgz_path}")
    with tarfile.open(tgz_path, "w:gz") as tar:
        tar.add(dirname, arcname=base)
    return tgz_path, base


def write_hex_from_tgz(tgz_path, hex_path):
    info(f"TGZ → HEX: {os.path.basename(tgz_path)} -> {hex_path}")
    with open(tgz_path, "rb") as f, open(hex_path, "wb") as hf:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            hf.write(binascii.hexlify(chunk))


def split_hex(hex_path, base, outdir, chunk_chars):
    with open(hex_path, "rb") as f:
        hexdata = f.read()
    total = len(hexdata)
    if total <= chunk_chars:
        if not os.path.exists(outdir): os.makedirs(outdir)
        final_one = os.path.join(outdir, f"0001_{base}.hex")
        with open(final_one, "wb") as out:
            out.write(hexdata)
        info(f"분할 불필요: {total} chars → {final_one}")
        return 1

    parts = int(math.ceil(float(total) / float(chunk_chars)))
    if not os.path.exists(outdir): os.makedirs(outdir)
    for i in range(parts):
        idx = f"{i+1:04d}"
        partfile = os.path.join(outdir, f"{idx}_{base}.hex")
        start = i * chunk_chars
        end = (i + 1) * chunk_chars
        with open(partfile, "wb") as pf:
            pf.write(hexdata[start:end])
        info(f"분할 생성: {partfile}")
    return parts


def do_pack(input_dir, output_dir, size_str):
    if not os.path.isdir(input_dir):
        die(f"입력 디렉토리 아님: {input_dir}")

    size_bytes = parse_size(size_str)
    chunk_chars = int(size_bytes * 2)  # 1 byte → 2 hex chars
    tgz_path, base = make_tgz(input_dir, output_dir if output_dir else ".")
    tmp_hex = os.path.join(os.path.dirname(tgz_path), f"__tmp_{base}.hex")

    try:
        write_hex_from_tgz(tgz_path, tmp_hex)
        n = split_hex(tmp_hex, base, output_dir, chunk_chars)
        info(f"총 {n}개 파츠 생성 완료 (base='{base}', out='{output_dir}')")
    finally:
        safe_remove(tmp_hex)
        safe_remove(tgz_path)
