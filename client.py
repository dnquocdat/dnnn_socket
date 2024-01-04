import tkinter as tk
from PIL import Image, ImageTk
import socket
import pickle
from tkinter import messagebox, font
import threading
import zlib

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client")
        large_font = font.Font(size=12)

        tk.Label(root, text="Server IP:", font=large_font).grid(row=0, column=0)
        self.ip_entry = tk.Entry(root, font=large_font)
        self.ip_entry.grid(row=0, column=1)

        tk.Label(root, text="Port:", font=large_font).grid(row=1, column=0)
        self.port_entry = tk.Entry(root, font=large_font)
        self.port_entry.grid(row=1, column=1)

        self.connect_button = tk.Button(root, text="Connect", command=self.connect_to_server, font=large_font)
        self.connect_button.grid(row=2, column=0)

        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect_from_server, state=tk.DISABLED, font=large_font)
        self.disconnect_button.grid(row=2, column=1)

        self.display_image_label = tk.Label(root)
        self.display_image_label.grid(row=3, column=0, columnspan=2)
        self.connection = None
        self.receive_thread = None

    def connect_to_server(self):
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((ip, port))
            messagebox.showinfo("Connection", "Successfully connected to the server.")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)

            self.receive_thread = threading.Thread(target=self.receive_screenshots, daemon=True)
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_from_server(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.receive_thread:
            self.receive_thread.join()
            self.receive_thread = None
        messagebox.showinfo("Connection", "Disconnected from the server.")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)

    def receive_screenshots(self):
        while self.connection:
            try:
                img = self.receive_screenshot(self.connection)
                if img is not None:
                    self.root.after(0, self.update_image, img)
            except ConnectionError:
                break
            except Exception as e:
                print("Error receiving screenshot:", e)
                break
        self.disconnect_from_server()

    def receive_screenshot(self, server_socket):
        try:
            img_size_data = server_socket.recv(4)
            if not img_size_data:
                raise ConnectionError("Lost connection to the server.")
            img_size = int.from_bytes(img_size_data, 'big')

            compressed_img_data = b''
            while len(compressed_img_data) < img_size:
                packet = server_socket.recv(4096)
                if not packet:
                    raise ConnectionError("Lost connection to the server.")
                compressed_img_data += packet

            img_data = zlib.decompress(compressed_img_data)
            img = pickle.loads(img_data)
            return img
        except ConnectionError as e:
            print(e)
            self.disconnect_from_server()
        except Exception as e:
            print("General error:", e)
        
    def update_image(self, img):
        image = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
        tk_image = ImageTk.PhotoImage(image)
        self.display_image_label.config(image=tk_image)
        self.display_image_label.image = tk_image
        self.root.update_idletasks()  # Cập nhật giao diện người dùng

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()

# 192.168.199.170