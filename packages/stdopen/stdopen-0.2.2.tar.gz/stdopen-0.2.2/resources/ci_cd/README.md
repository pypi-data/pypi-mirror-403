# Continuous integration scripts
This allows the testing of various continuous integration scripts before committing to GitLab. It is a major pain in the backside to debug against that so it is easier to do a test run before setting it up.

The various `run_<pipeline>.sh` scripts represent different scripts that can be run on different pipelines. The other scripts represent small sections that can be run in a pipeline.

To run a test build prior to committing:

```
# ./run_docker.sh <docker image> <repo root>
./run_docker.sh chrisfin/pypan:base-3.13 ~/code/stdopen/
```
