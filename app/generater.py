from typing import List, Dict
from pathlib import Path
import json
from app.homework import Homework, HomeworkType, Section
import subprocess
from bs4 import BeautifulSoup
from app import converter

TEMPLATE = r"""
\documentclass{article}
\usepackage[legalpaper, margin=0.5in]{geometry}

\usepackage{textcomp}
\usepackage{fontspec}
\usepackage{unicode-math}
\everymath{\displaystyle\scriptstyle}
\usepackage{cprotect}
\setmainfont{Latin Modern Roman}
\setmathfont{Latin Modern Math}

\usepackage{hyperref}

\usepackage{amsmath}

\relpenalty=10000
\binoppenalty=10000

\setlength{\parindent}{0pt}

\begin{document}

\newlength{\partheight}
\setlength{\partheight}{0.2375\textheight}

\begin{minipage}[t]{\textwidth}
\centering
{\Large \textbf{Homework Template}}
\end{minipage}
"""

#: { 'examples': [1, 2, 3] }
HWSelection = Dict[HomeworkType, List[int]]


class Generator:
   selection: Dict[str, HWSelection]

   sections: Dict[str, Section]
   problems: Dict[str, Homework]
   answers: Dict[str, str]
   references: Dict[int, str]

   reading: Path
   writing: Path

   answering: bool = False

   def __init__(self, reading: str, writing: str, selection: Dict[str, HWSelection]) -> None:
      self.reading = Path(reading).resolve()
      self.writing = Path(writing)
      self.writing.parent.touch()
      self.selection = selection

      self.load_selected()
      self.establish_keymaps()
   
   def load_selected(self):
      with open(self.reading, "r", encoding='utf-8') as fp:
         homework = json.load(fp)
         data = { str(k): Section.from_dict(v) for k, v in homework.items() }
      
      selection: Dict[str, Section] = {}

      for item in self.selection.keys():
         if item in data.keys():
            selection[item] = data[item]
      
      self.sections = selection

   def establish_keymaps(self):
      problems: Dict[str, Homework] = {}
      answers: Dict[str, str] = {}
      references: Dict[int, str] = {}

      for name, section in self.sections.items():
         folders = self.selection[name]
         
         for folder, numbers in folders.items():
            solved = section.answers.get(folder, {})
            for num in numbers:
               item = section.search_in(folder, num)
               if item is None: continue

               label = f"{name}.{num}"
               problems[label] = item

               if item.refr is not None: 
                  refr = section.search_in('reference', item.refr)

                  if refr is not None: 
                     references[item.refr] = refr.html               


               ans = solved.get(num)
               if ans is not None:
                  answers[label] = ans


      self.problems = problems
      self.references = references
      self.answers = answers

   def write_latex(self) -> str:
      sects = list(self.selection.keys())
      title = f"Homework {sects[0]}-{sects[-1]}"

      contents = [TEMPLATE.replace("Homework Template", title)]
      refers = set()

      for label, item in self.problems.items():
         block = [
            r"\begin{minipage}[t][\partheight]{\textwidth}",
            r"",
            r"\end{minipage}",
            r"\par"
         ]

         if item.refr is not None and item.refr not in refers:
            refers.add(item.refr)
            refer = self.references[item.refr]
            block[1] += converter.into_latex(refer) + r'\\\\' '\n'

         block[1] += r"\textbf{" + label + r'.}\quad ' + item.latexify('displaystyle')

         contents.append('\n'.join(block))

      contents.append('\n'.join([
         r"\newpage",
         r"\begin{center}",
         r"{\Large \textbf{Answer Key}}",
         r"\end{center}",
         r"\vspace{1em}"
      ]))

      for label, item in self.answers.items():
         latex = converter.into_latex(item)

         contents.append(
            "\n".join([
               r"\noindent\textbf{" + label + r".}",
               r"\par",
               latex,
               r"\vspace{1em}"
            ])
         )
         
         
      contents.append('\n\\end{document}')

      FILENAME = str(self.writing).replace('.pdf', '.tex')
      with open(FILENAME, "w", encoding='utf-8') as fp:
         fp.write('\n'.join(contents))

      return FILENAME

   def generate_pdf(self):
      tex_path = Path(self.write_latex())
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
      for ident, item in self.problems.items():
         print(f"{ident}: {BeautifulSoup(item.html, 'lxml').text}")
         if item.refr is None: continue

         print(f"{ident} -> {item.refr}: {BeautifulSoup(self.references.get(item.refr) or "", 'lxml').text}")

