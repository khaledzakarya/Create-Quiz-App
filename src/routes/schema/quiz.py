from pydantic import BaseModel
from typing import Optional,List

class QuizRequest(BaseModel):
    pdf_path: str
    n_questions: Optional[int] = None         
    n_focus: Optional[int] = None
    n_remain: Optional[int] = None                           
    focus_pages: Optional[List[int]] = None
    remain_pages: Optional[List[int]] = None
    f_mcq_ratio: float = 0.6
    f_tf_ratio: float = 0.2
    f_written_ratio: float = 0.2                
    r_mcq_ratio: Optional[float] = 0.6
    r_tf_ratio: Optional[float] = 0.2
    r_written_ratio: Optional[float] = 0.2