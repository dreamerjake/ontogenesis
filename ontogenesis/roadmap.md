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
    
    * Assets
        * Sprites
            * Use spritesheet metadata file
    
    * Player
        * Attributes
            * World Map Location
        * Animations
        * State Tracking
        
    * NPC
        * Class Definition
        * Skill Training
        
    * Enemy
        * Class Definition
        
    * Map
        * World Map
            * Class Definition
        
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

* ####UI
    * GUI Toolkit
        * Button
        * Checkbox
        * Slider?
        * Text Input?
    * Character Screen
    * Inventory Screen (merge into Character Screen???)
    * Map Screen
    * Skills Screen
    * HUD - Active Skill
    * Settings Screen
    * Help Screen
        * Keybinds Display
    * Minimap

* ####SYSTEM
    * Display
        * ~~Fullscreen Mode~~
        * Resolution Changing
        * Resizeable Windows
    * Audio
    