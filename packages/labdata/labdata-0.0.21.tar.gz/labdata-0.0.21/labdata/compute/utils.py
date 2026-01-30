from ..utils import *
import traceback

def load_analysis_object(analysis):
    if not analysis in prefs['compute']['analysis'].keys():
        print(f'''
Could not find {tcolor['r'](analysis)} analysis.

    The analysis are {tcolor['g'](','.join(prefs["compute"]["analysis"].keys()))}

Add the analysis to the "{tcolor['y']("compute")}" section of the preference file {tcolor['y']("{analysis_name:analysis_object}")}.

''')
        sys.exit()        
        raise ValueError('Add the analysis to the "compute" section of the preference file {analysis_name:analysis_object}.\n\n')
        
    import labdata
    return eval(prefs['compute']['analysis'][analysis])

def handle_compute(job_id,project = None):
    schema = load_project_schema(project)
    jobinfo = pd.DataFrame((schema.ComputeTask() & dict(job_id = job_id)).fetch())
    if not len(jobinfo):
        print(f'No task with id: {job_id}')
    jobinfo = jobinfo.iloc[0]
    if jobinfo.task_waiting == 0:
        print(f'Task {job_id} is running on {jobinfo.task_host}')
    obj = load_analysis_object(jobinfo.task_name)(jobinfo.job_id,project)
    return obj

def parse_analysis(analysis, job_id = None,
                   subject = None,
                   session = None,
                   secondary_args = [],
                   parameter_number = None,
                   full_command = None,
                   launch_singularity = False,
                   force_submit = False,
                   multisession = False,
                   project = None,
                   **kwargs):

    obj = load_analysis_object(analysis)(job_id, project = project)
    obj.secondary_parse(secondary_args, parameter_number)
    if obj.job_id is None:
        # then we have to create jobs and assign
        if not hasattr(obj,'schema'):
            schema = load_project_schema(project)
        else:
            schema = obj.schema
         # first check if there is a task that has already been submitted with the exact same command.
         # this has a caveat: if the order of the arguments is switched, it wont work..
        if not full_command is None:
            task_command = str(full_command)
            if len(full_command) >500:
                task_command = task_command[:499]
            submittedjobs = (schema.ComputeTask() & dict(task_cmd = task_command))
            if len(submittedjobs) and not force_submit:
                print(f'{tcolor["r"]("A similar task command is already submitted:")} \n {submittedjobs}')
                return [], None
        if not subject is None or not session is None:
            datasets = obj.find_datasets(subject_name = subject, session_name = session)
        else:
            datasets = None
        job_ids = obj.place_tasks_in_queue(datasets,
                                           task_cmd = full_command,
                                           force_submit = force_submit,
                                           multisession = multisession)
        # now we have the job ids, need to figure out how to launch the jobs
        return job_ids, obj # returns the job ids and the task

def check_archived(jobid, check_local=False,schema = None):
    if schema is None:
        import labdata.schema as schema
    # check if the files are archived before launching remote jobs
    files = schema.File() & (schema.ComputeTask.AssignedFiles() & f'job_id = {jobid}')
    if not len(files):
        return False # there are no files to fetch
    if check_local:
        localfiles, _ = files.check_if_files_local()
        if len(files) == len(localfiles):
            print('Found local files.')
            return False # all files are local

    skip_archive = True # check if the storages are "s3"
    storages = np.unique(files.fetch('storage'))
    for storage in storages:
        if prefs['storage'][storage]['protocol'] == 's3':
            skip_archive = False
    if skip_archive:
        return False
    
    files_archived = files.check_if_files_archived(restore = False, suppress_error = True)
    if files_archived:
        response = None
        while response not in ['y','yes','n','no']:
            response = input(f'Files are archived for {jobid}, do you want to unarchive?' + " [Y/N]: ")
            response = response.lower()
        if response in ['y','yes']:
            files_archived = files.check_if_files_archived(restore = True, suppress_error = True)
    return files_archived

