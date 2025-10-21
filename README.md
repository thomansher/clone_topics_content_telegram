### CLONE TOPICS WITH CONTENT TO YOUR CHAT/GROUP

### Important
Script work on Python 3.12!
Work only with chat/group with topics!
You must be subscribed to the chat/group!
Script work with type media: text, document, photo, video, audio, voice!
The script creates the chat/group automatically.
Work with private chat/group.

### How it Works
script get messages text/media
from source chat/group and download to temp dir
upload messages text/media to your chat/group

### Requirements
Install all requirements command:
```shell
pip install -r requirements.txt
```

### Get API Keys
go to https://my.telegram.org/apps and create app
get App api_id and App api_hash

### Enter API Keys
create file ".env"
in file enter api keys ".env":
API_ID=123456789
API_HASH=43fh5gf4hgf53h5hjf45hf43hf5g

### Settings
go to file "config.py" and enter your data
LIST_TOPIC take list(enter name topics) or None(get all topics)
TEMP_DIR_PATH take str(enter path to dir) or None(create dir in .)

### Troubleshooting
if you have problem with install TgCrypto:
(This library is optional; it only speeds up performance)
install Build Tools (https://visualstudio.microsoft.com/visual-cpp-build-tools/)
during installation, select the "C++ build tools" option
