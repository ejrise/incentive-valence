% List of subjects
subjects = arrayfun(@(x) sprintf('7T_control_%02d', x), 9:28, 'UniformOutput', false);

% Base directory for physio logs
base_dir = '/path/to/physio/files';

% Loop through each subject and create the job script
for i = 1:length(subjects)
    subject = subjects{i};
    save_dir = fullfile(base_dir, subject, 'physio_out');
    cardiac_log = fullfile(base_dir, subject, [subject '_PULS.log']);
    respiration_log = fullfile(base_dir, subject, [subject '_RESP.log']);
    scan_timing_log = fullfile(base_dir, subject, [subject '_Info.log']);
    
    % Create matlabbatch structure
    matlabbatch{1}.spm.tools.physio.save_dir = {save_dir};
    matlabbatch{1}.spm.tools.physio.log_files.vendor = 'Siemens_Tics';
    matlabbatch{1}.spm.tools.physio.log_files.cardiac = {cardiac_log};
    matlabbatch{1}.spm.tools.physio.log_files.respiration = {respiration_log};
    matlabbatch{1}.spm.tools.physio.log_files.scan_timing = {scan_timing_log};
    matlabbatch{1}.spm.tools.physio.log_files.sampling_interval = [];
    matlabbatch{1}.spm.tools.physio.log_files.relative_start_acquisition = 0;
    matlabbatch{1}.spm.tools.physio.log_files.align_scan = 'last';
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.Nslices = 100; % this is 84 for subs 01-08
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.NslicesPerBeat = [];
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.TR = 2.1;
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.Ndummies = 0;
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.Nscans = 300;
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.onset_slice = 50; % change to 42 for subs 01-08
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.time_slice_to_slice = [];
    matlabbatch{1}.spm.tools.physio.scan_timing.sqpar.Nprep = [];
    matlabbatch{1}.spm.tools.physio.scan_timing.sync.scan_timing_log = struct([]);
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.modality = 'PPU';
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.filter.no = struct([]);
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.initial_cpulse_select.auto_matched.min = 0.4;
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.initial_cpulse_select.auto_matched.file = 'initial_cpulse_kRpeakfile.mat';
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.initial_cpulse_select.auto_matched.max_heart_rate_bpm = 100;
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.posthoc_cpulse_select.manual.file = 'posthoc_cpulse.mat';
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.posthoc_cpulse_select.manual.percentile = 80;
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.posthoc_cpulse_select.manual.upper_thresh = 60;
    matlabbatch{1}.spm.tools.physio.preproc.cardiac.posthoc_cpulse_select.manual.lower_thresh = 60;
    matlabbatch{1}.spm.tools.physio.preproc.respiratory.filter.passband = [0.01 2];
    matlabbatch{1}.spm.tools.physio.preproc.respiratory.despike = true;
    matlabbatch{1}.spm.tools.physio.model.output_multiple_regressors = 'multiple_regressors.txt';
    matlabbatch{1}.spm.tools.physio.model.output_physio = 'physio.mat';
    matlabbatch{1}.spm.tools.physio.model.orthogonalise = 'none';
    matlabbatch{1}.spm.tools.physio.model.censor_unreliable_recording_intervals = true;
    matlabbatch{1}.spm.tools.physio.model.retroicor.yes.order.c = 3;
    matlabbatch{1}.spm.tools.physio.model.retroicor.yes.order.r = 4;
    matlabbatch{1}.spm.tools.physio.model.retroicor.yes.order.cr = 1;
    matlabbatch{1}.spm.tools.physio.model.rvt.no = struct([]);
    matlabbatch{1}.spm.tools.physio.model.hrv.no = struct([]);
    matlabbatch{1}.spm.tools.physio.model.noise_rois.no = struct([]);
    matlabbatch{1}.spm.tools.physio.model.movement.no = struct([]);
    matlabbatch{1}.spm.tools.physio.model.other.no = struct([]);
    matlabbatch{1}.spm.tools.physio.verbose.level = 3;
    matlabbatch{1}.spm.tools.physio.verbose.fig_output_file = '.png';
    matlabbatch{1}.spm.tools.physio.verbose.use_tabs = false;
    
    % Save the job script
    save(fullfile(base_dir, subject, 'physio_job.mat'), 'matlabbatch');
end
