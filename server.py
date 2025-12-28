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