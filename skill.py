
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

handguns = Skill(
    name='Handguns',
    level=1
)

rifles = Skill(
    name='Rifles',
    level=1
)

shotguns = Skill(
    name='Shotguns',
    level=1
)

medical = Skill(
    name='Medical',
    level=1
)

blades = Skill(
    name='Blades',
    level=1
)

misc = Skill(
    name='Placeholder',
    level=1
)