def run_analysis(target, jobids, compute_obj, project = None):
    '''
    Launches a set if analysis on a specific target
    '''
    
    from .singularity import run_on_apptainer
    container_file = (Path(prefs['compute']['containers']['local'])/compute_obj.container).with_suffix('.sif')
    def _get_cmds(jobids,
                  project,
                  container_file = container_file,
                  bind = [],
                  bind_from_prefs = True):
        cmds = []
        from shutil import which
        for j in jobids:
            cc = f'labdata2 task {j}'
            if not project is None:
                cc += f' -p {project}'
            if container_file.exists() and which('apptainer'):
                cmds.append(run_on_apptainer(container_file,
                                             command = cc,
                                             cuda = compute_obj.cuda,
                                             bind = bind,
                                             bind_from_prefs = bind_from_prefs,
                                             dry_run = True))
            else:
                cmds.append(cc)
        return cmds
    task_host = prefs['hostname']
    if hasattr(compute_obj,'schema'): # reuse the schema
        schema = compute_obj.schema
    else:
        schema = load_project_schema(project)
    if target == 'slurm':  # run with slurm
        from .schedulers import slurm_exists, slurm_submit
        if slurm_exists():
            for jid,cmd in zip(jobids,_get_cmds(jobids,project)):
                begin = None
                files_archived = check_archived(jid,check_local = True, schema = schema)
                if files_archived:
                    begin = "now+5hour"
                    print('Delaying job for 5 hours (retrieve archive). ')
                    schema.ComputeTask.update1(dict(job_id = jid,task_status = 'WAITING (ARCHIVE)'))

                if container_file.exists():

                    cmd += ' | ' +  run_on_apptainer(container_file,
                                                     command = f'labdata2 logpipe {jid}',
                                                     dry_run = True)
                else:
                    cmd += f' | labdata2 logpipe {jid}'
                slurmjob = slurm_submit(compute_obj.name,
                                        cmd,
                                        begin = begin,
                                        ntasks = 1,
                                        ncpuspertask = DEFAULT_N_JOBS, # change later to be called by the job.
                                        gpus = 1 if compute_obj.cuda else None,
                                        project = project)
                print(f'Submitted {tcolor["g"](compute_obj.name)} {tcolor["y"](jid)} to slurm [{tcolor["y"](slurmjob)}]')
                schema.ComputeTask.update1(dict(job_id = jid,
                                         task_host = task_host + f'@{slurmjob}',
                                         task_target = target))
        else:
            print(f'{tcolor["r"]("Could not find SLURM: did not submit compute tasks:")}')
            print('\t\n'.join(cmds))
    elif target == 'local':  # run locally without scheduler
        for job_id in jobids:
            task = handle_compute(job_id, project = project)
            task.compute()
            
    elif 'ec2' in target:   # launch dedicated instance on AWS
        # TODO: delayed begin not used here.
        from .ec2 import ec2_cmd_for_launch,ec2_create_instance,ec2_connect
        session,ec2 = ec2_connect()
        for jid, cmd in zip(jobids,_get_cmds(
                jobids,
                project,
                compute_obj.cuda,
                container_file = Path('idontexist'))):
            cmd = ec2_cmd_for_launch(compute_obj.container,
                                     cmd,
                                     singularity_cuda = compute_obj.cuda,
                                     append_log = jid)
            # check if the target contains the words small or large
            
            instance_type = target.replace('ec2-','')
            if instance_type in compute_obj.ec2.keys():
                instance_opts = compute_obj.ec2[instance_type]
            else:
                # using small instance
                instance_opts = compute_obj.ec2['small']
            ins = ec2_create_instance(ec2, user_data = cmd,
                                      **instance_opts)
            print(f'Submitted job to {tcolor["r"](ins["id"])} on an ec2 {instance_opts}')
            task_host = ins["id"]
            schema.ComputeTask.update1(dict(job_id = jid,
                                     task_host = task_host,
                                     task_target = target))
    else:
        # check if there are remote services to launch
        if 'remotes' in prefs['compute'].keys():
            names = prefs['compute']['remotes'].keys()
            targetname = str(target)
            if target in names:
                target = prefs['compute']['remotes'][target]
            else:
                raise(ValueError(f'Could not find target [{target}]'))
            from .schedulers import ssh_connect,slurm_schedule_remote
            container_file = f"$LABDATA_PATH/containers/{compute_obj.container}.sif"
            with ssh_connect(target['address'],target['user'],target['permission_key']) as conn:
                for j in jobids:
                    begin = None
                    files_archived = check_archived(j,schema = schema)
                    if files_archived:
                        begin = "now+5hour"
                        print('Delaying job for 5 hours (retrieve archive). ')
                        schema.ComputeTask.update1(dict(job_id = j,task_status = 'WAITING (ARCHIVE)'))
                    # needs to have LABDATA_PATH defined in the remote
                    cmd = run_on_apptainer(container_file,
                                           command = f'labdata2 task {j}',
                                           cuda = compute_obj.cuda,
                                           dry_run = True)
                    # generate slurm cmd and launch
                    cmd += '|' + run_on_apptainer(container_file,
                                                  command = f'labdata2 logpipe {j}',
                                                  dry_run = True)
                    opts = dict()
                    nt = str(targetname)
                    if compute_obj.name in target['analysis_options']:
                        opts = target['analysis_options'][compute_obj.name]
                        nt = f'{targetname}@{opts["queue"]}'
                    if 'pre' in opts.keys(): # this needs to be a list of things to add to the list of pre_cmds
                        target['pre_cmds'] += opts['pre']
                    slurmjob = slurm_schedule_remote(cmd,  
                                                     conn = conn,
                                                     begin = begin,
                                                     jobname = compute_obj.name+f'_{j}',
                                                     pre_cmds = target['pre_cmds'],
                                                     #remote_dir = '$LABDATA_PATH/remote_jobs',
                                                     container_path = container_file,
                                                     project = project,
                                                     database_user = prefs['database']['database.user'],
                                                     database_password = decrypt_string(prefs['database']['database.password'].replace('encrypted:','')) if 'encrypted:' in prefs['database']['database.password'] else prefs['database']['database.password'],
                                                     #key_dir = '$LABDATA_PATH',
                                                     **opts)
                    if not slurmjob is None:
                        print(f'Submitted {tcolor["r"](compute_obj.name)} job {tcolor["y"](j)} to {tcolor["y"](nt)}[{tcolor["y"](slurmjob)}]')
                    schema.ComputeTask.update1(dict(job_id = j,
                                             task_target = nt))
    
