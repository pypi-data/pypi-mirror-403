bakcode: Pack & Reveal Utility
===============================

Usage:
  Pack   : bakcode --pack {INPUT_DIR} {OUTPUT_DIR} {SIZE}
  Reveal : bakcode --reveal {INPUT_DIR} {OUTPUT_DIR}

Example:
  bakcode -p 00_source 01_compressed 1K 
  bakcode -r 01_compressed 02_decompressed 

Description:
  - PACK  : Create .tar.gz from INPUT_DIR, convert to HEX, split into chunks.
  - REVEAL: Combine HEX parts, restore .tar.gz, and extract to OUTPUT_DIR.
