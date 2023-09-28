
import argparse
import os
import os.path as path
from stat import S_ISDIR
from typing import Callable
import math

CHUNK_SIZE = 64 * 1024 # 64k
FENGSH_ENCODE_EXTENSION = "fe"
ZIP_FILE_EXTENSION = "zip"

def encode(chunk: bytes) -> bytes:
    ret_array = []
    for i in range(len(chunk)):
        ret_array.append((((chunk[i] ^ 0x80) + 0x11) & 0xff) ^ 0xb6)
    return bytes(ret_array)

def decode(chunk: bytes) -> bytes:
    ret_array = []
    for i in range(len(chunk)):
        ret_array.append((((chunk[i] ^ 0xb6) - 0x11) & 0xff) ^ 0x80)
    return bytes(ret_array)

def encode_file(src_file, dst_file):
    dst_file = dst_file if dst_file is not None else path.splitext(src_file)[0] + ".{0}".format(FENGSH_ENCODE_EXTENSION)
    process_file(src_file, dst_file, encode)

def decode_file(src_file, dst_file):
    dst_file = dst_file if dst_file is not None else path.splitext(src_file)[0] + ".{0}".format(ZIP_FILE_EXTENSION)
    process_file(src_file, dst_file, decode)
    
def process_file(src_file: str, dst_file: str, processing: Callable[[bytes], bytes]):
    file_size = os.stat(src_file).st_size
    with open(src_file, "rb") as fobj_src:
        with open(dst_file, "wb") as fobj_dst:
            nstep = math.floor(file_size / CHUNK_SIZE)
            for i in range(nstep):
                content = fobj_src.read(CHUNK_SIZE)
                encoded_content = processing(content)
                fobj_dst.write(encoded_content)
            if file_size - nstep * CHUNK_SIZE > 0:
                content = fobj_src.read(file_size - nstep * CHUNK_SIZE)
                encoded_content = processing(content)
                fobj_dst.write(encoded_content)

def process_folder(src_folder, dst_folder, src_ext, dst_ext, file_processer: Callable[[str, str], None]):
    files_to_process = []
    for root, _, files in os.walk(src_folder):
        files_to_process = [path.join(root, f) for f in files if f.endswith(src_ext)]
        # for f in files:
        #    files_to_process.append(path.join(root, f))
    
    dst_folder = dst_folder if dst_folder is not None else src_folder
    for f in files_to_process:
        src_basename = path.basename(f)
        dst_basename = ""
        if '.' in src_basename:
            dst_basename = path.splitext(src_basename)[0] + ".{0}".format(dst_ext)
        else:
            dst_basename = src_basename + ".{0}".format(dst_ext)
        dst_file = path.join(dst_folder, dst_basename)
        file_processer(f, dst_file)

def encode_folder(src_folder, dst_folder=None):
    process_folder(src_folder, dst_folder, ZIP_FILE_EXTENSION, FENGSH_ENCODE_EXTENSION, encode_file)

def decode_folder(src_folder, dst_folder=None):
    process_folder(src_folder, dst_folder, FENGSH_ENCODE_EXTENSION, ZIP_FILE_EXTENSION, decode_file)

def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--decoding", action="store_true", help="decoding or decoding, by default is encoding")
    parser.add_argument("source", help="source file or folder")
    parser.add_argument("destination", nargs="?", help="destination file or folder")
    args = vars(parser.parse_args())
    
    source = args["source"]
    mode = os.stat(source).st_mode
    if S_ISDIR(mode):
        destination = args["destination"] # can be None
        decoding = args["decoding"]
        if not decoding:
            encode_folder(source, destination)
        else:
            decode_folder(source, destination)
    else:
        destination = args["destination"]
        if args["decoding"] is None:
            if source.endswith(ZIP_FILE_EXTENSION):
                encode_file(source, destination)
            elif source.endswith(FENGSH_ENCODE_EXTENSION):
                decode_file(source, destination)
            else:
                print("[Error]: Only zip file is supported")
        else:
            if not destination:
                destination = source + ".zip"
                if os.path.exists(destination):
                    raise Exception(f"{destination} is already existed")
            decode_file(source, destination)


if __name__ == "__main__":
    main()


