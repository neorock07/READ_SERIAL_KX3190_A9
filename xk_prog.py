import serial
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
from PIL import ImageTk, Image
from datetime import datetime
import threading
import queue
import pymupdf as pdf


def check_port_availability(port):
    """
    Mengecek apakah port aktif atau tidak.
    """
    try:
        test_serial = serial.Serial(port=port)
        test_serial.close()  # Kalau bisa dibuka, berarti aktif
        return True
    except serial.SerialException:
        return False

def read_serial_data(baud_rate: int, port: str, timeout: int = 5, code="latin-1"):
    data = None
    index = 0

    if not check_port_availability(port):
        messagebox.showerror("Port Error", f"Port {port} tidak aktif atau tidak ada perangkat atau sedang dibuka!")
        return

    try:
        # ser = serial.Serial(baudrate=baud_rate, timeout=timeout, port=port)
        # ser.open()  # Pastikan port terbuka sebelum digunakan
        
        ser.baudrate = baud_rate
        ser.timeout = timeout
        ser.port = port 
        ser.open()
            
        while ser.is_open:
                if ser.in_waiting > 0:
                    data = ser.readline().decode(code).strip()
                    index +=1
                    timestamps = datetime.now().strftime("%d-%m-%y %H:%M:%S")
                    print(index, data, timestamps)
                    if index > 15:
                        ser.close()
                    else:    
                        queue_dt.put([[index, data, timestamps]])
                
                if condition is False:
                    ser.close()
        else:
            ser.close()
            messagebox.showerror("Connection Closed", "Port tidak menanggapi!")
    except serial.SerialException as e:
        logging.debug(f"Serial Error : {str(e)}")
        messagebox.showinfo("Warning", f"Port ditutup! {str(e)}")
    except UnicodeDecodeError:
        data = ser.readline().decode("latin-1", errors="ignore").strip()
    except Exception as e:
        messagebox.showerror("Error", f"Codec tidak cocok! {str(e)}")

def create_pdf():
    pass

def start_reading_serial(port, baud_rate, timeout, code):
    thread = threading.Thread(
        target=read_serial_data,
        args=(baud_rate, port, timeout, code),
        daemon=True
    )
    thread.start()


def stop_table(dialog):
    dialog.destroy()

def stop_serial_reading():
    ser.close()

def show_table(data):
    
    heading_arr = [
        "No.", 
        "Berat",
        "Waktu"
    ]
    # tree.pack(padx=10, pady=10)
    sty = ttk.Style()
    sty.theme_use('clam')
    sty.configure('Treeview', rowheight=80, font=("Arial", 11))
    
    for i in range(len(heading_arr)):
        index = i+1
        tree.heading(index, text=heading_arr[i])
    
    for row in data:
        tree.insert("", "end", values=row)
    
    v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=v_scroll.set)
    
    tree.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    
    # close_btn = tk.Button(
    #     # root,
    #     dialog, 
    #     text="Tutup", 
    #     command= stop_table(dialog)
    # )
    # close_btn.pack(pady=10)
    
    dialog.update_idletasks()
    dialog.geometry("650x400")

def run_table_onThread(data):
    th = threading.Thread(target=show_table, args=(data), daemon=True)
    th.start()

def insert_to_table(queue, tree):
    while not queue.empty():
        data = queue.get()
        for row in data:
            tree.insert("", "end", values=row)
    root.after(100, insert_to_table, queue, tree)    

def save_data(field_port, field_baud_rate, field_timeout=5, field_code="latin-1"):
    field_port = field_port.get()
    field_baud_rate = field_baud_rate.get()
    field_timeout = field_timeout.get()
    field_code = field_code.get()

    # Validasi input
    if not field_code or field_code == "Pilih":
        field_code = "latin-1"
    if not field_timeout or not field_baud_rate:
        field_timeout = 5
        field_baud_rate = 9600
    if not field_port:
        messagebox.showwarning("Warning!", "Port harus diisi!")
        return

    # Mulai pembacaan data di thread terpisah
    try:
        start_reading_serial(
            baud_rate=int(field_baud_rate),
            port=field_port,
            timeout=int(field_timeout),
            code=field_code
        )
        
        # Mulai thread untuk memonitor queue tanpa memblokir GUI
        thread_monitor = threading.Thread(
            target=monitor_queue,
            daemon=True
        )
        thread_monitor.start()
        print("asline tekan kene rung ")
        
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")

