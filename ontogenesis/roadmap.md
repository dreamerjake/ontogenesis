##ROADMAP:
* ####ENGINE
    * ~~Skill System~~
        * ~~Class Definition~~
            * Skill Type Subclasses
            * Skill Type List (Passive, Projectile, etc.)
            * Skill Tag System (for synergy effects)
        * Skill Mod Class (Skill attribute mods, Triggered Effects)
        * Ideas
            * Scouting
        * ~~Resource~~

    * Equipment System
        * ~~Function to adjust player stats based on equipment (call on equip/de-equip)~~
        * ~~Function to validate an equipment change~~
        * Equipment
            * ~~Class Definition~~
            * ~~Attributes~~
                * ~~Slot~~
        * Equipment Sets? (procedurally generated?)
                
    * ~~Currency System~~
        * ~~Concept: Food as the universal currency - constantly depleting and accepted in all trading~~
            * regen of health/resource consumes extra food
    
    * Controls
        * Namespace for controls mapping?
        * System Contols
            * Volume Control
            * ~~Music Mute~~
    
    * Assets
        * Sprites
            * Use spritesheet metadata file
    
    * Player
        * Attributes
            * ~~World Map Location~~
            * ~~Currency~~
        * ~~Animations~~
        * State Tracking
        
    * NPC
        * Class Definition
        * Skill Training

    * Enemy
        * ~~Class Definition~~
        * ~~mouseover highlighting~~
        * ~~Collisions~~
            * ~~Take damage on collision (until mobs are able to use skills/attacks)~~
        * Mob skills
        * Mob stats should scale with difficulty
        * Mob density should scale with difficulty
        * Edible tag

    * Map
        * ~~World Map~~
            * ~~Class Definition~~
        * Walls
            * Destructible walls?
        * Multiple Victory Conditions
            * ~~Kill Everything~~
            * Find the exit?
            * Waypoints / Other Fast Travel for previously beaten maps (maybe if the kill everything condition was met?)
            * Guide (in exchange for currency?)
        
    * Combat
        * Floating Damage Numbers
        * Melee attacks
        
    * AI
        
    * Procedural Generation
        * Map
            * ~~Wall Layout~~
            * Automatic Tiling
                * Walls
        * Skills
        * Equipment
        * Enemies
        * ~~Worldmap~~
    
    * Settings
        * Settings as SimpleNamespace?? (tuple keys??? e.g. game.settings[a, b, c])
        
    * Debugging
        * ~~Decorator to record spawn messages~~

* ####UI
    * GUI Toolkit
        * ~~Button~~
            * Resizeable?
            * Caption Text
        * Checkbox
        * Slider?
        * Text Input?
        * Grid System?
        * ~~Scrolling Window~~
        * Back Buttons
    * ~~Message Flashing (e.g. 'MUSIC MUTED')~~
    * Character Screen
    * Inventory Screen (merge into Character Screen???)
    * ~~Map Screen~~
    * ~~Skills Screen~~
    * HUD
        * ~~Active Skill~~
        * ~~Player Health~~
        * ~~Player Resource~~
        * ~~Player Currency~~
        * ~~Mob Healthbars on effects layer~~
    * Settings Screen
    * Help Screen
        * ~~Keybinds Display~~
    * ~~Minimap~~
        * Fog of War / Explored
        * Adjust for light radius

* ####SYSTEM
    * Display
        * ~~Fullscreen Mode~~
        * Resolution Changing
        * Resizeable Windows
    * ~~Audio~~
    * OSX Support
        * Keyboard Input
    
### Design Principles
(Meta): Build for yourself, predicting other people is *really hard*
1. Imbalance is fun.
    - The player should strive for, and attain, a state of imbalance and enjoy it until their character dies.
2. Consistency matters.
    - Mechanics and narrative elements should apply as *universally* as possible.
    - Negative experiences should feel fair and/or justified.
3. Time has value.
    - Don't prevent players from doing things efficiently
    - At any given time, the game should *quickly* move towards its current objective, not *slowly* move towards a distant finale

### Influences
(Note): These are just the ones that I explicitly thought about during creation and consciously thought
"yeah, elements of this would be nice", obviously no one can trace every influencing work
Solomon's Boneyard
Path of Exile
Diablo (before it got bad)
(The idea that led to) No Man's Sky

### Research - Interviews
Shattered Pixel Dungeon (Miles)

### Notes
tweenting library to keep in mind
    https://github.com/asweigart/pytweening
fix for warning "libpng warning: iCCP: known incorrect sRGB profile"
    mogrify *.png
alternative outlining method
    https://stackoverflow.com/questions/9319767/image-outline-using-python-pil
volume settings math
    https://www.reddit.com/r/gamedev/comments/7hht15/developers_fix_your_volume_sliders/
isometric example
    http://flarerpg.org/
    https://www.youtube.com/watch?v=KvSjJ-kdGio
'qol creep'?
    https://www.reddit.com/r/pathofexile/comments/7jk0kh/cohh_with_a_great_suggestion_this_is_why_external/
    
pyinstaller -c -d -F --add-data="assets;assets" game.py

### Idea Scratchpad
~~Worldmap has a series of nodes representing map points~~
    * ~~Each map node has a native enemy type~~
        * ~~Traveling from node A to node B will encounter a mix of A & B enemies~~
Reaching destination town(back home after quests???) will perma-unlock skills gained during run
Track the hometown over runs, for permanence
    * Play until you run out of population???
    * Each run's quests based on the current stats(needs) of the town
    * Finding the hometown is the objective of the story mode?
Dynamic mob generation based on the game's fps
Threat generation meter? (constant spawning?)
Monster Hunter type equipment?
Quick/intuitive way to evaluate whether an equippable is GOOD or not?
    * Total exp in a skill, % distribution, delta w/ current equip?
Have the characters realize they're living in a simulated world
Make a universal-ish 'Info' button that can be used on almost everything
The player could have a resource 'color' that changes represents their 'affinity' to various skilltypes
Chat system that interacts with the world?
    -Sentiment Analysis
    -Voice Radius
Being present when a skill is used by a npc or enemy should let the player learn it after a while?
    -Have this be in tutorial: start with no skills, and have NPC say "Watch closely..." etc
    -Alternatively, learn skill components rather than full skills?
Stamina system for movement and a basic attack?

### Mob AI Scratchpad
Predatory
    * Looks for food
Bloodthirsty
Carnivorous
    * Eats things it kills (Gets stronger / Gains Health)
Hostile
    * Threatens / Tries to Intimidate (snaps/growls)
Covert
    * Hides

### Sample Mob
'Giant Lizard'
Big   # hit box multiplier?
Fast  # speed
Spits Acid # skills
Burrow # skills

high collision damage
high knockback # hits you with his tail
low vision
high xp
inventory: lizard meat, various lizard parts


### Misc Notes
* too much info on minimap
* starving should have an indicator
* more (attack) skills
* needs button tutorial image
* needs tutorial
* oom sound / brighter resource globe

likes:
* controls
* difficulty
* intro placement
* minimap
* zombies
    * look
    * behavior

dislikes:
* hard to notice when oom

good starting skill:
* gun? - shoot bullets (sounds like a weapon equipment)
* THROW - throwing rocks? (ammo for a default throw skill)
* MELEE ATTACK

ideal skill:
* arrows
* multiple
* explosive
* flaming - burning damage effect
* fast fire rate
