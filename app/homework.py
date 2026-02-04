import json
from dataclasses import dataclass
from typing import Literal, Dict, Any
from app import converter


@dataclass
class Homework:
   html: str
   refr: int | None

   def __init__(self, html: str, refr: int | None) -> None:
      self.html = html
      self.refr = refr

   @classmethod
   def from_dict(cls, data: dict) -> "Homework":
      return cls(
         html=data['html'],
         refr=data['refr'],
      )
   
   def to_dict(self) -> Dict[str, Any]:
      return {
         'html': self.html,
         'refr': self.refr
      }
   
   def __repr__(self) -> str:
      return super().__repr__()

   def latexify(self, ref_text: str | None = None):
      return converter.latexify_homework(self.html, ref_text)

HomeworkType = Literal['problem', 'example', 'reference', 'answer']
FolderData = Dict[int, Homework]


class Section:
   examples: FolderData
   problems: FolderData
   references: FolderData
   answers: FolderData

   def __init__(self) -> None:
      self.examples = {  }
      self.problems = {  }
      self.references = {  }
      self.answers = {  }
   
   def _get_folder(self, hw_type: HomeworkType):
      folders: Dict[HomeworkType, Any] = {
         'problem': self.problems,
         'example': self.examples,
         'reference': self.references,
         'answer': self.answers,
      }
      
      return folders[hw_type]

   def append_to(self, hw_type: HomeworkType, value: Homework, number: int):
      folder = self._get_folder(hw_type)
      number = len(folder) if number == -1 else number
      folder[number] = value

      return number
   
   def search_in(self, hw_type: HomeworkType, number: int) -> Homework | None:
      return self._get_folder(hw_type).get(number)   


   def to_dict(self) -> Dict[str, Dict[str, Any]]:
      def serialize_folder(folder: FolderData):
         return {
            str(k): (v.to_dict()) if hasattr(v, 'to_dict') else v
            for k, v in folder.items()
         }
      
      dictionary = {
         "examples": serialize_folder(self.examples),
         "problems": serialize_folder(self.problems),
         "references": serialize_folder(self.references),
         "answers": serialize_folder(self.answers),
      }

      return dictionary
   
   @classmethod
   def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> 'Section':
      section = cls()

      def deserialize(folder: Dict[str, Any]) -> FolderData:
         return {
            int(k): (Homework.from_dict(v))
            for k, v in folder.items()
         }
      
      section.examples = deserialize(data.get('examples', {}))
      section.problems = deserialize(data.get('problems', {}))
      section.references = deserialize(data.get('references', {}))
      section.answers = deserialize(data.get('answers', {}))
      
      return section

