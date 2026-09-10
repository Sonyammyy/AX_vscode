import tkinter as tk
import random

def get_color(number):
    if 1 <= number <= 10:
        return "#FFD700"  # Yellow
    elif 11 <= number <= 20:
        return "#1E90FF"  # Blue
    elif 21 <= number <= 30:
        return "#FF4500"  # Red
    elif 31 <= number <= 40:
        return "#808080"  # Gray
    elif 41 <= number <= 45:
        return "#32CD32"  # Green
    return "#FFFFFF"

def generate_numbers():
    # Clear previous results
    for widget in result_frame.winfo_children():
        widget.destroy()
    
    for i in range(5):
        # Generate 6 unique numbers, sorted
        numbers = sorted(random.sample(range(1, 46), 6))
        
        row_frame = tk.Frame(result_frame, bg="white")
        row_frame.pack(pady=5)
        
        for num in numbers:
            lbl = tk.Label(
                row_frame, 
                text=str(num), 
                bg=get_color(num), 
                fg="white" if num > 10 else "black",
                font=("Arial", 12, "bold"),
                width=3, 
                height=1,
                relief="raised"
            )
            lbl.pack(side=tk.LEFT, padx=5)

# Setup GUI
root = tk.Tk()
root.title("로또 번호 생성기")
root.geometry("400x300")
root.configure(bg="white")

btn = tk.Button(root, text="번호 생성", command=generate_numbers, font=("Arial", 14))
btn.pack(pady=20)

result_frame = tk.Frame(root, bg="white")
result_frame.pack()

root.mainloop()
