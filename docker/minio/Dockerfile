FROM minio/minio:latest


# Start MinIO server
#
# /data is the persistent storage directory
#
# Console runs on port 9001

ENTRYPOINT ["minio", "server", "/data", "--console-address=:9001"]