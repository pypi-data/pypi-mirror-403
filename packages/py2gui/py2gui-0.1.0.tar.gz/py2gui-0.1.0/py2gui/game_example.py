"""
The Lost Artifact - A Text Adventure Game
A game where you explore ancient ruins, solve puzzles, and find hidden treasure.
"""

from py2gui import display, user_type_in, run, clear, exit_gui, user_write, display_colored, set_theme
import random
import time


class AdventureGame:
    def __init__(self):
        self.player_name = ""
        self.current_room = "entrance"
        self.inventory = []
        self.health = 100
        self.score = 0
        self.game_over = False
        self.has_torch = False
        self.has_key = False
        self.has_map = False
        self.solved_riddle = False
        self.visited_rooms = set()
        
        # Game map with descriptions and connections
        self.rooms = {
            "entrance": {
                "name": "Ancient Temple Entrance",
                "description": "\033[33mYou stand before the crumbling entrance of an ancient temple. "
                              "Vines cover the stone walls, and the heavy wooden door creaks in the wind. "
                              "The air smells of damp earth and mystery.\033[0m",
                "exits": {"north": "main_hall", "east": "garden"},
                "items": ["stone tablet"],
                "puzzle": None
            },
            "main_hall": {
                "name": "Grand Hall",
                "description": "\033[33mA vast hall with towering pillars. Faded murals decorate the walls, "
                              "depicting ancient rituals. Cobwebs hang from the ceiling like ghostly curtains.\033[0m",
                "exits": {"south": "entrance", "east": "library", "west": "statue_room"},
                "items": ["rusted sword"],
                "puzzle": None
            },
            "garden": {
                "name": "Overgrown Garden",
                "description": "\033[32mA once-beautiful garden now wild with vegetation. Strange glowing mushrooms "
                              "illuminate the path. A small fountain gurgles in the center.\033[0m",
                "exits": {"west": "entrance", "north": "library"},
                "items": ["herbs", "strange mushroom"],
                "puzzle": "mushroom"
            },
            "library": {
                "name": "Ancient Library",
                "description": "\033[35mDusty scrolls and crumbling books line the walls. A large stone desk "
                              "holds an open tome. Moonlight filters through a cracked ceiling.\033[0m",
                "exits": {"west": "main_hall", "south": "garden", "north": "dark_passage"},
                "items": ["old book", "quill"],
                "puzzle": "riddle"
            },
            "statue_room": {
                "name": "Chamber of Statues",
                "description": "\033[36mFour stone statues stand guard in this circular chamber. Each faces a "
                              "cardinal direction. One statue's hand is outstretched, as if offering something.\033[0m",
                "exits": {"east": "main_hall"},
                "items": ["torch"],
                "puzzle": "statues"
            },
            "dark_passage": {
                "name": "Dark Passage",
                "description": "\033[90mPitch darkness. You can't see more than a few inches ahead. "
                              "The air is cold and smells of decay. Something scuttles in the shadows.\033[0m",
                "exits": {"south": "library", "north": "treasure_room"},
                "items": [],
                "puzzle": "darkness"
            },
            "treasure_room": {
                "name": "Treasure Chamber",
                "description": "\033[93mA glittering hoard of gold, gems, and artifacts! In the center rests "
                              "a pedestal with the legendary Artifact of Aethelred.\033[0m",
                "exits": {"south": "dark_passage"},
                "items": ["gold coins", "ruby", "emerald", "Artifact of Aethelred"],
                "puzzle": "final"
            }
        }
        
        # Game messages with colors
        self.messages = {
            "welcome": "\033[1;36m========== THE LOST ARTIFACT ==========\033[0m\n"
                      "A Text Adventure Game\n\n"
                      "\033[3mLong ago, the powerful Artifact of Aethelred was hidden in an ancient temple. "
                      "Many have searched, but none have returned. Will you be the one to find it?\033[0m\n",
            
            "help": "\033[1;37m===== COMMANDS =====\033[0m\n"
                   "\033[32m• look/l: Look around the room\n"
                   "• go [direction]: Move (north, south, east, west)\n"
                   "• take [item]: Pick up an item\n"
                   "• use [item]: Use an item from inventory\n"
                   "• inv/i: Check inventory\n"
                   "• health/h: Check health\n"
                   "• score: Check score\n"
                   "• map: Show visited rooms\n"
                   "• help: Show this help\n"
                   "• quit: End the game\033[0m",
            
            "win": "\033[1;33m╔══════════════════════════════════════════╗\n"
                  "  CONGRATULATIONS, {name}!\n"
                  "  You have found the Artifact of Aethelred!\n"
                  "  Score: {score}\n"
                  "  Health: {health}\n"
                  "╚══════════════════════════════════════════╝\033[0m",
            
            "game_over": "\033[1;31m╔══════════════════════════════════════╗\n"
                        "  GAME OVER\n"
                        "  Your adventure ends here...\n"
                        "  Final Score: {score}\n"
                        "╚══════════════════════════════════════╝\033[0m"
        }
        
        # Room descriptions when revisiting
        self.brief_descriptions = {
            "entrance": "The temple entrance. The heavy door still creaks.",
            "main_hall": "The grand hall with its fading murals.",
            "garden": "The overgrown garden with glowing mushrooms.",
            "library": "The ancient library, dusty and silent.",
            "statue_room": "The chamber with four stone statues.",
            "dark_passage": "A terrifyingly dark passage.",
            "treasure_room": "THE TREASURE ROOM! Glittering wealth everywhere!"
        }

    def show_title(self):
        """Display the game title screen"""
        clear()
        display_colored("=" * 60, "cyan")
        display_colored("THE LOST ARTIFACT", "bright cyan", bold=True)
        display_colored("A Text Adventure Game", "white", italic=True)
        display_colored("=" * 60, "cyan")
        display("")
        
        # Create a simple ASCII art
        temple_art = """
              /\\
             /  \\
            /____\\
           /|    |\\
          /_|____|_\\
         /__________\\
        /____________\\
        """
        
        display_colored(temple_art, "yellow")
        display("")
        display_colored("Explore the ancient temple, solve puzzles,", "green")
        display_colored("find the legendary Artifact of Aethelred!", "green")
        display("")

    def get_player_name(self):
        """Get the player's name"""
        display_colored("What is your name, adventurer?", "bright magenta")
        name = user_type_in("Name: ")
        if name and name.strip():
            self.player_name = name.strip()
        else:
            self.player_name = "Adventurer"
        display(f"\nWelcome, {self.player_name}! Let the adventure begin!\n")
        time.sleep(1)

    def describe_room(self, room_name, first_visit=True):
        """Describe the current room"""
        room = self.rooms[room_name]
        self.visited_rooms.add(room_name)
        
        display_colored(f"\n[{room['name']}]", "bright yellow", bold=True)
        
        if first_visit or room_name not in self.brief_descriptions:
            display(room['description'])
        else:
            display_colored(self.brief_descriptions[room_name], "33")
        
        # Show exits
        exits = list(room['exits'].keys())
        if exits:
            display_colored(f"\nExits: {', '.join(exits)}", "bright blue")
        
        # Show items
        if room['items']:
            display_colored(f"\nYou see: {', '.join(room['items'])}", "bright green")
        
        # Special room descriptions
        if room_name == "dark_passage" and not self.has_torch:
            display_colored("\n\033[1;31mWARNING: It's too dark to proceed! You need a light source.\033[0m", "red", bold=True)
        
        display("")

    def process_command(self, command):
        """Process player commands"""
        cmd = command.lower().strip()
        parts = cmd.split()
        
        if not parts:
            return
        
        action = parts[0]
        
        # Movement commands
        if action in ["go", "move", "walk", "north", "south", "east", "west"]:
            if action in ["north", "south", "east", "west"]:
                direction = action
            elif len(parts) > 1:
                direction = parts[1]
            else:
                display("Go where?")
                return
            
            self.move_player(direction)
        
        # Look around
        elif action in ["look", "l"]:
            self.describe_room(self.current_room, first_visit=False)
        
        # Take item
        elif action == "take":
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.take_item(item_name)
            else:
                display("Take what?")
        
        # Use item
        elif action == "use":
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.use_item(item_name)
            else:
                display("Use what?")
        
        # Inventory
        elif action in ["inv", "inventory", "i"]:
            self.show_inventory()
        
        # Health
        elif action in ["health", "h", "hp"]:
            self.show_health()
        
        # Score
        elif action == "score":
            self.show_score()
        
        # Map
        elif action == "map":
            self.show_map()
        
        # Help
        elif action in ["help", "?"]:
            display(self.messages["help"])
        
        # Quit
        elif action in ["quit", "exit", "q"]:
            confirm = user_type_in("Are you sure you want to quit? (yes/no): ")
            if confirm and confirm.lower() in ["y", "yes"]:
                self.game_over = True
                display("\nThanks for playing!")
        
        else:
            display("I don't understand that. Type 'help' for commands.")

    def move_player(self, direction):
        """Move the player to a new room"""
        room = self.rooms[self.current_room]
        
        if direction in room["exits"]:
            new_room = room["exits"][direction]
            
            # Check for special conditions
            if new_room == "dark_passage" and not self.has_torch:
                display_colored("\n\033[1;31mYou stumble in the darkness and hurt yourself!\033[0m", "red")
                self.health -= 20
                display(f"Health: {self.health}")
                
                if self.health <= 0:
                    self.game_over = True
                    display(self.messages["game_over"].format(score=self.score))
                return
            
            self.current_room = new_room
            self.score += 5  # Points for exploring
            self.describe_room(new_room, first_visit=new_room not in self.visited_rooms)
            
            # Random event chance
            if random.random() < 0.3:  # 30% chance
                self.random_event()
        
        else:
            display(f"You can't go {direction} from here.")

    def take_item(self, item_name):
        """Take an item from the current room"""
        room = self.rooms[self.current_room]
        room_items = room["items"]
        
        # Check if item exists in room
        found_item = None
        for item in room_items:
            if item_name.lower() in item.lower():
                found_item = item
                break
        
        if found_item:
            room["items"].remove(found_item)
            self.inventory.append(found_item)
            display_colored(f"\nYou take the {found_item}.", "green")
            self.score += 10
            
            # Special items
            if found_item == "torch":
                self.has_torch = True
                display_colored("The torch flickers to life!", "yellow")
            elif found_item == "old book":
                self.has_map = True
                display_colored("Inside the book, you find a map of the temple!", "bright cyan")
            elif found_item == "stone tablet":
                display_colored("The tablet has an inscription: 'Seek the four guardians'", "cyan")
        else:
            display(f"There is no {item_name} here.")

    def use_item(self, item_name):
        """Use an item from inventory"""
        # Check if player has the item
        has_item = False
        for item in self.inventory:
            if item_name.lower() in item.lower():
                has_item = item
                break
        
        if not has_item:
            display(f"You don't have {item_name}.")
            return
        
        room = self.rooms[self.current_room]
        
        # Special item uses
        if "torch" in item_name.lower() and self.current_room == "dark_passage":
            display_colored("\nThe torch illuminates the dark passage! You can see the way forward.", "yellow")
            display("The passage leads to a treasure room!")
        
        elif "herbs" in item_name.lower() and self.health < 100:
            self.health = min(100, self.health + 30)
            self.inventory.remove(has_item)
            display_colored(f"\nYou use the healing herbs. Health: {self.health}", "green")
        
        elif "rusted sword" in item_name.lower():
            display_colored("\nYou swing the sword. It's rusty but still sharp!", "cyan")
        
        elif "strange mushroom" in item_name.lower():
            display_colored("\nYou eat the glowing mushroom...", "magenta")
            if random.random() < 0.5:
                self.health -= 20
                display_colored("It was poisonous! You feel sick.", "red")
            else:
                self.health += 25
                display_colored("You feel strangely energized!", "green")
            self.inventory.remove(has_item)
            display(f"Health: {self.health}")
        
        else:
            display(f"You use the {has_item}, but nothing happens.")

    def show_inventory(self):
        """Display player's inventory"""
        if self.inventory:
            display_colored("\n=== INVENTORY ===", "bright cyan")
            for item in self.inventory:
                display(f"  • {item}")
        else:
            display("Your inventory is empty.")

    def show_health(self):
        """Display player's health"""
        health_bar = "█" * (self.health // 10) + "░" * (10 - (self.health // 10))
        color = "green" if self.health > 50 else "yellow" if self.health > 25 else "red"
        
        display_colored(f"\nHealth: {self.health}/100", color)
        display_colored(f"[{health_bar}]", color)
        
        if self.health <= 30:
            display_colored("WARNING: Health is low! Find healing items!", "red", bold=True)

    def show_score(self):
        """Display player's score"""
        display_colored(f"\nScore: {self.score}", "bright yellow")
        
        # Give hints based on score
        if self.score < 50:
            display("Keep exploring to increase your score!")
        elif self.score < 100:
            display("You're making good progress!")
        else:
            display("Excellent! You're close to the treasure!")

    def show_map(self):
        """Show a map of visited rooms"""
        if not self.visited_rooms:
            display("You haven't explored anywhere yet!")
            return
        
        display_colored("\n=== TEMPLE MAP ===", "bright cyan")
        display_colored("(X = Current location, O = Visited)", "cyan")
        display("")
        
        # Simple grid representation
        room_positions = {
            "garden": (0, 0),
            "entrance": (1, 0),
            "main_hall": (2, 0),
            "library": (0, 1),
            "statue_room": (2, 1),
            "dark_passage": (0, 2),
            "treasure_room": (0, 3)
        }
        
        # Create a 4x4 grid
        for y in range(4):
            row = ""
            for x in range(3):
                room_here = None
                for room, (rx, ry) in room_positions.items():
                    if rx == x and ry == y:
                        room_here = room
                        break
                
                if room_here:
                    if room_here == self.current_room:
                        row += "[X] "
                    elif room_here in self.visited_rooms:
                        row += "[O] "
                    else:
                        row += "[ ] "
                else:
                    row += "    "
            display(row)
        
        display("")
        display_colored(f"Current room: {self.rooms[self.current_room]['name']}", "yellow")

    def random_event(self):
        """Random events that can happen when moving"""
        events = [
            ("You hear a distant echo...", "white"),
            ("A bat flies past your head!", "90"),
            ("Dust falls from the ceiling.", "white"),
            ("You see a glint in the shadows.", "yellow"),
            ("The ground rumbles slightly.", "white"),
            ("You hear whispering... or is it the wind?", "90")
        ]
        
        if random.random() < 0.2:  # 20% chance of event
            event, color = random.choice(events)
            display_colored(f"\n{event}", color)
            
            # Small chance of finding something
            if random.random() < 0.1:
                found_items = ["gold coin", "silver locket", "ancient coin"]
                item = random.choice(found_items)
                self.inventory.append(item)
                display_colored(f"You found a {item}!", "green")
                self.score += 5

    def check_puzzles(self):
        """Check and handle room-specific puzzles"""
        room = self.rooms[self.current_room]
        
        # Garden mushroom puzzle
        if self.current_room == "garden" and "strange mushroom" in self.inventory:
            display_colored("\nThe glowing mushrooms pulse with a soft light...", "magenta")
            response = user_type_in("Eat the mushroom? (yes/no): ")
            if response and response.lower() in ["y", "yes"]:
                if random.random() < 0.7:
                    self.health += 20
                    display_colored("The mushroom gives you a vision! You see a hidden path!", "bright green")
                else:
                    self.health -= 15
                    display_colored("The mushroom was poisonous!", "red")
                self.inventory.remove("strange mushroom")
        
        # Library riddle puzzle
        elif self.current_room == "library" and not self.solved_riddle:
            display_colored("\nThe open tome on the desk contains a riddle:", "cyan")
            display_colored("'I speak without a mouth and hear without ears.'", "bright cyan")
            display_colored("'I have no body, but I come alive with wind.'", "bright cyan")
            display_colored("'What am I?'", "bright cyan")
            
            answer = user_type_in("Your answer: ")
            if answer and answer.lower() in ["echo", "an echo"]:
                display_colored("\nCorrect! The bookcase slides open, revealing a passage!", "green")
                self.score += 50
                self.solved_riddle = True
                # Add the dark passage exit
                self.rooms["library"]["exits"]["north"] = "dark_passage"
            else:
                display_colored("\nNothing happens. The riddle remains unsolved.", "yellow")
        
        # Statue room puzzle
        elif self.current_room == "statue_room" and "torch" in self.inventory:
            display_colored("\nThe statues seem to be looking at something...", "yellow")
            display("One statue's hand is empty. Another holds a rusted bowl.")
            
            response = user_type_in("Place the torch in the statue's hand? (yes/no): ")
            if response and response.lower() in ["y", "yes"]:
                display_colored("\nThe torch fits perfectly! The statues' eyes glow red.", "yellow")
                display("A hidden compartment opens in the wall!")
                if "key" not in self.inventory:
                    self.inventory.append("ancient key")
                    display_colored("You find an ancient key!", "green")
                    self.has_key = True
        
        # Treasure room final puzzle
        elif self.current_room == "treasure_room" and "ancient key" in self.inventory:
            display_colored("\nThe Artifact of Aethelred is protected by a magical seal!", "bright yellow")
            response = user_type_in("Use the ancient key? (yes/no): ")
            if response and response.lower() in ["y", "yes"]:
                display_colored("\nThe key turns with a satisfying click!", "green")
                display_colored("The magical seal dissipates!", "bright green")
                display_colored("You have obtained the Artifact of Aethelred!", "bright yellow", bold=True)
                self.score += 1000
                self.game_over = True
                self.show_ending()

    def show_ending(self):
        """Show the winning ending"""
        clear()
        display(self.messages["win"].format(
            name=self.player_name,
            score=self.score,
            health=self.health
        ))
        display("")
        display_colored("THE END", "bright cyan", bold=True)
        display("")
        
        # Show final stats
        display_colored("=== FINAL STATISTICS ===", "bright yellow")
        display(f"Player: {self.player_name}")
        display(f"Final Score: {self.score}")
        display(f"Final Health: {self.health}")
        display(f"Rooms Explored: {len(self.visited_rooms)}/{len(self.rooms)}")
        display(f"Items Collected: {len(self.inventory)}")
        display("")
        
        if self.score >= 1000:
            display_colored("PERFECT SCORE! Legendary Adventurer!", "bright magenta", bold=True)
        elif self.score >= 500:
            display_colored("Great Success! Master Explorer!", "green", bold=True)
        else:
            display_colored("Well done! Novice Explorer!", "yellow", bold=True)
        
        display("")
        display_colored("Thank you for playing The Lost Artifact!", "cyan")

    def play(self):
        """Main game loop"""
        self.show_title()
        self.get_player_name()
        display(self.messages["help"])
        display("\n" + "="*60)
        display_colored("Press Enter to begin your adventure...", "bright white")
        user_type_in("")
        
        # Start in the entrance
        self.describe_room(self.current_room)
        
        # Main game loop
        while not self.game_over:
            # Check for death
            if self.health <= 0:
                display(self.messages["game_over"].format(score=self.score))
                break
            
            # Check for puzzles in current room
            self.check_puzzles()
            
            # Get player command
            command = user_type_in("> ")
            
            if command:
                self.process_command(command)
            
            # Small chance to lose health (danger of temple)
            if random.random() < 0.1:  # 10% chance per turn
                self.health -= random.randint(1, 5)
                if self.health <= 0:
                    display_colored("\nThe temple's dangers have overcome you...", "red")
                    display(self.messages["game_over"].format(score=self.score))
                    break
            
            # Check for win condition
            if "Artifact of Aethelred" in self.inventory:
                self.game_over = True
                self.show_ending()
                break
        
        # Game over
        display("")
        play_again = user_type_in("Play again? (yes/no): ")
        if play_again and play_again.lower() in ["y", "yes"]:
            return True
        return False


def main_game():
    """Main game function to be passed to run()"""
    display_colored("\nInitializing The Lost Artifact...", "cyan")
    time.sleep(1)
    
    while True:
        game = AdventureGame()
        play_again = game.play()
        
        if not play_again:
            display_colored("\nFarewell, adventurer!", "bright cyan")
            time.sleep(2)
            break
        else:
            display_colored("\nStarting new adventure...", "cyan")
            time.sleep(1)
            clear()

def start_game():
    """Start the adventure game with the Py2GUI framework"""
    # Set a theme for the game
    set_theme("dark")
    
    # Welcome message
    clear()
    display_colored("=" * 60, "bright cyan")
    display_colored("THE LOST ARTIFACT - TEXT ADVENTURE", "bright cyan", bold=True)
    display_colored("=" * 60, "bright cyan")
    display("")
    display("A game of exploration, puzzles, and discovery!")
    display("Type 'help' at any time for commands.")
    display("")
    
    # Start the game
    main_game()
    
    # Ask if user wants to exit
    display("")
    response = user_type_in("Return to main menu? (yes/no): ")
    if response and response.lower() in ["y", "yes"]:
        return
    else:
        exit_gui()

# For direct execution
if __name__ == "__main__":
    # Create a wrapper that uses the Py2GUI framework
    def game_wrapper():
        start_game()
    
    # Run the game with the GUI framework
    run(game_wrapper)
