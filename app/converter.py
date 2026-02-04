import re, pypandoc

def into_latex(text: str, clean = True):
   text = pypandoc.convert_text(
      text, extra_args=['--mathjax'],
      format='html', to='latex'
   )

   if clean: return _sanitize(text)
   else: return text

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

def latexify_homework(text: str, refr: str | None = None):
   problem = latexify_mathml(into_latex(text), inline=refr is not None)

   if refr is None: return r'\;' + problem
   reference = into_latex(refr)
   return reference + '\n' + problem

def _sanitize(text: str) -> str:
   text = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\caption\{.*?\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\label\{.*?\}", "", text, flags=re.DOTALL)
   text = re.sub(r"\\hyperlink\{[^}]*\}\{\{([^}]*)\}\s*\{([^}]*)\}\}", r" \1 \2", text)

   return text

