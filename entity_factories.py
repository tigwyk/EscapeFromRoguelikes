from components.ai import HostileEnemy, HostileHumanEnemy
from components import consumable, equippable, ammo_container
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.currency import Currency
from components.lore import Lore
from components.lightsource import LightSource
from entity import Actor, Item, Entity, Container
import color

from russian_names import RussianNames

player = Actor(
    char="@",
    color=(255, 255, 255),
    name=RussianNames().get_person(patronymic=False, transliterate=True, uppercase=True),
    #name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
    currency=Currency(roubles=100),
    lore=Lore(),
    light_source=LightSource(radius=15),
)

rat = Actor(
    char="r",
    color=(63, 127, 63),
    name="Giant Rat",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=3, base_defense=0, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=10),
    currency=Currency(roubles=0),
)
dog = Actor(
    char="d",
    color=(63, 127, 63),
    name="Mutant Dog",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=7, base_defense=0, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=17),
    currency=Currency(roubles=0),
)
scav = Actor(
    char="s",
    color=(63, 127, 63),
    name="Scavenger",
    ai_cls=HostileHumanEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=5),
    level=Level(xp_given=35),
    currency=Currency(roubles=5),
    gen_name=True,
    gen_kit=True
)
raider = Actor(
    char="R",
    color=(0, 127, 0),
    name="Raider",
    ai_cls=HostileHumanEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=6),
    inventory=Inventory(capacity=5),
    level=Level(xp_given=100),
    currency=Currency(roubles=50),
)
mutant1 = Actor(
    char="m",
    color=(0, 127, 0),
    name="Mutant Human",
    ai_cls=HostileHumanEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=2, base_power=9),
    inventory=Inventory(capacity=5),
    level=Level(xp_given=125),
    currency=Currency(roubles=0),
)
mutant2 = Actor(
    char="M",
    color=(0, 127, 0),
    name="Large Mutant Human",
    ai_cls=HostileHumanEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=2, base_power=12),
    inventory=Inventory(capacity=5),
    level=Level(xp_given=125),
    currency=Currency(roubles=0),
)

throwing_sand = Item(
    char="~",
    color=(207, 63, 255),
    name="sand (throwing)",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)
grenade = Item(
    char="!",
    color=(127, 0, 255),
    name="grenade",
    consumable=consumable.GrenadeDamageConsumable(damage=12, radius=3),
)
medkit = Item(
    # char="+",
    char="♥",
    color=(255, 0, 0),
    name="medkit",
    consumable=consumable.HealingConsumable(amount=6),
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="seeker drone",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)

makarov_mag = Item(
    char="=",
    color=(139, 69, 19),
    name="pistol magazine",
    ammo_container=ammo_container.AmmoMag(ammo=6,max_ammo=6,ammo_type="9x18mm")
)

shotgun_shells_box = Item(
    char="=",
    color=(139, 69, 19),
    name="shotgun shells",
    ammo_container=ammo_container.AmmoMag(ammo=6,max_ammo=6,ammo_type="12g")
)

shotgun_slugs_box = Item(
    char="=",
    color=(139, 69, 19),
    name="shotgun slugs",
    ammo_container=ammo_container.AmmoMag(ammo=6,max_ammo=6,ammo_type="12g")
)

ak_mag = Item(
    char="=",
    color=color.red,
    name="AK magazine",
    ammo_container=ammo_container.AmmoMag(ammo=30,max_ammo=30,ammo_type="5.45x39mm")
)

kitchen_knife = Item(
    char="/", color=(0, 191, 255), name="kitchen knife", equippable=equippable.Blade(power_bonus=1)
)

combat_knife = Item(
    char="/", color=(0, 191, 255), name="combat knife", equippable=equippable.Blade(power_bonus=2)
)

sword = Item(char="/", color=(0, 191, 255), name="sword", equippable=equippable.Blade(power_bonus=3))

pistol = Item(char="/", color=(0, 191, 255), name="makarov pistol", equippable=equippable.Firearm(power_bonus=1))

shotgun = Item(char="/", color=(0, 191, 255), name="mp-153 shotgun", equippable=equippable.Firearm(power_bonus=2))

rifle = Item(char="/", color=(0, 191, 255), name="mosin rifle", equippable=equippable.Firearm(power_bonus=4))

assault_rifle = Item(char="/", color=(139, 191, 255), name="AK-74m automatic rifle", equippable=equippable.Firearm(power_bonus=3))

shirt = Item(
    char="[",
    color=(139, 69, 19),
    name="tattered shirt",
    equippable=equippable.BodyArmor(defense_bonus=1),
)

body_armor = Item(
    char="[", color=(139, 69, 19), name="body armor", equippable=equippable.BodyArmor(defense_bonus=3)
)

rusty_helmet = Item(
    char="[",
    color=(139, 69, 19),
    name="rusty helmet",
    equippable=equippable.Helmet(defense_bonus=1),
)

tough_denim_jeans = Item(
    char="[",
    color=(139, 69, 19),
    name="tough denim jeans",
    equippable=equippable.LegArmor(defense_bonus=1),
)

hiking_boots = Item(
    char="[",
    color=(139, 69, 19),
    name="hiking boots",
    equippable=equippable.Boots(defense_bonus=1),
)

light = Entity(char=' ', color=(255,255,255), name='', light_source=LightSource(radius=2))

container_box = Container(char=' ',
                             color=(128,128,128),
                             name='weapons box',
                             inventory=Inventory(capacity=5),
                             )