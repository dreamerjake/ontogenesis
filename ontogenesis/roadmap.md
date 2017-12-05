##ROADMAP:
* ####ENGINE
    * Skill System
        * Class Definition
            * Skill Type Subclasses
            * Skill Type List (Passive, Projectile, etc.)
            * Skill Tag System (for synergy effects)
        * Skill Mod Class (Skill attribute mods, Triggered Effects)

    * Equipment System
        * Function to adjust player stats based on equipment (call on equip/de-equip)
        * Function to validate an equipment change
        * Equipment
            * Class Definition
            * Attributes
                * Slot
                
    * Currency System
        * Concept: Food as the universal currency - constantly depleting and accepted in all trading
    
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
            * World Map Location
            * Currency
        * Animations
        * State Tracking
        
    * NPC
        * Class Definition
        * Skill Training
        
    * Enemy
        * ~~Class Definition~~
        * ~~mouseover highlighting~~
        
    * Map
        * World Map
            * Class Definition
        * Walls
            * Destructible walls?
        
    * Combat
        * Floating Damage Numbers
        
    * AI
        
    * Procedural Generation
        * Map
            * ~~Wall Layout~~
            * Automatic Tiling
                * Walls
        * Skills
        * Equipment
        * Enemies
    
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
    * ~~Message Flashing (e.g. 'MUSIC MUTED')~~
    * Character Screen
    * Inventory Screen (merge into Character Screen???)
    * Map Screen
    * Skills Screen
    * HUD
        * Active Skill
        * ~~Player Health~~
        * Player Resource
        * Player Currency
    * Settings Screen
    * Help Screen
        * Keybinds Display
    * ~~Minimap~~

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

### Idea Scratchpad
Worldmap has a series of nodes representing map points
    * Each map node has a native enemy type
        * Traveling from node A to node B will encounter a mix of A & B enemies
Reaching destination town(back home after quests???) will perma-unlock skills gained during run
Track the hometown over runs, for permanence
    * Play until you run out of population???
    * Each run's quests based on the current stats(needs) of the town
    * Finding the hometown is the objective of the story mode?