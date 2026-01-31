# TikTokWebSign

TikTok Web signatures Algorithm!

## Installation
```bash
pip install TikTokWebSign

Example

from TikTokWebSign import TikTokWebSign

# ur query here
query = "aid=1988&device_id=123456&unique_id=cristiano....."

sigs = TikTokWebSign.sign(query, include_bogus=True)

print("X-Gnarly:", sigs['xGnarly'])
print("X-Bogus:", sigs['xBogus'])
