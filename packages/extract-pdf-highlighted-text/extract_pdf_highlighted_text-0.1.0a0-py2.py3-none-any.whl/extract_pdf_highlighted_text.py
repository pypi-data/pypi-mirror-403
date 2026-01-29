# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from __future__ import print_function
import argparse
from typing import Iterable, Iterator, Optional, Sequence, Text, Tuple
from PyPDF2 import PageObject, PdfReader
from PyPDF2.generic import IndirectObject, PdfObject
from pdfminer.layout import LTChar, LTItem, LTPage, LTTextBoxHorizontal, LTTextLineHorizontal
from pdfminer.high_level import extract_pages


def get_direct_pdf_object(
        pdf_object,  # type: PdfObject
):
    # type: (...) -> Optional[PdfObject]
    """
    Resolves an indirect PDF object to its direct object, if necessary.

    Args:
        pdf_object (PdfObject): The PDF object to resolve.

    Returns:
        Optional[PdfObject]: The direct object, or the original object if already direct.
    """
    if isinstance(pdf_object, IndirectObject):
        return pdf_object.get_object()
    else:
        return pdf_object


def yield_page_object_highlight_bboxes(
        page_object,  # type: PageObject
):
    # type: (...) -> Iterator[Tuple[float, float, float, float]]
    """
    Yields bounding boxes of highlight annotations on a PDF page.

    Args:
        page_object (PageObject): The PyPDF2 page object.

    Yields:
        Tuple[float, float, float, float]: The (x0, y0, x1, y1) bounding box for each highlight annotation.
    """
    annots = get_direct_pdf_object(page_object.get('/Annots'))
    if not isinstance(annots, Iterable):
        return

    for annot in map(get_direct_pdf_object, annots):
        subtype = annot.get('/Subtype')
        if subtype != '/Highlight':
            continue

        quad_points = annot.get('/QuadPoints')
        if not isinstance(quad_points, Sequence):
            continue

        num_lines = len(quad_points) // 8
        for i in range(num_lines):
            x_coords = [quad_points[8 * i + j] for j in (0, 2, 4, 6)]
            y_coords = [quad_points[8 * i + j] for j in (1, 3, 5, 7)]

            bottom_left_x = min(x_coords)
            bottom_left_y = min(y_coords)
            top_right_x = max(x_coords)
            top_right_y = max(y_coords)

            yield (
                float(bottom_left_x),
                float(bottom_left_y),
                float(top_right_x),
                float(top_right_y),
            )


def walk_atomic_ltitems(
        ltitem,  # type: LTItem
):
    # type: (...) -> Iterator[LTItem]
    """
    Yields all non-iterable ("atomic") pdfminer layout items in the hierarchy.

    Args:
        ltitem (LTItem): The root pdfminer layout item.

    Yields:
        LTItem: Each atomic (non-composite) layout item.
    """
    if not isinstance(ltitem, Iterable):
        yield ltitem
    else:
        for child_ltitem in ltitem:
            for atomic_ltitem in walk_atomic_ltitems(child_ltitem):
                yield atomic_ltitem


def yield_ltpage_chars_and_bboxes(
        ltpage,  # type: LTPage
):
    # type: (...) -> Iterator[Tuple[Text, Tuple[float, float, float, float]]]
    """
    Yields each character and its bounding box from a pdfminer LTPage.

    Args:
        ltpage (LTPage): The pdfminer page layout object.

    Yields:
        Tuple[Text, Tuple[float, float, float, float]]: (character, (x0, y0, x1, y1)) pairs.
    """
    for atomic_ltitem in walk_atomic_ltitems(ltpage):
        if isinstance(atomic_ltitem, LTChar):
            yield atomic_ltitem.get_text(), atomic_ltitem.bbox


def overlap(
        first_x0,  # type: float
        first_x1,  # type: float
        second_x0,  # type: float
        second_x1,  # type: float
):
    # type: (...) -> float
    """
    Calculates 1D overlap between two ranges.

    Args:
        first_x0 (float): Start of first range.
        first_x1 (float): End of first range.
        second_x0 (float): Start of second range.
        second_x1 (float): End of second range.

    Returns:
        float: The length of overlap.
    """
    if first_x1 <= second_x0:
        overlap_x = 0.
    elif first_x1 <= second_x1:
        if first_x0 <= second_x0:
            overlap_x = first_x1 - second_x0
        else:
            overlap_x = first_x1 - first_x0
    else:
        if first_x0 <= second_x0:
            overlap_x = second_x1 - second_x0
        elif first_x0 <= second_x1:
            overlap_x = second_x1 - first_x0
        else:
            overlap_x = 0.
    return overlap_x


def iou(
        first_bbox,  # type: Tuple[float, float, float, float]
        second_bbox,  # type: Tuple[float, float, float, float]
):
    # type: (...) -> float
    """
    Calculates the Intersection-over-Union (IoU) for two bounding boxes.

    Args:
        first_bbox (Tuple[float, float, float, float]): (x0, y0, x1, y1) of the first bbox.
        second_bbox (Tuple[float, float, float, float]): (x0, y0, x1, y1) of the second bbox.

    Returns:
        float: The IoU value (intersection area over union area).
    """
    first_x0, first_y0, first_x1, first_y1 = first_bbox
    second_x0, second_y0, second_x1, second_y1 = second_bbox

    first_area = (first_x1 - first_x0) * (first_y1 - first_y0)
    second_area = (second_x1 - second_x0) * (second_y1 - second_y0)

    overlap_x = overlap(first_x0, first_x1, second_x0, second_x1)
    overlap_y = overlap(first_y0, first_y1, second_y0, second_y1)

    overlap_area = overlap_x * overlap_y

    return overlap_area / (first_area + second_area - overlap_area)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'pdf_file_path',
        help='Path to the PDF file'
    )
    args = parser.parse_args()
    pdf_file_path = args.pdf_file_path

    reader = PdfReader(pdf_file_path)
    page_objects = reader.pages

    ltpages = extract_pages(pdf_file_path)
   
    for page_index, (page_object, ltpage) in enumerate(zip(page_objects, ltpages)):
        page_object_highlight_bboxes = list(yield_page_object_highlight_bboxes(page_object))
        page_object_highlight_bboxes.sort(key=lambda bbox: (bbox[1] + bbox[3]) / 2, reverse=True)
        if not page_object_highlight_bboxes:
            continue

        page_object_highlight_bbox_char_lists = [[] for _ in page_object_highlight_bboxes]

        for char, char_bbox in yield_ltpage_chars_and_bboxes(ltpage):
            ious = [
                iou(char_bbox, highlight_bbox)
                for highlight_bbox in page_object_highlight_bboxes
            ]

            if any(0 < iou <= 1 for iou in ious):
                argmax = max(range(len(ious)), key=lambda i: ious[i])
                page_object_highlight_bbox_char_lists[argmax].append(char)

        for page_object_highlight_bbox_char_list in page_object_highlight_bbox_char_lists:
            print(''.join(page_object_highlight_bbox_char_list))
            print()


if __name__ == '__main__':
    main()
