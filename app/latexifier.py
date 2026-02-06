import re
import pypandoc
from bs4 import BeautifulSoup
from typing import Literal, List, Tuple

_MATH_RE = re.compile( r"(\\\(|\\\[)(.+?)(\\\)|\\\])", re.DOTALL )
_PROBLEM_PART_RE = re.compile( r"\s*\\textbf\{\(([a-z])\)\}", flags=re.IGNORECASE)

StyleType = Literal['textstyle', 'displaystyle']

class Latexifier:
   style: Literal['textstyle', 'displaystyle']
   inline: bool
   indent: str
   sanitize: bool

   def __init__(self, *, style: StyleType, inline: bool = True, indent: str = '0.5em', sanitize: bool = True) -> None:
      self.style = style
      self.inline = inline
      self.indent = indent
      self.sanitize = sanitize
   
   def latexify(self, html: str) -> str:
      if self.sanitize:
         html = self._sanitize_html(html)
      
      latex = self._convert(html)
      latex = self._sanitize_latex(latex)
      latex = self._normalize_math(latex)
      latex = self._format_parts(latex)

      return latex
   
   def _convert(self, html: str) -> str:
      return pypandoc.convert_text(html, format='html', to='latex', extra_args=['--mathjax'])
   
   def _normalize_math(self, text: str) -> str:
      def repl(match: re.Match) -> str:
         content = match.group(2).strip()
         return rf"$\{self.style} {content}$"
      
      text = _MATH_RE.sub(repl, text)

      if not self.inline:
         text = self._set_block_display(text)
      
      return text
   
   def _set_block_display(self, text: str) -> str:
      return re.sub(
         r"\$(\\(?:textstyle|displaystyle)\s+.+?)\$",
         r"\\[\1\\]",
         text,
         flags=re.DOTALL,
      )
   
   def _format_parts(self, text: str) -> str:
      def repl(match: re.Match):
         letter = match.group(1)
         return (
            '\n\n'
            r"\vspace{0.5em}"
            rf'\hspace*{{{self.indent}}}\textbf{{({letter})}}'
         )
      
      return _PROBLEM_PART_RE.sub(repl, text)
   
   def _sanitize_html(self, html: str) -> str:
      soup = BeautifulSoup(html, 'lxml')

      DROPS = {
         'TAGS': {
            "a", "link", "base", "iframe", "object", 
            "embed", "script", "style", "img" 
         },
         'ATTR': {
            "href", "src", "srcset", "cite", "action", "formaction", 
            "data", "poster", "longdesc", "xlink:href", "xmlns"
         },
      }

      KEEPS = {
         'ATTR': { 'class' }
      }

      for tag in soup.find_all(True):
         if tag.name == 'h1' and 'title' in tag.attrs.get('class', []) and 'solution' in tag.text.lower():
            tag.decompose()
            continue

         if tag.name in DROPS['TAGS']:
            tag.decompose()
            continue

         for attr in list(tag.attrs or []):
            if attr not in KEEPS['ATTR'] or attr in DROPS['ATTR'] or attr.startswith(("on", "xmlns")):
               del tag.attrs[attr]
         
      for tag in soup.find_all(re.compile("^m")):
         for attr in list(tag.attrs):
            if attr != 'class':
               del tag.attrs[attr]
      
      text = str(soup)

      text = re.sub(r"(https?://\S+|www\.\S+|mailto:\S+)", "", text)
      text = re.sub(r"\s+", " ", text)

      return text
   
   def _sanitize_latex(self, text: str) -> str:
      rules: List[Tuple[str, str]] = [
         ( r"\{\$(.*?)\$\}", r"$\1$" ),
         ( r"\\hyperlink\{[^}]*\}\{\{([^}]*)\}\s*\{([^}]*)\}\}", r" \1 \2", ),
         ( r";", r"\;;\;\; " ),
         ( r"\n\s*\n+", " " ),
         
         ( r"\\begin\{figure\}.*?\\end\{figure\}", ""),
         ( r"\\caption\{.*?\}", ""),
         ( r"\\label\{.*?\}", ""),
      ]

      for rule, repl in rules:
         text = re.sub(rule, repl, text, flags=re.DOTALL)
      
      return text
   
