import argparse
import struct
import sys
import shutil
import hashlib
import base64
import os
import zipfile
import io
import traceback

def calculate_md5(file_path, chunk_size=8192):
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                md5_hash.update(byte_block)
        return md5_hash.hexdigest()
    except Exception as e:
        return None

def patch_hl_to_kc(dir, hit_sound, counts):
    print("Applying KC patches...")
    for item in KC_FILES:
        try:
            if item["type"] == "patched_file":
                if os.path.exists(os.path.join(dir, item["backup_path"])):
                    print("Patches have already been applied. Skipping...")
                    break
                print(f"Patching {item['original_path']}...")
                # Make a backup of original file
                shutil.copy2(os.path.join(dir, item["original_path"]), os.path.join(dir, item["backup_path"]))
                # Write patched file
                with open(os.path.join(dir, item["original_path"]), 'wb+') as newfile:
                    newfile.write(base64.b64decode(item["data"]))
                # Sanity check md5 after writing patched file
                calculated_md5 = calculate_md5(os.path.join(dir, item["original_path"]))
                if calculated_md5 != item["md5"]:
                    print(f"Checksum failure on patched file: {item['original_path']}. Expected: {item['patched_md5']}, got: {calculated_md5}\n")
                    undo_kc_patch(dir)
                    sys.exit(1)
            elif item["type"] == "newfile":
                # Special case for hit sounds
                if item['path'] == "valve_WON/sound/kc/hitmarker.wav" and hit_sound:
                    print(f"Copying hitsound from {hitsound} to {item['path']}...")
                    shutil.copy2(hitsound, item['path'])
                    continue
                # Special case for counts.txt
                elif item['path'] == "valve_WON/counts.txt" and counts:
                    print(f"Copying hitsound from {counts} to {item['path']}...")
                    shutil.copy2(counts, item['path'])
                    continue
                print(f"Creating {item['path']}...")
                if not os.path.exists(os.path.dirname(os.path.join(dir, item["path"]))):
                    os.makedirs(os.path.dirname(os.path.join(dir, item["path"])))
                with open(os.path.join(dir, item["path"]), 'wb+') as newfile:
                    newfile.write(base64.b64decode(item["data"]))
                # Sanity check md5
                calculated_md5 = calculate_md5(os.path.join(dir, item["path"]))
                if calculated_md5 != item["md5"]:
                    print(f"Checksum failure on file: {item['path']}. Expected: {item['md5']}, got: {calculated_md5}\n")
                    undo_kc_patch(dir)
                    sys.exit(1)
            elif item["type"] == "move_and_restore":
                print(f"Moving {item['original_path']}...")
                if os.path.isfile(os.path.join(dir, item["original_path"])) and os.path.exists(os.path.join(dir, item["original_path"])):
                    shutil.copy2(os.path.join(dir, item["original_path"]), os.path.join(dir, item["backup_path"]))
                elif os.path.exists(os.path.join(dir, item["original_path"])):
                    shutil.copytree(os.path.join(dir, item["original_path"]), os.path.join(dir, item["backup_path"]))
            elif item["type"] == "zip":
                print(f"Extracting to {item['extract_to_path']}...")
                if not os.path.exists(os.path.dirname(os.path.join(dir, item["extract_to_path"]))):
                    os.makedirs(os.path.dirname(os.path.join(dir, item["extract_to_path"])))
                z = zipfile.ZipFile(io.BytesIO(base64.b64decode(item["data"])))
                z.extractall(os.path.join(dir, item["extract_to_path"]))
        except Exception as e:
            print(f"Error occurred while trying to apply patches: {traceback.format_exc()}\n")
            undo_kc_patch(dir)
            sys.exit(1)


