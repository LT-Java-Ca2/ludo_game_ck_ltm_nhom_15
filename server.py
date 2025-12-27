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