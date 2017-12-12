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
    * Settings Screen
    * Help Screen
        * Keybinds Display
    * ~~Minimap~~
        * Fog of War / Explored

* ####SYSTEM
    * Display
        * ~~Fullscreen Mode~~
        * Resolution Changing
        * Resizeable Windows
    * ~~Audio~~
    * OSX Support
        * Keyboard Input
    
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