def undo_kc_patch(dir):
    print("Undoing KC patches...")
    for item in KC_FILES:
        try:
            if item["type"] == "patched_file":
                print(f"Restoring {item['original_path']}...")
                if os.path.exists(os.path.join(dir, item["backup_path"])):
                    shutil.copy2(os.path.join(dir, item["backup_path"]), os.path.join(dir, item["original_path"]))
                    os.remove(os.path.join(dir, item["backup_path"]))
                else:
                    print(f"WARNING: Failed to restore {os.path.join(dir, item['original_path'])} !")
            elif item["type"] == "newfile":
                print(f"Deleting {item['path']}...")
                if os.path.exists(os.path.join(dir, item["path"])):
                    os.remove(os.path.join(dir, item["path"]))
            elif item["type"] == "move_and_restore":
                print(f"Restoring {item['original_path']}...")
                if os.path.exists(os.path.join(dir, item["backup_path"])):
                    # Remove the patched path first
                    if os.path.exists(os.path.join(dir, item["original_path"])):
                        if os.path.isfile(os.path.join(dir, item["original_path"])):
                            os.remove(os.path.join(dir, item["original_path"]))
                        else:
                            shutil.rmtree(os.path.join(dir, item["original_path"]))
                    
                    # Copy backup back to original path
                    if os.path.isfile(os.path.join(dir, item["original_path"])):
                        shutil.copy2(os.path.join(dir, item["backup_path"]), os.path.join(dir, item["original_path"]))
                    else:
                        shutil.copytree(os.path.join(dir, item["backup_path"]), os.path.join(dir, item["original_path"]))
                    
                    # Remove backup
                    if os.path.isfile(os.path.join(dir, item["backup_path"])):
                        os.remove(os.path.join(dir, item["backup_path"]))
                    else:
                        shutil.rmtree(os.path.join(dir, item["backup_path"]))
                else:
                    print(f"WARNING: Failed to restore {os.path.join(dir, item['original_path'])} !")
        except Exception as e:
            print(f"Error happened during one of the cleanup steps: {traceback.format_exc()}. Continuing...")
            continue      

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str, default="", help="'patch' or 'clean'")
    parser.add_argument("--dir", "-d", type=str, default="Half-Life", help="Directory containing 'valve' and 'valve_WON' folders (i.e. Half-Life directory)")
    parser.add_argument("--hitsound", "-s", type=str, default="", help="Path to a .wav you want to play when you get a kill")
    parser.add_argument("--counts", "-c", type=str, default="", help="Path to a counts.txt file")
    args = parser.parse_args()
    
    if not os.path.exists(os.path.join(args.dir, "valve")):
        sys.exit("Could not find Half-Life/valve directory! Set the 'dir' argument to the Half-Life directory within the HL2005 or GoldSrc Package.")
    if not os.path.exists(os.path.join(args.dir, "valve_WON")):
        sys.exit("Could not find Half-Life/valve_WON directory! Set the 'dir' argument to the Half-Life directory within the HL2005 or GoldSrc Package.")
    if args.hitsound and not os.path.exists(args.hitsound):
        sys.exit(f"Could not find custom hit sound at {args.hitsound}")
    if args.counts and not os.path.exists(args.counts):
        sys.exit(f"Could not find custom counts file at {args.counts}")

    if args.action == "patch" or args.action == "":
        try:
            patch_hl_to_kc(args.dir, args.hitsound, args.counts)
        except KeyboardInterrupt:
            undo_kc_patch(args.dir)
    elif args.action == "clean":
        undo_kc_patch(args.dir)
    else:
        print(f"Unrecognized argument: {args.action}")

KC_FILES = [
    {
        "type": "patched_file",
        "original_path": "valve_WON/cl_dlls/client.dll",
        "backup_path": "valve_WON/cl_dlls/client.dll.kcbak",
        "md5" : "1c44d75f97afbe448af0b0b68839083c",
        "data": "$client.dll"
    },
    {
        "type": "patched_file",
        "original_path": "valve_WON/dlls/hl.dll",
        "backup_path": "valve_WON/dlls/hl.dll.kcbak",
        "md5" : "a12e6483deb11cccdf52179168ad2642",
        "data": "$hl.dll"
    },
    {
        "type": "newfile",
        "path": "valve_WON/counts.txt",
        "md5" : "629c3580a9affa5d23a66400d088ede7",
        "data": "$counts.txt"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c1a0c.bsp",
        "md5" : "2e1cf4d5c386cb5fb1e762a98818689e",
        "data": "$c1a0c.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c1a0e.bsp",
        "md5" : "642e175c00f7bde7db79c5b5de123792",
        "data": "$c1a0e.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c1a4f.bsp",
        "md5" : "b5bb0a4f8f362ac790f584c07263ab02",
        "data": "$c1a4f.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c1a4i.bsp",
        "md5" : "856478fcdbcbaea96071011708020bb3",
        "data": "$c1a4i.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c2a2b1.bsp",
        "md5" : "6b45dd1a808b2452a0767c1262f2679a",
        "data": "$c2a2b1.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c2a5.bsp",
        "md5" : "0679eefd8e2c3332aa534e73de5d6eb8",
        "data": "$c2a5.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c2a5b.bsp",
        "md5" : "8fdad6206020a1edc6068d2c6494fc81",
        "data": "$c2a5b.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c2a5d.bsp",
        "md5" : "10c6f694d5a4902336e4a1854c86a7aa",
        "data": "$c2a5d.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c2a5e.bsp",
        "md5" : "cb591fd28e573c97a383469fd385274a",
        "data": "$c2a5e.bsp"
    },
    {
        "type": "newfile",
        "path": "valve_WON/maps/c4a1b.bsp",
        "md5" : "8e97e8fe1a3903581b17e92010661c53",
        "data": "$c4a1b.bsp"
    },
    {
        "type": "move_and_restore",
        "original_path": "valve_WON/maps/graphs",
        "backup_path": "valve_WON/maps/graphs.kcbak"
    },
    {
        "type": "zip",
        "extract_to_path": "valve_WON/maps/graphs/",
        "md5" : "2e3cc1c9671f911abd3d2e87852a41a5",
        "data": "$graphs.zip"
    },
    {
        "type": "newfile",
        "path": "valve_WON/resource/background/800_1_a_loading.tga",
        "md5" : "fe353a6a267db032181e81981130e120",
        "data": "$800_1_a_loading.tga"
    },
    {
        "type": "newfile",
        "path": "valve_WON/resource/background/800_1_c_loading.tga",
        "md5" : "b8b6a06976a2ba0687467af53ed47308",
        "data": "$800_1_c_loading.tga"
    },
    {
        "type": "newfile",
        "path": "valve_WON/resource/background/800_2_c_loading.tga",
        "md5" : "5c1c8b04d08658a35fd63d35bcf926d6",
        "data": "$800_2_c_loading.tga"
    },
    {
        "type": "newfile",
        "path": "valve_WON/sound/kc/hitmarker.wav",
        "md5" : "dcd1a09efaff1e972d661f4143e0fe21",
        "data": "$hitmarker.wav"
    }
]

if __name__ == "__main__":
    main()