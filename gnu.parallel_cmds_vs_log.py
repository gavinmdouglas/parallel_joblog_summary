#!/usr/bin/python3

import argparse
import sys
import os


def main():

    parser = argparse.ArgumentParser(

            description="Compare an input file containing all commands passed to GNU parallel using the approach of \"cat FILE | parallel \'{}\'\". "
                        "There should be one command per line in this file. This script compares this file with the resulting logfile created by using "
                        "the --joblog option.\nIt will provide a breakdown of how many commands fit into the following categories (to standard output):\n"
                        "    (1) Finished successfully (and only present once in log)\n"
                        "    (2) Failed (and only present once in log)\n"
                        "    (3) Were never run (i.e., not found in log)\n"
                        "    (4) Present multiple times in log, but was successful everytime. Indicates redundancy and likely user error.\n"
                        "    (5) Present multiple times in log, but failed everytime.\n"
                        "    (6) Finished successfully upon last instance, but failed when run earlier in log (so likely re-run after an error)\n"
                        "    (7) Produced error upon last instance in log, but was successful at least once in another instance. This is a redflag that a successful job might have been partially overwritten.\n"
                        "An error will be thrown if there are any commands in the log file that are not present in the commands file. Also, note that empty commands "
                        "(in input command file or in logfile) will be ignored. This can happen if people put empty lines in between input commands accidently.\n\n"
                        "If specified, jobs that were never run, and jobs that were run but failed, can be written out to new (separate) command files.\n",

epilog='''Usage example:

python gnu.parallel_cmds_vs_log.py --cmds CMDS_FILE.txt --log JOBLOG.txt --cmds_to_run NEW_CMDS_FILE.txt --failed_cmds FAILED_CMDS.txt

''', formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--cmds', metavar="CMDS_INPUT", type=str,
                        help="Path to input commands file that was input to parallel", required = True)

    parser.add_argument('--log', metavar="LOG_INPUT", type=str,
                        help="Path to input log file created with parallel --joblog", required = True)

    parser.add_argument('--cmds_to_run', metavar="REMAINING_CMDS", type=str,
                        help="Path to new commands file containing only commands that have not been run yet (i.e., they have not even been tried yet, so this does not include failed commands). "
                             "Note that these commands will not be output at all unless this option is specified.",
                        default = None,
                        required = False)

    parser.add_argument('--failed_cmds', metavar="FAILED_CMDS", type=str,
                        help="Path to new commands file containing only commands that are marked as failed at least once in the job log file. "
                             "Note that these commands will not be output at all unless this option is specified.",
                        default = None,
                        required = False)

    args = parser.parse_args()

    # Read commands into set.
    cmds = set()

    blank_cmds = 0
    with open(args.cmds, 'r') as cmds_infile:
        for raw_cmd in cmds_infile:
            raw_cmd = raw_cmd.rstrip()

            if raw_cmd == "":
                blank_cmds += 1
                continue

            if raw_cmd in cmds:
                sys.exit('Error, this command (in between quotes) is present multiple times in the commands infile: \"' + raw_cmd + '\"')
            else:   
                cmds.add(raw_cmd)


    jobs_to_run = cmds.copy()

    successful_jobs_any = set()
    successful_jobs_unique = set()
    successful_jobs_after_fail = set()
    successful_jobs_redundant = set()

    failed_jobs_any = set()
    failed_jobs_unique = set()
    failed_jobs_repeated = set()
    failed_jobs_after_success = set()

    log_cmds = set()

    # Parse log file.
    blank_log_cmds = 0
    with open(args.log, 'r') as log_infile:

        # Skip header.
        next(log_infile)
        for raw_log in log_infile:
            raw_log = raw_log.rstrip()
            raw_log_split = raw_log.split('\t')

            log_cmd = "\t".join(raw_log_split[8:])

            if log_cmd == "":
                blank_log_cmds += 1
                continue

            # Make sure that cmd present in cmd infile.
            if log_cmd not in cmds:
                sys.exit('Error, this command was not present in the infile of commands:\n' + log_cmd)

            # Check if job failed.
            if raw_log_split[6] != '0' or raw_log_split[7] != '0':
                failed_flag = True
            else:
                failed_flag = False

            if not failed_flag:
                # If job passed, then there are three options:
                # 1) Passed and this is the first instance (must remove from jobs to run). Generally this is probably the most likely outcome (hopefully!).
                # 2) Passed, but was run earlier and failed (most likely a re-run failed command).
                # 3) Passed, and was run earlier too and passed (so seems like it was run again accidentally? This is referred to as "redundant").

                if log_cmd in jobs_to_run:
                    jobs_to_run.remove(log_cmd)
                    successful_jobs_unique.add(log_cmd)
                    successful_jobs_any.add(log_cmd)

                elif log_cmd in successful_jobs_unique:
                    successful_jobs_unique.remove(log_cmd)
                    successful_jobs_redundant.add(log_cmd)

                elif log_cmd in failed_jobs_any:

                    successful_jobs_any.add(log_cmd)
                    successful_jobs_after_fail.add(log_cmd)

                    if log_cmd in failed_jobs_unique:
                        failed_jobs_unique.remove(log_cmd)

                    elif log_cmd in failed_jobs_repeated:
                        failed_jobs_repeated.remove(log_cmd)

                    elif log_cmd in failed_jobs_after_success:
                        failed_jobs_after_success.remove(log_cmd)
                        
            else:
                # If job failed, then these are the options:
                # 1) First instance and failed
                # 2) Failed earlier as well.
                # 3) Failed after at least one success earlier.

                if log_cmd in jobs_to_run:
                    jobs_to_run.remove(log_cmd)
                    failed_jobs_unique.add(log_cmd)
                    failed_jobs_any.add(log_cmd)

                elif log_cmd in failed_jobs_unique:
                    failed_jobs_unique.remove(log_cmd)
                    failed_jobs_repeated.add(log_cmd)

                elif log_cmd in successful_jobs_any:

                    failed_jobs_any.add(log_cmd)
                    failed_jobs_after_success.add(log_cmd)

                    if log_cmd in successful_jobs_unique:
                        successful_jobs_unique.remove(log_cmd)

                    elif log_cmd in successful_jobs_redundant:
                        successful_jobs_redundant.remove(log_cmd)

                    elif log_cmd in successful_jobs_after_fail:
                        successful_jobs_after_fail.remove(log_cmd)


        # Print out summary table to standard output.
        print('successful_jobs_unique ' + str(len(successful_jobs_unique)))
        print('failed_jobs_unique ' + str(len(failed_jobs_unique)))
        print('jobs_not_run ' + str(len(jobs_to_run)))
        print('successful_jobs_redundant ' + str(len(successful_jobs_redundant)))
        print('failed_jobs_repeated ' + str(len(failed_jobs_repeated)))
        print('successful_jobs_after_fail ' + str(len(successful_jobs_after_fail)))
        print('failed_jobs_after_success ' + str(len(failed_jobs_after_success)))

        if args.cmds_to_run:
            with open(args.cmds_to_run, 'w') as cmds_out:
                for cmd in jobs_to_run:
                    print(cmd, file = cmds_out)

        if args.failed_cmds:
            with open(args.failed_cmds, 'w') as failed_out:
                for failed_cmd in failed_jobs_any:
                    print(failed_cmd, file = failed_out)

        if blank_cmds > 0 or blank_log_cmds > 0:
            print('\n\nThere were ' + str(blank_cmds) + ' empty lines in the input command file, and ' + str(blank_log_cmds) + ' empty commands in the logfile.\n',
                  file = sys.stderr)

if __name__ == '__main__':
    main()
