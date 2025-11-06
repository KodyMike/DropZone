# DropZone
A uploader webserver python based. Designed to only recive files

- TARGET_BASE_DIR=/path/to/output PORT=9090 python3 upload_server.py
- curl -F "file=@sample.json" http://localhost:9090/upload
- JSON/XML/CSV land in <base>/data/; other files stay in <base>.
