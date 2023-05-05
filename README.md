# parallel_joblog_summary

**Script for summarizing GNU parallel joblog file, to identify how many and which jobs failed (if any)**

[GNU parallel](https://git.savannah.gnu.org/cgit/parallel.git) is an extremely useful tool for parallelizing commands on the command-line. You can see this [tutorial](https://github.com/LangilleLab/microbiome_helper/wiki/Quick-Introduction-to-GNU-Parallel) from 2017 that I wrote to showcase some of the key features.

## Script description

Compares an input file containing all commands passed to GNU parallel using the approach of `cat FILE | parallel '{}'`.

There should be one command per line in this file. This script compares this file with the resulting logfile created by using the `--joblog` option.

It will provide a breakdown of how many commands fit into the following categories (to standard output):
1. Finished successfully (and only present once in log)
2. Failed (and only present once in log)
3. Were never run (i.e., not found in log)
4. Present multiple times in log, but was successful everytime. Indicates redundancy and likely user error.
5. Present multiple times in log, but failed everytime.
6. Finished successfully upon last instance, but failed when run earlier in log (so likely re-run after an error)
7. Produced error upon last instance in log, but was successful at least once in another instance. This is a redflag that a successful job might have been partially overwritten.

An error will be thrown if there are any commands in the log file that are not present in the commands file. Also, note that empty commands (in input command file or in logfile) will be ignored. This can happen if people put empty lines in between input commands accidently.
 
If specified, jobs that were never run, and jobs that were run but failed, can be written out to new (separate) command files.

**Usage example:**

```
python gnu.parallel_cmds_vs_log.py --cmds CMDS_FILE.txt --log JOBLOG.txt --cmds_to_run NEW_CMDS_FILE.txt --failed_cmds FAILED_CMDS.txt
```


## Standard GNU Parallel examples

Below are basic `parallel` usage examples. First, to create empty testfiles for the example:

```
mkdir example
cd example

for i in {1..10}; do
  TESTFILE="testfile.$i.txt"
  touch $TESTFILE
 done
```

If you look at the directory file listing (`ls`), you should see:
```
testfile.10.txt  testfile.2.txt  testfile.4.txt  testfile.6.txt  testfile.8.txt
testfile.1.txt   testfile.3.txt  testfile.5.txt  testfile.7.txt  testfile.9.txt
```

Let's say we wanted to run two `gzip` commands at a time to compress these files. We could do so with this `parallel` commands:

```
parallel -j 2 --eta --joblog gzip_log.txt 'gzip {}' ::: testfile*txt
```

The files should now all be gzipped and you can look in `gzip_log.txt` to see the job running summay per command (the `Exitval` and `Signal` columns should all contains 0's to indicate they finished successfully).

Note that in the above example, we specified the command structure `gzip {}` and the input files `::: testfile*txt` separately. If you use this `--dry-run` option you can see a print out of the full commands without running them.

You can also explicitly write out the commands you want to run and pass them to `parallel`.

As an example, decompress the files and create a new file containing the gzip command we want to run:
```
gunzip testfile*txt.gz

for i in {1..10}; do
  TESTFILE="testfile.$i.txt"
  echo "gzip $TESTFILE" >> gzip_cmds.sh
 done
```

We can pass these commands to `parallel` to run like so:
```
cat gzip_cmds.sh | parallel -j 2 --eta --joblog gzip_log2.txt '{}'
```

The result should be the same as above!


## gnu.parallel_cmds_vs_log.py usage example

`gnu.parallel_cmds_vs_log.py` 

