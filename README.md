# TrueColorize Vast.ai Serverless v1

Upload these files to the root of:
https://github.com/joeywoey5-a11y/truecolorize-vast-worker

Build:
docker build --platform linux/amd64 -t jaw2351968/truecolorize-vast:v1 .
docker push jaw2351968/truecolorize-vast:v1

Vast template:
Image: jaw2351968/truecolorize-vast:v1
Launch mode: Docker ENTRYPOINT
Disk: 20 GB
Visibility: Private

Environment variables:
PYWORKER_REPO=https://github.com/joeywoey5-a11y/truecolorize-vast-worker
PYWORKER_REF=main
PYWORKER_DIR=/workspace/truecolorize-vast-worker

On-start Script:
wget -qO /tmp/truecolorize-start.sh https://raw.githubusercontent.com/joeywoey5-a11y/truecolorize-vast-worker/main/start_server.sh && bash /tmp/truecolorize-start.sh

Serverless route:
POST /colorize
