import urllib.request
import re

url = "https://halfcodeblood.github.io/pune-builtup-ghsl/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8")

# Extract image tags
img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print("Images found in HTML:")
for src in img_srcs:
    print(" -", src)

# Extract sections / headers
headers = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html)
print("\nHeaders:")
for h in headers:
    print(" -", h)
