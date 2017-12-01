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
        * Class Definition
        
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
        * Decorator to record spawn messages

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
    * HUD
        * Active Skill
        * Player Health
        * Player Resource
        * Player Currency
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
    