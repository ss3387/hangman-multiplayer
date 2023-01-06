import socketio, threading, turtle, time
from tkinter import *
from tkinter import simpledialog, ttk

class HangmanClient:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.withdraw()
        self.url = simpledialog.askstring(title="Connect", prompt="Enter url")
        if self.url:
            self.name = simpledialog.askstring(title="Name", prompt="Enter your name")
            if self.name: self.start_application()
    
    def run_socket(self):

        self.socketclient = socketio.Client()
        self.socketclient.connect(self.url)
        self.socketclient.send({'type': 'join', 'name': self.name})

        @self.socketclient.on('message')
        def on_message(msg):
            self.handle_message(msg)

    def start_application(self):
        self.root.deiconify()
        self.root.title("Hangman")
        self.root.geometry("1280x720")
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.configure(background="white")

        
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

        self.display_theme = Label(self.root, text="Game starts if there is more than 1 player", font=("Comic Sans MS", 35), bg="white", fg="black")
        self.display_theme.grid(row=0, column=1, columnspan=2, sticky=NSEW)
        self.display_word = Label(self.root, font=("Comic Sans MS", 30), bg="white", fg="black")
        self.display_word.grid(row=1, column=1, columnspan=2, sticky=NSEW)

        self.hangman = Canvas(self.root)
        self.hangman.grid(row=2, column=2, rowspan=2, sticky=NSEW)
        self.hangman_screen = turtle.TurtleScreen(self.hangman)
        self.animator = turtle.RawTurtle(self.hangman)
        self.animator.speed(10)
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
                        if Entry == type(event.widget):
                            return
                    except AttributeError:
                        guessed_letter = event
                    guessed_letter = guessed_letter.replace(' ', '')
                    if guessed_letter and not(guessed_letter in self.guessed_letters):
                        self.guessed_letters.append(guessed_letter)
                        self.socketclient.send({'type': 'guess', 'guess': guessed_letter})
                btn = Button(self.keyboard, text=key.upper(), command=guess, highlightbackground="black", font=('Comic Sans MS', 20), disabledforeground="black")
                self.keybuttons[key] = btn
                btn.grid(row=row, column=col, padx=2, pady=2, ipady=5, sticky=NSEW)
        
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("TProgressbar", thickness=50, background="#378D99", foreground="#378D99", troughcolor="#2d2d2d")
        self.time_bar = ttk.Progressbar(self.keyboard, orient=HORIZONTAL, mode='determinate', value=100, style="TProgressbar")
        #self.time_bar.grid(row=3, column=0, columnspan=10, sticky=NSEW)
        self.display_time = Label(self.keyboard, font=("Comic Sans MS", 25), bg="white", fg="black")

        self.chatting_frame = Frame(self.root, background="white", highlightthickness=3, highlightcolor="black")
        self.chatting_frame.grid(row=3, column=1, sticky=NSEW, padx=5, pady=5)
        self.chatting_frame.rowconfigure(0, weight=8)
        self.chatting_frame.rowconfigure(1, weight=1)
        self.chatting_frame.columnconfigure(0, weight=1)

        self.chat = Text(self.chatting_frame, font=("Calibri", 20), bg="white", fg="black", height=1, width=1, highlightthickness=0)
        self.chat.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        self.chat.bind('<Button>', lambda _: 'break')

        self.chat_input = Entry(self.chatting_frame, font=("Comic Sans MS", 15), bg="white", fg="black", insertbackground="black")
        self.chat_input.grid(row=1, column=0, sticky=EW, padx=5)
        self.chat_input.insert(0, "Type something to chat...")
        self.chat_input.bind('<Button>', self.focus)
        self.chat_input.bind('<Return>', self.send_chat)
        self.chat_input.bind('<Escape>', self.unfocus)
        self.chatting_frame.bind('<Leave>', self.unfocus)

        self.root.columnconfigure((0, 1, 2), weight=2)
        self.root.rowconfigure(3, weight=1)
        self.root.bind('<KeyRelease>', guess)

        self.keyboard.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1)
        self.keyboard.rowconfigure((0, 1, 2, 3, 4), weight=1)
        
        threading.Thread(target=self.run_socket, daemon=True).start()

        self.root.mainloop()
    
    def unfocus(self, *args):
        self.chat_input['bg'] = 'white'
        self.root.focus()
    
    def focus(self, *args):
        self.chat_input['bg'] = '#f6f6f6'
        if self.chat_input.get() == "Type something to chat...": self.chat_input.delete(0, END)

    def send_chat(self, *args):
        text = self.chat_input.get().replace(' ', '')
        if len(text) > 0: 
            self.socketclient.send({'type': 'chat', 'message': text})
            self.chat_input.delete(0, END)
        self.root.focus()

    def handle_message(self, msg):
        if msg['type'] == 'new_puzzle':
            self.display_theme['text'] = msg['theme']
            self.display_word['text'] = ''.join(msg['split_word'])
            self.header['text'] = f"Puzzle {msg['puzzle_number']} of 5"
            self.guessed_letters.clear()
            for button in self.keybuttons.values():
                button['highlightbackground'] = "black"
                button['state'] = NORMAL
        if msg['type'] == 'guess':
            self.display_word['text'] = ''.join(msg['split_word'])
            self.keybuttons[msg['guess']]['state'] = 'disabled'
            if not msg['guessed']:
                self.keybuttons[msg['guess']]['highlightbackground'] = "red"
                self.display_tries['text'] = f"Tries Left: {msg['tries']}"
                threading.Thread(target=lambda: self.do_animation(msg['tries']), daemon=True).start()
            else:
                self.keybuttons[msg['guess']]['highlightbackground'] = "green"
                
        if msg['type'] == 'leaderboard_update':
            n = 0
            for f in self.leaderboard_frames: 
                for w in f.winfo_children(): w.destroy()
            
            for player in msg['standings']:
                try:
                    if n % 2 == 1:
                        color = "#eeeeee"
                    else:
                        color = "#e1e1e1"
                    self.leaderboard_frames[n]['bg'] = color
                    self.leaderboard_frames[n].grid(row=n+1, column=0, sticky='ew')
                    Label(self.leaderboard_frames[n], text=player[0].upper(), font=("Comic Sans MS", 15), bg=color, fg="black").grid(row=0, column=0)
                    Label(self.leaderboard_frames[n], text=player[1], font=("Comic Sans MS", 15), bg=color, fg="black").grid(row=1, column=0)
                    if player[2] == '✓' or player[2] == '𐄂':
                        Label(self.leaderboard_frames[n], text=player[2], font=("Arial", 30), bg=color, fg="black").grid(row=0, column=3, rowspan=2)
                    else: 
                        Label(self.leaderboard_frames[n], text=player[2], font=("Comic Sans MS", 20), bg=color, fg="black").grid(row=0, column=3, rowspan=2)
                    n += 1
                except IndexError as e:
                    continue
        
        if msg['type'] == 'chat':
            self.chat.insert(END, msg['message'])
            self.chat.see('end')

        if msg['type'] == 'time_update':
            self.time_bar.grid(row=4, column=0, columnspan=10, sticky=NSEW)
            self.display_time.grid(row=3, column=0, columnspan=10, sticky=NSEW)
            self.time_bar['value'] = (msg['time']/msg['total'])*100
            if msg['keyword'] == 'puzzle':
                self.display_time['text'] = f"Time Left: {msg['time']} seconds"
            elif msg['keyword'] == 'w_puzzle':
                self.display_time['text'] = f"New puzzle in: {msg['time']} seconds"
            else:
                self.display_time['text'] = f"{msg['winners'].upper()} won this round. Next round in: {msg['time']} seconds"
        
        if msg['type'] == 'wait':
            self.time_bar.grid(row=4, column=0, columnspan=10, sticky=NSEW)
            self.display_time.grid(row=3, column=0, columnspan=10, sticky=NSEW)
            self.time_bar['value'] = (msg['time']/msg['total'])*100
            self.display_time['text'] = f"Time Left: {msg['time']}"
        
        if msg['type'] == 'split_word_update':
            self.display_word['text'] = ''.join(msg['split_word'])
            self.display_tries['text'] = "Tries Left: "
            self.time_bar.grid_forget()
            self.display_time.grid_forget()
            self.animator.clear()
            self.animator.setheading(0)
        
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
        self.animator.left(eval(left_limb + angle))
        self.animator.forward(distance)
        self.animator.left(eval(left_limb + '-' + angle))
        self.move(*body_pos)
        if left_limb: self.move(self.animator.pos()[0], self.animator.pos()[1] - 40)

    def do_animation(self, tries):
        while True:
            if len(self.animation_queue) <= 1:
                self.animation_queue.append(self.animations[tries])
                break
            time.sleep(0.25)
        while True:
            if len(self.animation_queue) == 1:
                self.animation_queue[0]()
                self.animation_queue.pop(0)
                break
            time.sleep(0.25)
    

HangmanClient()