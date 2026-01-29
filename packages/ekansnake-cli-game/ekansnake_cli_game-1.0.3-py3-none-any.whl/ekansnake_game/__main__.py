import curses
import random
import time
import os

# --- Configuration ---
SNAKE_CHAR = 'O' 
FOOD_CHAR = '🍥'
OBSTACLE_CHAR = '🧱'
BG_CHAR = ' '

# Speed configuration
INITIAL_SPEED = 150  
SPEED_INCREASE = 2   
HIGHSCORE_FILE = "highscore.txt"
NUM_OBSTACLES = 10  

def get_high_score():
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            return int(f.read().strip())
    except ValueError:
        return 0

def save_high_score(score):
    with open(HIGHSCORE_FILE, 'w') as f:
        f.write(str(score))

def get_random_coord(sh, sw, occupied_coords):
    """
    Generates a random coordinate (y, x).
    Safe zones: 1 to sh-2 (height) and 1 to sw-2 (width) to avoid borders.
    """
    while True:
        y = random.randint(1, sh - 2)
        x = random.randint(1, sw - 2)
        if [y, x] not in occupied_coords:
            return [y, x]

def play_one_round(stdscr):
    # --- Setup Round ---
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(INITIAL_SPEED)
    
    sh, sw = stdscr.getmaxyx()
    
    high_score = get_high_score()
    score = 0
    
    # Snake starts in middle
    snake = [
        [sh // 2, sw // 4],
        [sh // 2, sw // 4 - 1],
        [sh // 2, sw // 4 - 2]
    ]
    
    # Initial Obstacles Generation
    obstacles = []
    for _ in range(NUM_OBSTACLES):
        obstacles.append(get_random_coord(sh, sw, snake + obstacles))

    # Initial Food Generation
    food = get_random_coord(sh, sw, snake + obstacles)
    
    key = curses.KEY_RIGHT
    
    # --- Game Loop ---
    while True:
        next_key = stdscr.getch()
        prev_key = key
        
        # 1. Input Handling
        if next_key != -1:
            if next_key == curses.KEY_DOWN and prev_key != curses.KEY_UP: key = next_key
            elif next_key == curses.KEY_UP and prev_key != curses.KEY_DOWN: key = next_key
            elif next_key == curses.KEY_LEFT and prev_key != curses.KEY_RIGHT: key = next_key
            elif next_key == curses.KEY_RIGHT and prev_key != curses.KEY_LEFT: key = next_key

        # 2. Movement Calculation
        head = snake[0]
        new_head = [head[0], head[1]]

        if key == curses.KEY_DOWN: new_head[0] += 1
        elif key == curses.KEY_UP: new_head[0] -= 1
        elif key == curses.KEY_LEFT: new_head[1] -= 1
        elif key == curses.KEY_RIGHT: new_head[1] += 1

        # 3. Collision Logic
        if (new_head[0] <= 0 or new_head[0] >= sh - 1 or 
            new_head[1] <= 0 or new_head[1] >= sw - 1 or 
            new_head in snake or
            new_head in obstacles):
            
            if score > high_score:
                save_high_score(score)
            return score

        # 4. Move & Eat
        snake.insert(0, new_head)
        
        if snake[0] == food:
            score += 1
            
            # --- NEW FEATURE: Regenerate Obstacles ---
            obstacles = []
            for _ in range(NUM_OBSTACLES):
                # We pass 'snake' to ensure obstacles don't spawn on the snake body
                obstacles.append(get_random_coord(sh, sw, snake + obstacles))

            # --- Regenerate Food ---
            # Now we must pass 'snake' AND the 'new obstacles' so food doesn't overlap either
            food = get_random_coord(sh, sw, snake + obstacles)
            
            # Speed up
            cur_speed = max(30, INITIAL_SPEED - (score * SPEED_INCREASE))
            stdscr.timeout(cur_speed)
        else:
            tail = snake.pop()

        # 5. Rendering
        stdscr.clear() 
        stdscr.box()
        
        # Draw Title
        header = f" Score: {score} | High Score: {max(score, high_score)} "
        # Check width to prevent crash if window is too small
        if len(header) < sw:
            stdscr.addstr(0, 2, header)
        
        # Draw Obstacles
        for obs in obstacles:
            try:
                stdscr.addstr(obs[0], obs[1], OBSTACLE_CHAR)
            except curses.error: pass

        # Draw Snake
        for part in snake:
            try:
                stdscr.addstr(part[0], part[1], SNAKE_CHAR)
            except curses.error: pass

        # Draw Food (Last to ensure visibility)
        try:
            stdscr.addstr(food[0], food[1], FOOD_CHAR)
        except curses.error: pass
            
        stdscr.refresh()

def main_menu(stdscr):
    curses.curs_set(0)
    while True:
        final_score = play_one_round(stdscr)
        
        stdscr.nodelay(0) 
        sh, sw = stdscr.getmaxyx()
        
        msg_over = "GAME OVER"
        msg_score = f"Final Score: {final_score}"
        msg_opt = "Press 'p' to Play Again or 'q' to Quit"
        
        stdscr.clear()
        stdscr.box()
        
        try:
            stdscr.addstr(sh//2 - 2, sw//2 - len(msg_over)//2, msg_over, curses.A_BOLD)
            stdscr.addstr(sh//2, sw//2 - len(msg_score)//2, msg_score)
            stdscr.addstr(sh//2 + 2, sw//2 - len(msg_opt)//2, msg_opt)
        except curses.error: pass
            
        stdscr.refresh()
        
        while True:
            key = stdscr.getch()
            if key in [ord('p'), ord('P')]:
                break 
            elif key in [ord('q'), ord('Q')]:
                return 

if __name__ == "__main__":
    try:
        curses.wrapper(main_menu)
    except curses.error as e:
        print(f"Terminal Error: {e}")
        print("Try resizing your terminal window to be larger.")