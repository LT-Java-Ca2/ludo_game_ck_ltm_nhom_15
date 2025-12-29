




#trung- ui
    def show_start_button(self):
        if hasattr(self, 'start_btn'):
            return
        self.start_btn = Button(self.make_canvas, text="BẮT ĐẦU", 
                               bg="green", fg="white", font=("Arial", 16, "bold"),
                               command=self.start_game)
        self.start_btn.place(x=320, y=280)
        


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