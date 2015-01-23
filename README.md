= About =

This Python script is able to extract all music tracks from a Runescape cache.
It is not necessary to have the game installed. Only the cache files need to be
present in a directory. Specifically the files `main_file_cache.dat2`,
`main_file_cache.idx17` and `main_file_cache.idx40` are needed.

= Usage =

If you have Runescape installed, you can find the cache in your user directory
in `jagexcache/runescape/LIVE/`. If you run Runescape under Wine, then they
will be located in
`$WINEPREFIX/drive_c/windows/profiles/josch/jagexcache/runescape/LIVE/`.

Then run the script like this:

	./rsmusicextract.py path/to/cache path/for/extracted/files

You can omit the path to extract the music files to, in which case the program
will only list which music tracks are available.

You can also add the `--incomplete` option in which case also incomplete music
tracks will be extracted (or displayed in case you omitted the directory to
extract to).

= Combining the music =

If an output directory is given, then the script will create it if necessary
and extract the individual music chunks into subdirectories which are named
after the music track they belong to. The chunks are mostly either 3.918 s or
7.836 s long.

Each individual chunk is an ogg vorbis file which, when concatenated, make the
full music track. They are numbered sequentially to concatenate them in the
right order.

The vorbis container format allows to concatenate multiple vorbis files by
simply running (on unix-like operating systems):

	cat file1.ogg file2.ogg file3.ogg > combined.ogg

The problem is, that there are some players which either do not support ogg
files of that kind and will only play the very first chunk or which add
split-second pauses between the individual parts. Even using the ffmpeg concat
demuxer will leave audible gaps between the individual chunks. I posted the
following questions to find a solution to this problem:

 - http://superuser.com/questions/864911/lossless-concatenation-of-ogg-vorbis-files
 - http://stackoverflow.com/questions/27980960/how-to-lossless-concatenate-ogg-vorbis-files

Until that problem is solved, you can concatenate the individual tracks in a
single file by re-encoding the output stream. To not loose any quality, flac
can be used as the codex. The following snippet will combine the individual ogg
chunks in every directory into a single file of the same name:

	$ mkdir combined
	$ for dir in */; do \
		dir=${dir%*/}; \
		sox --combine concatenate "$dir"/* -C 8 "combined/$dir.flac"; \
	done

= Origin =

This code is inspired by RSCacheTool by Villermen:

https://github.com/Villermen/RSCacheTool

It especially benefits from the reverse engineering that was done to create
that tool.

This script was written because of certain fundamental design shortcomings of
RSCacheTool which made it suboptimal for my use case. For example, to just list
all music tracks, RSCacheTool first has to extract all files from archive 40
which can take up a couple of gigabytes of disk space.

While RSCacheTool aims to be a swiss army knife for Runescape cache files, this
script only wants to provide the means to display and extract the Runescape
music from Runescape cache files.

RSCacheTool also has to be run in two stages to extract and name the music
track. This script does both actions in one go.

This script works "the other way round" compared to RSCacheTool. While
RSCacheTool first extracts all files and allows to rename them later, this
script will first extract the list of all available music and then extract the
necessary files from the archive. This allows to list all available music
tracks without having to extract them first.

Finally, because of its simplicity, this script is only 20% of the length of
RSCacheTool. For example it does not attempt to join the extract music as this
can be done by a small shell invocation as demonstrated above.
