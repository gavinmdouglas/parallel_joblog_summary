# GNU Parallel joblog summary

**Script for summarizing GNU parallel joblog file. Useful for identifying how many and which jobs failed (if any), and to ensure that all commands finished successfully.**

[GNU parallel](https://git.savannah.gnu.org/cgit/parallel.git) is an extremely useful tool for parallelizing commands on the command-line. You can see this [tutorial](https://github.com/LangilleLab/microbiome_helper/wiki/Quick-Introduction-to-GNU-Parallel) from 2017 that I wrote to showcase some of the key features.

## Script description

Compares an input file containing all commands passed to GNU parallel using the approach of `cat FILE | parallel '{}'`.

There should be one command per line in this file. This script compares this file with the resulting logfile created by using the `--joblog` option.

It will provide a breakdown of how many commands fit into the following categories (to standard output):
1. Finished successfully (and only present once in log).
2. Failed (and only present once in log).
3. Were never run (i.e., not found in log).

This information about duplicate commands in the logfile can also be output, but only if there is at least one occurrence (because they are rare issues):  

* Present multiple times in log, but was successful everytime. Indicates redundancy and likely user error.
* Present multiple times in log, but failed everytime.
* Finished successfully upon last instance, but failed when run earlier in log (so likely re-run after an error).
* Produced error upon last instance in log, but was successful at least once in another instance. This is a redflag that a successful job might have been partially overwritten.  

An error will be thrown if there are any commands in the log file that are not present in the commands file. Also, note that empty commands (in input command file or in logfile) will be ignored. This can happen if people put empty lines in between input commands accidently.
 
If specified, jobs that were never run, and jobs that were run but failed, can be written out to new (separate) command files.

**Usage example:**

```
python joblog_summary.py --cmds CMDS_FILE.txt \
                         --log JOBLOG.txt \
                         --cmds_to_run REMAINING_CMDS_FILE.txt \
                         --failed_cmds FAILED_CMDS.txt
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

The files should now all be gzipped and you can look in `gzip_log.txt` to see the job running summary per command (the `Exitval` and `Signal` columns should all contains 0's to indicate they finished successfully).

Note that in the above example, we specified the command structure `gzip {}` and the input files `::: testfile*txt` separately. If you use the `--dry-run` option, the full commands will be printed to screen without running them.

You can also explicitly write out the commands you want to run and pass them to `parallel`. As an example, decompress the files and create a new file containing the gzip command we want to run:
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


## Detailed joblog_summary.py usage example

`joblog_summary.py` is useful when you are running many commands in parallel, and you are concerned that some jobs may not have run or threw an error. Note that this requires that the commands run are present in a file, using the approach we used to run `gzip_cmds.sh` above, so that the original commands can be compared to those in the `--joblog` output table.

The basic usage is to just get summary counts of the numbers of jobs in different categories (corresponding to the seven categories described at the top of this page).

For instance, if you run:
```
python ../joblog_summary.py --cmds gzip_cmds.sh --log gzip_log2.txt
```

You should see:
```
Successful (and present once in joblog)	10
Failed (and present once in joblog)	0
Not run (i.e., not present in joblog)	0
```

In this case all jobs were run, and no jobs failed. Note that additional information can also be output in rare cases where they are wonky lines in the joblog file (especially when commands are present twice), but that information was not output here as there were no duplicate commands in the logfile.

**But what about if there _are_ failed jobs?** We can create this scenario by simply adding another command to gzip a file that doesn't exist.

Decompress the files a final time:
```
gunzip testfile*txt.gz
```

Add an additional gzip command for a file that does not exist, which will cause an error, and re-run gzip commands with `parallel`:
```
echo "gzip testfile.Iamgonnafail.txt" >> gzip_cmds.sh
cat gzip_cmds.sh | parallel -j 2 --eta --joblog gzip_log3.txt '{}'
```
You should have the error `gzip: testfile.Iamgonnafail.txt: No such file or directory` and you will note an Exitval of 1 for this command in `gzip_log3.txt`, but you can imagine this would be easy to miss if you were running 1000's of commands in parallel.

To get a summary of the parallel joblog file, and **to get a file containing all failed commands** (which can make it easier to re-run commands after you fix the problem):
```
python ../joblog_summary.py --cmds gzip_cmds.sh \
                            --log gzip_log3.txt \
                            --failed_cmds gzip_failed_cmds.txt
```

The summary counts should indicate that one job failed, which you can see in `gzip_failed_cmds.txt`.
