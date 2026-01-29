# shortulr

Python library to creating:
- Create a short link

## Installation
```bash
pip install shortulr
```
## Usage

```python

import shortulr

# لتنزيل الحزمة cmd اكتب هذا الامر في
# pip install shortulr

s = Short_url("URL")

short = s.shorten()
print("Short URL:", short)

s.generate_qr("img.png")


