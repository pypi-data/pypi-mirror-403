# -*- coding: utf-8 -*-
"""Handles revealing: HEX parts → .tar.gz → directory"""

import os, re, shutil, tarfile, binascii
from .utils import info, die, safe_remove

HEX_PART_RE = re.compile(r'^(\d{4})_(.+)\.hex$', re.IGNORECASE)


def list_hex_parts(parts_dir):
    entries, bases = [], set()
    for name in os.listdir(parts_dir):
        m = HEX_PART_RE.match(name)
        if not m:
            continue
        idx, base = m.group(1), m.group(2)
        bases.add(base)
        entries.append((int(idx), name, base))

    if not entries:
        die(f"'{parts_dir}'에 ####_BASE.hex 파츠가 없습니다.")
    if len(bases) != 1:
        die(f"다른 BASE가 섞여 있음: {', '.join(sorted(bases))}")

    base = next(iter(bases))
    entries.sort(key=lambda t: t[0])
    expect = 1
    for idx, name, _ in entries:
        if idx != expect:
            die(f"파츠 번호 불연속: 기대 {expect:04d}, 실제 {idx:04d} ({name})")
        expect += 1

    files = [os.path.join(parts_dir, name) for _, name, _ in entries]
    return base, files


def concat_hex_parts(parts, out_hex_path):
    info(f"HEX 파츠 합치기 → {out_hex_path}")
    with open(out_hex_path, "wb") as wf:
        for p in parts:
            info(f"  + {os.path.basename(p)}")
            with open(p, "rb") as rf:
                while True:
                    chunk = rf.read(1 << 20)
                    if not chunk:
                        break
                    wf.write(b"".join(chunk.split()))


def hexfile_to_binary_tgz(hex_path, tgz_path):
    info(f"HEX → TGZ 복원: {hex_path} -> {tgz_path}")
    with open(hex_path, "rb") as hf, open(tgz_path, "wb") as bf:
        carry = b""
        while True:
            chunk = hf.read(1 << 20)
            if not chunk:
                break
            chunk = carry + b"".join(chunk.split())
            if len(chunk) % 2:
                carry, chunk = chunk[-1:], chunk[:-1]
            else:
                carry = b""
            if chunk:
                bf.write(binascii.unhexlify(chunk))
        if carry:
            die("HEX 길이가 홀수입니다. 손상 의심.")


def extract_tgz_to_outdir(tgz_path, out_dir):
    tmp_root = os.path.join(os.path.dirname(out_dir) or ".", ".bakcode_extract_tmp")
    if os.path.exists(tmp_root):
        shutil.rmtree(tmp_root)
    os.makedirs(tmp_root)
    info(f"TGZ 임시 추출: {tgz_path} → {tmp_root}")

    with tarfile.open(tgz_path, "r:gz") as tar:
        for m in tar.getmembers():
            target = os.path.abspath(os.path.join(tmp_root, m.name))
            root = os.path.abspath(tmp_root)
            if not (target == root or target.startswith(root + os.sep)):
                die(f"의심스러운 경로: {m.name}")
        tar.extractall(path=tmp_root)

    entries = [os.path.join(tmp_root, n) for n in os.listdir(tmp_root)]
    top_dirs = [p for p in entries if os.path.isdir(p)]
    if len(top_dirs) != 1:
        shutil.rmtree(tmp_root)
        die("예상과 다른 아카이브 구조입니다. 최상위 폴더가 1개가 아닙니다.")
    src_dir = top_dirs[0]

    if os.path.exists(out_dir) and os.listdir(out_dir):
        shutil.rmtree(tmp_root)
        die(f"출력 디렉토리 '{out_dir}' 가 이미 존재하고 비어있지 않습니다.")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for name in os.listdir(src_dir):
        shutil.move(os.path.join(src_dir, name), out_dir)

    shutil.rmtree(tmp_root)
    info(f"복원 완료: {out_dir}")


def do_reveal(input_dir, output_dir):
    parts_dir = os.path.abspath(input_dir)
    out_dir = os.path.abspath(output_dir)
    if not os.path.isdir(parts_dir):
        die(f"입력 디렉토리 아님: {parts_dir}")

    base, parts = list_hex_parts(parts_dir)
    mid_hex = os.path.join(parts_dir, f"{base}.hex")
    mid_tgz = os.path.join(parts_dir, f"{base}.tar.gz")

    try:
        concat_hex_parts(parts, mid_hex)
        hexfile_to_binary_tgz(mid_hex, mid_tgz)
        extract_tgz_to_outdir(mid_tgz, out_dir)
    finally:
        safe_remove(mid_tgz)
        safe_remove(mid_hex)
