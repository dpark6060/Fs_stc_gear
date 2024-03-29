# Create a base docker container from flywheel's fsl-base repository
# Use v5.0 for compatibility with the compiled slice timing correction code

FROM flywheel/fsl-base:5.0

RUN python3 -m pip install pathlib


ENV  FLYWHEEL /flywheel/v0

# Make a fake file in the flywheel/v0 dir to determine if flywheel actually maintains docker input to this area
# (unline flywheel CLI run local)
RUN echo "FakeFile">${FLYWHEEL}/FakeFile.txt
# (Turns out, it does)

# Set entrypoint for docker
ENTRYPOINT ["python3 /flywheel/v0/run.py"]
