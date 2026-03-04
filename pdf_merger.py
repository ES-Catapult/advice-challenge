from pypdf import PdfWriter, PdfReader
import os

merger = PdfWriter()
pdfs = [f for f in os.listdir('.') if f.endswith('.pdf')]
pdfs.sort(key = lambda x: int(os.path.splitext(x)[0]))  # sort numerically

print(pdfs)

for pdf in pdfs:
    merger.append(pdf)

merger.write("merged-cards.pdf")