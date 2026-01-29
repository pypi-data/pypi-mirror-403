# `extract-pdf-highlighted-text`

Extract text that has been highlighted in PDF documents.

## How it works

- Locates all highlight annotations in each page using PyPDF2.
- Computes the bounding boxes of each highlight annotation.
- Uses pdfminer.six to determine locations of all visible characters on the page.
- For each annotation, matches the characters whose bounding boxes overlap the annotation's bounding box (using IoU).
- Groups and prints out the highlighted text in reading order.

## Installation

```bash
pip install extract-pdf-highlighted-text
```

*Dependencies*: 

- PyPDF2 (for annotation geometry)
- pdfminer.six (for text locations)

## Usage

```bash
python -m extract_pdf_highlighted_text your_file.pdf
```

The script will print each extracted highlight in reading order.

## Example Output

```
This is a highlighted passage.

Another highlighted bit here.
```

## Limitations

- Does not support image-based PDFs (no OCR).
- Precision may depend on PDF quality and producer.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
