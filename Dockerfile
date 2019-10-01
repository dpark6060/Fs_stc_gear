# Create a base docker container from flywheel's fsl-base repository
# Use v5.0 for compatibility with the compiled slice timing correction code

FROM flywheel/fsl-base:5.0

RUN python3 -m pip install pathlib

# Make run directy for flywheel spec

#ENV  FLYWHEEL /flywheel/v0
#RUN  mkdir -p ${FLYWHEEL}
#COPY run.py ${FLYWHEEL}/run.py
#COPY manifest.json ${FLYWHEEL}/manifest.json
#COPY filtershift ${FLYWHEEL}/filtershift


# Set entrypoint for docker
ENTRYPOINT ["python3 /flywheel/v0/run.py"]
