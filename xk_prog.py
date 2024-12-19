import serial
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
from PIL import ImageTk, Image
from datetime import datetime
import threading
import queue
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os
from serial.tools import list_ports

folder = "documents"



def init_pdf(filename="sample.pdf"):
    """
    Function untuk menginisiasi pembuatan dan menyimpan dokumen pdf.
    
    :params filename (str): nama file.
    :return pdf, title, time_doc, spacer
    """
     
    global folder
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    filename = os.path.join(f"{folder}", filename)
    pdf = SimpleDocTemplate(filename=filename, pagesize=A4)
    sty = getSampleStyleSheet() 
    sty_title = sty['Title']
    sty_head2 = sty['Heading2']
    
    title = Paragraph(f"HASIL PEMBACAAN XK-3190-A9", sty_title)
    time_now = datetime.now().strftime("%d/%m/%y %H:%M")
    time_doc = Paragraph(f"Pada : {time_now}", sty_head2)
    spacer = Spacer(1, 20)
    
    return pdf, title, time_doc, spacer

def create_pdf(pdf, title, time_doc, spacer, data):
    """
    Function untuk membuat dokumen data hasil pengukuran dalam 
    bentuk tabel.
    
    :param pdf: objek hasil inisisi SimpleDocTemplate class;
    :param title (str):judul dokumen;
    :param time_doc (str): waktu pembuatan dokumen;
    :param spacer: objek spasi 
    :param data (list): data streaming yang di assign.
    
    """
    
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ])
    table.setStyle(style)
    pdf.build([title, time_doc, spacer, table])
 

def check_port_availability(port):
    """
    Mengecek apakah port aktif atau tidak.
    
    :param port (str): port yang akan digunakan.
    """
    try:
        test_serial = serial.Serial(port=port)
        test_serial.close()
        return True
    except serial.SerialException:
        return False
    

def read_serial_data(baud_rate: int, port: str, timeout: int = 5, code="latin-1"):
    """
    Function untuk membaca data streaming serial, cek terlebih dahulu
    `port`, `baud_rate`, dan `jenis decode` yang digunakan alat.
    
    :param baud_rate (int): frekuensi baud yang digunakan oleh alat.
    :param port (str): port yang digunakan oleh alat.
    :param timeout (int): waktu tunggu untuk menghubungkan port.
    :param code (str): jenis decode yang digunakan untuk mengubah data serial biner ke string.
    """
    
    data = None
    no = 0
    global isPick
    if not check_port_availability(port):
        messagebox.showerror("Port Error", f"Port {port} tidak aktif atau tidak ada perangkat atau sedang dibuka!")
        return

    try:
        # inisiasi serial port session
        ser.baudrate = baud_rate
        ser.timeout = timeout
        ser.port = port 
        ser.open()
        
        # array untuk menyimpan data yang di pick
        line_arr = []
        headers = ["No Serial", "Berat (kg)", "Timestamp"]
        line_arr.insert(0, headers)
        filename = f"HASIL_TIMBANGAN_{datetime.now().strftime('%d-%m-%y %H-%M-%S')}.pdf"    
        
        # inisiasi pdf
        pdf, title, time_doc, spacer = init_pdf(filename=filename)
        
        while ser.is_open:
                # baca serial ketika port sudah terbuka
                if ser.in_waiting > 0:
                    data = ser.readline().decode(code).strip()
                    no +=1
                    timestamps = datetime.now().strftime("%d-%m-%y %H:%M:%S")
                    print(no, data, timestamps)

                    # tambahkan data hasil pembacaan ke Queue untuk ditampilkan ke Tabel GUI.
                    # hapus ketika data sudah tidak terpakai untuk mengurangi beban penyimpanan
                    queue_dt.put([[no, data, timestamps]])
                
                    if isPick is True:
                        line_arr.append([no, data, timestamps])
                        create_pdf(pdf, title, time_doc, spacer, line_arr)
                        isPick = False
                if condition is False:
                    ser.close()
        else:
            ser.close()
            messagebox.showerror("Connection Closed", "Port tidak menanggapi!")
    except serial.SerialException as e:
        logging.debug(f"Serial Error : {str(e)}")
        messagebox.showinfo("Warning", f"Port ditutup!")
    except UnicodeDecodeError:
        data = ser.readline().decode("latin-1", errors="ignore").strip()
    except Exception as e:
        messagebox.showerror("Error", f"Codec tidak cocok! {str(e)}")



