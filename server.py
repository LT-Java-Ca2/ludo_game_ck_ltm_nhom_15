import socket
import threading
import pickle
from random import randint
import sys

class LudoServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.player_colors = ['red', 'sky_blue', 'yellow', 'green']
        self.game_state = {
            'players': [],
            'current_turn': 0,
            'red_positions': [-1, -1, -1, -1],
            'sky_blue_positions': [-1, -1, -1, -1],
            'yellow_positions': [-1, -1, -1, -1],
            'green_positions': [-1, -1, -1, -1],
            'red_coords': [-1, -1, -1, -1],
            'sky_blue_coords': [-1, -1, -1, -1],
            'yellow_coords': [-1, -1, -1, -1],
            'green_coords': [-1, -1, -1, -1],
            'game_started': False,
            'winners': [],
            'six_counters': [0, 0, 0, 0]  
        }
        self.lock = threading.Lock()
        
    def start(self):
        try:
            self.server.bind((self.host, self.port))
          
            self.server.listen(4)
            self.server.settimeout(1.0)  
            
            print(f"[SERVER] Đang chạy trên {self.host}:{self.port}")
            print(f"[SERVER] Đợi người chơi...")
            print(f"[SERVER] Nhấn Ctrl+C để dừng server...")
            
          
            while len(self.clients) < 4:
                try:
                    client, address = self.server.accept()
                except socket.timeout:
                 
                    continue
                print(f"[SERVER] Kết nối từ {address}")
                
              
                player_id = len(self.clients)
                color = self.player_colors[player_id]
                
                client_info = {
                    'socket': client,
                    'address': address,
                    'player_id': player_id,
                    'color': color
                }
                
                self.clients.append(client_info)
                self.game_state['players'].append(color)
                
             
                self.send_data(client, {
                    'type': 'player_info',
                    'player_id': player_id,
                    'color': color,
                    'total_players': len(self.clients)
                })
                
              
                self.broadcast({
                    'type': 'player_joined',
                    'total_players': len(self.clients),
                    'players': self.game_state['players']
                })
                
               
                thread = threading.Thread(target=self.handle_client, args=(client_info,), daemon=True)
                thread.start()
                
               
                
                if len(self.clients) >= 2:
                    print(f"[SERVER] Đã có {len(self.clients)} người. Đủ điều kiện chơi!")
                    
                   

        except KeyboardInterrupt:
           
            print("\n[SERVER] Đang tắt server...")
            self.shutdown()
        except Exception as e:
            print(f"[SERVER ERROR] {e}")
    
    def shutdown(self):
        """Đóng server và ngắt kết nối"""
        for c in self.clients:
            try:
                c['socket'].close()
            except:
                pass
        self.server.close()
        sys.exit(0)

    def handle_client(self, client_info):
        client = client_info['socket']
        player_id = client_info['player_id']
        
        try:
            while True:
                data = self.receive_data(client)
                if not data:
                    break
                    
                with self.lock:
                    self.process_request(client_info, data)
                    
        except Exception as e:
            print(f"[ERROR] Lỗi client {player_id}: {e}")
        finally:
            self.disconnect_client(client_info)
            
    def process_request(self, client_info, data):
        msg_type = data.get('type')
        print(f"[SERVER] Nhận request: {msg_type} từ player {client_info['player_id']}")
        
        if msg_type == 'start_game':
            if len(self.clients) >= 2 and not self.game_state['game_started']:
                self.game_state['game_started'] = True
                print("[SERVER] Game bắt đầu!")
                self.broadcast({
                    'type': 'game_started',
                    'players': self.game_state['players'],
                    'current_turn': 0
                })
                
        elif msg_type == 'roll_dice':
            player_id = client_info['player_id']
            print(f"[SERVER] Roll dice: player_id={player_id}, current_turn={self.game_state['current_turn']}")
            
            if self.game_state['current_turn'] == player_id:
                dice_value = randint(1, 6)
                
                # Đếm số 6 liên tiếp
                if dice_value == 6:
                    self.game_state['six_counters'][player_id] += 1
                else:
                    self.game_state['six_counters'][player_id] = 0
                
                print(f"[SERVER] Player {player_id} ({client_info['color']}) tung được {dice_value}")
                
                self.broadcast({
                    'type': 'dice_rolled',
                    'player_id': player_id,
                    'value': dice_value,
                    'color': client_info['color']
                })
            else:
                print(f"[SERVER] Không phải lượt của player {player_id}")
                
        elif msg_type == 'move_coin':
            self.handle_move(client_info, data)
            
        elif msg_type == 'next_turn':
            print(f"[SERVER] Chuyển lượt từ player {client_info['player_id']}")
            self.next_turn()

