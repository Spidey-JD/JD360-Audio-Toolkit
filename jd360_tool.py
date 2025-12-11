#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
import shutil
import os
import stat

# ---------- Helpers ----------

def ask_path(prompt: str) -> Path | None:
    p = input(prompt).strip().strip('"')
    if not p:
        print("[-] No path provided.")
        return None
    path = Path(p)
    if not path.is_file():
        print(f"[-] File not found: {path}")
        return None
    return path

def find_exe(name: str):
    exe = shutil.which(name) or shutil.which(name + ".exe")
    if not exe:
        print(f"[-] {name} not found on PATH. Make sure you can run '{name}' in cmd.")
        return None
    return exe

def get_output_dir() -> Path:
    """
    Always write recooked files into an 'output' folder next to this script.
    This avoids permission issues in game folders / Program Files / mounted ISOs, etc.
    """
    try:
        base = Path(__file__).resolve().parent
    except NameError:
        # Fallback if __file__ is not defined for some reason
        base = Path.cwd()
    out_dir = base / "output"
    out_dir.mkdir(exist_ok=True)
    return out_dir

def safe_write_bytes(path: Path, data: bytes):
    """
    Try to overwrite an existing file safely:
    - If it exists and is read-only, clear the read-only bit.
    - Then write bytes.
    """
    path = path.resolve()
    print(f"[+] Attempting to write CKD to: {path}")

    if path.exists():
        try:
            # Clear read-only bit if set
            attrs = os.stat(path).st_mode
            os.chmod(path, attrs | stat.S_IWRITE)
        except Exception as e:
            print(f"[!] Warning: couldn't adjust permissions on existing file: {e}")
        try:
            path.unlink()
        except Exception as e:
            print(f"[!] Warning: couldn't delete existing file before overwrite: {e}")

    # Now actually write
    path.write_bytes(data)

# ---------- Uncook: CKD -> WAV ----------

def uncook_ckd():
    print("\n=== Uncook CKD -> WAV ===")
    ckd = ask_path("Drag or type the .wav.ckd file here: ")
    if not ckd:
        return

    vgm = find_exe("vgmstream-cli")
    if not vgm:
        return

    out_wav = ckd.with_suffix(".wav")
    print(f"[+] Converting {ckd.name} -> {out_wav.name}")

    cmd = [vgm, "-o", str(out_wav), str(ckd)]
    try:
        subprocess.run(cmd, check=True)
        print(f"[+] Done! Created: {out_wav}")
    except subprocess.CalledProcessError as e:
        print("[-] vgmstream-cli failed:")
        print(e)

# ---------- Recook: CKD + WAV -> CKD ----------

def run_xma2encode(input_wav: Path) -> Path:
    xma2 = find_exe("xma2encode")
    if not xma2:
        raise RuntimeError("xma2encode not found on PATH.")

    input_wav = input_wav.resolve()
    print(f"[+] Running xma2encode on {input_wav.name}")
    subprocess.run([xma2, str(input_wav)], check=True)

    # Try common output names
    candidates = [
        input_wav.with_suffix(".xma"),
        input_wav.with_suffix(".xma2"),
        input_wav.with_name(input_wav.stem + "_xma2.wav"),
        input_wav.with_name(input_wav.stem + "_xma.wav"),
    ]
    for c in candidates:
        if c.is_file():
            print(f"[+] Found encoded XMA file: {c.name}")
            return c

    raise RuntimeError(
        "xma2encode ran, but I couldn't find the output file.\n"
        "Check which file it created and we can add that pattern."
    )

def get_xma2_payload(xma_file: Path) -> bytes:
    data = xma_file.read_bytes()
    if data[:4] == b"RIFF":
        # RIFF WAVE: extract 'data' chunk
        off = data.find(b"data")
        if off == -1:
            raise RuntimeError(f"'data' chunk not found in XMA2 WAV: {xma_file}")
        size = int.from_bytes(data[off+4:off+8], "little")
        payload_off = off + 8
        if payload_off + size > len(data):
            raise RuntimeError("XMA2 WAV 'data' size goes past end of file.")
        print(f"[+] XMA2 WAV 'data' size: {size} bytes")
        return data[payload_off:payload_off+size]
    else:
        # Treat as raw XMA bitstream
        print(f"[+] Treating {xma_file.name} as raw XMA payload ({len(data)} bytes)")
        return data

def recook_ckd_header(template_ckd: Path, xma2_payload: bytes, out_ckd: Path):
    tmpl = template_ckd.read_bytes()

    # header size at 0x14 (big-endian)
    header_size = int.from_bytes(tmpl[0x14:0x18], "big")
    print(f"[+] Header size: 0x{header_size:X} ({header_size} bytes)")

    header = bytearray(tmpl[:header_size])

    # find 'data' tag inside header
    data_tag_off = header.find(b"data")
    if data_tag_off == -1 or data_tag_off + 12 > len(header):
        raise RuntimeError("'data' tag not found in CKD header.")

    header_size_field = int.from_bytes(header[data_tag_off+4:data_tag_off+8], "big")
    print(f"[+] Header size from 'data' chunk: 0x{header_size_field:X}")
    if header_size_field != header_size:
        print("[!] Warning: header_size mismatch, continuing anyway.")

    orig_audio_size = int.from_bytes(header[data_tag_off+8:data_tag_off+12], "big")
    print(f"[+] Original audio size: {orig_audio_size} bytes")

    new_audio_size = len(xma2_payload)
    print(f"[+] New audio size: {new_audio_size} bytes")

    # update audio size field
    header[data_tag_off+8:data_tag_off+12] = new_audio_size.to_bytes(4, "big")

    new_ckd = bytes(header) + xma2_payload
    print(f"[+] New CKD total size: {len(new_ckd)} bytes")

    # Write using our safe helper
    safe_write_bytes(out_ckd, new_ckd)
    print(f"[+] Wrote recooked CKD: {out_ckd}")

def recook_ckd():
    print("\n=== Recook CKD (template CKD + edited WAV -> new CKD) ===")
    template = ask_path("Drag or type the ORIGINAL .wav.ckd (template) here: ")
    if not template:
        return

    edited_wav = ask_path("Drag or type your EDITED .wav (48kHz PCM) here: ")
    if not edited_wav:
        return

    out_name = input("Output CKD name (e.g. seven_mod.wav.ckd): ").strip().strip('"')
    if not out_name:
        print("[-] No output name given.")
        return

    # Always write outputs into a safe 'output' folder next to the script
    out_dir = get_output_dir()
    out_ckd = out_dir / out_name

    try:
        xma_file = run_xma2encode(edited_wav)
        xma_payload = get_xma2_payload(xma_file)
        recook_ckd_header(template, xma_payload, out_ckd)
    except PermissionError as e:
        print("[-] PermissionError while writing CKD:")
        print(e)
        print("[!] Try running this script from a normal folder (like Desktop or Documents),")
        print("    and avoid Program Files, mounted ISOs, or read-only locations.")
    except Exception as e:
        print("[-] Error during recook:")
        print(e)

# ---------- Main menu ----------

def main():
    while True:
        print("\n=== Just Dance 360 Audio Tool ===")
        print("1) Uncook .wav.ckd -> .wav")
        print("2) Recook (template .wav.ckd + edited .wav -> new .wav.ckd)")
        print("0) Exit")

        choice = input("Select an option: ").strip()
        if choice == "1":
            uncook_ckd()
        elif choice == "2":
            recook_ckd()
        elif choice == "0":
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