def start_reading_serial(port, baud_rate, timeout, code):
    """
    Function untuk menjalankan fungsi `read_serial_data` pada thread terpisah
    dari main thread.
    
    :param port (int): port yang akan digunakan;
    :param baud_rate (int): baud rate yang akan digunakan
    :param timeout (int): waktu tunggu.
    :param code (str): jenis decode;
    
    """
    
    thread = threading.Thread(
        target=read_serial_data,
        name="thread_read_serial",
        args=(baud_rate, port, timeout, code),
        daemon=True
    )
    thread.start()


def stop_table(dialog):
    """
    Menghancurkan pop-up dialog table.
    
    :param dialog : dialog GUI pop-up
    """
    dialog.destroy()

def stop_serial_reading():
    """
    Untuk menutup koneksi port.
    """
    ser.close()

def show_table(data):
    """
    Membuat GUI table.
    
    :param data: streaming serial data;
    """
    
    heading_arr = [
        "No.", 
        "Berat",
        "Waktu"
    ]
    sty = ttk.Style()
    sty.theme_use('clam')
    sty.configure('Treeview', rowheight=80, font=("Arial", 11))
    
    for i in range(len(heading_arr)):
        index = i+1
        tree.heading(index, text=heading_arr[i])
    
    for row in data:
        tree.insert("", "end", values=row)
        tree.see(tree.get_children()[-1])
    v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=v_scroll.set)
    
    tree.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    
    dialog.update_idletasks()
    dialog.geometry("650x400")

def run_table_onThread(data):
    """
    Menjalankan GUI table pada thread yang terpisah dari Main Thread.
    """
    th = threading.Thread(
        target=show_table,
        name="thread_show_table",
        args=(data),
        daemon=True)
    th.start()

def insert_to_table(queue, tree, max_rows=100):
    """
    Insert serial data ke tabel;
    :param queue: objek Queue hasil pembacaan serial.
    :param tree: objek TreeView untuk pembentuk dialog GUI.
    
    """
    while not queue.empty():
        data = queue.get()
        for row in data:
            tree.insert("", "end", values=row)
        
        if len(tree.get_children()) > max_rows:
            first_item = tree.get_children()[0]
            tree.delete(first_item)
                 
    #update data setiap 500 ms        
    root.after(2000, insert_to_table, queue, tree, max_rows)    

def save_data(field_port, field_baud_rate, field_timeout=5, field_code="latin-1"):
    """
    Function yang digunakan saat button `start listening` ditekan.
    """
    
    field_port = field_port.get()
    field_port = str(field_port).split(" ")[0]
    print(field_port)
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
        
        thread_monitor = threading.Thread(
            target=monitor_queue,
            name="thread_monitor",
            daemon=True
        )
        thread_monitor.start()
        
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")

def monitor_queue():
    """
    Fungsi untuk mendapatkan nilai queue dan memproses data yang masuk
    tanpa memblokir thread utama (GUI).
    """
    while True:
        try:
            data = queue_dt.get(timeout=5)
            if data:
                #Jalankan GUI Tabel di thrad lain;
                run_table_onThread([data])
                print(data)
                #menambahkan nilai dari Queue ke table GUI
                insert_to_table(queue_dt, tree)
        except Exception as e:
            continue
        
def run_save(field_port, field_baud_rate, field_timeout=5, field_code="latin-1"):
    """
    menjalankan `save_data` pada thread yang terpisah agar tidak blocking IO.
    """
    
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
        tree.heading(1, text="No.")
        tree.heading(2, text="Berat")
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
        name="thread_save",
        args=(field_port, field_baud_rate, field_timeout, field_code),
        daemon=True
    )
    th.start()

def pick_serial_data():
    """"
    Function untuk mengubah kondisi agar dapat mengambil data dari stream serial 
    ke pdf.
    """
    global isPick
    isPick = True

