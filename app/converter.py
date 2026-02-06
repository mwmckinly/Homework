import re, pypandoc
from bs4 import BeautifulSoup

def into_latex(text: str, clean = True, inline=True):
   if clean: text = _strip_bloat(text)

   text = pypandoc.convert_text(
      text, extra_args=['--mathjax'],
      format='html', to='latex'
   )

   if clean: text = _sanitize(text)

   text = latexify_mathml(text, inline=inline)
   text = format_problem_parts(text)

   return text

def latexify_mathml(text: str, inline=True) -> str:
   patterns = {
      'block': re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
      'inline': re.compile(r"\\\((.+?)\\\)", re.DOTALL)
   }

   preserve = patterns['inline' if inline else 'block']
   replace = patterns['block' if inline else 'inline']

   mathjax = []
   PRESERVE = "@@PRESERVE{}@@"


   def preserver(match):
      mathjax.append(match.group(0))
      return PRESERVE.format(len(mathjax) - 1)
   
   text = preserve.sub(preserver, text)
   remove = r'\\(\1\\)' if inline else r'\\[\1\\]'
   text = replace.sub(remove, text)

   for i, mathml in enumerate(mathjax):
      text = text.replace(f"@@PRESERVE{i}@@", mathml)

   return text

def wrap_display_inline(text):
   math_pattern = re.compile(r'\$(\displaystyle[^$]+)\$')
   def repl(match):
      return r'\mbox{' + match.group(0) + r'}'
   return math_pattern.sub(repl, text)

def format_math(text: str, style: str):
   math_pattern = re.compile(r"(\\\(|\\\[)(.+?)(\\\)|\\\])", re.DOTALL)

   def repl(match):
      content = match.group(2).strip()
      replacement = rf"$\{style} {content}$"
      return replacement
   
   return math_pattern.sub(repl, text)

def _strip_bloat(text: str) -> str:
   soup = BeautifulSoup(text, "lxml")

   # Tags that should never survive
   DROP_TAGS = {
      "a", "link", "base", "iframe", "object", "embed",
      "script", "style", "img"
   }

   # Attributes that can produce links or external refs
   DROP_ATTRS = {
      "href", "src", "srcset", "cite", "action", "formaction",
      "data", "poster", "longdesc", "xlink:href",
      "xmlns"
   }

   KEEP_ATTRS = {"class"}

   # Remove dangerous tags entirely
   for tag in soup.find_all(DROP_TAGS):
      tag.decompose()

   # Strip attributes
   for tag in soup.find_all(True):
      for attr in list(tag.attrs):
         if (
               attr not in KEEP_ATTRS
               or attr in DROP_ATTRS
               or attr.startswith("on")
               or attr.startswith("xmlns")
         ):
               del tag.attrs[attr]

   # Extra pass for MathML
   for math_tag in soup.find_all(re.compile("^m")):
      for attr in list(math_tag.attrs):
         if attr != "class":
               del math_tag.attrs[attr]

   cleaned = str(soup)

   # Remove URL-like plaintext that LaTeX auto-links
   cleaned = re.sub(r"(https?://\S+|www\.\S+|mailto:\S+)", "", cleaned)

   # Normalize whitespace
   cleaned = re.sub(r"\s+", " ", cleaned)

   return cleaned.strip()
   
def _sanitize(text: str) -> str:
   text = re.sub(r"\{\$(.*?)\$\}", r"$\1$", text)

   text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\caption\{.*?\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\label\{.*?\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\hyperlink\{[^}]*\}\{\{([^}]*)\}\s*\{([^}]*)\}\}", r" \1 \2", text)
   text = re.sub(r';', r'\;;\;\; ', text)
   text = re.sub(r"\n\s*\n+", " ", text)

   return text

def format_problem_parts(text: str, indent="1.5em") -> str:
   pattern = re.compile(
      r"\s*\\textbf\{\(([a-z])\)\}",
      flags=re.IGNORECASE
   )

   def repl(match):
      letter = match.group(1)
      return (
         "\n\n"
         rf"\hspace*{{{indent}}}\textbf{{({letter})}}"
      )

   return pattern.sub(repl, text)