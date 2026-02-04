# from src.extract import Extractor
from app.generater import Generator, HWSelection
from app.extractor import Extrator
from app.homework import Section, Homework
from typing import Dict, List

TEXTBOOK = "app/data/textbook.html"
ANSWERS = "app/data/answers.html"

PROBLEMS_JSON = "app/data/problems.json"
ANSWERS_JSON = PROBLEMS_JSON.replace('.json', '.key.json')

PDF = "app/out/homework.pdf"

"""
Section 1.3: 11,13,14 (only need to determine whether existence and uniqueness of solutions is guaranteed), 28

Section 1.4 (skip Toricelli's law): 1,7,21,24,27,34,51

Section 1.5 (through Example 3): 3,5,7,16,23,24
"""

SELECTED: Dict[str, HWSelection] = {
   '1.3': { 'problem': [ 11, 13, 14 ], },
   '1.4': { 'problem': [1, 7, 22, 24, 27, 34, 51], },
   '1.5': { 
      'problem': [3, 5, 7, 16, 23, 24],
      'example': [1, 2, 3]
   }
}

if __name__ == "__main__":
   Extrator(TEXTBOOK, PROBLEMS_JSON).extract_homework()
   # Extrator(ANSWERS, ANSWERS_JSON).extract_homework()

   gen = Generator(PROBLEMS_JSON, PDF, SELECTED, answering=False)

   gen.test()
   