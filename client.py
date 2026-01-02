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

    def update_status(self, text):
        if not hasattr(self, 'status_label'):
            self.status_label = Label(self.make_canvas, text=text, 
                                     bg="#4d4dff", fg="white", font=("Arial", 12, "bold"))
            self.status_label.place(x=300, y=5)
        else:
            self.status_label.config(text=text)

    def make_prediction(self, color):
        if self.current_turn != self.my_player_id:
            return
        self.send_data({'type': 'roll_dice', 'color': color})
        


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
    def get_absolute_coord(self, color, relative_pos):
        """
        Chuyển đổi vị trí tương đối (1-52) sang tuyệt đối để check overlap
        """
        if relative_pos == -1:
            return -1
        
        if relative_pos >= 100:
            return relative_pos  # Đã vào home, không cần chuyển
        
        # Offset điểm xuất phát của mỗi màu
        start_offsets = {
            'red': 0,        # Bắt đầu từ ô 1
            'green': 13,     # Bắt đầu từ ô 14
            'yellow': 26,    # Bắt đầu từ ô 27
            'sky_blue': 39   # Bắt đầu từ ô 40
        }
        
        offset = start_offsets.get(color, 0)
        absolute = relative_pos + offset
        
        # Wrap around
        if absolute > 52:
            absolute = absolute - 52
        
        return absolute
    def send_move_to_server(self, color, coin_idx):
        """
        SỬA: Gửi cả position (tương đối) VÀ coord (tuyệt đối) lên server
        """
        coords_map = {
            'red': (self.red_coin_position, self.red_coord_store),
            'sky_blue': (self.sky_blue_coin_position, self.sky_blue_coord_store),
            'yellow': (self.yellow_coin_position, self.yellow_coord_store),
            'green': (self.green_coin_position, self.green_coord_store)
        }
        
        positions, coords = coords_map[color]
        
        # QUAN TRỌNG: Phải tính coord (tuyệt đối) từ position (tương đối)
        position_relative = positions[coin_idx]
        coord_absolute = self.get_absolute_coord(color, position_relative)
        
        print(f"[CLIENT] Gửi move: {color} coin {coin_idx+1}, pos={position_relative}, coord={coord_absolute}")
        
        self.send_data({
            'type': 'move_coin',
            'color': color,
            'coin_number': coin_idx,
            'new_position': position_relative,    # Vị trí tương đối (1-52 hoặc 100-106)
            'new_coord': coord_absolute            # Vị trí tuyệt đối để check overlap
        })
        
        self.send_data({'type': 'next_turn'})


    def input_filtering(self, coin_number):
        try:
            return 1 <= int(coin_number) <= 4
        except:
            return False

    # ============ BOARD & COINS ============
    def board_set_up(self):
        """Vẽ bàn cờ Ludo hoàn chỉnh"""
        # Cover Box
        self.make_canvas.create_rectangle(100, 15, 100 + (40 * 15), 15 + (40 * 15), width=6, fill="white")

        # 4 ô lớn màu
        self.make_canvas.create_rectangle(100, 15, 100+240, 15+240, width=3, fill="red")
        self.make_canvas.create_rectangle(100, (15+240)+(40*3), 100+240, (15+240)+(40*3)+(40*6), width=3, fill="#04d9ff")
        self.make_canvas.create_rectangle(340+(40*3), 15, 340+(40*3)+(40*6), 15+240, width=3, fill="#00FF00")
        self.make_canvas.create_rectangle(340+(40*3), (15+240)+(40*3), 340+(40*3)+(40*6), (15+240)+(40*3)+(40*6), width=3, fill="yellow")

        # Left 3 box
        self.make_canvas.create_rectangle(100, (15+240), 100+240, (15+240)+40, width=3)
        self.make_canvas.create_rectangle(100+40, (15 + 240)+40, 100 + 240, (15 + 240) + 40+40, width=3, fill="#F00000")
        self.make_canvas.create_rectangle(100, (15 + 240)+80, 100 + 240, (15 + 240) + 80+40, width=3)

        # Right 3 box
        self.make_canvas.create_rectangle(100+240, 15, 100 + 240+40, 15 + (40*6), width=3)
        self.make_canvas.create_rectangle(100+240+40, 15+40, 100+240+80, 15 + (40*6), width=3, fill="#00FF00")
        self.make_canvas.create_rectangle(100+240+80, 15, 100 + 240+80+40, 15 + (40*6), width=3)

        # Up 3 box
        self.make_canvas.create_rectangle(340+(40*3), 15+240, 340+(40*3)+(40*6), 15+240+40, width=3)
        self.make_canvas.create_rectangle(340+(40*3), 15+240+40, 340+(40*3)+(40*6)-40, 15+240+80, width=3, fill="yellow")
        self.make_canvas.create_rectangle(340+(40*3), 15+240+80, 340+(40*3)+(40*6), 15+240+120, width=3)

        # Down 3 box
        self.make_canvas.create_rectangle(100, (15 + 240)+(40*3), 100 + 240+40, (15 + 240)+(40*3)+(40*6), width=3)
        self.make_canvas.create_rectangle(100+240+40, (15 + 240)+(40*3), 100 + 240+40+40, (15 + 240)+(40*3)+(40*6)-40, width=3, fill="#04d9ff")
        self.make_canvas.create_rectangle(100 + 240+40+40, (15 + 240)+(40*3), 100 + 240+40+40+40, (15 + 240)+(40*3)+(40*6), width=3)

        # Vẽ các đường kẻ
        for i in range(5):
            # Left lines
            self.make_canvas.create_line(100+40*(i+1), 15+240, 100+40*(i+1), 15+240+(40*3), width=3)
            # Right lines
            self.make_canvas.create_line(100+240+(40*3)+40*(i+1), 15+240, 100+240+(40*3)+40*(i+1), 15+240+(40*3), width=3)
            # Up lines
            self.make_canvas.create_line(100+240, 15+40*(i+1), 100+240+(40*3), 15+40*(i+1), width=3)
            # Down lines
            self.make_canvas.create_line(100+240, 15+(40*6)+(40*3)+40*(i+1), 100+240+(40*3), 15+(40*6)+(40*3)+40*(i+1), width=3)

        # Ô trắng chứa quân cờ
        self.make_canvas.create_rectangle(100+20, 15+40-20, 100+40+60+40+60+20, 15+40+40+40+100-20, width=3, fill="white")
        self.make_canvas.create_rectangle(340+(40*3)+40-20, 15+40-20, 340+(40*3)+40+60+40+40+20+20, 15+40+40+40+100-20, width=3, fill="white")
        self.make_canvas.create_rectangle(100+20, 340+80-20+15, 100+40+60+40+60+20, 340+80+60+40+40+20+15, width=3, fill="white")
        self.make_canvas.create_rectangle(340+(40*3)+40-20, 340+80-20+15, 340+(40*3)+40+60+40+40+20+20, 340+80+60+40+40+20+15, width=3, fill="white")

        # Ô nhỏ chứa quân - Red (4 ô)
        coords_red = [(100+40, 15+40, 100+80, 15+80), (100+160, 15+40, 100+200, 15+80),
                      (100+160, 15+140, 100+200, 15+180), (100+40, 15+140, 100+80, 15+180)]
        for coord in coords_red:
            self.make_canvas.create_rectangle(*coord, width=3, fill="red")

        # Ô nhỏ chứa quân - Green (4 ô)
        coords_green = [(340+(40*3)+40, 15+40, 340+(40*3)+80, 15+80),
                        (340+(40*3)+160, 15+40, 340+(40*3)+200, 15+80),
                        (340+(40*3)+160, 15+140, 340+(40*3)+200, 15+180),
                        (340+(40*3)+40, 15+140, 340+(40*3)+80, 15+180)]
        for coord in coords_green:
            self.make_canvas.create_rectangle(*coord, width=3, fill="#00FF00")

        # Ô nhỏ chứa quân - Sky Blue (4 ô)
        coords_sky = [(100+40, 340+80+15, 100+80, 340+120+15),
                      (100+160, 340+80+15, 100+200, 340+120+15),
                      (100+160, 340+180+15, 100+200, 340+220+15),
                      (100+40, 340+180+15, 100+80, 340+220+15)]
        for coord in coords_sky:
            self.make_canvas.create_rectangle(*coord, width=3, fill="#04d9ff")

        # Ô nhỏ chứa quân - Yellow (4 ô)
        coords_yellow = [(340+(40*3)+40, 340+80+15, 340+(40*3)+80, 340+120+15),
                         (340+(40*3)+160, 340+80+15, 340+(40*3)+200, 340+120+15),
                         (340+(40*3)+160, 340+180+15, 340+(40*3)+200, 340+220+15),
                         (340+(40*3)+40, 340+180+15, 340+(40*3)+80, 340+220+15)]
        for coord in coords_yellow:
            self.make_canvas.create_rectangle(*coord, width=3, fill="yellow")

        # Vị trí bắt đầu (Start)
        self.make_canvas.create_rectangle(100+240, 340+(40*5)-5, 100+280, 340+(40*6)-5, fill="#04d9ff", width=3)
        self.make_canvas.create_rectangle(100+40, 15+(40*6), 100+80, 15+(40*7), fill="red", width=3)
        self.make_canvas.create_rectangle(100+(40*8), 15+40, 100+(40*9), 15+80, fill="#00FF00", width=3)
        self.make_canvas.create_rectangle(100+(40*13), 15+(40*8), 100+(40*14), 15+(40*9), fill="yellow", width=3)

        # Tam giác giữa
        self.make_canvas.create_polygon(100+240, 15+240, 100+300, 15+300, 100+240, 15+360, width=3, fill="red", outline="black")
        self.make_canvas.create_polygon(100+360, 15+240, 100+300, 15+300, 100+360, 15+360, width=3, fill="yellow", outline="black")
        self.make_canvas.create_polygon(100+240, 15+240, 100+300, 15+300, 100+360, 15+240, width=3, fill="#00FF00", outline="black")
        self.make_canvas.create_polygon(100+240, 15+360, 100+300, 15+300, 100+360, 15+360, width=3, fill="#04d9ff", outline="black")

        # Vẽ các ngôi sao (safe zones)
        star_coords = [(340+(40*6)+20, 15+240+2), (100+240+20, 15+80+2), 
                       (100+80+20, 15+240+80+2), (100+240+80+2, 15+(40*12)+2)]
        
        for cx, cy in star_coords:
            coord = [cx, cy, cx+5, cy+15, cx+15, cy+15, cx+8, cy+20, cx+15, cy+25, 
                    cx+5, cy+25, cx, cy+35, cx-5, cy+25, cx-16, cy+25, cx-8, cy+20, 
                    cx-15, cy+15, cx-5, cy+15]
            self.make_canvas.create_polygon(coord, width=3, fill="blue")

        # Tạo quân cờ và label
        self._create_all_coins()

    def _create_all_coins(self):
        """Tạo tất cả quân cờ và label"""
        # RED COINS
        red_positions = [(100+40, 15+40), (100+160, 15+40), (100+160, 15+140), (100+40, 15+140)]
        for i, (x, y) in enumerate(red_positions):
            coin = self.make_canvas.create_oval(x, y, x+40, y+40, width=3, fill="red", outline="black")
            self.made_red_coin.append(coin)
            label = Label(self.make_canvas, text=str(i+1), font=("Arial", 15, "bold"), bg="red", fg="black")
            label.place(x=x+10, y=y+5)
            self.red_number_label.append(label)

        # GREEN COINS
        green_positions = [(340+(40*3)+40, 15+40), (340+(40*3)+160, 15+40), 
                          (340+(40*3)+160, 15+140), (340+(40*3)+40, 15+140)]
        for i, (x, y) in enumerate(green_positions):
            coin = self.make_canvas.create_oval(x, y, x+40, y+40, width=3, fill="#00FF00", outline="black")
            self.made_green_coin.append(coin)
            label = Label(self.make_canvas, text=str(i+1), font=("Arial", 15, "bold"), bg="#00FF00", fg="black")
            label.place(x=x+10, y=y+5)
            self.green_number_label.append(label)

        # SKY BLUE COINS
        sky_positions = [(100+40, 340+95), (100+160, 340+95), (100+160, 340+195), (100+40, 340+195)]
        for i, (x, y) in enumerate(sky_positions):
            coin = self.make_canvas.create_oval(x, y, x+40, y+40, width=3, fill="#04d9ff", outline="black")
            self.made_sky_blue_coin.append(coin)
            label = Label(self.make_canvas, text=str(i+1), font=("Arial", 15, "bold"), bg="#04d9ff", fg="black")
            label.place(x=x+10, y=y+5)
            self.sky_blue_number_label.append(label)

        # YELLOW COINS
        yellow_positions = [(340+(40*3)+40, 340+95), (340+(40*3)+160, 340+95), 
                           (340+(40*3)+160, 340+195), (340+(40*3)+40, 340+195)]
        for i, (x, y) in enumerate(yellow_positions):
            coin = self.make_canvas.create_oval(x, y, x+40, y+40, width=3, fill="yellow", outline="black")
            self.made_yellow_coin.append(coin)
            label = Label(self.make_canvas, text=str(i+1), font=("Arial", 15, "bold"), bg="yellow", fg="black")
            label.place(x=x+10, y=y+5)
            self.yellow_number_label.append(label)

    # ============ INSTRUCTION BUTTONS ============
    def instruction_btn_red(self):
        block_predict_red = Label(self.make_canvas, image=self.block_number_side[0])
        block_predict_red.place(x=45, y=15)
        predict_red = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                            text="Predict", font=("Arial", 8, "bold"), 
                            command=lambda: self.make_prediction("red"))
        predict_red.place(x=37, y=55)
        entry_take_red = Entry(self.make_canvas, bg="white", fg="blue", 
                              font=("Arial", 25, "bold", "italic"), width=2, relief=SUNKEN, bd=5)
        entry_take_red.place(x=40, y=95)
        final_move = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                           text="Give", font=("Arial", 8, "bold"), 
                           command=lambda: self.main_controller("red", entry_take_red.get()), 
                           state=DISABLED)
        final_move.place(x=42, y=155)
        Label(self.make_canvas, text="Player 1", bg="#4d4dff", fg="gold", 
              font=("Arial", 15, "bold")).place(x=15, y=195)
        self.store_instructional_btn(block_predict_red, predict_red, entry_take_red, final_move)

    def instruction_btn_sky_blue(self):
        block_predict_sky_blue = Label(self.make_canvas, image=self.block_number_side[0])
        block_predict_sky_blue.place(x=45, y=405)
        predict_sky_blue = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                                  text="Predict", font=("Arial", 8, "bold"), 
                                  command=lambda: self.make_prediction("sky_blue"))
        predict_sky_blue.place(x=37, y=445)
        entry_take_sky_blue = Entry(self.make_canvas, bg="white", fg="blue", 
                                    font=("Arial", 25, "bold", "italic"), width=2, relief=SUNKEN, bd=5)
        entry_take_sky_blue.place(x=40, y=485)
        final_move = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                           text="Give", font=("Arial", 8, "bold"), 
                           command=lambda: self.main_controller("sky_blue", entry_take_sky_blue.get()), 
                           state=DISABLED)
        final_move.place(x=42, y=545)
        Label(self.make_canvas, text="Player 2", bg="#4d4dff", fg="gold", 
              font=("Arial", 15, "bold")).place(x=15, y=585)
        self.store_instructional_btn(block_predict_sky_blue, predict_sky_blue, entry_take_sky_blue, final_move)

    def instruction_btn_yellow(self):
        block_predict_yellow = Label(self.make_canvas, image=self.block_number_side[0])
        block_predict_yellow.place(x=715, y=405)
        predict_yellow = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                               text="Predict", font=("Arial", 8, "bold"), 
                               command=lambda: self.make_prediction("yellow"))
        predict_yellow.place(x=707, y=445)
        entry_take_yellow = Entry(self.make_canvas, bg="white", fg="blue", 
                                 font=("Arial", 25, "bold", "italic"), width=2, relief=SUNKEN, bd=5)
        entry_take_yellow.place(x=710, y=485)
        final_move = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                           text="Give", font=("Arial", 8, "bold"), 
                           command=lambda: self.main_controller("yellow", entry_take_yellow.get()), 
                           state=DISABLED)
        final_move.place(x=712, y=545)
        Label(self.make_canvas, text="Player 3", bg="#4d4dff", fg="gold", 
              font=("Arial", 15, "bold")).place(x=685, y=585)
        self.store_instructional_btn(block_predict_yellow, predict_yellow, entry_take_yellow, final_move)

    def instruction_btn_green(self):
        block_predict_green = Label(self.make_canvas, image=self.block_number_side[0])
        block_predict_green.place(x=715, y=15)
        predict_green = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                              text="Predict", font=("Arial", 8, "bold"), 
                              command=lambda: self.make_prediction("green"))
        predict_green.place(x=707, y=55)
        entry_take_green = Entry(self.make_canvas, bg="white", fg="blue", 
                                font=("Arial", 25, "bold", "italic"), width=2, relief=SUNKEN, bd=5)
        entry_take_green.place(x=710, y=95)
        final_move = Button(self.make_canvas, bg="black", fg="#00FF00", relief=RAISED, bd=5, 
                           text="Give", font=("Arial", 8, "bold"), 
                           command=lambda: self.main_controller("green", entry_take_green.get()), 
                           state=DISABLED)
        final_move.place(x=712, y=155)
        Label(self.make_canvas, text="Player 4", bg="#4d4dff", fg="gold", 
              font=("Arial", 15, "bold")).place(x=685, y=195)
        self.store_instructional_btn(block_predict_green, predict_green, entry_take_green, final_move)

    def store_instructional_btn(self, block, predictor, entry, give):
        self.block_value_predict.append([block, predictor, entry, give])

    # ============ COIN MOVEMENT ============
    def move_coin_to_start(self, color, coin_number):
        """
        SỬA: Vị trí xuất phát - Cập nhật theo hệ tọa độ tương đối
        """
        coin_idx = int(coin_number) - 1
        
        if color == "red":
            self.make_canvas.delete(self.made_red_coin[coin_idx])
            self.made_red_coin[coin_idx] = self.make_canvas.create_oval(
                100+40, 15+(40*6), 100+80, 15+(40*7), 
                fill="red", width=3, outline="black"
            )
            self.red_number_label[coin_idx].place_forget()
            self.red_number_label[coin_idx].place(x=100+50, y=15+(40*6)+5)
            self.red_coin_position[coin_idx] = 1  # Vị trí tương đối = 1
            self.red_coord_store[coin_idx] = 1
            
        elif color == "green":
            self.make_canvas.delete(self.made_green_coin[coin_idx])
            self.made_green_coin[coin_idx] = self.make_canvas.create_oval(
                100+(40*8), 15+40, 100+(40*9), 15+80, 
                fill="#00FF00", width=3, outline="black"
            )
            self.green_number_label[coin_idx].place_forget()
            self.green_number_label[coin_idx].place(x=100+(40*8)+10, y=15+45)
            self.green_coin_position[coin_idx] = 1  # SỬA: Từ 14 → 1 (tương đối)
            self.green_coord_store[coin_idx] = 14   # Coord vẫn giữ tuyệt đối cho overlap
            
        elif color == "yellow":
            self.make_canvas.delete(self.made_yellow_coin[coin_idx])
            self.made_yellow_coin[coin_idx] = self.make_canvas.create_oval(
                100+(40*13), 15+(40*8), 100+(40*14), 15+(40*9), 
                fill="yellow", width=3, outline="black"
            )
            self.yellow_number_label[coin_idx].place_forget()
            self.yellow_number_label[coin_idx].place(x=100+(40*13)+10, y=15+(40*8)+5)
            self.yellow_coin_position[coin_idx] = 1  # SỬA: Từ 27 → 1 (tương đối)
            self.yellow_coord_store[coin_idx] = 27   # Coord vẫn giữ tuyệt đối
            
        else:  # sky_blue
            self.make_canvas.delete(self.made_sky_blue_coin[coin_idx])
            self.made_sky_blue_coin[coin_idx] = self.make_canvas.create_oval(
                100+240, 340+(40*5)-5, 100+280, 340+(40*6)-5, 
                fill="#04d9ff", width=3, outline="black"
            )
            self.sky_blue_number_label[coin_idx].place_forget()
            self.sky_blue_number_label[coin_idx].place(x=100+250, y=340+(40*5))
            self.sky_blue_coin_position[coin_idx] = 1  # SỬA: Từ 40 → 1 (tương đối)
            self.sky_blue_coord_store[coin_idx] = 40   # Coord vẫn giữ tuyệt đối
        
        self.window.update()
        time.sleep(0.2)

    def move_coin_normal(self, color, coin_number, steps):
        """
        SỬA: Hàm di chuyển bình thường - gọi hàm motion_of_coin_fixed
        """
        coin_idx = int(coin_number) - 1
        
        coins_map = {
            'red': (self.red_coin_position, self.red_coord_store, 
                    self.made_red_coin, self.red_number_label),
            'green': (self.green_coin_position, self.green_coord_store, 
                    self.made_green_coin, self.green_number_label),
            'yellow': (self.yellow_coin_position, self.yellow_coord_store, 
                    self.made_yellow_coin, self.yellow_number_label),
            'sky_blue': (self.sky_blue_coin_position, self.sky_blue_coord_store, 
                        self.made_sky_blue_coin, self.sky_blue_number_label)
        }
        
        positions, coords, coins, labels = coins_map[color]
        current_pos = positions[coin_idx]
        
        # Lấy tọa độ hiện tại
        take_coord = self.make_canvas.coords(coins[coin_idx])
        label_x = take_coord[0] + 10
        label_y = take_coord[1] + 5
        labels[coin_idx].place(x=label_x, y=label_y)
        
        # QUAN TRỌNG: Gọi hàm motion_of_coin_fixed thay vì motion_of_coin
        new_pos = self.motion_of_coin_fixed(
            current_pos, coins[coin_idx], labels[coin_idx], 
            label_x, label_y, color, steps
        )
        
        positions[coin_idx] = new_pos
        coords[coin_idx] = new_pos

    def motion_of_coin_fixed(self, counter_coin, specific_coin, number_label, 
                         number_label_x, number_label_y, color_coin, path_counter):
        """
        SỬA LỖI: Hàm di chuyển ĐÚNG cho tất cả màu
        
        LOGIC:
        - Mỗi màu có 1 hệ tọa độ riêng (1-52)
        - Ô 51 của mỗi màu = cổng vào home
        - Ô 1-52: đường chính
        - Ô >= 100: đường vào đích
        """
        number_label.place(x=number_label_x, y=number_label_y)
        
        # Mapping cổng vào home theo màu (vị trí tương đối)
        home_entry_relative = {
            'red': 51,        # Ô cuối cùng trước khi vào home
            'green': 51,      # Tương tự cho các màu khác
            'yellow': 51,
            'sky_blue': 51
        }
        
        # Mapping điểm xuất phát (vị trí tuyệt đối trên bàn cờ)
        start_positions = {
            'red': 1,
            'green': 14, 
            'yellow': 27,
            'sky_blue': 40
        }
        
        start_pos = start_positions[color_coin]
        
        while path_counter > 0:
            # Kiểm tra đã vào home chưa
            if counter_coin >= 100:
                counter_coin = self.under_room_traversal_control(
                    specific_coin, number_label, number_label_x, 
                    number_label_y, path_counter, counter_coin, color_coin
                )
                
                if counter_coin == 106:
                    messagebox.showinfo("Đích đến", "Chúc mừng! Đã về đích!")
                break
            
            # Kiểm tra vào cổng home
            if counter_coin == home_entry_relative.get(color_coin):
                counter_coin = 100
                counter_coin = self.under_room_traversal_control(
                    specific_coin, number_label, number_label_x, 
                    number_label_y, path_counter, counter_coin, color_coin
                )
                
                if counter_coin == 106:
                    messagebox.showinfo("Đích đến", "Chúc mừng! Đã về đích!")
                break
            
            # Di chuyển 1 bước
            old_pos = counter_coin
            counter_coin += 1
            path_counter -= 1
            
            # Wrap around (quay vòng)
            if counter_coin > 52:
                counter_coin = 1
            
            # Tính vị trí tuyệt đối trên bàn cờ để biết hướng di chuyển
            abs_old = (old_pos + start_pos - 1)
            if abs_old > 52:
                abs_old -= 52
                
            abs_new = (counter_coin + start_pos - 1)
            if abs_new > 52:
                abs_new -= 52
            
            # Di chuyển theo vị trí tuyệt đối
            number_label.place_forget()
            
            # Ánh xạ di chuyển theo bàn cờ
            if abs_new <= 5:
                self.make_canvas.move(specific_coin, 40, 0)
                number_label_x += 40
            elif abs_new == 6:
                self.make_canvas.move(specific_coin, 40, -40)
                number_label_x += 40
                number_label_y -= 40
            elif 6 < abs_new <= 11:
                self.make_canvas.move(specific_coin, 0, -40)
                number_label_y -= 40
            elif abs_new <= 13:
                self.make_canvas.move(specific_coin, 40, 0)
                number_label_x += 40
            elif abs_new <= 18:
                self.make_canvas.move(specific_coin, 0, 40)
                number_label_y += 40
            elif abs_new == 19:
                self.make_canvas.move(specific_coin, 40, 40)
                number_label_x += 40
                number_label_y += 40
            elif abs_new <= 24:
                self.make_canvas.move(specific_coin, 40, 0)
                number_label_x += 40
            elif abs_new <= 26:
                self.make_canvas.move(specific_coin, 0, 40)
                number_label_y += 40
            elif abs_new <= 31:
                self.make_canvas.move(specific_coin, -40, 0)
                number_label_x -= 40
            elif abs_new == 32:
                self.make_canvas.move(specific_coin, -40, 40)
                number_label_x -= 40
                number_label_y += 40
            elif abs_new <= 37:
                self.make_canvas.move(specific_coin, 0, 40)
                number_label_y += 40
            elif abs_new <= 39:
                self.make_canvas.move(specific_coin, -40, 0)
                number_label_x -= 40
            elif abs_new <= 44:
                self.make_canvas.move(specific_coin, 0, -40)
                number_label_y -= 40
            elif abs_new == 45:
                self.make_canvas.move(specific_coin, -40, -40)
                number_label_x -= 40
                number_label_y -= 40
            elif abs_new <= 50:
                self.make_canvas.move(specific_coin, -40, 0)
                number_label_x -= 40
            elif 50 < abs_new <= 52:
                self.make_canvas.move(specific_coin, 0, -40)
                number_label_y -= 40
            elif abs_new == 1:  # Quay vòng về đầu
                self.make_canvas.move(specific_coin, 40, 0)
                number_label_x += 40
            
            number_label.place(x=number_label_x, y=number_label_y)
            self.window.update()
            time.sleep(0.2)
        
        return counter_coin

    # ============ HOME PATH (Đường về đích) ============
    def under_room_traversal_control(self, specific_coin, number_label, 
                                     number_label_x, number_label_y, 
                                     path_counter, counter_coin, color_coin):
        """Điều khiển di chuyển trong đường về đích"""
        traversal_funcs = {
            'red': self.room_red_traversal,
            'green': self.room_green_traversal,
            'yellow': self.room_yellow_traversal,
            'sky_blue': self.room_sky_blue_traversal
        }
        
        if color_coin in traversal_funcs and counter_coin >= 100:
            if int(counter_coin) + int(path_counter) <= 106:
                counter_coin = traversal_funcs[color_coin](
                    specific_coin, number_label, number_label_x, 
                    number_label_y, path_counter, counter_coin
                )
        
        return counter_coin

    def room_red_traversal(self, specific_coin, number_label, 
                          number_label_x, number_label_y, 
                          path_counter, counter_coin):
        """Đường về đích của Red - đi sang phải"""
        while path_counter > 0:
            counter_coin += 1
            path_counter -= 1
            self.make_canvas.move(specific_coin, 40, 0)
            number_label_x += 40
            number_label.place(x=number_label_x, y=number_label_y)
            self.window.update()
            time.sleep(0.2)
        return counter_coin

    def room_green_traversal(self, specific_coin, number_label, 
                            number_label_x, number_label_y, 
                            path_counter, counter_coin):
        """Đường về đích của Green - đi xuống"""
        while path_counter > 0:
            counter_coin += 1
            path_counter -= 1
            self.make_canvas.move(specific_coin, 0, 40)
            number_label_y += 40
            number_label.place(x=number_label_x, y=number_label_y)
            self.window.update()
            time.sleep(0.2)
        return counter_coin

    def room_yellow_traversal(self, specific_coin, number_label, 
                             number_label_x, number_label_y, 
                             path_counter, counter_coin):
        """Đường về đích của Yellow - đi sang trái"""
        while path_counter > 0:
            counter_coin += 1
            path_counter -= 1
            self.make_canvas.move(specific_coin, -40, 0)
            number_label_x -= 40
            number_label.place(x=number_label_x, y=number_label_y)
            self.window.update()
            time.sleep(0.2)
        return counter_coin

    def room_sky_blue_traversal(self, specific_coin, number_label, 
                                number_label_x, number_label_y, 
                                path_counter, counter_coin):
        """Đường về đích của Sky Blue - đi lên"""
        while path_counter > 0:
            counter_coin += 1
            path_counter -= 1
            self.make_canvas.move(specific_coin, 0, -40)
            number_label_y -= 40
            number_label.place(x=number_label_x, y=number_label_y)
            self.window.update()
            time.sleep(0.2)
        return counter_coin

    # ============ RESET COIN ============
    def reset_coin_to_home(self, color, coin_number):
        """Đưa quân cờ về nhà khi bị ăn"""
        
        # Vị trí ban đầu của từng màu
        home_positions = {
            'red': [
                (100+40, 15+40, 100+80, 15+80, 100+50, 15+45),
                (100+160, 15+40, 100+200, 15+80, 100+170, 15+45),
                (100+160, 15+140, 100+200, 15+180, 100+170, 15+145),
                (100+40, 15+140, 100+80, 15+180, 100+50, 15+145)
            ],
            'green': [
                (340+(40*3)+40, 15+40, 340+(40*3)+80, 15+80, 340+(40*3)+50, 15+45),
                (340+(40*3)+160, 15+40, 340+(40*3)+200, 15+80, 340+(40*3)+170, 15+45),
                (340+(40*3)+160, 15+140, 340+(40*3)+200, 15+180, 340+(40*3)+170, 15+145),
                (340+(40*3)+40, 15+140, 340+(40*3)+80, 15+180, 340+(40*3)+50, 15+145)
            ],
            'yellow': [
                (340+(40*3)+40, 340+95, 340+(40*3)+80, 340+135, 340+(40*3)+50, 340+100),
                (340+(40*3)+160, 340+95, 340+(40*3)+200, 340+135, 340+(40*3)+170, 340+100),
                (340+(40*3)+160, 340+195, 340+(40*3)+200, 340+235, 340+(40*3)+170, 340+200),
                (340+(40*3)+40, 340+195, 340+(40*3)+80, 340+235, 340+(40*3)+50, 340+200)
            ],
            'sky_blue': [
                (100+40, 340+95, 100+80, 340+135, 100+50, 340+100),
                (100+160, 340+95, 100+200, 340+135, 100+170, 340+100),
                (100+160, 340+195, 100+200, 340+235, 100+170, 340+200),
                (100+40, 340+195, 100+80, 340+235, 100+50, 340+200)
            ]
        }
        
        coin_colors = {
            'red': ('red', self.red_coin_position, self.red_coord_store, 
                    self.made_red_coin, self.red_number_label),
            'green': ('#00FF00', self.green_coin_position, self.green_coord_store, 
                      self.made_green_coin, self.green_number_label),
            'yellow': ('yellow', self.yellow_coin_position, self.yellow_coord_store, 
                       self.made_yellow_coin, self.yellow_number_label),
            'sky_blue': ('#04d9ff', self.sky_blue_coin_position, self.sky_blue_coord_store, 
                         self.made_sky_blue_coin, self.sky_blue_number_label)
        }
        
        if color not in coin_colors:
            return
        
        fill_color, positions, coords, coins, labels = coin_colors[color]
        
        # Reset position
        positions[coin_number] = -1
        coords[coin_number] = -1
        
        # Xóa coin cũ
        self.make_canvas.delete(coins[coin_number])
        labels[coin_number].place_forget()
        
        # Tạo lại coin ở vị trí ban đầu
        x1, y1, x2, y2, lx, ly = home_positions[color][coin_number]
        
        coins[coin_number] = self.make_canvas.create_oval(
            x1, y1, x2, y2, 
            width=3, fill=fill_color, outline="black"
        )
        labels[coin_number].place(x=lx, y=ly)
        
        self.window.update()


if __name__ == '__main__':
    root = Tk()
    root.withdraw()
    
    host = simpledialog.askstring("Server", "IP:", initialvalue="localhost")
    if not host:
        host = "localhost"
    
    root.deiconify()
    root.geometry("800x630")
    root.title("Cờ Cá Ngựa - Multiplayer")
    
    block_six = ImageTk.PhotoImage(Image.open("Images/6_block.png").resize((33, 33)))
    block_five = ImageTk.PhotoImage(Image.open("Images/5_block.png").resize((33, 33)))
    block_four = ImageTk.PhotoImage(Image.open("Images/4_block.png").resize((33, 33)))
    block_three = ImageTk.PhotoImage(Image.open("Images/3_block.png").resize((33, 33)))
    block_two = ImageTk.PhotoImage(Image.open("Images/2_block.png").resize((33, 33)))
    block_one = ImageTk.PhotoImage(Image.open("Images/1_block.png").resize((33, 33)))
    
    LudoClient(root, block_six, block_five, block_four, block_three, block_two, block_one, host=host)
    root.mainloop()