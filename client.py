import socketio, threading
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
        self.root.geometry("1280x720")
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        threading.Thread(target=self.run_socket, daemon=True).start()
        self.guessed_letters = []

        self.leaderboard = Frame(self.root)
        self.leaderboard.grid(row=0, column=0, rowspan=4, sticky=NSEW)
        self.leaderboard.columnconfigure(0, weight=1)
        self.header = Label(self.leaderboard, fg="white", bg="black", text="Waiting...", font=("Comic Sans MS", 20))
        self.header.grid(row=0, column=0, sticky='ew')
        self.leaderboard_frames = []
        for _ in range(10):
            f = Frame(self.leaderboard)
            f.rowconfigure((0, 1), weight=1)
            f.columnconfigure((0, 1, 2, 3), weight=1)
            self.leaderboard_frames.append(f)
        

        self.display_theme = Label(self.root, text="Game hasn't started yet", font=("Comic Sans MS", 50))
        self.display_theme.grid(row=0, column=1, columnspan=2, sticky=NSEW)
        self.display_word = Label(self.root, font=("Comic Sans MS", 30))
        self.display_word.grid(row=1, column=1, columnspan=2, sticky=NSEW)

        self.keyboard = Frame(self.root)
        self.keyboard.grid(row=2, column=1, sticky=NSEW)
        

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
                btn = Button(self.keyboard, text=key, command=guess)
                self.keybuttons[key] = btn
                btn.grid(row=row, column=col, sticky=NSEW)
        
        self.root.columnconfigure(1, weight=3)
        self.root.columnconfigure((0, 2), weight=1)
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
        if msg['type'] == 'leaderboard_update':
            print(msg)
            n = 0
            for player in msg['standings']:
                try:
                    print(player)
                    self.leaderboard_frames[n].grid(row=n+1, column=0, sticky='ew')
                    Label(self.leaderboard_frames[n], text=player[0], font=("Comic Sans MS", 15)).grid(row=0, column=0)
                    Label(self.leaderboard_frames[n], text=player[1], font=("Comic Sans MS", 15)).grid(row=1, column=0)
                    Label(self.leaderboard_frames[n], text=player[2], font=("Comic Sans MS", 20)).grid(row=0, column=3, rowspan=2)
                    n += 1
                except IndexError as e:
                    print(e)
                
    
    def on_close(self):
        self.socketclient.send({'type': 'quit'})
        self.root.destroy()
    

HangmanClient()