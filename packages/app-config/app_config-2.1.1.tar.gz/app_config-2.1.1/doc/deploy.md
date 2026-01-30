# Deploy a new package version

## In the branch, run the test deploy script

1. **Go to your GitLab project**
2. **Navigate to CI/CD → Pipelines**
3. **Find the pipeline** that ran when you pushed your tag
4. **Click on the pipeline** to open it
5. **Look for the `deploy_test_pypi` job** in the deploy stage
6. **Click the "Play" button** (▶️) next to the job name

The job will show as "manual" with a play button since the build and deploy stages are set to  `when: manual`.

## Test the new package

1. Create a test proj
    `uv init test-proj-name'
2. Add the new package
    `uv add app-config==xx.xx.xx.devxx`
3. Create a src and data dir
4. cd to the src directory
5. Create the config file
    `uv run app_config-init`
6. Update the main module to 
    `import config as cfg 
     cfg.run() 
     cfg.cu.print_config_vars()`
7. Run main.py and it should print out the contents of the config file

## Deploy the package

1. Merge the branch to main
2. Tag the main branch 
3. Navigate to the CI/CD Piple for the merge
4. Run the build
5. Run the deploy for production (pypi)

On local machine:
3. in local main, pull tag
4. run
    `uv build'
5. Clear the dist/ folder of all except the current deployment files
6. Activate the virtual env
    `source .venv/bin/activate`
7. Upload the new release
    'python -m twine upload dist/*`

    provide the token when prompted.