def get_ports():
    """
    Function untuk mendapatkan list port yang tersedia.
    """
    ports_arr = []
    ports = list_ports.comports()
    for port, d, h in sorted(ports):
        if d[:3] == "USB":
            ports_arr.append(f"{port} ({d[:3]})")
        else:    
            ports_arr.append(port)
            
    return ports_arr   

def refresh_ports():
    global field_port
    ports = get_ports()
    field_port_menu = field_port["menu"]
    print("f_port ", field_port)
    field_port_menu.delete(0, "end")
    for port in ports:
        field_port_menu.add_command(label=port, command=lambda value=port: var_option_ports.set(value))
    var_option_ports.set("Pilih")

def gui_window():
    "Menampilkan GUI menu utama"
    
    # daftar codec
    option_codes = [
        "utf-8", 
        "utf-16", 
        "utf-32",
        "latin-1",
        "latin-2",
        "ISO-8859-1",
        "base64", 
        "GB18030",
        "GB2312",
        "GBK",
        "Big5",
        "Shift-JIS",
        "EUC-JP",
        "KOI8-R",
        "ISO-8859-9",
        "windows-1252",
        "windows-1254",
        
    ]
      
     
    tk.Label(root, text="Port:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
    field_port.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    
    btn_refresh = tk.Button(root, 
                           text="refresh", 
                           height=1,
                        #    background='green', 
                           width=6,
                           relief="groove",
                           command=lambda : refresh_ports())
    btn_refresh.grid(row=1, column=1, columnspan=3, pady=10, sticky="w", padx=100)
    
    tk.Label(root, text="Baud Rate:", font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    field_baud_rate = tk.Entry(root, width=60, font=("Arial", 10))
    field_baud_rate.insert(0, "9600")
    field_baud_rate.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(root, text="TimeOut (5 detik default):", font=("Arial", 10)).grid(row=3, column=0, padx=10, pady=5, sticky="w")
    field_timeout = tk.Entry(root, width=60, font=("Arial", 10))
    field_timeout.insert(0, "5")
    field_timeout.grid(row=3, column=1, padx=10, pady=5)
    
    #membuat option codec
    var_option = tk.StringVar(root)
    var_option.set("Pilih")
    
    tk.Label(root, text="[Optional]\nCode (latin-1 default):", font=("Arial", 10)).grid(row=4, column=0, padx=10, pady=5, sticky="w")
    field_code = tk.OptionMenu(root, var_option, *option_codes)
    field_code.grid(row=4, column=1, padx=10, pady=5, sticky="w")

    btn_listen = tk.Button(root, 
                           text="Start Listen", 
                           height=5,
                           background='green', 
                           width=30,
                           relief="groove",
                           command=lambda : run_save(field_port=var_option_ports,
                                             field_baud_rate=field_baud_rate,
                                             field_code=var_option, 
                                             field_timeout=field_timeout))
    btn_listen.grid(row=6, column=0, columnspan=3, pady=10)
    
    btn_take = tk.Button(root, 
                           text="Pick Data", 
                           height=5, 
                           width=30,
                           relief="groove",
                           command=lambda : pick_serial_data())
    btn_take.grid(row=7, column=0, columnspan=2, pady=10)
    
    btn_stop = tk.Button(root, 
                           text="Stop Listen", 
                           height=5, 
                           width=30,
                           background="red",
                           relief="groove",
                           command=lambda : stop_serial_reading())
    btn_stop.grid(row=8, column=0, columnspan=3, pady=10)
    
    


if __name__=='__main__':
    root = tk.Tk()
    root.title("XK-3190-A9 READER PROGRAM")
    root.geometry("650x550")
    root.resizable(0.1, 0.2)
  
    dialog = tk.Toplevel(root)
    dialog.title("HASIL PENGUKURAN")
    frame = tk.Frame(dialog)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    tree = ttk.Treeview(frame, columns=(1, 2, 3), show="headings", height=2)
    
    queue_dt = queue.Queue(maxsize=100)
    stop_event = threading.Event()
    condition = True
    ser = serial.Serial()
    isPick = False
    
    ports = get_ports()
    var_option_ports = tk.StringVar(root)
    var_option_ports.set("Pilih") 
    field_port = tk.OptionMenu(root, var_option_ports, *ports)
    
    gui_window()
    root.mainloop()
    

    