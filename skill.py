
from components import skills


class Skill:
    name: str
    level: int
    xp: int

    def __init__(self, name, level=1):
        self.name = name
        self.level = level

    def learn(self, student):
        if(student.skills and self not in student.skills.skills):
            student.skills.learn(self)
    
    def unlearn(self, student):
        if(student.skills and (self in student.skills.skills)):
            student.skills.unlearn(self)