# this class will execute compute jobs, it should be independent from the CLI but work with it.
class BaseCompute():
    name = None
    container = 'labdata-base'
    cuda = False
    ec2 = dict(small = dict(instance_type = 'g4dn.2xlarge'),   # 8 cpus, 32 GB mem, 200 GB nvme, 1 gpu
               large = dict(instance_type = 'g6.4xlarge',
                            availability_zone = 'us-west-2b')) # 16 cpus, 64 GB mem, 600 GB nvme, 1 gpu

    def __init__(self,job_id, project = None, allow_s3 = None, keep_intermediate = False):
        '''
        Executes a computation on a dataset, that can be remote or local
        Uses a singularity/apptainer image if possible
        '''
        self.file_filters = ['.'] # selects all files...
        self.parameters = dict()
        self.schema = load_project_schema(project)
        self.keep_intermediate = keep_intermediate
        self.job_id = job_id
        if not self.job_id is None:
            self._check_if_taken()
            
        self.paths = None
        self.local_path = Path(prefs['local_paths'][0])
        self.scratch_path = Path(prefs['scratch_path'])
        self.assigned_files = None
        self.dataset_key = None
        self.is_container = False
        if allow_s3 is None:
            self.allow_s3 = prefs['allow_s3_download']
        if 'LABDATA_CONTAINER' in os.environ.keys():
            # then it is running inside a container
            self.is_container = True
        #self.is_ec2 = False # then files should be taken from s3

    def _init_job(self): # to run in the init function
        if not self.job_id is None:
            with self.schema.dj.conn().transaction:
                self.jobquery = (self.schema.ComputeTask() & dict(job_id = self.job_id))
                job_status = self.jobquery.fetch(as_dict = True)
                if len(job_status):
                    if not job_status[0]['task_waiting']:
                        print(f'Checking job_status - task was not waiting: {job_status}', flush = True)
                        if 'SLURM_RESTART_COUNT' in os.environ.keys():
                            # then the job is running on slurm.. its a putative restart, try to run it..
                            self.set_job_status(job_status = 'WORKING',
                                                job_waiting = 0)
                        else:
                            print(f"Compute task [{self.job_id}] is already taken.")
                            print(job_status, flush = True)
                            return # exit.
                    else:
                        self.set_job_status(job_status = 'WORKING',
                                            job_waiting = 0)
                        
                        def cleanup_function(job_id = self.job_id):
                            # if it quits then register as canceled and put as waiting
                            print('Running the cleanup function.', flush = True)
                            status = (self.schema.ComputeTask() & dict(job_id = job_id)).fetch(as_dict = True)[0]
                            if status['task_status'] in ['WORKING']:
                                self.schema.ComputeTask.update1(dict(job_id = job_id,
                                                                     task_status = 'CANCELLED',
                                                                     task_waiting = 1,
                                                                     task_endtime = datetime.now()))
                        
                        self.cleanup_function = cleanup_function       
                        self.register_safe_exit()
                        par = json.loads(job_status[0]['task_parameters'])
                        for k in par.keys():
                            self.parameters[k] = par[k]
                        self.assigned_files = pd.DataFrame((self.schema.ComputeTask.AssignedFiles() & dict(job_id = self.job_id)).fetch())
                        self.dataset_key = dict(subject_name = job_status[0]['subject_name'],
                                                session_name = job_status[0]['session_name'],
                                                dataset_name = job_status[0]['dataset_name'])
                        if '--multisession' in job_status[0]['task_cmd']:
                            self.dataset_key = (self.schema.Dataset() &
                                                (self.schema.Dataset.DataFiles & self.assigned_files)).proj().fetch(as_dict = True)
                        # delete the job if has --delete-on-complete
                        job_status = self.jobquery.fetch(as_dict = True)
                        if '--keep-files' in job_status[0]['task_cmd']:
                            self.keep_intermediate = True
                else:
                    # that should just be a problem to fix
                    raise ValueError(f'job_id {self.job_id} does not exist.')
    
    def register_safe_exit(self):
        import safe_exit
        safe_exit.register(self.cleanup_function)
    
    def unregister_safe_exit(self):
        import safe_exit
        safe_exit.unregister(self.cleanup_function)
    
    def get_files(self, dset, allowed_extensions=[]):
        '''
        Gets the paths and downloads from S3 if needed.
        '''
        if type(dset) is list:
            # then it is a list of dicts, convert to DataFrame
            dset = pd.DataFrame(dset)
        files = dset.file_path.values
        print('---')
        print(files)
        print('---')
        storage = dset.storage.values
        localpath = Path(prefs['local_paths'][0])
        self.files_existed = True
        localfiles = [find_local_filepath(f,
                                          allowed_extensions = allowed_extensions) for f in files]
        localfiles = np.unique(list(filter(lambda x: not x is None,localfiles)))
        if not len(localfiles) >= len(self.dataset_key): # tries to have at least one file per dataset (check this assumption, it is here because of the "allowed extensions")
            # then you can try downloading the files
            if self.allow_s3: # get the files from s3
                #TODO: then it should download using "File"
                from ..s3 import copy_from_s3
                for s in np.unique(storage):
                    # so it can work with multiple storages
                    srcfiles = [f for f in files[storage == s]]
                    dstfiles = [localpath/f for f in srcfiles]
                print(f'Downloading {len(srcfiles)} files from S3 [{s}].')
                copy_from_s3(srcfiles,dstfiles,storage_name = s)
                localfiles = np.unique([find_local_filepath(
                    f,
                    allowed_extensions = allowed_extensions) for f in files])
                if len(localfiles):
                    self.files_existed = False # delete the files in the end if they were not local.
            else:
                print(files, localpath)
                raise(ValueError('Files not found locally, set allow_s3 in the preferences to download.'))
        return localfiles

    def place_tasks_in_queue(self,datasets,task_cmd = None, force_submit = False, multisession = False):
        # overwride this to submit special compute tasks (e.g. SpksCompute)
        return self._place_tasks_in_queue(datasets, task_cmd = task_cmd,
                                   force_submit = force_submit,
                                   multisession = multisession)
        
    def _place_tasks_in_queue(self,datasets, task_cmd = None, force_submit = False, multisession = False, parameters = None):
        ''' This will put the tasks in the queue for each dataset.
        If the task and parameters are the same it will return the job_id instead.
        
        '''
        if parameters is None:
            parameters = self.parameters # so we can pass multiple parameters (e.g. in the multiprobe case)
        job_ids = []
        if datasets is None:
            datasets = [None]
        if multisession:
            print('Combining data from multiple sessions/datasets.')
            datasets = [datasets]
        for dataset in datasets:
            if not dataset is None: # then there are no associated files.
                files = pd.DataFrame((self.schema.Dataset.DataFiles() & dataset).fetch())
                idx = []
                for f in self.file_filters:
                    idx += list(filter(lambda x: not x is None,[i if f in s else None for i,s in enumerate(
                        files.file_path.values)]))
                if len(idx) == 0:
                    raise ValueError(f'Could not find valid Dataset.DataFiles for {dataset}')
                files = files.iloc[idx]
                if type(dataset) is dict:
                    key = dict(dataset,task_name = self.name)
                else:
                    key = dict(dataset[0],task_name = self.name)
                exists = self.schema.ComputeTask() & key
                if len(exists):
                    d = pd.DataFrame(exists.fetch())
                    # if any(d.task_status.values=='WORKING'):
                    #     print('A task was running for this dataset, stop or delete it first.')
                    #     print(key)
                    #     continue

                    idx = np.where(np.array(d.task_parameters.values) == json.dumps(parameters))[0]
                    if len(idx):
                        job_id = d.iloc[idx].job_id.values[0]
                        print(f'There is a task to analyse dataset {key} with the same parameters. [{job_id}]')
                        if force_submit:
                            print('Deleting the previous job because force_submit is set.')
                            with self.schema.dj.conn().transaction:
                                self.schema.dj.config['safemode'] = False
                                # delete part table because the reference priviledge is not sufficient
                                (self.schema.ComputeTask.AssignedFiles & f'job_id = {job_id}').delete(force = True) 
                                (self.schema.ComputeTask & f'job_id = {job_id}').delete() # deleting a previous job because of force_submit
                                self.schema.dj.config['safemode'] = True
                        else:
                            continue
            else:
                key = dict(task_name = self.name)
                files = None
                
            with self.schema.dj.conn().transaction:
                job_id = self.schema.ComputeTask().fetch('job_id')
                if len(job_id):
                    job_id = np.max(job_id) + 1 
                else:
                    job_id = 1
                if not task_cmd is None:
                    if len(task_cmd) >500:
                        task_cmd = task_cmd[:499]
                self.schema.ComputeTask().insert1(dict(key,
                                                       job_id = job_id,
                                                       task_waiting = 1,
                                                       task_status = "WAITING",
                                                       task_target = None,
                                                       task_host = None,
                                                       task_cmd = task_cmd,
                                                       task_parameters = json.dumps(parameters),
                                                       task_log = None))
                if not files is None:
                    self.schema.ComputeTask.AssignedFiles().insert([dict(job_id = job_id,
                                                                         storage = f.storage,
                                                                         file_path = f.file_path)
                                                                for i,f in files.iterrows()])
                job_ids.append(job_id)
        return job_ids
    
    def find_datasets(self,subject_name = None, session_name = None, dataset_name = None):
        '''
        Find datasets to analyze, this function will search in the proper tables if datasets are available.
        Has to be implemented per Compute class since it varies.
        '''
        raise NotImplementedError('The find_datasets method has to be implemented.')
        
    def secondary_parse(self,secondary_arguments, parameter_number = None):
        self._secondary_parse(secondary_arguments, parameter_number)
        
    def _secondary_parse(self,secondary_arguments):
        return
        
    def _check_if_taken(self):
        if not self.job_id is None:
            self.jobquery = (self.schema.ComputeTask() & dict(job_id = self.job_id))
            job_status = self.jobquery.fetch(as_dict = True)
            if len(job_status):
                if job_status[0]['task_waiting']:
                    return
                else:
                    print(job_status, flush = True)
                    raise ValueError(f'job_id {self.job_id} is already taken.')
                    return # exit.
            else:
                raise ValueError(f'job_id {self.job_id} does not exist.')
            # get the paths?
            #self.src_paths = pd.DataFrame((ComputeTask.AssignedFiles() &
            #                               dict(job_id = self.job_id)).fetch())
            #if not len(self.src_paths):
            #    self.set_job_status(job_status = 'FAILED',
            #                        job_log = f'Could not find files for {self.job_id} in ComputeTask.AssignedFiles.')
            #    raise ValueError(f'Could not find files for {self.job_id} in ComputeTask.AssignedFiles.')
        else:
            raise ValueError(f'Compute: job_id not specified.')
        
    def compute(self):
        '''This calls the compute function. 
If "use_s3" is true it will download the files from s3 when needed.'''
        try:
            if not self.job_id is None:
                dd = dict(job_id = self.job_id,
                          task_starttime = datetime.now())
                self.schema.ComputeTask().update1(dd)
            self._compute() # can use the src_paths
        except Exception as err:
            # log the error
            print(f'There was an error processing job {self.job_id}.')
            err =  str(traceback.format_exc()) + "ERROR" +str(err)
            print(err)

            if len(err) > 1999: # then get only the last part of the error.
                err = err[-1900:]
            if type(err) is str:
                # avoid encoding errors
                err = err.encode('utf-8')
            self.set_job_status(job_status = 'FAILED',
                                job_log = f'{err}')
            return
        
        # get the job from the DB if the status is not failed, mark completed (remember to clean the log)
        self.jobquery = (self.schema.ComputeTask() & dict(job_id = self.job_id))
        job_status = self.jobquery.fetch(as_dict = True)

        if not job_status[0]['task_status'] in ['FAILED']:
            self._post_compute() # so the rules can insert tables and all.
            # delete the job if has --delete-on-complete
            if '--delete-on-complete' in job_status[0]['task_cmd']:
                self.jobquery.delete(safemode = False)
                self.job_id = None
                self.unregister_safe_exit()
            else:
                self.set_job_status(job_status = 'COMPLETED')
                
        if not self.job_id is None: # set the complete time
            dd = dict(job_id = self.job_id,
                      task_endtime = datetime.now())
            self.schema.ComputeTask().update1(dd)

    def set_job_status(self, job_status = None, job_log = None,job_waiting = 0):
        from ..schema import ComputeTask
        if not self.job_id is None:
            dd = dict(job_id = self.job_id,
                      task_waiting = job_waiting,
                      task_host = prefs['hostname']) # so we know where it failed.)
            if not job_status is None:
                dd['task_status'] = job_status
            if not job_log is None:
                dd['task_log'] = job_log  
                if type(dd['task_log']) is str:
                    #prevent error due to unsupported characters
                    dd['task_log'] = dd['task_log'].encode('utf-8')
            self.schema.ComputeTask.update1(dd)
            if not job_status is None:
                if not 'WORK' in job_status: # display the message
                    print(f'Check job_id {self.job_id} : {job_status}')

    def _post_compute(self):
        '''
        Inserts the data to the database
        '''
        return
    
    def _compute(self):
        '''
        Runs the compute job on a scratch folder.
        '''
        return

