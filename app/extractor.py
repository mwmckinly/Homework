from typing import Dict, Callable
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import json

from app.homework import Homework, HomeworkType, Section

"""
{
   '1.1': {
      problems: {
         '1': { ... },
         '2': { ... },
      },
      examples: {
         '1': { ... },
         '2': { ... },
      },
      remarks: {
         '1': { ... },
         '2': { ... },
      },
      references: {
         '1': { ... },
         '2': { ... },
      },
   },
}
"""

SectionAnswers = Dict[HomeworkType, Dict[int, str]]

class Extrator:
   reading: list[Path]
   writing: Path
   soup: BeautifulSoup

   content: Dict[str, Section] = {}
   section = "1.1"
   current = 1 

   references: set[str] = set()
   reference: int = 1

   def __init__(self, reading: list[str], writing: str) -> None:
      self.reading = [ Path(f).resolve() for f in reading ]
      self.writing = Path(writing)

      self.writing.touch(exist_ok=True)

      self.soup = self.brew_soup()

   def brew_soup(self):
      combined = ""
      for filepath in self.reading:
         with open(filepath, "r", encoding='utf-8') as fp:
            combined += fp.read() + '\n\n'
      
      return BeautifulSoup(combined, 'lxml')
   
   def extract_homework(self):
      self.extract()

      writeable = {
         key: section.to_dict()
         for key, section in self.content.items()
      }

      with open(self.writing, "w", encoding='utf-8') as fp:
         json.dump(writeable, fp, indent=2)

   def extract(self):
      valid_classes = ['example', 'practice', 'level1', 'answersetdiv']

      def extract_folder(soup: Tag, class_: str):
         mapping: Dict[str, Callable] = {
            'level1': self.handle_section,
            'practice': self.extract_problems,
            'example': self.extract_example,
            'answersetdiv': self.extract_answer,
         }

         extractor = mapping.get(class_)
         if extractor is None:
            return {}
         
         extractor(soup)

      for section in self.soup.find_all('section', class_=valid_classes):
         if section.attrs is None: continue
         classes = [ str(c) for c in list(section.attrs['class']) ]
         extract_folder(section, classes[0])

   def extract_problems(self, body: Tag):
      refers = body.find_all('div', class_='instructions')
      r_htmls = [ str(div) for div in refers]
      
      divs = body.find_all('ol', class_='practicelist')

      count = 1

      for idx, problems in enumerate(divs):
         r_html = r_htmls[idx] if idx < len(r_htmls) else None
         ref_id = self.next_reference(r_html) if r_html is not None else None

         for problem in problems.find_all('li', recursive=False):
            homework = Homework(str(problem), ref_id)
            self.append('problem', homework, count)
            count += 1
         
   def extract_example(self, body: Tag):
      header = body.find('h1', class_='title')
      if header is None: return

      number_span = header.find('span', class_='number')
      if number_span is None: return

      number = int(number_span.get_text(strip=True).rstrip('.'))

      solution = body.find('section', class_=['level3', 'level4'])

      if solution is not None:
         self.content[self.section].answers['example'][number] = str(solution)
         solution.extract()
      
      header.extract()
      homework = Homework(str(body), None)
      self.append('example', homework, number)

   def extract_answer(self, body: Tag):
      self.handle_section(body)

      answers = body.find('ol', class_='answerlist')
      if answers is None: return

      problem = 1

      for item in answers.find_all('li', class_='answer'):
         header = item.find('span', class_='number')
         
         if header is None: continue
         
         label = header.extract().get_text(strip=True)
         problem = int(label.rstrip('.'))

         self.content[self.section].answers['problem'][problem] = str(item)
      
   def handle_section(self, body: Tag):
      header = body.find('h1', class_='title', recursive=True)
      if header is None: return

      header = header.find('span', class_='number')
      if header is None: return

      self.section = str(header.text)
      self.current = 1

      self.content.setdefault(self.section, Section())

   def next_reference(self, html: str) -> int:
      ref = self.reference
      self.reference += 1

      self.content[self.section].references[ref] = Homework(html, None)

      return ref

   def append(self, folder: HomeworkType, item: Homework, count: int):
      self.content[self.section].append_to(folder, item, count)
   
   def insert(self, section: str, folder: HomeworkType, item: Homework, count: int):
      self.content[section].append_to(folder, item, count)