def monitor_queue():
    """
    Fungsi untuk memantau queue dan memproses data yang masuk
    tanpa memblokir thread utama (GUI).
    """
    while True:
        try:
            data = queue_dt.get(timeout=5)  # Timeout 1 detik
            if data:
                # Proses data (misalnya tampilkan ke tabel)
                run_table_onThread([data])
                print(data)
                # Contoh masukkan ke TreeView
                insert_to_table(queue_dt, tree)
        except Exception as e:
            # Timeout habis atau queue kosong (bisa diabaikan)
            continue
        
def run_save(field_port, field_baud_rate, field_timeout=5, field_code="latin-1"):
    global tree, frame, dialog

    # Cek keberadaan objek dialog
    if 'dialog' not in globals() or not dialog.winfo_exists():
        dialog = tk.Toplevel(root)
        dialog.title("HASIL PENGUKURAN")
    
    # Cek keberadaan frame di dalam dialog
    if 'frame' not in globals() or not frame.winfo_exists():
        frame = tk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Cek keberadaan Treeview di dalam frame
    if 'tree' not in globals() or not tree.winfo_exists():
        tree = ttk.Treeview(frame, columns=(1, 2, 3), show="headings", height=10)
        tree.heading(1, text="Index")
        tree.heading(2, text="Data")
        tree.heading(3, text="Timestamp")
        tree.pack(fill="both", expand=True)
    
    print(
        f"Apakah tree ada: {tree.winfo_exists()}, "
        f"frame: {frame.winfo_exists()}, "
        f"dialog: {dialog.winfo_exists()}"
    )

    # Mulai thread untuk menjalankan fungsi save_data
    th = threading.Thread(
        target=save_data,
        args=(field_port, field_baud_rate, field_timeout, field_code),
        daemon=True
    )
    th.start()



def gui_window():
    option_codes = [
        "utf-8", 
        "utf-16", 
        "latin-1",
        "latin-2",
        "ISO-8859-1",
    ]
     
    image = ImageTk.PhotoImage(Image.open("kl.png"))
    lb_img = tk.Label(root, image=image)
    lb_img.grid(row=0, column=0, padx=10, pady=5, sticky="w")
     
    tk.Label(root, text="Port:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
    field_port = tk.Entry(root, width=60,font=("Arial", 10))
    field_port.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(root, text="Baud Rate:", font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    field_baud_rate = tk.Entry(root, width=60, font=("Arial", 10))
    field_baud_rate.insert(0, "9600")
    field_baud_rate.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(root, text="TimeOut (5 detik default):", font=("Arial", 10)).grid(row=3, column=0, padx=10, pady=5, sticky="w")
    field_timeout = tk.Entry(root, width=60, font=("Arial", 10))
    field_timeout.insert(0, "5")
    field_timeout.grid(row=3, column=1, padx=10, pady=5)
    
    var_option = tk.StringVar(root)
    var_option.set("Pilih")
    
    tk.Label(root, text="[Optional]\nCode (latin-1 default):", font=("Arial", 10)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
    field_code = tk.OptionMenu(root, var_option, *option_codes)
    field_code.grid(row=5, column=0, padx=10, pady=5)

    btn_listen = tk.Button(root, 
                           text="Start Listen", 
                           height=5, 
                           width=30,
                           relief="groove",
                           command=lambda : run_save(field_port=field_port,
                                             field_baud_rate=field_baud_rate,
                                             field_code=var_option, 
                                             field_timeout=field_timeout))
    btn_listen.grid(row=6, column=0, columnspan=2, pady=10)
    
    btn_stop = tk.Button(root, 
                           text="Stop Listen", 
                           height=5, 
                           width=30,
                           relief="groove",
                           command=lambda : stop_serial_reading())
    btn_stop.grid(row=7, column=0, columnspan=3, pady=10)
    
    


if __name__=='__main__':
    root = tk.Tk()
    root.title("XK-3190-A9 READER PROGRAM")
    root.geometry("650x500")
    root.resizable(0.1, 0.2)
  
    dialog = tk.Toplevel(root)
    dialog.title("HASIL PENGUKURAN")
    frame = tk.Frame(dialog)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    tree = ttk.Treeview(frame, columns=(1, 2, 3), show="headings", height=2)
    
    queue_dt = queue.Queue()
    stop_event = threading.Event()
    condition = True
    ser = serial.Serial()
    
    # root.protocol("WM_DELETE_WINDOW", stop_serial_reading)
    gui_window()
    root.mainloop()
    

    