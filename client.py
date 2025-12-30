#an
from tkinter import *
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import time
import socket
import threading
import pickle

class LudoClient:
    def __init__(self, root, six_side_block, five_side_block, four_side_block, 
                 three_side_block, two_side_block, one_side_block, host='localhost', port=5555):
        self.window = root
        self.host = host
        self.port = port
        self.client_socket = None
        self.my_player_id = None
        self.my_color = None
        self.connected = False
        
        self.make_canvas = Canvas(self.window, bg="#4d4dff", width=800, height=630)
        self.make_canvas.pack(fill=BOTH, expand=1)

        # Containers
        self.made_red_coin = []
        self.made_green_coin = []
        self.made_yellow_coin = []
        self.made_sky_blue_coin = []
        self.red_number_label = []
        self.green_number_label = []
        self.yellow_number_label = []
        self.sky_blue_number_label = []
        self.block_value_predict = []
        self.total_people_play = []
        self.block_number_side = [one_side_block, two_side_block, three_side_block, 
                                  four_side_block, five_side_block, six_side_block]

        # Positions
        self.red_coord_store = [-1, -1, -1, -1]
        self.green_coord_store = [-1, -1, -1, -1]
        self.yellow_coord_store = [-1, -1, -1, -1]
        self.sky_blue_coord_store = [-1, -1, -1, -1]
        self.red_coin_position = [-1, -1, -1, -1]
        self.green_coin_position = [-1, -1, -1, -1]
        self.yellow_coin_position = [-1, -1, -1, -1]
        self.sky_blue_coin_position = [-1, -1, -1, -1]

        # Counters
        self.move_red_counter = 0
        self.move_green_counter = 0
        self.move_yellow_counter = 0
        self.move_sky_blue_counter = 0
        self.current_turn = -1
        self.current_dice_value = 0
        self.six_counter = 0
        self.six_with_overlap = 0
        
        # Setup
        self.board_set_up()
        self.instruction_btn_red()
        self.instruction_btn_sky_blue()
        self.instruction_btn_yellow()
        self.instruction_btn_green()
        
        for i in range(4):
            self.block_value_predict[i][1]['state'] = DISABLED
            self.block_value_predict[i][3]['state'] = DISABLED
        
        self.connect_to_server()

    # ============ NETWORK ============
    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            thread = threading.Thread(target=self.receive_messages, daemon=True)
            thread.start()
            #messagebox.showinfo("Kết nối", "Đã kết nối đến server!")
            print("[CLIENT] Đã kết nối thành công!")
        except Exception as e:
            #messagebox.showerror("Lỗi", f"Không thể kết nối: {e}")
            print("[CLIENT] Không thể kết nối!")
            self.window.destroy()

#trung- ui
    def show_start_button(self):
        if hasattr(self, 'start_btn'):
            return
        self.start_btn = Button(self.make_canvas, text="BẮT ĐẦU", 
                               bg="green", fg="white", font=("Arial", 16, "bold"),
                               command=self.start_game)
        self.start_btn.place(x=320, y=280)

    def start_game(self):
        self.send_data({'type': 'start_game'})
        if hasattr(self, 'start_btn'):
            self.start_btn.destroy()

    def update_turn_display(self):
        for i in range(4):
            self.block_value_predict[i][1]['state'] = DISABLED
        if self.current_turn == self.my_player_id:
            color_idx = ['red', 'sky_blue', 'yellow', 'green'].index(self.my_color)
            self.block_value_predict[color_idx][1]['state'] = NORMAL
        


#khang - controller
    def main_controller(self, color_coin, coin_number):
        """Điều khiển di chuyển quân cờ"""
        print(f"[CLIENT] Main controller: {color_coin}, coin: {coin_number}")
        
        if not self.input_filtering(coin_number):
            messagebox.showerror("Lỗi", "Vui lòng nhập số quân từ 1-4")
            return
        
        coin_idx = int(coin_number) - 1
        color_idx = ['red', 'sky_blue', 'yellow', 'green'].index(color_coin)
        
        # Lấy position và counter
        positions = {
            'red': (self.red_coin_position, self.move_red_counter),
            'sky_blue': (self.sky_blue_coin_position, self.move_sky_blue_counter),
            'yellow': (self.yellow_coin_position, self.move_yellow_counter),
            'green': (self.green_coin_position, self.move_green_counter)
        }
        
        position, counter = positions[color_coin]
        current_pos = position[coin_idx]
        
        print(f"[CLIENT] Quân {coin_idx+1}: position={current_pos}, counter={counter}")
        
        # Kiểm tra hợp lệ
        if current_pos == -1 and counter != 6:
            messagebox.showerror("Lỗi", "Phải ra 6 mới được xuất quân!")
            return
        
        if current_pos > -1 and current_pos + counter > 106:
            messagebox.showerror("Lỗi", "Không thể di chuyển quá đích!")
            return
        
        # Disable button Give
        self.block_value_predict[color_idx][3]['state'] = DISABLED
        
        # Di chuyển
        if current_pos == -1 and counter == 6:
            print(f"[CLIENT] Xuất quân {coin_idx+1}")
            self.move_coin_to_start(color_coin, coin_number)
        elif current_pos > -1:
            print(f"[CLIENT] Di chuyển quân {coin_idx+1} từ {current_pos}")
            self.move_coin_normal(color_coin, coin_number, counter)
        
        # Gửi đến server
        self.send_move_to_server(color_coin, coin_idx)
        
        # Reset counter sau khi di chuyển
        if color_coin == "red":
            self.move_red_counter = 0
        elif color_coin == "sky_blue":
            self.move_sky_blue_counter = 0
        elif color_coin == "yellow":
            self.move_yellow_counter = 0
        else:
            self.move_green_counter = 0