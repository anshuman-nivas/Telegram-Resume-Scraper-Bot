import easyocr

reader = easyocr.Reader(['en'], gpu=False)

result = reader.readtext("test.png")

for r in result:
    print(r[1])