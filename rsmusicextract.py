#!/usr/bin/python3
#
# Copyright 2015 Johannes 'josch' Schauer <j.schauer@email.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

import os, struct, io, zlib, sys

def bytes_to_int(data):
    return sum([b << ((len(data) - i - 1) * 8) for i, b in enumerate(data)])

def unpack_file(cache_dir, archive_idx, file_idx):
    idx_fname = os.path.join(cache_dir, "main_file_cache.idx" + str(archive_idx))
    with open(idx_fname, "rb") as idx_file:
        idx_file.seek(file_idx*6)
        fsize = bytes_to_int(idx_file.read(3))
        curr_chunk_offs = bytes_to_int(idx_file.read(3)) * 520
    write_offs, chunk_idx, fbuf = 0, 0, b""
    with open(os.path.join(cache_dir, "main_file_cache.dat2"), "rb") as cache_file:
        while curr_chunk_offs != 0:
            cache_file.seek(curr_chunk_offs)
            if file_idx >= 65536:
                assert file_idx == struct.unpack(">I", cache_file.read(4))[0]
                chunk_size = min(510, fsize - write_offs)
            else:
                assert file_idx == struct.unpack(">H", cache_file.read(2))[0]
                chunk_size = min(512, fsize - write_offs)
            assert chunk_idx == struct.unpack(">H", cache_file.read(2))[0]
            curr_chunk_offs = bytes_to_int(cache_file.read(3)) * 520
            assert archive_idx == struct.unpack("B", cache_file.read(1))[0]
            chunk_idx += 1
            write_offs += chunk_size
            fbuf += cache_file.read(chunk_size)
    assert len(fbuf) == fsize
    if fbuf[9:11] == b"\x1f\x8b":
        return zlib.decompress(fbuf[19:], -zlib.MAX_WBITS)
    elif fbuf[4:10] == b"\x31\x41\x59\x26\x53\x59":
        raise Exception("bzip2 decompression not implemented")
    else:
        return fbuf[5:]

def get_tname_dict(inf):
    track_id2name = dict()
    music_num, = struct.unpack(">H", inf.read(2))
    for i in range(music_num):
        track_id, = struct.unpack(">H", inf.read(2))
        s = b""
        while True:
            b = inf.read(1)
            if b == b"\x00":
                break
            s += b
        if s in [b'', b' ', b'  ', b'   ']:
            continue
        track_id2name[track_id] = s.decode("utf8")
    return track_id2name

def get_tid_dict(inf, track_id2name):
    file_id2track = dict()
    file_num, = struct.unpack(">H", inf.read(2))
    for i in range(file_num):
        track_id, file_id = struct.unpack(">HI", inf.read(6))
        if track_id not in track_id2name:
            continue
        file_id2track[file_id] = track_id
    return file_id2track

def main(cache_dir, out_dir, process_incomplete):
    # archive 15, file 5 stores the track names
    resolve = unpack_file(cache_dir, 17, 5)
    # this is a gross hack because I don't know a better way to find the right
    # sections in the archive
    names = resolve.index(b"\x00\x66\x24\x07")
    files = resolve.index(b"\x00\x66\x0b\x08")
    assert names != -1 and files != -1
    track_id2name = get_tname_dict(io.BytesIO(resolve[names+6:]))
    file_id2track = get_tid_dict(io.BytesIO(resolve[files+6:]), track_id2name.keys())

    # go through all track ids and get the associated file from the archive
    tracklist = []
    for i,(file_id, track_id) in enumerate(sorted(file_id2track.items())):
        jaga = unpack_file(cache_dir, 40, file_id)
        if jaga is None or jaga[:4] != b"JAGA":
            continue
        jaga, incomplete, ogg_chunks = io.BytesIO(jaga[32:]), False, []
        while jaga.read(4) != b"OggS":
            file_id, = struct.unpack(">I", jaga.read(4))
            ogg = unpack_file(cache_dir, 40, file_id)
            if ogg is None or ogg[:4] != b"OggS":
                incomplete = True
                break
            ogg_chunks.append(ogg)
        print("%f %%"%((i*100)/len(file_id2track)), end='\r', file=sys.stderr)
        if incomplete and not process_incomplete:
            continue
        if not out_dir:
            tracklist.append(track_id2name[track_id])
            continue
        ogg_chunks = [ b"OggS" + jaga.read() ] + ogg_chunks
        if incomplete:
            outdir = os.path.join(out_dir, "incomplete", track_id2name[track_id])
        else:
            outdir = os.path.join(out_dir, track_id2name[track_id])
        os.makedirs(outdir, exist_ok=True)
        for i,chunk in enumerate(ogg_chunks):
            with open(os.path.join(outdir, "%03d.ogg"%i), "wb") as f:
                f.write(chunk)
    if not out_dir:
        print("\n".join(sorted(tracklist)))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract music tracks from runescape cache file.")
    parser.add_argument("cache", help="The runescape cache directory (probably ends with jagexcache/runescape/LIVE/).")
    parser.add_argument("out", nargs="?", help="Output directory for extracted music. If this is not supplied, the available music is simply listed.")
    parser.add_argument("-i", "--incomplete", action="store_true", help="Also process incomplete music.")
    args = parser.parse_args()
    main(args.cache, args.out, args.incomplete)
