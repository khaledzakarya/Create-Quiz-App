from typing import List, Optional

class Question:
    def __init__(self, qtype: str, question: str,
                 options: Optional[List[str]] = None, answer: str = ''):
        self.type = qtype
        self.question = question
        self.options = options if options else []
        self.answer = answer

    def to_dict(self):
        return {
            'type': self.type,
            'question': self.question,
            'options': self.options,
            'answer': self.answer
        }
        
class Quiz:
    def __init__(self, questions: List[Question]):
        self.questions = questions

    def filter_by_type(self, qtype: str) -> List[Question]:
        return [q for q in self.questions if q.type == qtype]
    
    def to_dict(self):
        return {
            'quiz': [q.to_dict() for q in self.questions]
        }
    
        