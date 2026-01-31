from mcp.server.fastmcp import FastMCP
from qiniu import Auth, put_file
import os
import uuid

# Get Qiniu config from environment variables
QINIU_ACCESS_KEY = os.environ.get("QINIU_ACCESS_KEY", "")
QINIU_SECRET_KEY = os.environ.get("QINIU_SECRET_KEY", "")
QINIU_BUCKET_NAME = os.environ.get("QINIU_BUCKET_NAME", "")
QINIU_DOMAIN = os.environ.get("QINIU_DOMAIN", "")
QINIU_UPLOAD_EXPIRES = int(os.environ.get("QINIU_UPLOAD_EXPIRES", "3600"))

# Initialize Qiniu Auth
q = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)

# Create MCP server
mcp = FastMCP("qiniu-uploader")

@mcp.tool()
def upload_file(file_path: str) -> str:
    """Uploads a file to Qiniu and returns its public URL"""
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    # Generate unique key
    key = f"mcp-uploads/{uuid.uuid4()}{os.path.splitext(file_path)[1]}"

    # Generate upload token
    token = q.upload_token(QINIU_BUCKET_NAME, key, QINIU_UPLOAD_EXPIRES)

    # Upload file
    ret, info = put_file(token, key, file_path)

    if info.status_code == 200:
        return f"{QINIU_DOMAIN}/{key}"
    else:
        raise Exception(f"Upload failed: {info}")

def main():
    mcp.run()

if __name__ == "__main__":
    main()