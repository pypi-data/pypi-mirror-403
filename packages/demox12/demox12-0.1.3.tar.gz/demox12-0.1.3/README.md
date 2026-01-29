# demox12

This package distributes PDFs, images, DOCX files, and other assets.

## Usage

```python
from demox12 import get_data_path

data_dir = get_data_path()

pdf = data_dir / "file1.pdf"
img = data_dir / "subfolder/chart.png"

print(pdf.exists())
print(img.exists())
