#!/usr/bin/env python3
"""
    Wrapper utility around qstat -f that parses the output (given in json format)
    and returns a wide listing.
"""

import paramiko
import subprocess
import json
from functools import reduce 
import time
import socket

# Fields to Extract from qstat full output
fields = [
    ['Job_Name'],
    ['Job_Owner'],
    ['job_state'], 
    ['queue'],
    ['Resource_List', 'nodect'],
    ['Resource_List', 'walltime']
]
field_character_limit = 50

def get_local_qstat_raw():
    """Responsibility: Local OS Execution"""
    try:
        return subprocess.check_output('qstat -f -Fjson', shell=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_remote_qstat_raw(machine):
    """Responsibility: Network/SSH Execution"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=machine, timeout=5)
        stdin, stdout, stderr = ssh.exec_command('/opt/pbs/bin/qstat -f -Fjson')
        
        output = None
        if stdout.channel.recv_exit_status() == 0:
            output = stdout.read()
        ssh.close()
        return output
    except Exception:
        return None

def get_qstat_output(machine=None):
    """Responsibility: Orchestration and Data Transformation"""
    raw_data = get_remote_qstat_raw(machine) if machine else get_local_qstat_raw()
    
    if not raw_data:
        host = machine if machine else socket.gethostname()
        print(f"Error: Could not retrieve PBS data from {host}. Is this a valid machine with PBS installed?")
        return None

    return json.loads(raw_data)

def print_wide_status(Job_ID, Job_Name, Job_Owner, job_state, queue, nodect, walltime, walltime_used):
    # we only apply the field character limit to the output job_name as the other fields should be much less
    print(f'{Job_ID:20s} {Job_Name:{field_character_limit}s} {Job_Owner:8s} {job_state:5s} {queue:15s} {nodect:5s} {walltime:15s} {walltime_used:15s}')

def pbs_q_query(user=None, machine=None):
    # 1. Fetch the data
    qstat_output = get_qstat_output(machine)
    
    # 2. Determine the host display name
    host_label = machine if machine else socket.gethostname()

    # 3. Guard Clause: Stop if data is missing
    if qstat_output is None:
        # Note: get_qstat_output already printed the specific error message
        return 

    # 4. Print Header with Machine Name
    print(f"\n -------------- qstat wide ({host_label}) -------------- ")
    print_wide_status("JOB ID", "JOB NAME", "OWNER", "STATE", "QUEUE", "NODES", "REQ. WALLTIME", "USED WALLTIME")
    for job, job_info in qstat_output['Jobs'].items():
        job_vals = { "Job_ID" : job }
        for field in fields:
            # first get the actual final field id from the nest 'fields' list
            field_id = reduce( lambda a,b: b, field )

            # now desired entry from job info dictionary (again reduce to get nested entries)
            field_entry = str(reduce(dict.get, field, job_info))
            if field_id == "Job_Owner":
                field_entry = field_entry.split('@')[0] # remove PBS server from Job_Owner
            job_vals[field_id] = field_entry[:field_character_limit]
              
        # Only for running jobs do used times exist    
        walltime_used = "--:--"
        if job_info['job_state'] == 'R':
            if 'resources_used' in job_info.keys():
                if 'walltime' in job_info['resources_used'].keys():
                    walltime_used = str(job_info['resources_used']['walltime'])
        job_vals["walltime_used"] = walltime_used
            
        if user:
            if (job_vals['Job_Owner'] != user):
                continue
        print_wide_status(**job_vals)

def monitor_queue(user=None, machine=None, ntimes=1, freq=30):
    """
        Query the pbs queue ntimes, every freq seconds.
    """
    for _ in range(ntimes):
        pbs_q_query(user=user, machine=machine)
        if ntimes > 1:
            time.sleep(freq)



