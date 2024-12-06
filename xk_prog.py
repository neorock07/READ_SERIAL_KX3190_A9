import serial
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
from PIL import ImageTk, Image
from datetime import datetime
import threading
import queue

def read_serial_data(baud_rate:int, port:int, timeout:int=5, code="latin-1"):
    data = None
    index = 0
    try:
        # with serial.Serial(port=port, baudrate=baud_rate, timeout=timeout) as ser:
        ser.baudrate = baud_rate
        ser.timeout = timeout
        ser.port = port 
        ser.open()   
        
        if ser.is_open:
                global condition
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
                messagebox.showerror("Connection closed", "Port tidak menanggapi!")        
    except serial.SerialException as e:
        logging.debug(f"Serial Error : {str(e)}")
        messagebox.showerror("Error", f"Gagal membaca data serial ! {str(e)}")
    except UnicodeDecodeError:
        data = ser.readline().decode("latin-1", errors="ignore").st
    except Exception as e:
        messagebox.showerror("Error", f"Codec tidak cocok ! {str(e)}")
        # root.destroy()
        
    return data, index    

def start_reading_serial(port, baud_rate, timeout, code):
    thread = threading.Thread(
        target=read_serial_data,
        args=(baud_rate, port, timeout, code),
        daemon=True
    )
    thread.start()

def stop_serial_reading():
    # stop_event.set()
    ser.close()
    
def stop_table(dialog):
    # stop_event.set()
    dialog.destroy()
    

def show_table(data):
    heading_arr = [
        "No.", 
        "Berat",
        "Waktu"
    ]
    tree.pack(padx=10, pady=10)
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
    
    close_btn = tk.Button(
        dialog, 
        text="Tutup", 
        command=lambda:root.protocol("WM_DELETE_WINDOW", stop_table(dialog))
    )
    close_btn.pack(pady=10)
    
    dialog.update_idletasks()
    dialog.geometry("650x400")

def insert_to_table(queue, tree):
    while not queue.empty():
        data = queue.get()
        for row in data:
            tree.insert("", "end", values=row)
    root.after(100, insert_to_table, queue, tree)    

def save_data(field_port, field_baud_rate, field_timeout=5, field_code="latin1"):
    field_port = field_port.get()
    field_baud_rate = field_baud_rate.get()
    field_timeout = field_timeout.get()
    field_code = field_code.get()
    
    try:    
        if not field_code or not field_baud_rate or not field_timeout or field_code=="Pilih":
            field_code = "latin-1"
            field_timeout = 5
            field_baud_rate = 9600
        
        if not field_port:    
            messagebox.showwarning("Warning!", "Port harus diisi!")
            return
        else:
            
            start_reading_serial(baud_rate= field_baud_rate,port= field_port,timeout=int(field_timeout),code=field_code)
            data = queue_dt.get()
            show_table(data)
            print("neng kene ra")
            print(queue_dt.get())
            insert_to_table(queue_dt, tree)        
            print(field_port, field_code, field_timeout, field_baud_rate)
    except Exception as e:
        messagebox.showerror("Error!", f"Terjadi Kesalahan!\n {e}")

def run_save(field_port, field_baud_rate, field_timeout, field_code):
    th = threading.Thread(target=save_data(field_port=field_port, field_baud_rate=field_baud_rate,field_timeout= field_timeout,field_code=field_code), daemon=True)
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
    
    tk.Label(root, text="[Optional]\nCode (latin1 default):", font=("Arial", 10)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
    field_code = tk.OptionMenu(root, var_option, *option_codes)
    field_code.grid(row=5, column=0, padx=10, pady=5)

    btn_listen = tk.Button(root, 
                           text="Start Listen", 
                           height=5, 
                           width=30,
                           relief="groove",
                           command=lambda : save_data(field_port=field_port,
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
    
    gui_window()
    root.mainloop()
    

    