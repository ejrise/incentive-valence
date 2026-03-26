% Open parallel pool with desired number of workers
parpool('local', 4); % Adjust the number of workers as needed
subjects = arrayfun(@(x) sprintf('7T_control_%02d', x), 1:28, 'UniformOutput', false);
base_dir = '/path/to/physio/files/';

% Use parfor to run jobs in parallel
parfor i = 1:length(subjects)
    subject = subjects{i};
    job_file = fullfile(base_dir, subject, 'physio_job.mat');
    
    % Load the job file into a variable
    job_data = load(job_file);
    matlabbatch = job_data.matlabbatch;
    
    % Run the job
    spm_jobman('run', matlabbatch);
end

% Close parallel pool
delete(gcp('nocreate'));