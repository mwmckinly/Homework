# from src.extract import Extractor
from app.generater import Generator, HWSelection
from app.extractor import Extrator
from typing import Dict

TEXTBOOK = "app/data/textbook.html"
ANSWERS = "app/data/answers.html"
DATABASE = "app/data/problems.json"

OUTPUT_PDF = "app/out/homework.pdf"

"""
Section 1.5 (Mixture problems):33,37

Section 2.1: 3,5,12,13,26,27

Section 2.2 (skip Bifurcation):1,3,7,26,27

Section 2.3 (through Example 2): 7, 9.    (Example 3 is dropped)
"""

SELECTED: Dict[str, HWSelection] = {
   '1.5': { 'problem': [33, 37] },
   '2.1': { 'problem': [3,5,12,13,26,27] },
   '2.2': { 'problem': [1,3,7,26,27] },
   '2.3': { 'example': [1, 2], 'problem': [7, 9] }
}

if __name__ == "__main__":
   # Extrator([TEXTBOOK, ANSWERS], PROBLEMS_JSON).extract_homework()

   gen = Generator(DATABASE, OUTPUT_PDF, SELECTED)
   gen.generate_pdf()
