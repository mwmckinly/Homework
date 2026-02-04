from typing import List, Dict
from pathlib import Path
import json
from app.homework import Homework, FolderData, HomeworkType, Section
import subprocess, tempfile, os, shutil
from bs4 import BeautifulSoup

TEMPLATE = """
\\documentclass{article}
\\usepackage[legalpaper, margin=0.5in]{geometry}

\\usepackage{textcomp}
\\usepackage{fontspec}
\\usepackage{unicode-math}
\\usepackage{cprotect}
\\setmainfont{Latin Modern Roman}
\\setmathfont{Latin Modern Math}

\\usepackage{hyperref}

\\usepackage{amsmath}

\\setlength{\\parindent}{0pt}

\\begin{document}

\\newlength{\\partheight}
\\setlength{\\partheight}{0.2375\\textheight}

\\begin{minipage}[t][0.05\\textheight]{\\textwidth}
\\centering
{\\Large \\textbf{Homework Template}}
\\end{minipage}

"""

#: { 'examples': [1, 2, 3] }
HWSelection = Dict[HomeworkType, List[int]]


class Generator:
   sections: Dict[str, Section]
   selection: Dict[str, HWSelection]

   lookup_table: Dict[str, Homework]
   references: Dict[int, str]

   reading: Path
   writing: Path

   answering: bool = False

   def __init__(self, reading: str, writing: str, selection: Dict[str, HWSelection], answering = False) -> None:
      self.reading = Path(reading).resolve()
      self.writing = Path(writing)
      self.writing.parent.touch()
      self.answering = answering
      self.selection = selection

      self.load_selected()
      self.create_table()
   
   def load_selected(self):
      with open(self.reading, "r", encoding='utf-8') as fp:
         homework = json.load(fp)
         data = { str(k): Section.from_dict(v) for k, v in homework.items() }
      
      selection: Dict[str, Section] = {}

      for item in self.selection.keys():
         if item in data.keys():
            selection[item] = data[item]
      
      if not self.answering:
         self.sections = selection
         return
      
      answer_file = str(self.reading).replace('.json', '.key.json')
      with open(answer_file, "r", encoding='utf-8') as fp:
         answers = json.load(fp)
         data = { str(k): Section.from_dict(v) for k, v in answers.items() }

      for item in selection.keys():
         if item in data.keys():
            homework = data[item].answers.copy()
            for num, hw in homework.items():
               selection[item].append_to('answer', hw, num)
      
      self.sections = selection
      return
   
   def create_table(self):
      lookup_table: Dict[str, Homework] = {} #: '1.1': Homework
      references: Dict[int, str] = {} #: x: 'html-content'

      for name, section in self.sections.items():
         folders = self.selection[name]
         for folder, numbers in folders.items():
            for num in numbers:
               item = section.search_in(folder, num)
               if item is None: continue

               label = f"{name}.{num}"
               lookup_table[label] = item

               if item.refr is None: continue

               refr = section.search_in('reference', item.refr)

               if refr is None: continue

               references[item.refr] = refr.html


      self.lookup_table = lookup_table
      self.references = references
   
   def generate_latex(self) -> str:
      content = [TEMPLATE]
      refers: set[int] = set()

      for ident, item in self.lookup_table.items():
         if item.refr in refers:
            item.refr = None

         label = f"{ident}"
         latex = item.latexify(self.references.get(item.refr or -1))
         
         homework = [
            r"\begin{minipage}[t][\partheight]{\textwidth}",
            r"\textbf{" + label + r'}\;' + latex,
            r"\end{minipage}",
            r"\par"
         ]

         content.extend(homework)

      content.append('\n\\end{document}')

      FILENAME = str(self.writing).replace('.pdf', '.tex')

      with open(FILENAME, "w", encoding='utf-8') as fp:
         fp.write('\n'.join(content))

      return FILENAME
   
   def generate_pdf(self):
      tex_path = Path(self.generate_latex())
      output_dir = self.writing.parent

      command = [
         'latexmk',
         '-xelatex',
         '-interaction=nonstopmode',
         f'-output-directory={str(output_dir)}',
         str(tex_path)
      ]

      proc = subprocess.run(
         command, 
         stdout=subprocess.PIPE, 
         stderr=subprocess.STDOUT,
         text=True
      )

      if proc.returncode != 0:
         print(proc.stdout)
      else:
         print(f"PDF saved to {self.writing}")

      aux_extensions = [
        ".aux", ".log", ".fdb_latexmk", ".fls", ".toc",
        ".out", ".synctex.gz", ".nav", ".snm", ".xdv"
      ]

      for ext in aux_extensions:
         file_path = output_dir / (tex_path.stem + ext)
         if file_path.exists():
            file_path.unlink()

   def test(self):
      for ident, item in self.lookup_table.items():
         print(f"{ident}: {BeautifulSoup(item.html, 'lxml').text}")
         if item.refr is None: continue

         print(f"{ident} -> {item.refr}: {BeautifulSoup(self.references.get(item.refr) or "", 'lxml').text}")