class PopulateCompute(BaseCompute):
    container = 'labdata-base'
    cuda = False
    name = 'populate'
    url = 'http://github.com/jcouto/labdata'
    def __init__(self,job_id, project = None, allow_s3 = None, **kwargs):
        super(PopulateCompute,self).__init__(job_id, project = project, allow_s3 = allow_s3)
        self.file_filters = None
        # default parameters
        self.parameters = dict(imports = 'labdata.schema',
                               table = 'UnitMetrics',
                               processes = 10)
        
        self._init_job() # gets the parameters
        
    def _secondary_parse(self,arguments,parameter_number):
        '''
        Handles parsing the command line interface
        '''
        import argparse
        parser = argparse.ArgumentParser(
            description = 'Populate arbitrary tables',
            usage = 'populate -- -t <TABLE> -i <IMPORTS>')
        
        parser.add_argument('table',action='store',type = str,
                            help = 'Table to populate')
        parser.add_argument('-s','--stop-on-errors',action='store_true',default= False,
                            help = 'Stop on errors (negates suppress_errors)')
        parser.add_argument('-r','--restrictions',action='store',default= '',
                            help = 'Restrictions to the populate table (dict(X = "x")) or completed_today (to run for sessions that were completed less than 24h ago)')
        parser.add_argument('-i','--imports',action='store',default= 'labdata.schema',type = str,
                            help = 'import modules to load the table')
        parser.add_argument('-p','--processes',
                            action='store', default=1, type = int,
                            help = "Required imports.")
        parser.add_argument

        args = parser.parse_args(arguments[1:])
        self.parameters = dict(table = args.table,
                               imports = args.imports,
                               processes = args.processes,
                               suppress_errors = not args.stop_on_errors,
                               restrictions = args.restrictions)
        # try the import and check if the default container exists.
        if not self.parameters["imports"] in ['none','']:
            to_import = self.parameters["table"]
            if '.' in to_import: # to import plugins
                to_import = to_import.split('.')[0]
            exec(f'from {self.parameters["imports"]} import {to_import}')
        table = eval(f'{self.parameters["table"]}')
        if hasattr(table,'default_container'):
            self.container = table.default_container
        print(self.parameters)

    def find_datasets(self):
        return
    
    def _compute(self):
        # import
        if not self.parameters["imports"] in ['none','']:
            to_import = self.parameters["table"]
            if '.' in to_import: # to import plugins
                to_import = to_import.split('.')[0]
            exec(f'from {self.parameters["imports"]} import {to_import}')
        processes = 1
        # check nprocesses
        if 'processes' in self.parameters.keys():
            processes = int(self.parameters['processes'])
        # submit populate
        suppress_errors = self.parameters['suppress_errors']
        if self.parameters['restrictions'] == '':
            exec(f'{self.parameters["table"]}.populate(suppress_errors={suppress_errors}, processes = {processes}, display_progress = True)')
        else:
            if self.parameters['restrictions'] == 'completed_today': # this will look for uploads that happened less than 24h ago
                restrictions = (self.schema.Session() & (self.schema.UploadJob() & 'job_status = "COMPLETED"') & 'session_datetime > DATE_SUB(CURDATE(), INTERVAL 24 HOUR)').proj().fetch(as_dict = True)
            else:
                restrictions = eval(self.parameters['restrictions'])
            exec(f'{self.parameters["table"]}.populate({restrictions}, suppress_errors={suppress_errors}, processes = {processes}, display_progress = True)')
