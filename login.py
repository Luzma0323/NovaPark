import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import sys
from motos import crearFramesMotos
from chazas import crearFramesChazas
from bicicletas import crearFramesBicicletas
from administrativo import crearFramesAdministrativo
from database import conectar_bd_parqueaderojmj

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


def set_window_icon(window, path):
    try:
        if os.path.exists(path):
            window.iconbitmap(path)
            return
    except Exception:
        pass

    try:
        img = Image.open(path)
        photo = ImageTk.PhotoImage(img)
        window.iconphoto(False, photo)
        window._icon_photo = photo
    except Exception:
        return

def verificar_login():
    usuario = entry_usuario.get()
    clave = entry_clave.get()

    conexion = conectar_bd_parqueaderojmj()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        query = "SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?"
        cursor.execute(query, (usuario, clave))
        resultado = cursor.fetchone()

        if resultado:
            usuario_actual = resultado[7]
            clasificacion_actual = resultado[6]
            login_win.destroy()
            mostrar_principal(usuario_actual, clasificacion_actual)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")
    finally:
        conexion.close()

def mostrar_principal(usuario, clasificacion):
    root = tk.Tk()
    root.title("NovaPark")
    set_window_icon(root, resource_path("NovaPark.ico"))
    root.state('zoomed')
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    administrativo = ttk.Frame(notebook)
    notebook.add(administrativo, text="Administrativo")
    crearFramesAdministrativo(administrativo, usuario, clasificacion)

    motos = ttk.Frame(notebook)
    notebook.add(motos, text="Motos")
    crearFramesMotos(motos, usuario, clasificacion)

    chazas = ttk.Frame(notebook)
    notebook.add(chazas, text="Chazas")
    crearFramesChazas(chazas, usuario, clasificacion)

    bicicletas = ttk.Frame(notebook)
    notebook.add(bicicletas, text="Bicicletas")
    crearFramesBicicletas(bicicletas, usuario, clasificacion)

    notebook.select(motos)
    root.mainloop()

login_win = tk.Tk()
login_win.title("NovaPark")
set_window_icon(login_win, resource_path("NovaPark.ico"))

ancho, alto = 440, 300
x = (login_win.winfo_screenwidth() // 2) - (ancho // 2)
y = (login_win.winfo_screenheight() // 2) - (alto // 2)
login_win.geometry(f"{ancho}x{alto}+{x}+{y}")
login_win.resizable(False, False)

try:
    img = Image.open(resource_path("fondoLogin.png")).resize((ancho, alto))
    fondo_img = ImageTk.PhotoImage(img)
    lbl_fondo = tk.Label(login_win, image=fondo_img)
    lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    login_win.configure(bg="black")

frm_central = tk.Frame(login_win, bg="#111111", bd=0, relief="flat")
frm_central.place(relx=0.5, rely=0.5, anchor="center", width=340, height=270)

lbl_titulo = tk.Label(frm_central, text="NovaPark", bg="#111111", fg="#E5C41E", font=("Times New Roman", 20, "bold"))
lbl_titulo.pack(pady=(10, 5))

lbl_usuario = tk.Label(frm_central, text="Usuario:", bg="#111111", fg="#E5C41E", font=("Times New Roman", 15, "bold"))
lbl_usuario.pack(pady=(5, 2))

entry_usuario = tk.Entry(frm_central, width=18, font=("Times New Roman", 14), bg="#F1E7B1", fg="black", insertbackground="black", justify="center")
entry_usuario.pack(pady=5)
entry_usuario.focus_set()

def focus_to_clave(event=None):
    entry_clave.focus_set()
    return "break"
entry_usuario.bind("<Return>", focus_to_clave)

lbl_clave = tk.Label(frm_central, text="Contraseña:", bg="#111111", fg="#E5C41E", font=("Times New Roman", 15, "bold"))
lbl_clave.pack(pady=(5, 2))

entry_clave = tk.Entry(frm_central, show="*", width=18, font=("Times New Roman", 14), bg="#F1E7B1", fg="black", insertbackground="black", justify="center")
entry_clave.pack(pady=5)

def focus_to_usuario(event=None):
    if entry_clave.get() == "":
        entry_usuario.focus_set()
entry_clave.bind("<BackSpace>", focus_to_usuario)

def trigger_login(event=None):
    btn_ingresar.invoke()
    return "break"
entry_clave.bind("<Return>", trigger_login)

btn_ingresar = tk.Button(frm_central, text="Ingresar", command=verificar_login, bg="#E5C41E", fg="black", font=("Times New Roman", 15, "bold"), activebackground="black", activeforeground="#E5C41E", cursor="hand2")
btn_ingresar.pack(pady=15)

for btn in [
        btn_ingresar
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

login_win.mainloop()