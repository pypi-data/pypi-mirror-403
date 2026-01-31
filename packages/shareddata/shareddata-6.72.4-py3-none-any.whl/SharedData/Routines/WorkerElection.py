import os
import time
import random
import json
import requests
import boto3
import pandas as pd

from SharedData.Metadata import Metadata  
from SharedData.Logger import Logger
from SharedData.Routines.WorkerLib import *
Logger.connect(__file__)


Logger.log.info('ROUTINE STARTED!')

# Get own IP using ECS metadata
metadata_uri = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')
if metadata_uri:
    response = requests.get(metadata_uri).json()
    own_ip = response['Networks'][0]['IPv4Addresses'][0]
else:
    # Fallback for non-ECS environments
    import socket
    # gethostbyname often returns 127.0.0.1, use alternative method
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable, just used to determine the interface
        s.connect(('10.255.255.255', 1))
        own_ip = s.getsockname()[0]
    except Exception:
        own_ip = '127.0.0.1'
    finally:
        s.close()

# Use IP as the identifier instead of COMPUTERNAME for consistency with initial description
own_id = os.environ.get('COMPUTERNAME', own_ip)
own_id = own_id.replace('.','#')

folder = 'CLUSTERS/MASTER/'
own_path = f'{folder}{own_id}'

req_cols = ['create_time', 'heartbeat', 'ip', 'id', 'is_master']

# Instantiate own Metadata (triggers read)
md = Metadata(own_path)
self_metadata = md.static.to_dict(orient='records')[0] if not md.static.empty else {}

# If file didn't exist or static is empty, initialize
if 'create_time' not in self_metadata or 'heartbeat' not in self_metadata:
    Logger.log.info(f'Checking in new instance {own_id} to cluster MASTER.')
    # get utc time independent of local instance time zone
    time_utc = pd.Timestamp.utcnow().timestamp()
    md.static = pd.DataFrame([{
        'create_time': time_utc,
        'heartbeat': time_utc,
        'ip': own_ip,
        'id': own_id,
        'is_master': False
    }], columns=req_cols)
    md.save()

# Variables for master confirmation
master_count = 0

while True:
    # Add random jitter
    jitter = random.uniform(0, 2)
    time.sleep(jitter)
    
    md = Metadata(own_path)
    self_metadata = md.static.to_dict(orient='records')[0] if not md.static.empty else {}
    is_current_master = self_metadata.get('is_master', False)

    # Update own heartbeat and save
    time_utc = pd.Timestamp.utcnow().timestamp()
    md.static['heartbeat'] = time_utc
    md.save()    

    # Get all online instances (including self)
    online_instances = get_online_instances(folder)
    
    if len(online_instances)==0:            
        # Sleep to make loop ~15 seconds total
        Logger.log.warning(f'No online instances found, but self should exist at {own_path}')
        time.sleep(15 - jitter)
        continue

    # Sort to find oldest: smallest create_time, then lexical id
    online_instances.sort(key=lambda x: (x['create_time'], x['id']))

    oldest_create, oldest_id, oldest_path = online_instances[0]['create_time'], online_instances[0]['id'], online_instances[0]['path']

    is_candidate = (own_id == oldest_id)

    # Master confirmation logic
    if is_current_master:
        if not is_candidate:
            is_current_master = False
            master_count = 0
            # Update own metadata to reflect demotion
            md.static['is_master'] = False
            md.save()
            Logger.log.info(f'Instance {own_id} demoted from master in cluster MASTER.')
            # Configure nginx as slave, proxying to the new master
            master_ip = get_master_ip(online_instances)
            if master_ip:
                demote_to_slave(master_ip)
                # Update SHAREDDATA_ENDPOINT to point to master
                new_endpoint = f'http://{master_ip}:8080'
                os.environ['SHAREDDATA_ENDPOINT'] = new_endpoint
                persist_environment_variable('SHAREDDATA_ENDPOINT', new_endpoint)
                Logger.log.info(f'Updated SHAREDDATA_ENDPOINT to {new_endpoint}')
            else:
                Logger.log.warning('Could not determine master IP for nginx slave configuration.')

    else:
        if is_candidate:
            master_count += 1
            if master_count >= 3:
                # Check if any other instance claims to be master since less than 2 minutes
                # if yes , do not promote self
                other_masters = [inst for inst in online_instances if inst['is_master'] and inst['id'] != own_id]
                if not other_masters:
                    is_current_master = True
                    master_count = 0
                    # Update own metadata to reflect master status
                    md.static['is_master'] = True
                    md.save()
                    Logger.log.info(f'Instance {own_id} promoted to master in cluster MASTER.')
                    # Configure nginx as master
                    promote_to_master()
                    # Update SHAREDDATA_ENDPOINT to point to self
                    new_endpoint = f'http://{own_ip}:8080'
                    os.environ['SHAREDDATA_ENDPOINT'] = new_endpoint
                    persist_environment_variable('SHAREDDATA_ENDPOINT', new_endpoint)
                    Logger.log.info(f'Updated SHAREDDATA_ENDPOINT to {new_endpoint}')

        else:
            master_count = 0

    # Ensure nginx configuration matches current role
    if is_current_master:
        Logger.log.debug(f"#heartbeat# Instance {own_id} is the master.")
        ensure_nginx_master_config()
        # Ensure SHAREDDATA_ENDPOINT points to self
        expected_endpoint = f'http://{own_ip}:8080'
        if os.environ.get('SHAREDDATA_ENDPOINT') != expected_endpoint:
            os.environ['SHAREDDATA_ENDPOINT'] = expected_endpoint
            persist_environment_variable('SHAREDDATA_ENDPOINT', expected_endpoint)
            Logger.log.info(f'Corrected SHAREDDATA_ENDPOINT to {expected_endpoint}')
    else:
        Logger.log.debug(f"#heartbeat# Instance {own_id} is a worker.")
        master_ip = get_master_ip(online_instances)
        if master_ip:
            ensure_nginx_slave_config(master_ip)
            # Ensure SHAREDDATA_ENDPOINT points to master
            expected_endpoint = f'http://{master_ip}:8080'
            if os.environ.get('SHAREDDATA_ENDPOINT') != expected_endpoint:
                os.environ['SHAREDDATA_ENDPOINT'] = expected_endpoint
                persist_environment_variable('SHAREDDATA_ENDPOINT', expected_endpoint)
                Logger.log.info(f'Corrected SHAREDDATA_ENDPOINT to {expected_endpoint}')
        else:
            Logger.log.warning('No master found in cluster, cannot configure nginx as slave.')

    # Sleep to make loop ~15 seconds total
    time.sleep(15 - jitter)