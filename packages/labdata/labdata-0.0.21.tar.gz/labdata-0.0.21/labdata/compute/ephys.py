from ..utils import *
from .utils import BaseCompute

class SpksCompute(BaseCompute):
    container = 'labdata-spks'
    cuda = True
    ec2 = dict(small = dict(instance_type = 'g4dn.2xlarge'),   # 8 cpus, 32 GB mem, 200 GB nvme, 1 gpu
               large = dict(instance_type = 'g6.4xlarge',
                            availability_zone = 'us-west-2b')) # 16 cpus, 64 GB mem, 600 GB nvme, 1 gpu
    name = 'spks'
    url = 'http://github.com/spkware/spks'
    def __init__(self,job_id, project = None, allow_s3 = None,  **kwargs):
        '''
#1) find the files
#2) copy just the file you need to scratch
#3) run spike sorting on that file/folder
#4) delete the raw files
#5) repeat until all probes are processed.
        '''
        super(SpksCompute,self).__init__(job_id, project = project, allow_s3 = allow_s3)
        self.file_filters = ['.ap.']
        # default parameters
        self.parameters = dict(algorithm_name = 'spks_kilosort4.0',
                               motion_correction = True,
                               low_pass = 300.,
                               high_pass = 13000.)
        self.parameter_keys = ['motion_correction','low_pass','high_pass','thresholds','remove_cross_duplicates',
                               'waveforms_from_input','dredge']
        # the parameters that go on the SpikeSortingParams
        self.use_hdf5 = True  # flag to use h5py or zarr format for the waveforms.
        self.parameter_set_num = None # identifier in SpikeSortingParams
        self._init_job()
        if type(self.dataset_key) is dict:
            self.dataset_key = [self.dataset_key] # make it a list
        if not self.job_id is None:
            self.add_parameter_key()

    def _get_parameter_number(self):
        parameter_set_num = None
        # check if in spike sorting
        parameters = pd.DataFrame(self.schema.SpikeSortingParams().fetch())
        filtered_par = {k:self.parameters[k] for k in self.parameter_keys if k in self.parameters.keys()}  
        for i,r in parameters.iterrows():
            # go through every algo
            if filtered_par == json.loads(r.parameters_dict):
                parameter_set_num = r.parameter_set_num
        if parameter_set_num is None:
            if len(parameters) == 0:
                parameter_set_num = 1
            else:
                parameter_set_num = np.max(parameters.parameter_set_num.values)+1
            print(f'  --> Using parameter set num {parameter_set_num}')
        return parameter_set_num,parameters
    
    def add_parameter_key(self):
        parameter_set_num, parameters = self._get_parameter_number()
        if not parameter_set_num in parameters.parameter_set_num.values:
            filtered_par = {k:self.parameters[k] for k in self.parameter_keys if k in self.parameters.keys()}
            self.schema.SpikeSortingParams().insert1(dict(parameter_set_num = parameter_set_num,
                                               algorithm_name = self.parameters['algorithm_name'],
                                               parameters_dict = json.dumps(filtered_par),
                                               code_link = self.url),
                                          skip_duplicates=True)
        self.parameter_set_num = parameter_set_num
        recordings = self.schema.EphysRecording.ProbeSetting() & self.dataset_key
        sortings = self.schema.SpikeSorting() & [dict(d, parameter_set_num = self.parameter_set_num) for d in self.dataset_key]
        if len(recordings) == len(sortings):
            self.set_job_status(
                job_status = 'FAILED',
                job_waiting = 0,
                job_log = f'{self.dataset_key[0]} was already sorted with parameters {self.parameter_set_num}.')    
            raise(ValueError(f'{self.dataset_key[0]} was already sorted with parameters {self.parameter_set_num}.'))
           
    def _secondary_parse(self,arguments,parameter_number = None):
        '''
        Handles parsing the command line interface
        '''
        if not parameter_number is None:
            self.parameters = json.loads((self.schema.SpikeSortingParams() & f'parameter_set_num = {parameter_number}').fetch('parameters_dict'))
            self.parameters['algorithm_name'] = ((self.schema.SpikeSortingParams() & f'parameter_set_num = {parameter_number}')).fetch1('algorith_name')
            if not len(self.parameters):
                raise(f'Could not find parameter {parameter_number} in SpikeSortingParams.')
            self.parameters = self.parameters[0]
        else:
            import argparse
            parser = argparse.ArgumentParser(
                description = 'Analysis of spike data using kilosort version 2.5 through the spks package.',
                usage = 'spks -a <SUBJECT> -s <SESSION> -- <PARAMETERS>')
            
            parser.add_argument('-p','--probe',
                                action='store', default=None, type = int,
                                help = "THIS DOES NOTHING NOW. WILL BE FOR OPENING PHY")
            parser.add_argument('-m','--method',action='store',default = 'ks4.0',type = str,
                                help = 'Method for spike sorting [Kilosort] ks2.5, ks3.0, ks4.0 or [MountainSort] ms5 (default ks4.0)')
            parser.add_argument('-l','--low-pass',
                                action='store', default=self.parameters['low_pass'], type = float,
                                help = "Lowpass filter (default 300.Hz)")
            parser.add_argument('-i','--high-pass',
                                action='store', default=self.parameters['high_pass'], type = float,
                                help = "Highpass filter (default 13000.Hz)")
            parser.add_argument('-t','--thresholds',
                                action='store', default=None, type = float, nargs = 2,
                                help = "Thresholds for spike detection default depends on method.")
            parser.add_argument('-n','--motion-correction',
                                action='store', default = 1, type = int,
                                help = "Motion correction (0 to disable, 1 for rigid, 2+ for blockwise)")
            parser.add_argument('-c','--remove_cross-unit-duplicates',
                                action='store_true', default = False,
                                help = "Skip removing duplicates across units.")
            parser.add_argument('--waveforms-from-sorter',
                                action='store_true', default = False,
                                help = "Extract the waveforms from the file processed by the sorter.")
            parser.add_argument('--interval',
                                action='store', default = None, nargs=2, type = float,
                                help = "Interval to sort in seconds: start end")
            parser.add_argument('--dredge',
                                action='store_true', default = False, 
                                help = "Motion correction using dredge")
            
            args = parser.parse_args(arguments[1:])
            if 'ks2.5' in  args.method: # defaults for ks2.5
                self.parameters = dict(algorithm_name = 'spks_kilosort2.5',
                                    motion_correction = args.motion_correction>0,
                                    low_pass = args.low_pass,
                                    high_pass = args.high_pass,
                                    thresholds = [9.,3.],
                                    remove_cross_duplicates = args.remove_cross_unit_duplicates)
            elif 'ks3.0' in  args.method: # defaults for ks3.0
                self.parameters = dict(algorithm_name = 'spks_kilosort3.0',
                                    motion_correction = args.no_motion_correction>0,
                                    low_pass = args.low_pass,
                                    high_pass = args.high_pass,
                                    thresholds = [9.,9.],
                                    remove_cross_duplicates = args.remove_cross_unit_duplicates)
            elif 'ks4.0' in  args.method: # defaults for ks4.0
                self.parameters = dict(algorithm_name = 'spks_kilosort4.0',
                                    motion_correction = args.motion_correction,
                                    low_pass = args.low_pass,
                                    high_pass = args.high_pass,
                                    thresholds = [9.,8.],
                                    remove_cross_duplicates = args.remove_cross_unit_duplicates)
            else:
                raise(NotImplemented(f'{args.method} not implemented.'))
            if args.waveforms_from_sorter:
                # default is to extract from the original input file
                self.parameters['waveforms_from_input'] = False 
            if args.dredge:
                # default is to extract from the original input file
                self.parameters['dredge'] = True 

            if not args.thresholds is None:
                self.parameters['thresholds'] = args.thresholds
            if self.parameters['motion_correction'] < 2:
                self.parameters['motion_correction'] = bool(self.parameters['motion_correction'])
        self.probe = args.probe
        if not self.probe is None:
            self.parameters['probe'] = int(self.probe) # submit a single probe

    def find_datasets(self, subject_name = None, session_name = None):
        '''
        Searches for subjects and sessions in EphysRecording
        '''
        if subject_name is None and session_name is None:
            print("\n\nPlease specify a 'subject_name' and a 'session_name' to perform spike-sorting.\n\n")

        parameter_set_num, parameters = self._get_parameter_number()
        keys = []
        if not subject_name is None:
            if len(subject_name) > 1:
                raise ValueError(f'Please submit one subject at a time {subject_name}.')
            if not subject_name[0] == '':
                subject_name = subject_name[0]
        if not session_name is None:
            for s in session_name:
                if not s == '':
                    keys.append(dict(subject_name = subject_name,
                                     session_name = s))
        else:
            # find all sessions that can be spike sorted
            sessions = np.unique(((
                (self.schema.EphysRecording() & f'subject_name = "{subject_name}"') -
                (self.schema.SpikeSorting() & f'parameter_set_num = {parameter_set_num}'))).fetch('session_name'))
            for ses in sessions:
                keys.append(dict(subject_name = subject_name,
                                 session_name = ses))
        datasets = []
        for k in keys:
            datasets += (self.schema.EphysRecording()& k).proj('subject_name','session_name','dataset_name').fetch(as_dict = True)
            
        if not parameter_set_num is None:
            datasets = ((self.schema.EphysRecording() & datasets) -
                        (self.schema.SpikeSorting() & f'parameter_set_num = {parameter_set_num}')).proj(
                            'subject_name',
                            'session_name',
                            'dataset_name').fetch(as_dict = True)

        return datasets
    
    def place_tasks_in_queue(self,datasets,task_cmd = None, force_submit = False, multisession = False):
        # this is a special place tasks so we can submit a compute task per probe (when there are multiple probes per dataset)
        if not 'probe' in self.parameters.keys():
            probes = np.unique((self.schema.EphysRecording.ProbeSetting & datasets).fetch('probe_num'))
            jobids = []
            for probe in probes:
                p = dict(self.parameters,probe = int(probe))
                jobids.extend(self._place_tasks_in_queue(datasets,
                                           task_cmd = task_cmd, 
                                           force_submit = force_submit, 
                                           multisession = multisession, 
                                           parameters = p))
            return jobids
        else:
            return self._place_tasks_in_queue(datasets,
                                              task_cmd = task_cmd, 
                                              force_submit = force_submit, 
                                              multisession = multisession, 
                                              parameters = self.parameters)
    def _compute(self):
        print(self.parameters)
        # this performs the actual spike sorting.
        datasets = pd.DataFrame((self.schema.EphysRecording.ProbeFile() & self.dataset_key).fetch())
        # check if a probe was selected
        print(datasets)
        if 'probe' in self.parameters.keys():
            datasets = datasets[datasets.probe_num.values == self.parameters['probe']]
        for probe_num in np.unique(datasets.probe_num):
            self.set_job_status(job_log = f'Sorting {probe_num}')
            files = datasets[datasets.probe_num.values == probe_num]
            dset = []
            for i,f in files.iterrows():
                if 'ap.cbin' in f.file_path or 'ap.ch' in f.file_path:
                    dset.append(i)
                elif 'ap.meta' in f.file_path: # requires a metadata file (spikeglx)
                    dset.append(i)
            dset = files.loc[dset]
            if not len(dset):
                print(files)
                raise(ValueError(f'Could not find ap.cbin files for probe {probe_num}'))
            localfiles = self.get_files(dset, allowed_extensions = ['.ap.bin'])
            probepath = list(filter(lambda x: str(x).endswith('bin'),localfiles))
            if 'kilosort' in self.parameters['algorithm_name']:
                from spks.sorting import run_kilosort
            dredge_motion_correction = False
            if 'dredge' in self.parameters.keys():
                dredge_motion_correction = self.parameters['dredge']
            if self.parameters['algorithm_name'] == 'spks_kilosort2.5':      
                results_folder = run_kilosort(version = '2.5',sessionfiles = probepath,
                                              temporary_folder = prefs['scratch_path'],
                                              do_post_processing = False,
                                              motion_correction = self.parameters['motion_correction'],
                                              thresholds = self.parameters['thresholds'],
                                              lowpass = self.parameters['low_pass'],
                                              highpass = self.parameters['high_pass'],
                                              dredge_motion_correction = dredge_motion_correction)
            elif self.parameters['algorithm_name'] == 'spks_kilosort3.0':      
                results_folder = run_kilosort(version = '3.0',
                                              sessionfiles = probepath,
                                              temporary_folder = prefs['scratch_path'],
                                              do_post_processing = False,
                                              motion_correction = self.parameters['motion_correction'],
                                              thresholds = self.parameters['thresholds'],
                                              lowpass = self.parameters['low_pass'],
                                              highpass = self.parameters['high_pass'],
                                              dredge_motion_correction = dredge_motion_correction)

            elif self.parameters['algorithm_name'] == 'spks_kilosort4.0':      
                results_folder = run_kilosort(version = '4.0',
                                              sessionfiles = probepath,
                                              temporary_folder = prefs['scratch_path'],
                                              do_post_processing = False,
                                              motion_correction = self.parameters['motion_correction'],
                                              thresholds = self.parameters['thresholds'],
                                              lowpass = self.parameters['low_pass'],
                                              highpass = self.parameters['high_pass'],
                                              dredge_motion_correction = dredge_motion_correction)
            elif self.parameters['algorithm_name'] == 'spks_mountainsort5':
                raise(NotImplemented(f"[{self.name} job] - Algorithm {self.parameters['algorithm_name']} not implemented."))
            else:
                raise(NotImplemented(f"[{self.name} job] - Algorithm {self.parameters['algorithm_name']} not implemented."))
            self.set_job_status(job_log = f'Probe {probe_num} sorted, running post-processing.')
            try:
                import pylab as plt
                plt.close('all')
                # attempt to close all figures before using joblib
            except:
                pass
            self.postprocess_and_insert(results_folder,
                                        probe_num = probe_num,
                                        remove_duplicates = True,
                                        n_pre_samples = 45)
            self.unregister_safe_exit() # in case these get triggered by shutdown
            try:
                from joblib.externals.loky import get_reusable_executor
                get_reusable_executor().shutdown(wait=True)
                
            except:
                print(f'[{self.name} job] Tried to clear joblib Loky executers and failed.')
            self.register_safe_exit() # put it back..

            if not self.keep_intermediate:
                # delete results_folder
                print(f'[{self.name} job] Removing the results folder.')
                import shutil
                shutil.rmtree(results_folder)
                # delete local files if they did not exist
                if not self.files_existed:
                    for f in localfiles:
                        os.unlink(f)
            else:
                print(f'[{self.name} job] Kept the temporary folder {temporary_folder}.')


    def prepare_results(self,results_folder,
                        probe_num,
                        remove_duplicates,
                        n_pre_samples):
        from spks import Clusters
        if remove_duplicates:
            clu = Clusters(results_folder, get_waveforms = False, get_metrics = False)
            clu.remove_duplicate_spikes(
                overwrite_phy = True,
                remove_cross_duplicates = self.parameters['remove_cross_duplicates']) 
            del clu
        clu = Clusters(results_folder, get_waveforms = False, get_metrics = False)
        clu.compute_template_amplitudes_and_depths()
        # waveforms
        return
        udict = [] # unit
        for dataset_key in self.dataset_key:
            base_key = dict(dataset_key,
                            probe_num = probe_num,
                            parameter_set_num = self.parameter_set_num)
            ssdict = dict(base_key,
                          n_pre_samples = n_pre_samples,
                          n_sorted_units = len(clu),
                          n_detected_spikes = len(clu.spike_times),
                          sorting_datetime = datetime.fromtimestamp(
                            Path(results_folder).stat().st_ctime),
                          sorting_channel_indices = clu.channel_map.flatten(),
                          sorting_channel_coords = clu.channel_positions)
            
            for iclu in clu.cluster_id:
                idx = np.where(clu.spike_clusters == iclu)[0]
                udict.append(dict(
                    base_key,unit_id = iclu,
                    spike_positions = clu.spike_positions[idx,:].astype(np.float32),
                    spike_times = clu.spike_times[idx].flatten().astype(np.uint64),
                    spike_amplitudes = clu.spike_amplitudes[idx].flatten().astype(np.float32)))
                
            featurestosave = dict(template_features = clu.spike_pc_features.astype(np.float32),
                                spike_templates = clu.spike_templates,
                                cluster_indices = clu.spike_clusters,
                                whitening_matrix = clu.whitening_matrix,
                                templates = clu.templates,
                                template_feature_ind = clu.template_pc_features_ind)
        return clu,base_key,ssdict, udict, featurestosave
           
    def postprocess_and_insert(self,
                               results_folder,
                               probe_num,
                               remove_duplicates = True,
                               n_pre_samples = 45):
        '''Does the preprocessing for a spike sorting and inserts'''
        # get the results in a dictionary and remove duplicates
        clu,base_key,ssdict, udict, featurestosave = self.prepare_results(results_folder,
                                                                          probe_num,
                                                                          remove_duplicates,
                                                                          n_pre_samples)
        # save the features to a file, will take like 2 min
        if not featurestosave['template_features'] is None:
            save_dict_to_h5(Path(results_folder)/'features.hdf5',featurestosave)
        n_jobs = DEFAULT_N_JOBS  # gets the default number of jobs from labdata
        # extract the waveforms from the binary file
        n_jobs_wave = n_jobs
        if len(clu) > 800:
            n_jobs_wave = 2 # to prevent running out of memory when collecting waveforms
        udict, binaryfile, nchannels,res = self.extract_waveforms(udict,
                                                                  clu,
                                                                  results_folder,
                                                                  n_pre_samples,
                                                                  n_jobs_wave)
        def median_waves(r,gains):
            if not r is None:
                return np.median(r.astype(np.float32),axis = 0)*gains
            else:
                return None
        waves_dict = []
        extras = dict(compression = 'gzip',
                      compression_opts = 1,
                      chunks = True, 
                      shuffle = True)
        from tqdm import tqdm
        print('Collecting waveforms and saving.')
        # save these to zarr to be compressed faster
        if self.use_hdf5: # zarr not implemented yet.
            import h5py as h5
            with h5.File(Path(results_folder)/'waveforms.hdf5','w') as wavefile:
                for u,w in tqdm(zip(udict,res),desc = 'Saving waveforms to file'):
                    m = median_waves(w,gains = clu.channel_gains)
                    if not w is None:
                        waves_dict.append(dict(base_key,
                                                unit_id = u['unit_id'],
                                                waveform_median = m))
                        # save to the file
                        wavefile.create_dataset(str(u['unit_id'])+'/waveforms',data = w,**extras)
                        wavefile.create_dataset(str(u['unit_id'])+'/indices',data = u['waveform_indices'],**extras)
                    else:
                        print(f"Unit {u['unit_id']} had no spikes extracted")
        stream_name = f'imec{probe_num}' # to save the events and files
        src = [Path(results_folder)/'waveforms.hdf5',Path(results_folder)/'features.hdf5']
        dataset = dict(**self.dataset_key)
        dataset['dataset_name'] = f'spike_sorting/{stream_name}/{self.parameter_set_num}'
        
        filekeys = self.schema.AnalysisFile().upload_files(src,dataset)
        ssdict['waveforms_file'] = filekeys[0]['file_path']
        ssdict['waveforms_storage'] = filekeys[0]['storage']
        if not featurestosave['template_features'] is None:
            ssdict['features_file'] = filekeys[1]['file_path']
            ssdict['features_storage'] = filekeys[1]['storage']
        # insert the syncs
        events = []
        for c in clu.metadata.keys():
            if 'sync_onsets' in c:
                for k in clu.metadata[c].keys():
                    events.append(dict(self.dataset_key, # need to pass to multiple datasets
                                       stream_name = stream_name,
                                       event_name = str(k),
                                       event_timestamps = clu.metadata[c][k].astype(np.uint64)) )
        
        if len(events):
            # Add stream
            self.schema.DatasetEvents.insert1(dict(self.dataset_key,
                                       stream_name = stream_name),
                                       skip_duplicates = True, allow_direct_insert = True)
            self.schema.DatasetEvents.Digital.insert(events,
                                         skip_duplicates = True,
                                         allow_direct_insert = True)
    
        # inserts
        # do all the inserts here
        import logging
        logging.getLogger('datajoint').setLevel(logging.WARNING)
        # these can't be done in a safe way quickly so if they fail we have delete SpikeSorting
        self.schema.SpikeSorting.insert1(ssdict,skip_duplicates = True)
        # Insert datajoint in parallel.
        parallel_insert(self.schema.schema_project,'SpikeSorting.Unit',udict, n_jobs = DEFAULT_N_JOBS,
                        skip_duplicates = True, ignore_extra_fields = True)
        parallel_insert(self.schema.schema_project,'SpikeSorting.Waveforms',waves_dict, n_jobs = DEFAULT_N_JOBS,
                        skip_duplicates = True, ignore_extra_fields = True)

        # Add a segment from a random location.
        from spks.io import map_binary
        dat = map_binary(binaryfile, nchannels = nchannels)
        nsamples = int(clu.sampling_rate*2)
        offset_samples = int(np.random.uniform(nsamples, len(dat)-nsamples-1))
        self.schema.SpikeSorting.Segment.insert1(dict(base_key,
                                          segment_num = 1,
                                          offset_samples = offset_samples,
                                          segment = np.array(dat[offset_samples : offset_samples + nsamples])))
        del dat
        self.set_job_status(job_log = f'Completed {base_key}')
        from labdata.schema import UnitMetrics
        # limit number of jobs because of memory constraints
        self.schema.UnitMetrics.populate(base_key, processes = int(max(1,np.ceil(n_jobs/2))))
    
    def extract_waveforms(self,udict, clu, results_folder,n_pre_samples,n_jobs, offset):
        # extract the waveforms
        from spks.io import map_binary
        # if not 'waveforms_from_sorter' in self.parameters.keys(): 
        #     self.parameters['waveforms_from_sorter'] = False
        # if not self.parameters['waveforms_from_sorter']:    
        binaryfile = list(Path(results_folder).glob("filtered_recording*.bin"))[0]
        nchannels = clu.metadata['nchannels']
        # else: # not implemented
        #     binaryfile = list(Path(results_folder).glob("temp_wh.dat"))[0]
        #     nchannels = clu.metadata['nchannels']
        dat = map_binary(binaryfile,nchannels = nchannels) # to get the duration

        udict = select_random_waveforms(udict, 
                                        wpre = n_pre_samples, 
                                        wpost = n_pre_samples,
                                        duration = dat.shape[0])
        del dat
        res = get_waveforms_from_binary(binaryfile, nchannels,
                                        [u['waveform_indices'] for u in udict],
                                        wpre = n_pre_samples,
                                        wpost = n_pre_samples,
                                        n_jobs = n_jobs)
        return udict, binaryfile, nchannels,res
        
