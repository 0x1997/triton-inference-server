BASE_CONTAINER_IMAGE_NAME=nvcr.io/nvidia/tritonserver:23.10-py3-min
TENSORRTLLM_BACKEND_REPO_TAG=main
PYTHON_BACKEND_REPO_TAG=r23.10

# Run the build script. The flags for some features or endpoints can be removed if not needed.
exec ./build.py -v \
    --dryrun \
    -j 64 \
    --no-container-interactive \
    --enable-logging \
    --enable-stats \
    --enable-metrics \
    --enable-gpu-metrics \
    --enable-cpu-metrics \
    --endpoint=http \
    --endpoint=grpc \
    --enable-gpu \
    --backend=ensemble \
    --image=base,${BASE_CONTAINER_IMAGE_NAME} \
    --backend=tensorrtllm:${TENSORRTLLM_BACKEND_REPO_TAG} \
    --backend=python:${PYTHON_BACKEND_REPO_TAG}
