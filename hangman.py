import socketio, threading, turtle
from tkinter import *
from tkinter import simpledialog

class HangmanClient:
    def __init__(self) -> None:
        #self.address = simpledialog.askstring(title="Connect", prompt="Enter server address")
        self.address = 'http://127.0.0.1:8080'
        if self.address:
            self.name = simpledialog.askstring(title="Name", prompt="Enter your name")
            if self.name: self.start_application()
    
    def run_socket(self):

        self.socketclient = socketio.Client()
        self.socketclient.connect(self.address)
        self.socketclient.send({'type': 'join', 'name': self.name})

        @self.socketclient.on('message')
        def on_message(msg):
            self.handle_message(msg)

    def start_application(self):
        self.root = Tk()
        self.root.title("Hangman")
        self.root.geometry("1280x720")
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.configure(background="white")

        threading.Thread(target=self.run_socket, daemon=True).start()
        self.guessed_letters = []

        self.leaderboard = Frame(self.root, background="#ededed")
        self.leaderboard.grid(row=0, column=0, rowspan=4, sticky=NSEW)
        self.leaderboard.columnconfigure(0, weight=1)
        self.header = Label(self.leaderboard, fg="white", bg="black", text="Waiting...", font=("Comic Sans MS", 20))
        self.header.grid(row=0, column=0, ipady=5, sticky='ew')
        self.leaderboard_frames = []
        for _ in range(10):
            f = Frame(self.leaderboard)
            f.rowconfigure((0, 1), weight=1)
            f.columnconfigure((0, 1, 2, 3), weight=1)
            self.leaderboard_frames.append(f)

        self.display_theme = Label(self.root, text="Game starts if there is more than 1 player", font=("Comic Sans MS", 40), bg="white", fg="black")
        self.display_theme.grid(row=0, column=1, columnspan=2, sticky=NSEW)
        self.display_word = Label(self.root, font=("Comic Sans MS", 30), bg="white", fg="black")
        self.display_word.grid(row=1, column=1, columnspan=2, sticky=NSEW)

        self.hangman = Canvas(self.root)
        self.hangman.grid(row=2, column=2, rowspan=2, sticky=NSEW)
        self.hangman_screen = turtle.TurtleScreen(self.hangman)
        self.animator = turtle.RawTurtle(self.hangman)
        self.animator.hideturtle()
        self.animator.pensize(5)
        self.animations = [
            lambda: self.draw_limb(self.animator.pos(), '30', 80, '-'),
            lambda: self.draw_limb(self.animator.pos(), '30', 80),
            lambda: self.draw_limb(self.animator.pos(), '120', 50, '-'),
            lambda: self.draw_limb(self.animator.pos(), '120', 50),
            self.draw_body, self.draw_head, self.draw_post
        ]
        self.animation_queue = []

        self.display_tries = Label(self.root, text="Tries Left: ", font=("Comic Sans MS", 30), bg="white", fg="black")
        self.hangman.create_window(50, -25, window=self.display_tries)

        self.keyboard = Frame(self.root, bg="white", padx=10)
        self.keyboard.grid(row=2, column=1, sticky='nsw')
        
        self.keys = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm']
        ]

        self.keybuttons = {}
        
        for row in range(3):
            for col in range(len(self.keys[row])):
                key = self.keys[row][col]
                def guess(event=key):
                    try:
                        guessed_letter = event.char
                    except AttributeError:
                        guessed_letter = event
                    guessed_letter = guessed_letter.replace(' ', '')
                    if guessed_letter and not(guessed_letter in self.guessed_letters):
                        self.guessed_letters.append(guessed_letter)
                        self.socketclient.send({'type': 'guess', 'guess': guessed_letter})
                btn = Button(self.keyboard, text=key.upper(), command=guess, highlightbackground="white", font=("Comic Sans MS", 20))
                self.keybuttons[key] = btn
                btn.grid(row=row, column=col, padx=2, pady=2, ipady=5, sticky=NSEW)

        
        self.root.columnconfigure((0, 1, 2), weight=2)
        self.root.rowconfigure(3, weight=1)
        self.root.bind('<KeyRelease>', guess)

        self.keyboard.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1)
        self.keyboard.rowconfigure((0, 1, 2), weight=1)
        

        self.root.mainloop()
    
    
    def handle_message(self, msg):
        if msg['type'] == 'new_puzzle':
            self.display_theme['text'] = msg['theme']
            self.display_word['text'] = ''.join(msg['split_word'])
            self.header['text'] = f"Puzzle {msg['puzzle_number']}"
        if msg['type'] == 'guess':
            self.display_word['text'] = ''.join(msg['split_word'])
            if not msg['guessed']:
                self.animation_queue.append(self.animations[msg['tries']])
                while True:
                    if len(self.animation_queue) == 1:
                        self.animation_queue[0]()
                        self.animation_queue.pop(0)
                        break
        if msg['type'] == 'leaderboard_update':
            print(msg)
            n = 0
            for f in self.leaderboard_frames: 
                for w in f.winfo_children(): w.destroy()
            
            for player in msg['standings']:
                try:

                    print(player)
                    if n % 2 == 1:
                        color = "#eeeeee"
                    else:
                        color = "#e1e1e1"
                    self.leaderboard_frames[n]['bg'] = color
                    self.leaderboard_frames[n].grid(row=n+1, column=0, sticky='ew')
                    Label(self.leaderboard_frames[n], text=player[0], font=("Comic Sans MS", 15), bg=color, fg="black").grid(row=0, column=0)
                    Label(self.leaderboard_frames[n], text=player[1], font=("Comic Sans MS", 15), bg=color, fg="black").grid(row=1, column=0)
                    if player[2] == '✓' or player[2] == '𐄂':
                        Label(self.leaderboard_frames[n], text=player[2], font=("Arial", 30), bg=color, fg="black").grid(row=0, column=3, rowspan=2)
                    else: 
                        Label(self.leaderboard_frames[n], text=player[2], font=("Comic Sans MS", 20), bg=color, fg="black").grid(row=0, column=3, rowspan=2)
                    n += 1
                except IndexError as e:
                    print(e)
        
    def on_close(self):
        self.socketclient.send({'type': 'quit'})
        self.root.destroy()
    
    def move(self, *args):
        self.animator.penup()
        self.animator.goto(*args)
        self.animator.pendown()

    def draw_post(self):
        self.move(75, -350)
        self.animator.forward(100)
        self.move(125, -350)
        self.animator.left(90)
        self.animator.forward(250)
        self.move(self.animator.pos()[0], self.animator.pos()[1] - 20)
        self.animator.goto(self.animator.pos()[0] - 20, self.animator.pos()[1] + 20)
        self.move(self.animator.pos()[0] + 20, self.animator.pos()[1])
        self.animator.left(90)
        self.animator.forward(150)
        self.animator.left(90)
        self.animator.forward(30)
    
    def draw_head(self):
        self.animator.right(90)
        self.animator.circle(15)
        self.move(self.animator.pos()[0], self.animator.pos()[1] - 30)

    def draw_body(self):
        self.animator.left(90)
        self.animator.forward(75)
        self.move(self.animator.pos()[0], self.animator.pos()[1] + 40)

    def draw_limb(self, body_pos, angle, distance, left_limb=""):
        body_pos = self.animator.pos()
        print(left_limb)
        self.animator.left(eval(left_limb + angle))
        self.animator.forward(distance)
        self.animator.left(eval(left_limb + '-' + angle))
        self.move(*body_pos)
        if left_limb: self.move(self.animator.pos()[0], self.animator.pos()[1] - 40)
    

HangmanClient()