#!/usr/bin/env python
import sys
import csv
import numpy as np
import subprocess
import os

time = float(sys.argv[1])
n_time_pts = int(sys.argv[2])
data_file_prefix = sys.argv[3].split('/')[-1]
emp_est_dir = "/".join(sys.argv[3].split("/")[:-1])
cfg_file = sys.argv[4]
train_dir = sys.argv[5]
format_dir = sys.argv[6]

assert os.path.exists(emp_est_dir), f'the path, {emp_est_dir}, does not exist.'


# make a list of time points from time range and n_time_points
time_pts = np.arange(0, time, time/n_time_pts)

# open the 3 input files
with open(emp_est_dir + "/" + data_file_prefix + ".labels.csv", 'r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    label_dat = np.array(list(reader))
with open(emp_est_dir + "/" + data_file_prefix + ".dat.nex", 'r', newline='') as dat_nex_file:
    dat_nex = dat_nex_file.read()
with open(emp_est_dir + "/" + data_file_prefix + ".tre", 'r', newline='') as tre_file:
    tree = tre_file.read()


# get the time point column index
target_col_idx = np.where(label_dat[0] == "Time_before_present_0")


# loop through each time point, estimate prevalences and add to the time series output file
with open(emp_est_dir + "/" + data_file_prefix + ".time_series.csv", mode = "a") as time_series_out:

    # write to file
    for t in time_pts[1:][::-1]:

        # change time point
        label_dat[1,target_col_idx] = t

        time_file_prefix = "t" + str(t) + "_" + data_file_prefix
        time_file_prefix_path = emp_est_dir + "/" + time_file_prefix

        # write to file
        np.savetxt(time_file_prefix_path + ".labels.csv", label_dat, delimiter=',', fmt='%s')
        with open(time_file_prefix_path + ".dat.nex", 'w') as file:
            file.write(dat_nex)
        with open(time_file_prefix_path + ".tre", 'w') as file:
            file.write(tree)


        # run phyddle
        phyddle_command = [
                    'phyddle', '-s', 'E', '-c', cfg_file,
                    '--fmt_dir', format_dir, '--trn_dir', train_dir,
                    '--est_dir', emp_est_dir, '--est_prefix', time_file_prefix
                   ]
        subprocess.run(phyddle_command, capture_output = False, text=True)
        #phyddle -s E -c cfg_file --fmt_dir format_dir --trn_dir train_dir --est_dir emp_est_dir --est_prefix time_file_prefix

        # add emp_est result to growing time series prediction file
        with open(time_file_prefix_path + ".emp_est.labels.csv") as est_file:
            if t == time_pts[-1]:
                header = next(est_file)
                t_estimate = est_file.read()
                time_series_out.write("time_before_present," + header)
            else:
                next(est_file)
                t_estimate = est_file.read()

            time_series_out.write(str(t) + "," + t_estimate)

            # remove time_file_prefix_path files
            os.remove(time_file_prefix_path + ".labels.csv")
            os.remove(time_file_prefix_path + ".dat.nex")
            os.remove(time_file_prefix_path + ".tre")