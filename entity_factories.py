from components.ai import HostileEnemy
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.currency import Currency
from entity import Actor, Item

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
    currency=Currency(roubles=100),
)

rat = Actor(
    char="r",
    color=(63, 127, 63),
    name="Giant Rat",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=3, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=10),
    currency=Currency(roubles=0),
)
dog = Actor(
    char="d",
    color=(63, 127, 63),
    name="Mutated Dog",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=7, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=17),
    currency=Currency(roubles=0),
)
scav = Actor(
    char="s",
    color=(63, 127, 63),
    name="Scavenger",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
    currency=Currency(roubles=5),
)
raider = Actor(
    char="R",
    color=(0, 127, 0),
    name="Raider",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=5),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
    currency=Currency(roubles=50),
)
mutant = Actor(
    char="M",
    color=(0, 127, 0),
    name="Mutant",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=2, base_power=7),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=125),
    currency=Currency(roubles=0),
)

throwing_sand = Item(
    char="~",
    color=(207, 63, 255),
    name="Sand (throwing)",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)
grenade = Item(
    char="~",
    color=(255, 0, 0),
    name="Grenade",
    consumable=consumable.GrenadeDamageConsumable(damage=12, radius=3),
)
medkit = Item(
    char="!",
    color=(127, 0, 255),
    name="Medkit",
    consumable=consumable.HealingConsumable(amount=4),
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)

kitchen_knife = Item(
    char="/", color=(0, 191, 255), name="Kitchen Knife", equippable=equippable.Knife()
)

combat_knife = Item(
    char="/", color=(0, 191, 255), name="Combat Knife", equippable=equippable.Knife()
)

sword = Item(char="/", color=(0, 191, 255), name="Sword", equippable=equippable.Sword())

pistol = Item(char="/", color=(0, 191, 255), name="Makarov Pistol", equippable=equippable.Handgun())

shirt = Item(
    char="[",
    color=(139, 69, 19),
    name="Tattered Shirt",
    equippable=equippable.Shirt(),
)

body_armor = Item(
    char="[", color=(139, 69, 19), name="Body Armor", equippable=equippable.BodyArmor()
)

rusty_helmet = Item(
    char="[",
    color=(139, 69, 19),
    name="Rusty Helmet",
    equippable=equippable.BasicHelmet(),
)

tough_denim_jeans = Item(
    char="[",
    color=(139, 69, 19),
    name="Tough Denim Jeans",
    equippable=equippable.Pants(),
)

hiking_boots = Item(
    char="[",
    color=(139, 69, 19),
    name="Hiking Boots",
    equippable=equippable.Boots(),
)