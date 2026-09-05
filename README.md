# TrueColorize Vast.ai Serverless v2 Lite

This build is optimized for faster cold-start image pulling.

Removed:
- Stable DeOldify model
- ResNet101 cache
- unused runtime packages

Build:
```powershell
docker build --platform linux/amd64 -t jaw2351968/truecolorize-vast:v2-lite .
docker push jaw2351968/truecolorize-vast:v2-lite
```

In Vast use:
- Image: `jaw2351968/truecolorize-vast`
- Version Tag: `v2-lite`

In GitHub, replace these files in:
https://github.com/joeywoey5-a11y/truecolorize-vast-worker

- Dockerfile
- model_server.py
- README.md

The existing worker.py, run_model_server.py, requirements.txt and start_server.sh can remain unchanged.

Keep the same environment variables and on-start script.
