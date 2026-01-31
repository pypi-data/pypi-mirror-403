from lazysdk import lazyexcel

res = lazyexcel.read_xlsx(
    file="/Users/zeroseeker/Downloads/用户列表_001_001(4).xlsx",
    name_raw=2
)
# print(res)
for key, value in res.items():
    print(key, value)