def select_random_waveforms(unit_dict,
                            wpre = 45,
                            wpost = 45,
                            duration = None, # size of the file
                            nmax_waves = 500):
    
    if duration is None:
        duration = np.max([np.max(u['spike_times']) for u in unit_dict])
    for u in unit_dict:
        s = u['spike_times']
        s_begin = s[(s>(wpre+2))&(s<(duration//4))]
        s_end = s[(s>(3*(duration//4))) & (s<(duration-2*wpost))]
        sel = []
        if len(s_begin)>nmax_waves:
            sel = [t for t in np.random.choice(s_begin, nmax_waves, replace=True)]
        else:
            sel = [t for t in s_begin]
        if len(s_end)>nmax_waves:
            sel += [t for t in np.random.choice(s_end, nmax_waves, replace=True)]
        else:
            sel += [t for t in s_end]
        u['waveform_indices'] = np.sort(np.array(sel).flatten()) # add this to the  
    return unit_dict

def get_spike_waveforms(data,indices,wpre = 45,wpost = 45):
    idx = np.arange(-wpre,wpost,dtype = np.int64)
    waves = []
    for i in indices.astype(np.int64):
        waves.append(np.array(np.take(data,idx+i,axis = 0)))
    if len(waves):
        return np.stack(waves,dtype = data.dtype)
    else:
        return None

def get_waveforms_from_binary(binary_file,
                              binary_file_nchannels,
                              waveform_indices,
                              wpre = 45,
                              wpost = 45,
                              n_jobs = 8):
    from tqdm import tqdm
    from spks.io import map_binary
    dat = map_binary(binary_file,nchannels = binary_file_nchannels) 
    # return as generator to avoid having to use huge amounts of memory.
    res = Parallel(backend='loky',n_jobs=n_jobs,return_as = 'generator')(delayed(get_spike_waveforms)(
        dat,
        w,
        wpre = wpre,
        wpost = wpost) for w in tqdm(
            waveform_indices,desc = "Extracting waveforms"))
    return res
