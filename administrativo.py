import tkinter as tk 
import win32print
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import Scrollbar, filedialog
import os
import datetime as dt
from PIL import Image, ImageTk
from database import conectar_bd_parqueaderojmj, ejecutar_consulta
import sqlite3
import threading
from queue import Queue
from tkcalendar import DateEntry

def crearFramesAdministrativo(parent, usuario_actual, clasificacion_actual):
    def _set_rel_geometry(win, base_w, base_h):
        try:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            relw = float(base_w) / 1920.0
            relh = float(base_h) / 1080.0
            new_w = max(200, int(sw * relw))
            new_h = max(120, int(sh * relh))
            x = max(0, (sw - new_w) // 2)
            y = max(0, (sh - new_h) // 2)
            win.geometry(f"{new_w}x{new_h}+{x}+{y}")
        except Exception:
            try:
                win.geometry(f"{base_w}x{base_h}")
            except Exception:
                pass

    frmRegistro = tk.Frame(parent, bg="#86C0CA")
    frmRegistro.place(x=0, y=0, relheight=1, relwidth=1)
    frmRegistro.pack_propagate(False)

    

    lbl_fecha_hora = tk.Label(frmRegistro, font=("Times New Roman", 25, "bold"), bg="#86C0CA", fg="black")
    lbl_fecha_hora.pack(pady=20)
    
    def actualizar_fecha_hora():
        ahora = dt.datetime.now()
        dias_es = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        dia_semana = dias_es.get(ahora.strftime("%A"), ahora.strftime("%A"))
        fecha = ahora.strftime("%d/%m/%Y")
        hora = ahora.strftime("%H:%M:%S")
        lbl_fecha_hora.config(text=f"{dia_semana} {fecha} {hora}")
        lbl_fecha_hora.after(1000, actualizar_fecha_hora)

    actualizar_fecha_hora()


    frmArticulos = tk.Frame(parent, border=0, relief="solid", bg="#86C0CA")
    frmArticulos.place(x=0, y=0, relx=0, rely=0.1, relwidth=1, relheight=0.4)
    frmArticulos.pack_propagate(False)

    frameArticulosInterno = tk.Frame(frmArticulos, bg="#86C0CA")
    frameArticulosInterno.pack(expand=True)

    btnTarifas = tk.Button(frameArticulosInterno, text="Tarifas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnArqueoDeCaja = tk.Button(frameArticulosInterno, text="Arqueo de Caja", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnInventario = tk.Button(frameArticulosInterno, text="Inventario", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnFacturasDeCompra = tk.Button(frameArticulosInterno, text="Facturas de Compra", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")

    btnTarifas.grid(row=0, column=0, padx=50, pady=20)
    btnArqueoDeCaja.grid(row=0, column=1, padx=50, pady=20)
    btnInventario.grid(row=1, column=0, padx=50, pady=20)
    btnFacturasDeCompra.grid(row=1, column=1, padx=50, pady=20)

    for btn in [
        btnTarifas,
        btnArqueoDeCaja,
        btnInventario,
        btnFacturasDeCompra,
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="#1B1B1B", fg="white"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="white", fg="black"))

    def arqueo_general():
        if clasificacion_actual == "Usuario":
            messagebox.showerror("Error", "No tienes permiso para realizar un arqueo de caja.")
            return

        class FechaDialog(simpledialog.Dialog):
            def body(self, master):
                hoy = dt.datetime.now().strftime('%Y-%m-%d')
                tk.Label(master, text="Fecha inicial:").grid(row=0, column=0, padx=5, pady=5)
                tk.Label(master, text="Fecha final:").grid(row=1, column=0, padx=5, pady=5)
                self.fecha_inicial = tk.Entry(master)
                self.fecha_final = tk.Entry(master)
                self.fecha_inicial.insert(0, hoy)
                self.fecha_final.insert(0, hoy)
                self.fecha_inicial.grid(row=0, column=1, padx=5, pady=5)
                self.fecha_final.grid(row=1, column=1, padx=5, pady=5)
                return self.fecha_inicial
            def apply(self):
                self.result = (self.fecha_inicial.get(), self.fecha_final.get())

        root = frmRegistro.winfo_toplevel()
        dlg = FechaDialog(root, title="Arqueo de Caja")
        if dlg.result is None:
            return
        fecha_ini, fecha_fin = dlg.result

        def consultar_pagos(tabla):
            efectivo = 0
            nequi = 0
            bancolombia = 0
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                return efectivo, nequi, bancolombia
            try:
                cursor = conexion.cursor()
                query = f'''SELECT medio_pago, SUM(valor) FROM {tabla} WHERE date(fecha) >= ? AND date(fecha) <= ? GROUP BY medio_pago'''
                cursor.execute(query, (fecha_ini, fecha_fin))
                for medio, total in cursor.fetchall():
                    try:
                        t = float(total or 0)
                    except Exception:
                        t = 0
                    medio_norm = (str(medio or '')).strip().lower()
                    if medio_norm == 'efectivo':
                        efectivo = t
                    elif medio_norm == 'nequi':
                        nequi = t
                    elif medio_norm == 'bancolombia':
                        bancolombia = t
            except Exception as e:
                messagebox.showerror("Error", f"Error al consultar pagos en {tabla}: {e}", parent=root)
            finally:
                if conexion:
                    conexion.close()
            return efectivo, nequi, bancolombia

        motos = consultar_pagos('pagos')
        chazas = consultar_pagos('pagosChazas')
        bicicletas = consultar_pagos('pagosBicicletas')

        efectivo_motos, nequi_motos, banco_motos = motos
        efectivo_chazas, nequi_chazas, banco_chazas = chazas
        efectivo_bicis, nequi_bicis, banco_bicis = bicicletas

        total_motos = (efectivo_motos or 0) + (nequi_motos or 0) + (banco_motos or 0)
        total_chazas = (efectivo_chazas or 0) + (nequi_chazas or 0) + (banco_chazas or 0)
        total_bicis = (efectivo_bicis or 0) + (nequi_bicis or 0) + (banco_bicis or 0)
        total_efectivo = (efectivo_motos or 0) + (efectivo_chazas or 0) + (efectivo_bicis or 0)
        total_nequi = (nequi_motos or 0) + (nequi_chazas or 0) + (nequi_bicis or 0)
        total_banco = (banco_motos or 0) + (banco_chazas or 0) + (banco_bicis or 0)
        total_general = total_motos + total_chazas + total_bicis

        resumen = tk.Toplevel(root)
        resumen.title("Arqueo de Caja - General")
        _set_rel_geometry(resumen, 500, 700)
        hoy_str = dt.datetime.now().strftime('%d/%m/%Y')

        info = f"{hoy_str}\nParqueadero JMJ\nNIT: 87715766-9\nDireccion: Carrera 43 #52-36\n\n"
        info += f"Fecha inicial: {fecha_ini}\nFecha final: {fecha_fin}\n\n\n"
        line_width = 32
        title = "ARQUEO GENERAL"
        info += title.center(line_width)
        info += "\n\n"
        info += "VENTAS / FACTURACION\n\n"

        info += "Motos:\n"
        info += f"Efectivo: ${efectivo_motos:,.0f}\n"
        if nequi_motos > 0:
            info += f"Nequi: ${nequi_motos:,.0f}\n"
        if banco_motos > 0:
            info += f"Bancolombia: ${banco_motos:,.0f}\n"
        info += f"TOTAL: ${total_motos:,.0f}\n\n"

        info += "Chazas:\n"
        info += f"Efectivo: ${efectivo_chazas:,.0f}\n"
        if nequi_chazas > 0:
            info += f"Nequi: ${nequi_chazas:,.0f}\n"
        if banco_chazas > 0:
            info += f"Bancolombia: ${banco_chazas:,.0f}\n"
        info += f"TOTAL: ${total_chazas:,.0f}\n\n"

        info += "Bicicletas:\n"
        info += f"Efectivo: ${efectivo_bicis:,.0f}\n"
        if nequi_bicis > 0:
            info += f"Nequi: ${nequi_bicis:,.0f}\n"
        if banco_bicis > 0:
            info += f"Bancolombia: ${banco_bicis:,.0f}\n"
        info += f"TOTAL: ${total_bicis:,.0f}\n\n"

        info += f"TOTAL EFECTIVO: ${total_efectivo:,.0f}\n"
        if total_nequi > 0:
            info += f"TOTAL NEQUI: ${total_nequi:,.0f}\n"
        if total_banco > 0:
            info += f"TOTAL BANCOLOMBIA: ${total_banco:,.0f}\n"
        info += "\n"
        info += f"TOTAL: ${total_general:,.0f}\n"
        info += "\n" * 4

        canvas = tk.Canvas(resumen, borderwidth=0, background="white", height=700)
        frame_scroll = tk.Frame(canvas, background="white")
        vsb = tk.Scrollbar(resumen, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0,0), window=frame_scroll, anchor="nw")

        def onFrameConfigure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame_scroll.bind("<Configure>", onFrameConfigure)

        lbl = tk.Label(frame_scroll, text=info, font=("Times New Roman", 13), justify="left", bg="white")
        lbl.pack(padx=20, pady=20)

        def imprimir_ventana():
            try:
                import win32print
                printer_name = 'Xprinter Receipt Printer'
                hPrinter = None
                try:
                    try:
                        hPrinter = win32print.OpenPrinter(printer_name)
                    except Exception:
                        try:
                            default_printer = win32print.GetDefaultPrinter()
                            hPrinter = win32print.OpenPrinter(default_printer)
                        except Exception:
                            hPrinter = None

                    if not hPrinter:
                        raise RuntimeError('No se encontró una impresora disponible.')

                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("ArqueoCajaGeneral.txt", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    texto = info.replace('\n', '\r\n')
                    win32print.WritePrinter(hPrinter, texto.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    if hPrinter:
                        win32print.ClosePrinter(hPrinter)

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo imprimir en la impresora: {e}", parent=resumen)

        btn_imprimir = tk.Button(frame_scroll, text="Imprimir", font=("Times New Roman", 13, "bold"), bg="#86C0CA", fg="black", cursor="hand2", command=imprimir_ventana)
        btn_imprimir.pack(pady=50)

        btn_imprimir.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btn_imprimir.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        # Keyboard shortcuts: Escape closes, Enter triggers imprimir
        try:
            resumen.bind('<Escape>', lambda e: resumen.destroy())
            resumen.bind('<Return>', lambda e: btn_imprimir.invoke())
            btn_imprimir.focus_set()
        except Exception:
            pass

        resumen.transient(root)
        resumen.grab_set()
        resumen.wait_window()

    btnArqueoDeCaja.config(command=arqueo_general)

    frmPersonas = tk.Frame(parent, border=0, relief="solid", bg="#6EA1AB")
    frmPersonas.place(x=0, y=0, relx=0, rely=0.5, relwidth=1, relheight=0.5)
    frmPersonas.pack_propagate(False)

    framePersonasInterno = tk.Frame(frmPersonas, bg="#6EA1AB")
    framePersonasInterno.pack(expand=True)

    framePersonasTop = tk.Frame(framePersonasInterno, bg="#6EA1AB")
    framePersonasTop.pack(pady=25)
    framePersonasBottom = tk.Frame(framePersonasInterno, bg="#6EA1AB")
    framePersonasBottom.pack(pady=25)

    imgAdministrativo = Image.open("iconoAdministrativo.ico").resize((100, 100))
    iconoAdministrativo = ImageTk.PhotoImage(imgAdministrativo)
    lblIconoAdministrativo = tk.Label(frmPersonas, image=iconoAdministrativo, bg="#6EA1AB")
    lblIconoAdministrativo.image = iconoAdministrativo
    lblIconoAdministrativo.place(relx=0, rely=1, anchor="sw", x=10, y=-15)

    lblCopyright = tk.Label(frmPersonas, text="© TODOS LOS DERECHOS RESERVADOS || BRAULIO NARVÁEZ MARTÍNEZ || 2025", font=("Times New Roman", 10, "bold"), bg="#6EA1AB", fg="black")
    lblCopyright.pack(side="bottom", fill="x")

    inicial = usuario_actual.strip()[0].upper() if usuario_actual else "N"
    if inicial not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        inicial = "N"
    icono_path = f"{inicial}.png"
    try:
        imgUsuario = Image.open(icono_path).resize((90, 90))
    except Exception:
        imgUsuario = Image.open("N.png").resize((90, 90))
    iconoUsuario = ImageTk.PhotoImage(imgUsuario)
    lblIconoUsuario = tk.Label(frmPersonas, image=iconoUsuario, bg="#6EA1AB")
    lblIconoUsuario.image = iconoUsuario
    lblIconoUsuario.place(relx=0.91, rely=0.98, anchor="sw", x=10, y=-15)

    btnClientes = tk.Button(framePersonasTop, text="Clientes", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnProveedores = tk.Button(framePersonasTop, text="Proveedores", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnUsuarios = tk.Button(framePersonasTop, text="Usuarios", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnBackupBD = tk.Button(framePersonasBottom, text="Copia de Seguridad", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnRestaurarBD = tk.Button(framePersonasBottom, text="Restaurar BD", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")

    btnClientes.grid(row=0, column=0, padx=18)
    btnProveedores.grid(row=0, column=1, padx=18)
    btnUsuarios.grid(row=0, column=2, padx=18)
    btnBackupBD.grid(row=0, column=0, padx=18)
    btnRestaurarBD.grid(row=0, column=1, padx=18)

    for btn in [
        btnClientes,
        btnProveedores,
        btnUsuarios,
        btnBackupBD,
        btnRestaurarBD,
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="#1B1B1B", fg="white"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="white", fg="black"))

    def _show_progress_dialog(title, subtitle=""):
        dlg = tk.Toplevel(frmRegistro.winfo_toplevel())
        dlg.title(title)
        _set_rel_geometry(dlg, 420, 120)
        lbl = tk.Label(dlg, text=subtitle, font=("Times New Roman", 12))
        lbl.pack(pady=(10, 5))
        pb = ttk.Progressbar(dlg, length=360, mode="determinate")
        pb.pack(pady=(5, 10))
        return dlg, pb, lbl

    def _run_backup_thread(origen, destino_path, q):
        try:
            src = sqlite3.connect(origen)
            dst = sqlite3.connect(destino_path)

            def progress(status, remaining, total):
                q.put((remaining, total))

            src.backup(dst, pages=100, progress=progress)
            src.close()
            dst.close()
            q.put(("done", destino_path))
        except Exception as e:
            q.put(("error", str(e)))

    def hacer_backup():
        if clasificacion_actual == "Usuario":
            messagebox.showerror("Error", "No tienes permiso para realizar una copia de seguridad.", parent=frmRegistro.winfo_toplevel())
            return

        destino = filedialog.askdirectory(title="Seleccione la carpeta destino para el backup (conecte su USB)")
        if not destino:
            return

        try:
            origen = os.path.abspath("parqueaderojmj.db")
            if not os.path.exists(origen):
                messagebox.showerror("Error", f"Archivo de base de datos no encontrado: {origen}", parent=frmRegistro.winfo_toplevel())
                return

            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"parqueaderojmj_backup_{ts}.db"
            destino_path = os.path.join(destino, nombre_backup)

            q = Queue()
            dlg, pb, lbl = _show_progress_dialog("Backup en progreso", f"Guardando: {os.path.basename(destino_path)}")
            pb['value'] = 0

            thread = threading.Thread(target=_run_backup_thread, args=(origen, destino_path, q), daemon=True)
            thread.start()

            def poll():
                try:
                    item = q.get_nowait()
                except Exception:
                    dlg.after(200, poll)
                    return

                if item[0] == 'done':
                    dlg.destroy()
                    messagebox.showinfo("Backup completado", f"Copia de seguridad guardada en: {item[1]}", parent=frmRegistro.winfo_toplevel())
                elif item[0] == 'error':
                    dlg.destroy()
                    messagebox.showerror("Error", f"No se pudo realizar el backup: {item[1]}", parent=frmRegistro.winfo_toplevel())
                else:
                    remaining, total = item
                    try:
                        total = int(total)
                        remaining = int(remaining)
                        done = total - remaining
                        if total > 0:
                            pb['maximum'] = total
                            pb['value'] = done
                    except Exception:
                        pass
                    dlg.after(100, poll)

            dlg.after(100, poll)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el backup: {e}", parent=frmRegistro.winfo_toplevel())

    btnBackupBD.config(command=hacer_backup)

    def _run_restore_thread(src_file, origen_actual, q):
        try:
            src = sqlite3.connect(src_file)
            dst = sqlite3.connect(origen_actual)

            def progress(status, remaining, total):
                q.put((remaining, total))

            src.backup(dst, pages=100, progress=progress)
            src.close()
            dst.close()
            q.put(("done", origen_actual))
        except Exception as e:
            q.put(("error", str(e)))

    def restaurar_bd():
        if clasificacion_actual == "Usuario":
            messagebox.showerror("Error", "No tienes permiso para restaurar la base de datos.", parent=frmRegistro.winfo_toplevel())
            return

        archivo = filedialog.askopenfilename(title="Seleccione archivo .db de backup para restaurar", filetypes=[("SQLite DB", "*.db"), ("Todos los archivos", "*.*")])
        if not archivo:
            return

        confirm = messagebox.askyesno("Confirmar restauración", f"Va a restaurar la base de datos desde:\n{archivo}\nSe creará antes una copia de seguridad del estado actual. ¿Desea continuar?", parent=frmRegistro.winfo_toplevel())
        if not confirm:
            return

        try:
            origen_actual = os.path.abspath("parqueaderojmj.db")
            if not os.path.exists(origen_actual):
                messagebox.showerror("Error", f"Archivo de base de datos no encontrado: {origen_actual}", parent=frmRegistro.winfo_toplevel())
                return

            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_backup = os.path.join(os.path.dirname(origen_actual), f"parqueaderojmj_pre_restore_{ts}.db")
            q_pre = Queue()
            dlg_pre, pb_pre, lbl_pre = _show_progress_dialog("Preparando copia previa", f"Guardando copia previa: {os.path.basename(pre_backup)}")
            thread_pre = threading.Thread(target=_run_backup_thread, args=(origen_actual, pre_backup, q_pre), daemon=True)
            thread_pre.start()

            def poll_pre():
                try:
                    item = q_pre.get_nowait()
                except Exception:
                    dlg_pre.after(200, poll_pre)
                    return

                if item[0] == 'done':
                    dlg_pre.destroy()
                    q = Queue()
                    dlg, pb, lbl = _show_progress_dialog("Restauración en progreso", f"Restaurando desde: {os.path.basename(archivo)}")
                    thread = threading.Thread(target=_run_restore_thread, args=(archivo, origen_actual, q), daemon=True)
                    thread.start()

                    def poll():
                        try:
                            it = q.get_nowait()
                        except Exception:
                            dlg.after(200, poll)
                            return

                        if it[0] == 'done':
                            dlg.destroy()
                            messagebox.showinfo("Restauración completa", f"Base restaurada desde: {archivo}\nCopia previa guardada en: {pre_backup}", parent=frmRegistro.winfo_toplevel())
                        elif it[0] == 'error':
                            dlg.destroy()
                            messagebox.showerror("Error", f"No se pudo restaurar la base de datos: {it[1]}", parent=frmRegistro.winfo_toplevel())
                        else:
                            remaining, total = it
                            try:
                                total = int(total)
                                remaining = int(remaining)
                                done = total - remaining
                                if total > 0:
                                    pb['maximum'] = total
                                    pb['value'] = done
                            except Exception:
                                pass
                            dlg.after(100, poll)

                    dlg.after(100, poll)
                elif item[0] == 'error':
                    dlg_pre.destroy()
                    messagebox.showerror("Error", f"No se pudo crear copia previa: {item[1]}", parent=frmRegistro.winfo_toplevel())
                else:
                    remaining, total = item
                    try:
                        total = int(total)
                        remaining = int(remaining)
                        done = total - remaining
                        if total > 0:
                            pb_pre['maximum'] = total
                            pb_pre['value'] = done
                    except Exception:
                        pass
                    dlg_pre.after(100, poll_pre)

            dlg_pre.after(100, poll_pre)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar la restauración: {e}", parent=frmRegistro.winfo_toplevel())

    btnRestaurarBD.config(command=restaurar_bd)

    def gestionar_usuarios():
        ventana_usuarios = tk.Toplevel()
        ventana_usuarios.title("Gestión de Usuarios")
        _set_rel_geometry(ventana_usuarios, 800, 600)
        ventana_usuarios.bind('<Escape>', lambda e: ventana_usuarios.destroy())
        root = ventana_usuarios

        frame_tabla = tk.Frame(ventana_usuarios)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID", "Nombre Completo", "Cédula", "Correo", "Teléfono", "Dirección", "Clasificación", "Usuario", "Contraseña"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Nombre Completo", text="Nombre Completo")
        tree.heading("Cédula", text="Cédula")
        tree.heading("Correo", text="Correo")
        tree.heading("Teléfono", text="Teléfono")
        tree.heading("Dirección", text="Dirección")
        tree.heading("Clasificación", text="Clasificación")
        tree.heading("Usuario", text="Usuario")
        tree.heading("Contraseña", text="Contraseña")

        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre Completo", width=150, anchor="center")
        tree.column("Cédula", width=100, anchor="center")
        tree.column("Correo", width=150, anchor="center")
        tree.column("Teléfono", width=100, anchor="center")
        tree.column("Dirección", width=150, anchor="center")
        tree.column("Clasificación", width=100, anchor="center")
        tree.column("Usuario", width=100, anchor="center")
        tree.column("Contraseña", width=100, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_usuarios():
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.", parent=root)
                return
            try:
                cursor = conexion.cursor()
                if clasificacion_actual == "Superusuario":
                    cursor.execute("SELECT idUsuarios, nombreCompleto, cedula, correo, telefono, direccion, clasificacion, usuario, '********' FROM usuarios")
                elif clasificacion_actual == "Usuario":
                    cursor.execute("SELECT idUsuarios, nombreCompleto, cedula, correo, telefono, direccion, clasificacion, usuario, '********' FROM usuarios WHERE usuario = ? AND clasificacion != 'Superusuario'", (usuario_actual,))
                elif clasificacion_actual == "Usuario avanzado":
                    cursor.execute("SELECT idUsuarios, nombreCompleto, cedula, correo, telefono, direccion, clasificacion, usuario, '********' FROM usuarios WHERE (usuario = ? OR clasificacion = 'Usuario') AND clasificacion != 'Superusuario'", (usuario_actual,))
                else:
                    cursor.execute("SELECT idUsuarios, nombreCompleto, cedula, correo, telefono, direccion, clasificacion, usuario, '********' FROM usuarios WHERE clasificacion != 'Superusuario'")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", "", "", "", ""), tags=("oddrow",))
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar usuarios: {e}", parent=root)
            finally:
                conexion.close()
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()

        def eliminar_usuario():
            if clasificacion_actual != "Superusuario" or usuario_actual != "Usuario avanzado":
                messagebox.showerror("Error", "No tienes permiso para eliminar usuarios.", parent=root)
                ventana_usuarios.focus_set()
                return

            item = tree.focus()

            valores = tree.item(item, "values")
            if valores[0] == "":
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.", parent=root)
                ventana_usuarios.focus_set()
                return
            
            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al usuario {valores[1]}?", parent=root)
            if not confirmacion:
                try:
                    ventana_usuarios.focus_set()
                except Exception:
                    pass
                return

            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.", parent=root)
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM usuarios WHERE idUsuarios=?", (valores[0],))
                conexion.commit()
                cargar_usuarios()
                try:
                    root.deiconify()
                    root.lift()
                    root.focus_force()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {e}", parent=root)
            finally:
                conexion.close()

        def formulario_usuario(datos=None, modo="agregar", mostrar_usuario_contrasena=True, only_user_pass=False):
            win = tk.Toplevel(root)
            win.title("Formulario de Usuario")
            _set_rel_geometry(win, 400, 420)
            win.grab_set()
            win.focus_force()
            # Build labels/claves depending on visibility flags
            if only_user_pass:
                labels = ["Usuario", "Contraseña"]
                claves = ["usuario", "contrasena"]
            else:
                labels = ["Nombre Completo", "Cédula", "Correo", "Teléfono", "Dirección", "Clasificación"]
                claves = ["nombreCompleto", "cedula", "correo", "telefono", "direccion", "clasificacion"]
                if mostrar_usuario_contrasena:
                    labels += ["Usuario", "Contraseña"]
                    claves += ["usuario", "contrasena"]
            entries = []
            valores = []
            # Validadores para entradas: usan validate='key' para bloquear inserciones inválidas (incluye paste).
            def vc_uppercase(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                # Si el texto propuesto no está en mayúsculas, reemplazarlo por su versión en mayúsculas
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_nombre(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                # Rechazar si contiene algo que no sea letra o espacio
                if not all(c.isalpha() or c.isspace() for c in proposed):
                    return False
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_digits(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                return proposed.isdigit()

            vcmd_upper = win.register(vc_uppercase)
            vcmd_nombre = win.register(vc_nombre)
            vcmd_digits = win.register(vc_digits)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
                if key == "clasificacion":
                    cb = ttk.Combobox(win, values=["Superusuario", "Usuario avanzado", "Usuario"], state="readonly")
                    if datos:
                        cb.set(datos.get(key, "Usuario"))
                    else:
                        cb.set("Usuario")
                    cb.grid(row=i, column=1, padx=8, pady=6)
                    entries.append(cb)
                else:
                    var = tk.StringVar()
                    ent = tk.Entry(win, textvariable=var, show="*" if key=="contrasena" else None)
                    if datos:
                        # Only set usuario/contrasena if they are visible in this form
                        if key in datos or key not in ["usuario", "contrasena"]:
                            var.set(str(datos.get(key, "")))
                    ent.grid(row=i, column=1, padx=8, pady=6)
                    if key == "nombreCompleto":
                        ent.configure(validate="key", validatecommand=(vcmd_nombre, "%P", "%W"))
                    elif key in ["correo", "direccion"]:
                        ent.configure(validate="key", validatecommand=(vcmd_upper, "%P", "%W"))
                    elif key in ["cedula", "telefono"]:
                        ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                    entries.append(ent)
            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if isinstance(entries[idx+1], tk.Entry):
                        entries[idx+1].icursor("end")
                else:
                    guardar()
                return "break"
            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if isinstance(entries[idx-1], tk.Entry):
                        entries[idx-1].icursor("end")
                return "break"
            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    if isinstance(widget, tk.Entry) and widget.get() == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"
            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))
            entries[0].focus_set()
            # Colocar el cursor al final del contenido del primer entry (si el widget soporta icursor)
            try:
                if hasattr(entries[0], 'icursor'):
                    entries[0].icursor(tk.END)
            except Exception:
                pass
            def guardar():
                datos_usuario = {}
                # Collect values for present keys
                for i, key in enumerate(claves):
                    # Comboboxes and Entries both have get()
                    val = entries[i].get()
                    # Basic validations depending on key
                    if key in ["cedula", "telefono"]:
                        if val.strip() == "":
                            messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                            entries[i].focus_set()
                            return
                        if not val.isdigit():
                            messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                    if key == "nombreCompleto":
                        if any(c.isdigit() for c in val):
                            messagebox.showerror("Error", "El campo Nombre Completo no debe contener números.", parent=win)
                            entries[i].focus_set()
                            return
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    datos_usuario[key] = val.strip()

                if modo == "editar" and isinstance(datos, dict) and datos.get("idUsuarios"):
                    datos_usuario["idUsuarios"] = datos.get("idUsuarios")

                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        messagebox.showerror("Error", "No se pudo conectar a la base de datos.", parent=win)
                        return
                    cursor = conexion.cursor()
                    if modo == "agregar":
                        # Ensure usuario and contrasena provided when adding
                        if "usuario" not in datos_usuario or "contrasena" not in datos_usuario:
                            messagebox.showerror("Error", "Debe proporcionar usuario y contraseña al agregar.", parent=win)
                            return
                        cursor.execute(
                            "INSERT INTO usuarios (nombreCompleto, cedula, correo, telefono, direccion, clasificacion, usuario, contrasena) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                datos_usuario.get("nombreCompleto"), datos_usuario.get("cedula"), datos_usuario.get("correo"),
                                datos_usuario.get("telefono"), datos_usuario.get("direccion"), datos_usuario.get("clasificacion"),
                                datos_usuario.get("usuario"), datos_usuario.get("contrasena")
                            )
                        )
                    else:
                        # Build update dynamically based on which fields are present in datos_usuario
                        set_cols = []
                        params = []
                        updatable_order = ["nombreCompleto", "cedula", "correo", "telefono", "direccion", "clasificacion"]
                        for k in updatable_order:
                            if k in datos_usuario:
                                set_cols.append(f"{k} = ?")
                                params.append(datos_usuario[k])
                        # include usuario/contrasena only if visible in form
                        if mostrar_usuario_contrasena and "usuario" in datos_usuario and "contrasena" in datos_usuario:
                            set_cols.append("usuario = ?")
                            params.append(datos_usuario["usuario"])
                            set_cols.append("contrasena = ?")
                            params.append(datos_usuario["contrasena"])

                        if not set_cols:
                            messagebox.showerror("Error", "No hay campos para actualizar.", parent=win)
                            return

                        query = f"UPDATE usuarios SET {', '.join(set_cols)} WHERE idUsuarios = ?"
                        params.append(datos_usuario["idUsuarios"])
                        cursor.execute(query, tuple(params))

                    conexion.commit()
                    win.destroy()
                    cargar_usuarios()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar usuario: {e}", parent=win)
                finally:
                    if 'conexion' in locals():
                        conexion.close()
            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_usuario():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar usuarios.", parent=root)
                return
            formulario_usuario()

        def editar_usuario_formulario(event):
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            # Permisos y visibilidad exacta solicitada:
            # - Usuario: solo puede editar su propio registro y SOLO usuario+contraseña
            # - Usuario avanzado: puede editar TODO de su propio registro (incluye usuario+contraseña),
            #   y puede editar otros usuarios de clasificación 'Usuario' pero SIN poder ver/editar su usuario/contraseña
            # - Superusuario: acceso completo (se muestra todo)

            # Extraer datos básicos de la fila
            claves = ["nombreCompleto", "cedula", "correo", "telefono", "direccion", "clasificacion", "usuario", "contrasena"]
            datos = {k: v for k, v in zip(claves, valores[1:])}
            datos["idUsuarios"] = valores[0]

            fila_clasificacion = valores[6]
            fila_usuario = valores[7]

            # Caso: Usuario (normal)
            if clasificacion_actual == "Usuario":
                # Solo puede editar su propio registro
                if fila_usuario != usuario_actual:
                    messagebox.showerror("Error", "No tienes permiso para editar otros usuarios.", parent=root)
                    return
                # Abrir solo campos usuario+contrasena
                formulario_usuario(datos, modo="editar", mostrar_usuario_contrasena=True, only_user_pass=True)
                return

            # Caso: Usuario avanzado
            if clasificacion_actual == "Usuario avanzado":
                # Si es su propio registro: puede editar todo, incluido usuario+contrasena
                if fila_usuario == usuario_actual:
                    formulario_usuario(datos, modo="editar", mostrar_usuario_contrasena=True, only_user_pass=False)
                    return
                # Si edita a otro usuario normal: puede editar el resto de campos, pero NO usuario/contrasena
                if fila_clasificacion == "Usuario":
                    formulario_usuario(datos, modo="editar", mostrar_usuario_contrasena=False, only_user_pass=False)
                    return
                # No permitido editar otros avanzados o superusuarios
                messagebox.showerror("Error", "No tienes permiso para editar este usuario.", parent=root)
                return

            # Superusuario y demás: acceso completo por defecto
            formulario_usuario(datos, modo="editar", mostrar_usuario_contrasena=True, only_user_pass=False)

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_usuario_formulario)

        btn_agregar = tk.Button(ventana_usuarios, text="Agregar Usuario", command=agregar_usuario, cursor="hand2", background="#86C0CA", fg="black")
        btn_agregar.pack(side="left", padx=10, pady=10)

        btn_eliminar = tk.Button(ventana_usuarios, text="Eliminar Usuario", command=eliminar_usuario, cursor="hand2", background="#86C0CA", fg="black")
        btn_eliminar.pack(side="left", padx=10, pady=10)

        btn_agregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btn_agregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btn_eliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btn_eliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        cargar_usuarios()

    btnUsuarios.config(command=gestionar_usuarios)

    def gestionar_clientes():
        ventana_clientes = tk.Toplevel()
        ventana_clientes.title("Gestión de Clientes")
        _set_rel_geometry(ventana_clientes, 800, 600)
        ventana_clientes.bind('<Escape>', lambda e: ventana_clientes.destroy())

        frame_tabla = tk.Frame(ventana_clientes)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID", "Nombre Completo", "Cédula", "Correo", "Teléfono", "Dirección"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Nombre Completo", text="Nombre Completo")
        tree.heading("Cédula", text="Cédula")
        tree.heading("Correo", text="Correo")
        tree.heading("Teléfono", text="Teléfono")
        tree.heading("Dirección", text="Dirección")

        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre Completo", width=150, anchor="center")
        tree.column("Cédula", width=100, anchor="center")
        tree.column("Correo", width=150, anchor="center")
        tree.column("Teléfono", width=100, anchor="center")
        tree.column("Dirección", width=150, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_clientes():
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                if clasificacion_actual == "Usuario":
                    cursor.execute("SELECT idClientes, nombreCompleto, '***', '***', telefono, '***' FROM clientes")
                else:
                    cursor.execute("SELECT idClientes, nombreCompleto, cedula, correo, telefono, direccion FROM clientes")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", ""), tags=("oddrow",))
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar clientes: {e}", parent=ventana_clientes)
            finally:
                conexion.close()
            if tree.get_children():
                first_item = tree.get_children()[0]
                tree.focus(first_item)
                tree.selection_set(first_item)
                tree.see(first_item)
                tree.focus_set()

        def formulario_cliente(datos=None, modo="agregar"):
            win = tk.Toplevel(ventana_clientes)
            win.title("Formulario de Cliente")
            _set_rel_geometry(win, 420, 300)
            win.grab_set()
            win.focus_force()

            labels = ["Nombre Completo", "Cédula", "Correo", "Teléfono", "Dirección"]
            claves = ["nombreCompleto", "cedula", "correo", "telefono", "direccion"]
            entries = []

            def vc_uppercase(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_nombre(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                if not all(c.isalpha() or c.isspace() for c in proposed):
                    return False
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_digits(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                return proposed.isdigit()

            vcmd_upper = win.register(vc_uppercase)
            vcmd_nombre = win.register(vc_nombre)
            vcmd_digits = win.register(vc_digits)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":" ).grid(row=i, column=0, sticky="e", padx=8, pady=6)
                var = tk.StringVar()
                ent = tk.Entry(win, textvariable=var)
                if datos:
                    var.set(str(datos.get(key, "")))
                ent.grid(row=i, column=1, padx=8, pady=6)
                if key == "nombreCompleto":
                    ent.configure(validate="key", validatecommand=(vcmd_nombre, "%P", "%W"))
                elif key in ["correo", "direccion"]:
                    ent.configure(validate="key", validatecommand=(vcmd_upper, "%P", "%W"))
                elif key in ["cedula", "telefono"]:
                    ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                entries.append(ent)

            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if hasattr(entries[idx+1], 'icursor'):
                        entries[idx+1].icursor(tk.END)
                else:
                    guardar()
                return "break"

            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if hasattr(entries[idx-1], 'icursor'):
                        entries[idx-1].icursor(tk.END)
                return "break"

            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    try:
                        val = widget.get()
                    except Exception:
                        val = ""
                    if val == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"

            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))

            entries[0].focus_set()
            try:
                # If opening in edit mode (datos provided), place cursor at the end of the first entry
                if hasattr(entries[0], 'icursor') and datos:
                    entries[0].icursor(tk.END)
            except Exception:
                pass
            try:
                if hasattr(entries[0], 'icursor'):
                    entries[0].icursor(tk.END)
            except Exception:
                pass

            def guardar():
                datos_cliente = {}
                for i, key in enumerate(claves):
                    val = entries[i].get()
                    if key in ["cedula", "telefono"]:
                        if val.strip() == "":
                            messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                            entries[i].focus_set()
                            return
                        if not val.isdigit():
                            messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                    if key == "nombreCompleto":
                        if any(c.isdigit() for c in val):
                            messagebox.showerror("Error", "El campo Nombre Completo no debe contener números.", parent=win)
                            entries[i].focus_set()
                            return
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    datos_cliente[key] = val.strip()

                try:
                    if modo == "agregar":
                        query = "INSERT INTO clientes (nombreCompleto, cedula, correo, telefono, direccion) VALUES (?, ?, ?, ?, ?)"
                        parametros = (
                            datos_cliente["nombreCompleto"],
                            datos_cliente["cedula"],
                            datos_cliente["correo"],
                            datos_cliente["telefono"],
                            datos_cliente["direccion"]
                        )
                        resultado = ejecutar_consulta(query, parametros)
                    else:
                        # modo editar: datos debe contener idClientes
                        query = "UPDATE clientes SET nombreCompleto=?, cedula=?, correo=?, telefono=?, direccion=? WHERE idClientes=?"
                        parametros = (
                            datos_cliente["nombreCompleto"],
                            datos_cliente["cedula"],
                            datos_cliente["correo"],
                            datos_cliente["telefono"],
                            datos_cliente["direccion"],
                            datos.get("idClientes")
                        )
                        resultado = ejecutar_consulta(query, parametros)

                    if resultado:
                        win.destroy()
                        cargar_clientes()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar cliente: {e}", parent=win)

            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_cliente():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar clientes.", parent=ventana_clientes)
                return
            formulario_cliente()

        def editar_cliente_formulario(event):
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            # permisos: Usuario no puede editar
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para editar clientes.", parent=ventana_clientes)
                return
            datos = {
                "nombreCompleto": valores[1],
                "cedula": valores[2],
                "correo": valores[3],
                "telefono": valores[4],
                "direccion": valores[5],
                "idClientes": valores[0]
            }
            formulario_cliente(datos, modo="editar")

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_cliente_formulario)

        def eliminar_cliente():
            if clasificacion_actual != "Superusuario" or usuario_actual != "Usuario avanzado":
                messagebox.showerror("Error", "No tienes permiso para eliminar usuarios.")
                ventana_clientes.focus_set()
                return

            item = tree.focus()

            valores = tree.item(item, "values")
            if not valores[0]:
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.")
                ventana_clientes.focus_set()
                return

            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al cliente {valores[1]}?", parent=ventana_clientes)
            if not confirmacion:
                try:
                    ventana_clientes.focus_set()
                except Exception:
                    pass
                return

            query = "DELETE FROM clientes WHERE idClientes = ?"
            parametros = (valores[0],)
            resultado = ejecutar_consulta(query, parametros)
            if resultado:
                cargar_clientes()
                try:
                    ventana_clientes.deiconify()
                    ventana_clientes.lift()
                    ventana_clientes.focus_force()
                except Exception:
                    pass

        btnAgregar = tk.Button(ventana_clientes, text="Agregar Cliente", command=agregar_cliente, cursor="hand2", background="#86C0CA", fg="black")
        btnAgregar.pack(side="left", padx=10, pady=10)

        btnEliminar = tk.Button(ventana_clientes, text="Eliminar Cliente", command=eliminar_cliente, cursor="hand2", background="#86C0CA", fg="black")
        btnEliminar.pack(side="left", padx=10, pady=10)

        btnAgregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnAgregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btnEliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnEliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        cargar_clientes()

    btnClientes.config(command=gestionar_clientes)


    def gestionar_proveedores():
        ventana_proveedores = tk.Toplevel()
        ventana_proveedores.title("Gestión de Proveedores")
        _set_rel_geometry(ventana_proveedores, 800, 600)
        ventana_proveedores.bind('<Escape>', lambda e: ventana_proveedores.destroy())

        frame_tabla = tk.Frame(ventana_proveedores)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID","Razón Social", "NIT", "Correo", "Teléfono", "Dirección"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Razón Social", text="Razón Social")
        tree.heading("NIT", text="NIT")
        tree.heading("Correo", text="Correo")
        tree.heading("Teléfono", text="Teléfono")
        tree.heading("Dirección", text="Dirección")

        tree.column("ID", width=50, anchor="center")
        tree.column("Razón Social", width=150, anchor="center")
        tree.column("NIT", width=100, anchor="center")
        tree.column("Correo", width=150, anchor="center")
        tree.column("Teléfono", width=100, anchor="center")
        tree.column("Dirección", width=150, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_proveedores():
            ventana_proveedores.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idProveedores, razonSocial, nit, correo, telefono, direccion FROM proveedores")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", ""), tags=("oddrow",))
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar proveedores: {e}", parent=ventana_proveedores)
            finally:
                conexion.close()

        def formulario_proveedor(datos=None, modo="agregar"):
            win = tk.Toplevel(ventana_proveedores)
            win.title("Formulario de Proveedor")
            _set_rel_geometry(win, 420, 320)
            win.grab_set()
            win.focus_force()

            labels = ["Razón Social", "NIT", "Correo", "Teléfono", "Dirección"]
            claves = ["razonSocial", "nit", "correo", "telefono", "direccion"]
            entries = []

            def vc_uppercase(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_digits(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                return proposed.isdigit()

            vcmd_upper = win.register(vc_uppercase)
            vcmd_digits = win.register(vc_digits)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
                var = tk.StringVar()
                ent = tk.Entry(win, textvariable=var)
                if datos:
                    var.set(str(datos.get(key, "")))
                ent.grid(row=i, column=1, padx=8, pady=6)
                if key in ["correo", "direccion", "razonSocial"]:
                    ent.configure(validate="key", validatecommand=(vcmd_upper, "%P", "%W"))
                elif key == "nit":
                    ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                elif key == "telefono":
                    ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                entries.append(ent)

            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if hasattr(entries[idx+1], 'icursor'):
                        entries[idx+1].icursor(tk.END)
                else:
                    guardar()
                return "break"

            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if hasattr(entries[idx-1], 'icursor'):
                        entries[idx-1].icursor(tk.END)
                return "break"

            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    try:
                        val = widget.get()
                    except Exception:
                        val = ""
                    if val == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"

            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))

            entries[0].focus_set()
            try:
                if hasattr(entries[0], 'icursor'):
                    entries[0].icursor(tk.END)
            except Exception:
                pass

            def guardar():
                datos_proveedor = {}
                for i, key in enumerate(claves):
                    val = entries[i].get()
                    if key in ["nit", "telefono"]:
                        if val.strip() == "":
                            messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                            entries[i].focus_set()
                            return
                        if not val.isdigit():
                            messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    datos_proveedor[key] = val.strip()

                try:
                    if modo == "agregar":
                        query = "INSERT INTO proveedores (razonSocial, nit, correo, telefono, direccion) VALUES (?, ?, ?, ?, ?)"
                        parametros = (
                            datos_proveedor["razonSocial"],
                            datos_proveedor["nit"],
                            datos_proveedor["correo"],
                            datos_proveedor["telefono"],
                            datos_proveedor["direccion"]
                        )
                        resultado = ejecutar_consulta(query, parametros)
                    else:
                        query = "UPDATE proveedores SET razonSocial=?, nit=?, correo=?, telefono=?, direccion=? WHERE idProveedores=?"
                        parametros = (
                            datos_proveedor["razonSocial"],
                            datos_proveedor["nit"],
                            datos_proveedor["correo"],
                            datos_proveedor["telefono"],
                            datos_proveedor["direccion"],
                            datos.get("idProveedores")
                        )
                        resultado = ejecutar_consulta(query, parametros)

                    if resultado:
                        win.destroy()
                        cargar_proveedores()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar proveedor: {e}", parent=win)

            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_proveedor():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar proveedores.", parent=ventana_proveedores)
                return
            formulario_proveedor()

        def editar_proveedor_formulario(event):
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para editar proveedores.", parent=ventana_proveedores)
                return
            datos = {
                "razonSocial": valores[1],
                "nit": valores[2],
                "correo": valores[3],
                "telefono": valores[4],
                "direccion": valores[5],
                "idProveedores": valores[0]
            }
            formulario_proveedor(datos, modo="editar")

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_proveedor_formulario)

        def eliminar_proveedor():
            if clasificacion_actual != "Superusuario" or usuario_actual != "Usuario avanzado":
                messagebox.showerror("Error", "No tienes permiso para eliminar usuarios.")
                ventana_proveedores.focus_set()
                return

            item = tree.focus()

            valores = tree.item(item, "values")
            if not valores[0]:
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.")
                ventana_proveedores.focus_set()
                return

            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al proveedor {valores[1]}?", parent=ventana_proveedores)
            if not confirmacion:
                try:
                    ventana_proveedores.focus_set()
                except Exception:
                    pass
                return

            query = "DELETE FROM proveedores WHERE idProveedores = ?"
            parametros = (valores[0],)
            resultado = ejecutar_consulta(query, parametros)
            if resultado:
                cargar_proveedores()
                try:
                    ventana_proveedores.deiconify()
                    ventana_proveedores.lift()
                    ventana_proveedores.focus_force()
                except Exception:
                    pass

        btnAgregar = tk.Button(ventana_proveedores, text="Agregar Proveedor", command=agregar_proveedor, background="#86C0CA", fg="black", cursor="hand2")
        btnAgregar.pack(side="left", padx=10, pady=10)

        btnEliminar = tk.Button(ventana_proveedores, text="Eliminar Proveedor", command=eliminar_proveedor, background="#86C0CA", fg="black", cursor="hand2")
        btnEliminar.pack(side="left", padx=10, pady=10)

        btnAgregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnAgregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btnEliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnEliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        cargar_proveedores()

    btnProveedores.config(command=gestionar_proveedores)


    def gestionar_tarifas():
        ventana_tarifas = tk.Toplevel()
        ventana_tarifas.title("Gestión de Tarifas")
        _set_rel_geometry(ventana_tarifas, 800, 600)
        ventana_tarifas.bind('<Escape>', lambda e: ventana_tarifas.destroy())

        frame_tabla = tk.Frame(ventana_tarifas)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID", "Tarifa", "Duración", "Valor"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Tarifa", text="Tarifa")
        tree.heading("Duración", text="Duración")
        tree.heading("Valor", text="Valor")

        tree.column("ID", width=50, anchor="center")
        tree.column("Tarifa", width=150, anchor="center")
        tree.column("Duración", width=100, anchor="center")
        tree.column("Valor", width=150, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_tarifas():
            ventana_tarifas.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idTarifas, tarifa, duracion, valor FROM tarifas")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", ""), tags=("oddrow",))
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar tarifas: {e}")
            finally:
                conexion.close()

        def sincronizar_tarifa_local(tabla_destino, filtro, buscar, reemplazo):
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute(f"DELETE FROM {tabla_destino}")
                query_copiar = f"""
                    INSERT INTO {tabla_destino} (tarifa, duracion, valor)
                    SELECT tarifa, duracion, valor
                    FROM tarifas
                    WHERE tarifa LIKE ?
                """
                cursor.execute(query_copiar, (filtro,))
                conexion.commit()
                query_actualizar = f"""
                    UPDATE {tabla_destino}
                    SET tarifa = REPLACE(tarifa, ?, ?)
                """
                cursor.execute(query_actualizar, (buscar, reemplazo))
                conexion.commit()
            except Exception as e:
                messagebox.showerror("Error", f"Error al sincronizar tarifas ({tabla_destino}): {e}")
            finally:
                conexion.close()

        def sincronizar_todas():
            try:
                sincronizar_tarifa_local("tarifasmotos", "%Moto%", " Moto", "")
            except Exception:
                pass
            try:
                sincronizar_tarifa_local("tarifaschazas", "%Chaza%", "Chaza ", "")
            except Exception:
                pass
            try:
                sincronizar_tarifa_local("tarifasbicicletas", "%Bicicleta%", " Bicicleta", "")
            except Exception:
                pass

        def formulario_tarifa(datos=None, modo="agregar"):
            win = tk.Toplevel(ventana_tarifas)
            win.title("Formulario de Tarifa")
            _set_rel_geometry(win, 420, 260)
            win.grab_set()
            win.focus_force()

            labels = ["Tarifa", "Duración", "Valor"]
            claves = ["tarifa", "duracion", "valor"]
            entries = []

            def vc_float(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                try:
                    float(proposed)
                    return True
                except Exception:
                    return False

            vcmd_float = win.register(vc_float)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
                var = tk.StringVar()
                ent = tk.Entry(win, textvariable=var)
                if datos:
                    var.set(str(datos.get(key, "")))
                ent.grid(row=i, column=1, padx=8, pady=6)
                if key == "valor":
                    ent.configure(validate="key", validatecommand=(vcmd_float, "%P", "%W"))
                entries.append(ent)

            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if hasattr(entries[idx+1], 'icursor'):
                        entries[idx+1].icursor(tk.END)
                else:
                    guardar()
                return "break"

            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if hasattr(entries[idx-1], 'icursor'):
                        entries[idx-1].icursor(tk.END)
                return "break"

            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    try:
                        val = widget.get()
                    except Exception:
                        val = ""
                    if val == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"

            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))

            entries[0].focus_set()
            try:
                if hasattr(entries[0], 'icursor'):
                    entries[0].icursor(tk.END)
            except Exception:
                pass

            def guardar():
                datos_tarifa = {}
                for i, key in enumerate(claves):
                    val = entries[i].get()
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    if key == "valor":
                        try:
                            valf = float(val)
                        except Exception:
                            messagebox.showerror("Error", "El campo Valor debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                        datos_tarifa[key] = valf
                    else:
                        datos_tarifa[key] = val.strip()

                try:
                    if modo == "agregar":
                        query = "INSERT INTO tarifas (tarifa, duracion, valor) VALUES (?, ?, ?)"
                        parametros = (
                            datos_tarifa["tarifa"],
                            datos_tarifa["duracion"],
                            datos_tarifa["valor"]
                        )
                        resultado = ejecutar_consulta(query, parametros)
                    else:
                        query = "UPDATE tarifas SET tarifa=?, duracion=?, valor=? WHERE idTarifas=?"
                        parametros = (
                            datos_tarifa["tarifa"],
                            datos_tarifa["duracion"],
                            datos_tarifa["valor"],
                            datos.get("idTarifas")
                        )
                        resultado = ejecutar_consulta(query, parametros)

                    if resultado:
                        win.destroy()
                        cargar_tarifas()
                        try:
                            sincronizar_todas()
                        except Exception:
                            pass
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar tarifa: {e}", parent=win)

            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_tarifa():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar tarifas.", parent=ventana_tarifas)
                return
            formulario_tarifa()

        def editar_tarifa_formulario(event):
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para editar tarifas.", parent=ventana_tarifas)
                return
            datos = {
                "tarifa": valores[1],
                "duracion": valores[2],
                "valor": valores[3],
                "idTarifas": valores[0]
            }
            formulario_tarifa(datos, modo="editar")

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_tarifa_formulario)

        def eliminar_tarifa():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para eliminar tarifas.")
                ventana_tarifas.focus_set()
                return

            item = tree.focus()

            valores = tree.item(item, "values")
            if not valores[0]:
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.")
                ventana_tarifas.focus_set()
                return

            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la tarifa {valores[1]}?", parent=ventana_tarifas)
            if not confirmacion:
                try:
                    ventana_tarifas.focus_set()
                except Exception:
                    pass
                return

            query = "DELETE FROM tarifas WHERE idTarifas = ?"
            parametros = (valores[0],)
            resultado = ejecutar_consulta(query, parametros)
            if resultado:
                cargar_tarifas()
                try:
                    ventana_tarifas.deiconify()
                    ventana_tarifas.lift()
                    ventana_tarifas.focus_force()
                except Exception:
                    pass
                try:
                    sincronizar_todas()
                except Exception:
                    pass

        btnAgregar = tk.Button(ventana_tarifas, text="Agregar Tarifa", command=agregar_tarifa, background="#86C0CA", fg="black", cursor="hand2")
        btnAgregar.pack(side="left", padx=10, pady=10)

        btnEliminar = tk.Button(ventana_tarifas, text="Eliminar Tarifa", command=eliminar_tarifa, background="#86C0CA", fg="black", cursor="hand2")
        btnEliminar.pack(side="left", padx=10, pady=10)

        btnAgregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnAgregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btnEliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnEliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        cargar_tarifas()

    btnTarifas.config(command=gestionar_tarifas)


    def gestionar_inventario():
        ventana_inventario = tk.Toplevel()
        ventana_inventario.title("Gestión de Inventario")
        _set_rel_geometry(ventana_inventario, 800, 600)
        ventana_inventario.bind('<Escape>', lambda e: ventana_inventario.destroy())

        frame_tabla = tk.Frame(ventana_inventario)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID","Producto", "Tamaño", "Cantidad", "Color", "Valor de compra", "Valor de venta"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Producto", text="Producto")
        tree.heading("Tamaño", text="Tamaño")
        tree.heading("Cantidad", text="Cantidad")
        tree.heading("Color", text="Color")
        tree.heading("Valor de compra", text="Valor de compra")
        tree.heading("Valor de venta", text="Valor de venta")

        tree.column("ID", width=50, anchor="center")
        tree.column("Producto", width=150, anchor="center")
        tree.column("Tamaño", width=100, anchor="center")
        tree.column("Cantidad", width=150, anchor="center")
        tree.column("Color", width=100, anchor="center")
        tree.column("Valor de compra", width=150, anchor="center")
        tree.column("Valor de venta", width=150, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_inventario():
            ventana_inventario.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idInventario, producto, tamano, cantidad, color, valorCompra, valorVenta FROM inventario")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", ""), tags=("oddrow",))
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar inventario: {e}", parent=ventana_inventario)
            finally:
                conexion.close()
            if tree.get_children():
                first_item = tree.get_children()[0]
                tree.focus(first_item)
                tree.selection_set(first_item)
                tree.see(first_item)
                tree.focus_set()

        def formulario_inventario(datos=None, modo="agregar"):
            win = tk.Toplevel(ventana_inventario)
            win.title("Formulario de Inventario")
            _set_rel_geometry(win, 480, 360)
            win.grab_set()
            win.focus_force()

            labels = ["Producto", "Tamaño", "Cantidad", "Color", "Valor de compra", "Valor de venta"]
            claves = ["producto", "tamano", "cantidad", "color", "valorCompra", "valorVenta"]
            entries = []

            def vc_uppercase(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_digits(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                return proposed.isdigit()

            def vc_float(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                try:
                    float(proposed)
                    return True
                except Exception:
                    return False

            vcmd_upper = win.register(vc_uppercase)
            vcmd_digits = win.register(vc_digits)
            vcmd_float = win.register(vc_float)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
                var = tk.StringVar()
                ent = tk.Entry(win, textvariable=var)
                if datos:
                    var.set(str(datos.get(key, "")))
                ent.grid(row=i, column=1, padx=8, pady=6)
                if key in ["producto", "tamano", "color"]:
                    ent.configure(validate="key", validatecommand=(vcmd_upper, "%P", "%W"))
                elif key in ["cantidad"]:
                    ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                elif key in ["valorCompra", "valorVenta"]:
                    ent.configure(validate="key", validatecommand=(vcmd_float, "%P", "%W"))
                entries.append(ent)

            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if hasattr(entries[idx+1], 'icursor'):
                        entries[idx+1].icursor(tk.END)
                else:
                    guardar()
                return "break"

            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if hasattr(entries[idx-1], 'icursor'):
                        entries[idx-1].icursor(tk.END)
                return "break"

            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    try:
                        val = widget.get()
                    except Exception:
                        val = ""
                    if val == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"

            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))

            entries[0].focus_set()
            try:
                if hasattr(entries[0], 'icursor'):
                    entries[0].icursor(tk.END)
            except Exception:
                pass

            def guardar():
                datos_prod = {}
                for i, key in enumerate(claves):
                    val = entries[i].get()
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    if key in ["cantidad"] and not val.isdigit():
                        messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                        entries[i].focus_set()
                        return
                    if key in ["valorCompra", "valorVenta"]:
                        try:
                            fv = float(val)
                        except Exception:
                            messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                        datos_prod[key] = fv
                    else:
                        datos_prod[key] = val.strip()

                try:
                    if modo == "agregar":
                        query = "INSERT INTO inventario (producto, tamano, cantidad, color, valorCompra, valorVenta) VALUES (?, ?, ?, ?, ?, ?)"
                        parametros = (
                            datos_prod["producto"], datos_prod["tamano"], datos_prod["cantidad"],
                            datos_prod["color"], datos_prod["valorCompra"], datos_prod["valorVenta"]
                        )
                        resultado = ejecutar_consulta(query, parametros)
                    else:
                        query = "UPDATE inventario SET producto=?, tamano=?, cantidad=?, color=?, valorCompra=?, valorVenta=? WHERE idInventario=?"
                        parametros = (
                            datos_prod["producto"], datos_prod["tamano"], datos_prod["cantidad"],
                            datos_prod["color"], datos_prod["valorCompra"], datos_prod["valorVenta"], datos.get("idInventario")
                        )
                        resultado = ejecutar_consulta(query, parametros)

                    if resultado:
                        win.destroy()
                        cargar_inventario()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar producto: {e}", parent=win)

            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_producto():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar productos.", parent=ventana_inventario)
                return
            formulario_inventario()

        def editar_producto_formulario(event):
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para editar productos.", parent=ventana_inventario)
                return
            datos = {
                "producto": valores[1],
                "tamano": valores[2],
                "cantidad": valores[3],
                "color": valores[4],
                "valorCompra": valores[5],
                "valorVenta": valores[6],
                "idInventario": valores[0]
            }
            formulario_inventario(datos, modo="editar")

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_producto_formulario)

        def eliminar_producto():
            if clasificacion_actual != "Superusuario" or usuario_actual != "Usuario avanzado":
                messagebox.showerror("Error", "No tienes permiso para eliminar usuarios.")
                ventana_inventario.focus_set()
                return

            item = tree.focus()

            valores = tree.item(item, "values")
            if not valores[0]:
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.")
                ventana_inventario.focus_set()
                return

            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el producto {valores[1]}?", parent=ventana_inventario)
            if not confirmacion:
                try:
                    ventana_inventario.focus_set()
                except Exception:
                    pass
                return

            query = "DELETE FROM inventario WHERE idInventario = ?"
            parametros = (valores[0],)
            resultado = ejecutar_consulta(query, parametros)
            if resultado:
                cargar_inventario()
                try:
                    ventana_inventario.deiconify()
                    ventana_inventario.lift()
                    ventana_inventario.focus_force()
                except Exception:
                    pass

        btnAgregar = tk.Button(ventana_inventario, text="Agregar Producto", command=agregar_producto, cursor="hand2", background="#86C0CA", fg="black")
        btnAgregar.pack(side="left", padx=10, pady=10)

        btnEliminar = tk.Button(ventana_inventario, text="Eliminar Producto", command=eliminar_producto, cursor="hand2", background="#86C0CA", fg="black")
        btnEliminar.pack(side="left", padx=10, pady=10)

        btnAgregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnAgregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btnEliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnEliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        cargar_inventario()
        
    btnInventario.config(command=gestionar_inventario)

    def gestionar_facturascompra():
        ventana_facturas = tk.Toplevel()
        ventana_facturas.title("Gestión de Facturas de Compra")
        _set_rel_geometry(ventana_facturas, 900, 600)
        ventana_facturas.bind('<Escape>', lambda e: ventana_facturas.destroy())

        frame_tabla = tk.Frame(ventana_facturas)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID","Producto","Cantidad","Valor","Proveedor","NumeroFactura","Fecha"),
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set, selectmode="browse")

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("ID", text="ID")
        tree.heading("Producto", text="Producto")
        tree.heading("Cantidad", text="Cantidad")
        tree.heading("Valor", text="Valor")
        tree.heading("Proveedor", text="Proveedor")
        tree.heading("NumeroFactura", text="Número Factura")
        tree.heading("Fecha", text="Fecha")

        tree.column("ID", width=60, anchor="center")
        tree.column("Producto", width=200, anchor="center")
        tree.column("Cantidad", width=80, anchor="center")
        tree.column("Valor", width=100, anchor="center")
        tree.column("Proveedor", width=150, anchor="center")
        tree.column("NumeroFactura", width=120, anchor="center")
        tree.column("Fecha", width=100, anchor="center")

        tree.tag_configure("evenrow", background="#f2f2f2")
        tree.tag_configure("oddrow", background="#ffffff")

        def cargar_facturas():
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.", parent=ventana_facturas)
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idfacturasDeCompra, producto, cantidad, valor, proveedor, numeroDeFactura, fecha FROM facturasdecompra")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for index, row in enumerate(rows):
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    tree.insert("", "end", values=row, tags=(tag,))
                tree.insert("", "end", values=("", "", "", "", "", "", ""), tags=("oddrow",))
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar facturas: {e}", parent=ventana_facturas)
            finally:
                conexion.close()

        def formulario_factura(datos=None, modo="agregar"):
            win = tk.Toplevel(ventana_facturas)
            win.title("Formulario Factura de Compra")
            _set_rel_geometry(win, 520, 360)
            win.grab_set()
            win.focus_force()

            labels = ["Producto","Cantidad","Valor","Proveedor","Número Factura","Fecha (YYYY-MM-DD)"]
            claves = ["producto","cantidad","valor","proveedor","numeroDeFactura","fecha"]
            entries = []

            def vc_upper(proposed, widget_name):
                w = win.nametowidget(widget_name)
                if proposed is None:
                    return True
                if proposed != proposed.upper():
                    def replace():
                        try:
                            w.delete(0, tk.END)
                            w.insert(0, proposed.upper())
                        except Exception:
                            pass
                    win.after_idle(replace)
                    return False
                return True

            def vc_digits(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                return proposed.isdigit()

            def vc_float(proposed, widget_name):
                if proposed is None:
                    return True
                if proposed == "":
                    return True
                try:
                    float(proposed)
                    return True
                except Exception:
                    return False

            vcmd_upper = win.register(vc_upper)
            vcmd_digits = win.register(vc_digits)
            vcmd_float = win.register(vc_float)

            for i, (lbl, key) in enumerate(zip(labels, claves)):
                tk.Label(win, text=lbl+":").grid(row=i, column=0, sticky="e", padx=8, pady=6)
                # Use DateEntry for fecha field so users pick from a calendar
                if key == "fecha":
                    try:
                        ent = DateEntry(win, date_pattern='yyyy-mm-dd')
                        if datos and datos.get(key):
                            try:
                                ent.set_date(datos.get(key))
                            except Exception:
                                try:
                                    ent.set_date(str(datos.get(key)))
                                except Exception:
                                    pass
                    except Exception:
                        # Fallback to simple Entry if tkcalendar not available for some reason
                        var = tk.StringVar()
                        ent = tk.Entry(win, textvariable=var)
                        if datos:
                            var.set(str(datos.get(key, "")))
                else:
                    var = tk.StringVar()
                    ent = tk.Entry(win, textvariable=var)
                    if datos:
                        var.set(str(datos.get(key, "")))
                ent.grid(row=i, column=1, padx=8, pady=6)
                if key in ["producto","proveedor"]:
                    try:
                        ent.configure(validate="key", validatecommand=(vcmd_upper, "%P", "%W"))
                    except Exception:
                        pass
                elif key in ["cantidad","numeroDeFactura"]:
                    try:
                        ent.configure(validate="key", validatecommand=(vcmd_digits, "%P", "%W"))
                    except Exception:
                        pass
                elif key == "valor":
                    try:
                        ent.configure(validate="key", validatecommand=(vcmd_float, "%P", "%W"))
                    except Exception:
                        pass
                entries.append(ent)

            def focus_next(event, idx):
                if idx < len(entries)-1:
                    entries[idx+1].focus_set()
                    if hasattr(entries[idx+1], 'icursor'):
                        entries[idx+1].icursor(tk.END)
                else:
                    guardar()
                return "break"

            def focus_prev(event, idx):
                if idx > 0:
                    entries[idx-1].focus_set()
                    if hasattr(entries[idx-1], 'icursor'):
                        entries[idx-1].icursor(tk.END)
                return "break"

            def on_key(event, idx):
                if event.keysym == "Return":
                    return focus_next(event, idx)
                elif event.keysym == "BackSpace":
                    widget = entries[idx]
                    try:
                        val = widget.get()
                    except Exception:
                        val = ""
                    if val == "":
                        return focus_prev(event, idx)
                elif event.keysym == "Escape":
                    win.destroy()
                    return "break"

            for i, widget in enumerate(entries):
                widget.bind("<Key>", lambda e, idx=i: on_key(e, idx))

            entries[0].focus_set()
            entries[0].icursor(tk.END)

            def guardar():
                datos_fac = {}
                for i, key in enumerate(claves):
                    val = entries[i].get()
                    if val.strip() == "":
                        messagebox.showerror("Error", f"El campo {labels[i]} es obligatorio.", parent=win)
                        entries[i].focus_set()
                        return
                    if key in ["cantidad","numeroDeFactura"] and not val.isdigit():
                        messagebox.showerror("Error", f"El campo {labels[i]} debe ser numérico.", parent=win)
                        entries[i].focus_set()
                        return
                    if key == "valor":
                        try:
                            fv = float(val)
                        except Exception:
                            messagebox.showerror("Error", "El campo Valor debe ser numérico.", parent=win)
                            entries[i].focus_set()
                            return
                        datos_fac[key] = fv
                    else:
                        datos_fac[key] = val.strip()

                try:
                    if modo == "agregar":
                        query = "INSERT INTO facturasdecompra (producto, cantidad, valor, proveedor, numeroDeFactura, fecha) VALUES (?, ?, ?, ?, ?, ?)"
                        parametros = (
                            datos_fac["producto"], datos_fac["cantidad"], datos_fac["valor"],
                            datos_fac["proveedor"], datos_fac["numeroDeFactura"], datos_fac["fecha"]
                        )
                        resultado = ejecutar_consulta(query, parametros)
                    else:
                        query = "UPDATE facturasdecompra SET producto=?, cantidad=?, valor=?, proveedor=?, numeroDeFactura=?, fecha=? WHERE idfacturasDeCompra=?"
                        parametros = (
                            datos_fac["producto"], datos_fac["cantidad"], datos_fac["valor"],
                            datos_fac["proveedor"], datos_fac["numeroDeFactura"], datos_fac["fecha"], datos.get("idfacturasDeCompra")
                        )
                        resultado = ejecutar_consulta(query, parametros)

                    if resultado:
                        win.destroy()
                        cargar_facturas()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar factura: {e}", parent=win)

            btn_ok = tk.Button(win, text="OK", command=guardar, cursor="hand2", background="#86C0CA", fg="black")
            btn_ok.grid(row=len(labels), column=0, columnspan=2, pady=12)
            btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
            btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))
            win.bind("<Escape>", lambda e: win.destroy())

        def agregar_factura():
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para agregar facturas.", parent=ventana_facturas)
                return
            formulario_factura()

        def editar_factura_formulario(event):
            item = tree.focus()
            
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                return
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para editar facturas.", parent=ventana_facturas)
                return
            datos = {
                "producto": valores[1],
                "cantidad": valores[2],
                "valor": valores[3],
                "proveedor": valores[4],
                "numeroDeFactura": valores[5],
                "fecha": valores[6],
                "idfacturasDeCompra": valores[0]
            }
            formulario_factura(datos, modo="editar")

        def eliminar_factura():
            if clasificacion_actual != "Superusuario":
                messagebox.showerror("Error", "Solo el superusuario puede eliminar facturas.", parent=ventana_facturas)
                return
            item = tree.focus()
            valores = tree.item(item, "values")
            if not valores or valores[0] == "":
                messagebox.showerror("Error", "No se puede eliminar una fila en blanco.", parent=ventana_facturas)
                return
            confirmacion = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la factura {valores[5]} (Proveedor: {valores[4]})?", parent=ventana_facturas)
            if not confirmacion:
                return
            query = "DELETE FROM facturasdecompra WHERE idfacturasDeCompra = ?"
            parametros = (valores[0],)
            resultado = ejecutar_consulta(query, parametros)
            if resultado:
                cargar_facturas()

        btnAgregar = tk.Button(ventana_facturas, text="Agregar Factura", command=agregar_factura, cursor="hand2", background="#86C0CA", fg="black")
        btnAgregar.pack(side="left", padx=10, pady=10)

        btnEliminar = tk.Button(ventana_facturas, text="Eliminar Factura", command=eliminar_factura, cursor="hand2", background="#86C0CA", fg="black")
        btnEliminar.pack(side="left", padx=10, pady=10)

        btnAgregar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnAgregar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        btnEliminar.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#86C0CA"))
        btnEliminar.bind("<Leave>", lambda e: e.widget.config(bg="#86C0CA", fg="black"))

        tree.unbind("<Double-1>")
        tree.bind("<Double-1>", editar_factura_formulario)

        cargar_facturas()

    # enlazar el botón de facturas de compra creado arriba
    try:
        btnFacturasDeCompra.config(command=gestionar_facturascompra)
    except Exception:
        pass
    btnInventario.config(command=gestionar_inventario)

    frmRegistro.bind("<Configure>", lambda e: _set_rel_geometry(frmRegistro, 1920, 1080))

    # Bind fullscreen toggles on the toplevel window (parent may be a Frame)
    try:
        _root_win = frmRegistro.winfo_toplevel()
        _root_win.bind("<F11>", lambda e: _root_win.attributes("-fullscreen", not _root_win.attributes("-fullscreen")))
        _root_win.bind("<Escape>", lambda e: _root_win.attributes("-fullscreen", False))
    except Exception:
        # Fallback: attempt to bind on parent if it supports it
        try:
            parent.bind("<F11>", lambda e: frmRegistro.attributes("-fullscreen", not frmRegistro.attributes("-fullscreen")))
            parent.bind("<Escape>", lambda e: frmRegistro.attributes("-fullscreen", False))
        except Exception:
            pass

    return frmRegistro