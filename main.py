import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
import os
# Add Pillow imports
from PIL import Image, ImageTk

def parse_mcq_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    # Split by double newlines into questions
    blocks = content.split('\n\n')
    questions = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 6:
            question_text = lines[0]
            options = lines[1:5]
            answer = lines[5].replace('Answer: ', '').strip()
            questions.append({
                'question': question_text,
                'options': options,
                'answer': answer
            })
    return questions

class ModernMCQApp:
    def __init__(self, root, questions, show_options=True):
        self.root = root
        self.questions = questions
        self.current_question = 0
        self.show_options = show_options
        # Configure root window
        self.root.title("Space Quiz")
        self.root.geometry("900x650")
        self.root.configure(bg='#181c2b')
        # Load and resize rocket image for timer bar using Pillow
        self.rocket_img = None
        self.rocket_img_tk = None
        try:
            pil_img = Image.open("rocket.png")
            # Rotate -90 degrees (counterclockwise)
            pil_img = pil_img.rotate(90, expand=True)
            # Resize to higher resolution first for better quality, then downscale to 64px height
            h = 200  # upscale for anti-aliasing
            w = int(pil_img.width * (h / pil_img.height))
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
            # Downscale to final height
            final_h = 64
            final_w = int(pil_img.width * (final_h / pil_img.height))
            pil_img = pil_img.resize((final_w, final_h), Image.LANCZOS)
            self.rocket_img_tk = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Could not load or resize rocket.png: {e}")
        # Set up the main container with a starfield background
        self.main_frame = tk.Frame(root, bg='#181c2b')
        self.main_frame.pack(fill='both', expand=True, padx=0, pady=0)
        self.bg_canvas = tk.Canvas(self.main_frame, bg='#181c2b', highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.stars = []
        self.draw_starfield()
        self.root.bind('<Configure>', self.on_resize_starfield)
        self.main_frame.bind('<Configure>', self.on_resize_starfield)
        # Header (title only)
        self.setup_header()
        # Question display area
        self.setup_question_area()
        # Timer bar (now between question and options)
        self.setup_timer_bar()
        # Options area (only if show_options is True)
        if self.show_options:
            self.setup_options_area()
        # Navigation area
        self.setup_navigation()
        # Display first question
        self.display_question()
        # Bind keyboard shortcuts
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.root.bind('<space>', self.toggle_timer)
        self.root.bind('<Left>', lambda e: self.prev_question())
        self.root.bind('<Right>', lambda e: self.next_question())

    def draw_starfield(self):
        self.bg_canvas.delete('all')
        import random
        width = self.bg_canvas.winfo_width() or self.bg_canvas.winfo_reqwidth() or 900
        height = self.bg_canvas.winfo_height() or self.bg_canvas.winfo_reqheight() or 650
        self.stars = []
        for _ in range(120):
            x = random.randint(0, width)
            y = random.randint(0, height)
            
            r = random.choice([1, 1, 2])
            color = random.choice(['#fff', '#b3c6ff', '#e0e6ff', '#a3a8c9'])
            star = self.bg_canvas.create_oval(x, y, x+r, y+r, fill=color, outline=color)
            self.stars.append(star)

    def on_resize_starfield(self, event):
        # Always resize and redraw the starfield to fill the window
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas.config(width=self.main_frame.winfo_width(), height=self.main_frame.winfo_height())
        self.draw_starfield()

    def setup_header(self):
        header_frame = tk.Frame(self.main_frame, bg='#181c2b')
        header_frame.pack(fill='x', pady=(0, 20))
        # Title with rocket icon
        title_label = tk.Label(
            header_frame, 
            text="🚀 Space Quiz",
            font=('Orbitron', 32, 'bold'),
            fg='#fff',
            bg='#181c2b',
            pady=10
        )
        title_label.pack()

    def setup_timer_bar(self):
        self.timer_frame = tk.Frame(self.main_frame, bg='#181c2b')
        self.timer_frame.pack(fill='x', pady=(0, 20))
        self.timer_canvas = tk.Canvas(self.timer_frame, height=36, bg='#23264a', highlightthickness=0)
        self.timer_canvas.pack(fill='x', padx=40)
        self.timer_canvas.bind('<Button-1>', self.toggle_timer)
        self.timer_running = False
        self.timer_seconds = 30
        self.timer_remaining = self.timer_seconds
        self.timer_bar = None
        self.timer_text = None
        self.timer_update_job = None
        self.draw_timer_bar()

    def setup_question_area(self):
        question_frame = tk.Frame(self.main_frame, bg='#23264a', relief='flat', bd=1, highlightthickness=0)
        question_frame.pack(fill='x', pady=(0, 20), padx=40)
        # Add bottom border
        border = tk.Frame(question_frame, bg='#5f6fff', height=3)
        border.pack(side='bottom', fill='x')
        self.question_label = tk.Label(
            question_frame,
            text="",
            font=('Inter', 22, 'bold'),
            fg='#fff',
            bg='#23264a',
            wraplength=1280,
            justify='left',
            anchor='w',
            pady=18
        )
        self.question_label.pack(padx=20, pady=10)

    def setup_options_area(self):
        self.options_frame = tk.Frame(self.main_frame, bg='#181c2b')
        self.options_frame.pack(fill='both', expand=True, pady=(0, 20), padx=40)
        self.option_labels = []
        for i in range(4):
            option_frame = tk.Frame(self.options_frame, bg='#23264a', relief='flat', bd=1)
            option_frame.pack(fill='x', pady=8)
            label = tk.Label(
                option_frame,
                text="",
                font=('Inter', 18),
                fg='#fff',
                bg='#23264a',
                anchor='w',
                wraplength=700,
                padx=18,
                pady=10
            )
            label.pack(fill='x', padx=10, pady=2)
            self.option_labels.append(label)

    def setup_navigation(self):
        nav_frame = tk.Frame(self.main_frame, bg='#181c2b')
        nav_frame.pack(fill='x', padx=40)
        # Left side - Previous button
        self.prev_btn = tk.Button(
            nav_frame,
            text="← Previous",
            font=('Orbitron', 13, 'bold'),
            fg='#fff',
            bg='#3a3f5c',
            activebackground='#5f6fff',
            activeforeground='#fff',
            relief='flat',
            bd=0,
            padx=24,
            pady=12,
            command=self.prev_question,
            cursor='hand2',
            highlightthickness=0
        )
        self.prev_btn.pack(side='left', padx=(0, 10))
        # Center - Show answer button
        self.show_answer_btn = tk.Button(
            nav_frame,
            text="Reveal Answer",
            font=('Orbitron', 13, 'bold'),
            fg='#fff',
            bg='#27ae60',
            activebackground='#2ecc71',
            activeforeground='#fff',
            relief='flat',
            bd=0,
            padx=24,
            pady=12,
            command=self.show_answer,
            cursor='hand2',
            highlightthickness=0
        )
        # self.show_answer_btn.pack(side='left', padx=(10, 10))
        # Right side - Next button
        self.next_btn = tk.Button(
            nav_frame,
            text="Next →",
            font=('Orbitron', 13, 'bold'),
            fg='#fff',
            bg='#3a3f5c',
            activebackground='#5f6fff',
            activeforeground='#fff',
            relief='flat',
            bd=0,
            padx=24,
            pady=12,
            command=self.next_question,
            cursor='hand2',
            highlightthickness=0
        )
        self.next_btn.pack(side='right', padx=(10, 0))
        # Bind hover effects for navigation buttons
        for btn in [self.prev_btn, self.next_btn, self.show_answer_btn]:
            btn.bind('<Enter>', lambda e, b=btn: self.on_button_hover(b, True))
            btn.bind('<Leave>', lambda e, b=btn: self.on_button_hover(b, False))

    def on_button_hover(self, button, entering):
        if entering:
            if button == self.show_answer_btn:
                button.configure(bg='#2ecc71')
            else:
                button.configure(bg='#5f6fff')
        else:
            if button == self.show_answer_btn:
                button.configure(bg='#27ae60')
            else:
                button.configure(bg='#3a3f5c')

    def draw_timer_bar(self):
        self.timer_canvas.delete('all')
        width = self.timer_canvas.winfo_width() or 800
        percent = self.timer_remaining / self.timer_seconds
        fill_width = int(width * percent)
        bar_height = 36
        # Glowing energy bar effect
        if fill_width > 0:
            self.timer_canvas.create_rectangle(0, 0, fill_width, bar_height, fill='#5f6fff', outline='', width=0)
            self.timer_canvas.create_rectangle(0, 0, fill_width, bar_height, fill='', outline='#a3a8c9', width=2)
            self.timer_canvas.create_rectangle(0, 0, fill_width, bar_height, fill='', outline='#fff', width=1)
        # Outer border
        self.timer_canvas.create_rectangle(0, 0, width, bar_height, outline='#3a3f5c', width=2)
        # Timer text
        self.timer_text = self.timer_canvas.create_text(width//2, bar_height//2, text=f"{self.timer_remaining:02d} s", fill='#fff', font=('Inter', 14, 'bold'))
        # Rocket image just outside the bar
        if fill_width > 30 and self.rocket_img_tk is not None:
            rocket_x = min(fill_width + 30, width - 30)
            rocket_y = bar_height // 2
            self.timer_canvas.create_image(rocket_x, rocket_y, image=self.rocket_img_tk, anchor='center')

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def pause_timer(self):
        self.timer_running = False
        if self.timer_update_job:
            self.root.after_cancel(self.timer_update_job)
            self.timer_update_job = None

    def reset_timer(self):
        self.pause_timer()
        self.timer_remaining = self.timer_seconds
        self.draw_timer_bar()

    def toggle_timer(self, event=None):
        if self.timer_running:
            self.pause_timer()
        else:
            self.start_timer()

    def update_timer(self):
        if self.timer_running:
            if self.timer_remaining > 0:
                self.timer_remaining -= 1
                self.draw_timer_bar()
                self.timer_update_job = self.root.after(1000, self.update_timer)
            else:
                self.timer_running = False
                self.draw_timer_bar()

    def display_question(self):
        q = self.questions[self.current_question]
        
        # Update question text
        self.question_label.config(text=f"{q['question']}")
        
        # Update options (only if show_options is True)
        if self.show_options:
            for i, option in enumerate(q['options']):
                self.option_labels[i].config(text=f"{chr(65 + i)}. {option}")
        
        # Update navigation buttons
        self.prev_btn.config(state='normal' if self.current_question > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.current_question < len(self.questions) - 1 else 'disabled')
        # Reset timer
        self.reset_timer()



    def show_answer(self):
        q = self.questions[self.current_question]
        correct_answer = q['answer']
        
        # Find the index of the correct answer
        correct_index = None
        for i, option in enumerate(q['options']):
            if option.strip() == correct_answer.strip():
                correct_index = i
                break
        
        if correct_index is not None:
            if self.show_options:
                # Highlight correct answer in green
                self.option_labels[correct_index].configure(
                    bg='#27ae60',
                    fg='white'
                )
            
            # Show message
            messagebox.showinfo(
                "Correct Answer",
                f"The correct answer is: {chr(65 + correct_index)}. {q['options'][correct_index]}"
            )
        else:
            messagebox.showwarning(
                "Answer Not Found",
                f"Could not find the answer '{correct_answer}' in the options."
            )

    def prev_question(self):
        if self.current_question > 0:
            self.current_question -= 1
            self.display_question()

    def next_question(self):
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            self.display_question()

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)

def select_file_and_run():
    filename = filedialog.askopenfilename(
        title="Select MCQ File",
        filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')]
    )
    if filename:
        try:
            questions = parse_mcq_file(filename)
            if questions:
                # Ask user if they want to show options
                show_options = messagebox.askyesno(
                    "Display Options",
                    "Do you want to display the multiple choice options?\n\nClick 'Yes' to show options\nClick 'No' to show questions only"
                )
                root = tk.Tk()
                app = ModernMCQApp(root, questions, show_options=show_options)
                root.mainloop()
            else:
                messagebox.showwarning("No Questions", "No questions found in the selected file.")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
    else:
        messagebox.showinfo("No File Selected", "No file was selected.")

if __name__ == "__main__":
    select_file_and_run()