#bao up tiep
    def handle_move(self, client_info, data):
        player_id = client_info['player_id']
        color = client_info['color']
        coin_number = data['coin_number']
        new_position = data['new_position']
        new_coord = data['new_coord']
        
        # Cập nhật game state
        pos_key = f'{color}_positions'
        coord_key = f'{color}_coords'
        
        old_position = self.game_state[pos_key][coin_number]
        old_coord = self.game_state[coord_key][coin_number]
        
        self.game_state[pos_key][coin_number] = new_position
        self.game_state[coord_key][coin_number] = new_coord
        
        print(f"[SERVER] {color} coin {coin_number+1}: {old_position}→{new_position}, coord: {old_coord}→{new_coord}")
        
        # Kiểm tra overlap (ăn quân)
        overlap_info = []
        safe_coords = [1, 14, 27, 40, 22, 9, 48, 35]
        
        if new_coord not in safe_coords and new_coord < 100 and     new_coord > -1:
            overlap_info = self.check_overlap(color, new_coord)
    
        if overlap_info:
            print(f"[SERVER] Overlap detected: {overlap_info}")
        
        # Broadcast move
        broadcast_data = {
            'type': 'coin_moved',
            'player_id': player_id,
            'color': color,
            'coin_number': coin_number,
            'new_position': new_position,
            'new_coord': new_coord,
            'overlap': overlap_info
        }
        print(f"[SERVER] Broadcasting move to all clients")
        self.broadcast(broadcast_data)
        
        # Kiểm tra thắng
        if new_position == 106:
            self.check_winner(color, player_id)
            
    def check_overlap(self, moving_color, coord):
        """
        SỬA: Kiểm tra ăn quân - dùng COORD (tuyệt đối)
        """
        overlap_info = []
        
        # Kiểm tra từng màu khác
        for color in self.player_colors:
            if color != moving_color:
                coord_key = f'{color}_coords'
                for i, c in enumerate(self.game_state[coord_key]):
                    if c == coord and c > -1 and c < 100:
                        print(f"[SERVER] {moving_color} ăn {color} coin {i+1} tại coord {coord}")
                        overlap_info.append({
                            'color': color,
                            'coin_number': i
                        })
                        # Reset về nhà
                        self.game_state[coord_key][i] = -1
                        self.game_state[f'{color}_positions'][i] = -1
                        
        return overlap_info


#bao up tiep theo
    def check_winner(self, color, player_id):
        """Kiểm tra thắng - tất cả 4 quân về đích (106)"""
        pos_key = f'{color}_positions'
        all_home = all(pos == 106 for pos in self.game_state[pos_key])
        
        if all_home and color not in [w['color'] for w in self.game_state['winners']]:
            rank = len(self.game_state['winners']) + 1
            self.game_state['winners'].append({
                'color': color,
                'player_id': player_id,
                'rank': rank
            })
            
            print(f"[SERVER] {color} (Player {player_id+1}) đạt hạng {rank}!")
            
            self.broadcast({
                'type': 'player_won',
                'color': color,
                'player_id': player_id,
                'rank': rank
            })
            
            # Game over khi 3/4 người thắng
            if len(self.game_state['winners']) >= len(self.clients) - 1:
                print("[SERVER] Game kết thúc!")
                self.broadcast({
                    'type': 'game_over',
                    'winners': self.game_state['winners']
                })

#bao up het
    def next_turn(self):
        """
        Chuyển lượt - Theo logic Ludo_game.py
        - Ra 6 được tung lại
        - Ăn quân được tung lại
        - Ra 6 ba lần liên tiếp thì mất lượt
        """
        current_player = self.game_state['current_turn']
        
        # Lọc players còn chơi (chưa thắng)
        active_players = [i for i, color in enumerate(self.game_state['players']) 
                         if color not in [w['color'] for w in self.game_state['winners']]]
        
        if not active_players:
            return
        
        # Tìm player tiếp theo
        if current_player in active_players:
            current_idx = active_players.index(current_player)
            next_idx = (current_idx + 1) % len(active_players)
            self.game_state['current_turn'] = active_players[next_idx]
        else:
            self.game_state['current_turn'] = active_players[0]
        
        print(f"[SERVER] Chuyển lượt sang player {self.game_state['current_turn']}")
        
        self.broadcast({
            'type': 'turn_changed',
            'current_turn': self.game_state['current_turn']
        })
            

# vy up tiep
    def broadcast(self, data):
        """Gửi đến tất cả clients"""
        for client_info in self.clients[:]:
            try:
                self.send_data(client_info['socket'], data)
            except Exception as e:
                print(f"[ERROR] Broadcast failed to {client_info['player_id']}: {e}")
                
    def send_data(self, client, data):
        """Gửi dữ liệu pickle"""
        try:
            serialized = pickle.dumps(data)
            client.sendall(len(serialized).to_bytes(4, 'big'))
            client.sendall(serialized)
        except Exception as e:
            print(f"[ERROR] Send data: {e}")