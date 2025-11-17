import math
import win32print
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime as dt
from tkinter import simpledialog
from PIL import Image, ImageTk
from database import conectar_bd_parqueaderojmj
from tkcalendar import DateEntry
import tempfile
import os
import calendar

def crearFramesMotos(parent, usuario_actual, clasificacion_actual):
    def abrir_tabla_placas():
        consultarPlacas()
    parent.bind('<Control-b>', lambda event: abrir_tabla_placas())

    def add_months(dtobj, months=1):
        year = dtobj.year + (dtobj.month - 1 + months) // 12
        month = (dtobj.month - 1 + months) % 12 + 1
        day = dtobj.day
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        return dt.datetime(year, month, day, dtobj.hour, dtobj.minute, dtobj.second, dtobj.microsecond)
    def imprimir_factura_salida_fijo(modalidad, cedula, nombre, placa, entrada, salida, total, usuario):
        num_factura = obtener_numero_factura()
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n")
        recibo.append(f"Factura de venta: #{num_factura}\n")
        recibo.append("\nHORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSÁBADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "MOTOS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("FACTURA\n")
        recibo.append(f"Modalidad: {modalidad.replace('Mensualidade', 'Mes')}\n")
        recibo.append(f"Cedula: {cedula}\n")
        recibo.append(f"Cliente: {nombre}\n")
        recibo.append(f"Placa: {placa}\n")
        recibo.append(f"Desde: {entrada}\n")
        recibo.append(f"Hasta: {salida}\n")
        try:
            if isinstance(total, (int, float)):
                v = float(total)
                clean_total = str(int(v)) if v.is_integer() else f"{v:.2f}"
            else:
                s = str(total)
                for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                    s = s.replace(p, "")
                s = s.replace(',', '').strip()
                try:
                    v = float(s)
                    clean_total = str(int(v)) if v.is_integer() else f"{v:.2f}"
                except Exception:
                    clean_total = s
        except Exception:
            clean_total = str(total)
        recibo.append(f"TOTAL: ${clean_total}\n")
        recibo.append(f"Atendido por: {usuario}\n")
        recibo.append("\n" * 3)
        texto_recibo = "".join(recibo)
        try:
            import win32print
            hPrinter = None
            try:
                try:
                    default_printer = win32print.GetDefaultPrinter()
                    if default_printer:
                        hPrinter = win32print.OpenPrinter(default_printer)
                except Exception:
                    hPrinter = None

                if not hPrinter:
                    try:
                        hPrinter = win32print.OpenPrinter('Xprinter Receipt Printer')
                    except Exception:
                        hPrinter = None

                if not hPrinter:
                    raise RuntimeError('No se encontró una impresora disponible.')

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalidaFijo.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto_recibo.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    win32print.ClosePrinter(hPrinter)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir la factura: {e}")

    def obtener_numero_factura():
        import pathlib
        path = pathlib.Path('numero_factura.txt')
        if path.exists():
            try:
                with open(path, 'r') as f:
                    num = int(f.read().strip())
            except Exception:
                num = 1
        else:
            num = 1
        with open(path, 'w') as f:
            f.write(str(num + 1))
        return num

    def imprimir_factura_salida(placa, modalidad, fecha_entrada, fecha_salida, duracion, total, usuario):
        num_factura = obtener_numero_factura()
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n")
        recibo.append(f"Factura de venta: #{num_factura}\n\n")
        recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSÁBADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "MOTOS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("FACTURA\n")
        recibo.append(f"Placa: {placa}\n")
        recibo.append(f"Modalidad: {modalidad.replace('Día', 'Dia')}\n")
        recibo.append(f"Ingreso: {fecha_entrada}\n")
        recibo.append(f"Salida: {fecha_salida}\n")
        recibo.append(f"Duracion: {duracion}\n")
        try:
            if isinstance(total, (int, float)):
                v = float(total)
                clean_total = str(int(v)) if v.is_integer() else f"{v:.2f}"
            else:
                s = str(total)
                for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                    s = s.replace(p, "")
                s = s.replace(',', '').strip()
                try:
                    v = float(s)
                    clean_total = str(int(v)) if v.is_integer() else f"{v:.2f}"
                except Exception:
                    clean_total = s
        except Exception:
            clean_total = str(total)
        recibo.append(f"TOTAL: ${clean_total}\n")
        recibo.append(f"Atendido por: {usuario}\n")
        recibo.append("\n" * 3)
        texto_recibo = "".join(recibo)
        try:
            import win32print
            hPrinter = None
            try:
                try:
                    default_printer = win32print.GetDefaultPrinter()
                    if default_printer:
                        hPrinter = win32print.OpenPrinter(default_printer)
                except Exception:
                    hPrinter = None

                if not hPrinter:
                    try:
                        hPrinter = win32print.OpenPrinter('Xprinter Receipt Printer')
                    except Exception:
                        hPrinter = None

                if not hPrinter:
                    raise RuntimeError('No se encontró una impresora disponible.')

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalida.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto_recibo.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    win32print.ClosePrinter(hPrinter)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir la factura: {e}")

    def imprimir_recibo_entrada(placa, modalidad, casco, fecha_entrada, usuario):
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n\n")
        recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "MOTOS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("\nRECIBO DE ENTRADA\nModalidad: {}\n********************************\n".format(modalidad.replace('Día', 'Dia')))
        recibo.append("Placa: {}\n********************************\n".format(placa))
        if casco:
            recibo.append("Casco: {}\n".format(casco))
        recibo.append("Entrada: {}\n".format(fecha_entrada))
        recibo.append("Atendido por: {}\n".format(usuario))
        recibo.append("\n" * 3)

        texto_recibo = "".join(recibo)
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

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("ReciboEntrada.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto_recibo.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    win32print.ClosePrinter(hPrinter)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir el recibo: {e}")

    def sincronizar_tarifas(tabla_destino, filtro):
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
                SET tarifa = REPLACE(tarifa, ' Moto', '')
            """
            cursor.execute(query_actualizar)
            conexion.commit()

        except Exception as e:
            messagebox.showerror("Error", f"Error al sincronizar tarifas: {e}")
        finally:
            conexion.close()
    sincronizar_tarifas("tarifasmotos", "%Moto%")

    frmRegistro = tk.Frame(parent, bg="#E5C41E")
    frmRegistro.place(x=0, y=0, relheight=1, relwidth=0.65)
    frmRegistro.pack_propagate(False)


    img_motos = Image.open("icono.ico").resize((100, 100))
    icono_motos = ImageTk.PhotoImage(img_motos)
    lbl_icono_motos = tk.Label(frmRegistro, image=icono_motos, bg="#E5C41E")
    lbl_icono_motos.image = icono_motos
    lbl_icono_motos.place(relx=0, rely=1, anchor="sw", x=10, y=10)

    inicial = usuario_actual.strip()[0].upper() if usuario_actual else "N"
    if inicial not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        inicial = "N"
    icono_path = f"{inicial}.png"
    try:
        imgUsuario = Image.open(icono_path).resize((90, 90))
    except Exception:
        imgUsuario = Image.open("N.png").resize((90, 90))
    iconoUsuario = ImageTk.PhotoImage(imgUsuario)
    lblIconoUsuario = tk.Label(frmRegistro, image=iconoUsuario, bg="#E5C41E")
    lblIconoUsuario.image = iconoUsuario
    lblIconoUsuario.place(relx=0, rely=0, anchor="nw", x=10, y=10)

    frmRegistroInterno = tk.Frame(frmRegistro, bg="#E5C41E")
    frmRegistroInterno.pack(expand=True)

    lbl_fecha_hora = tk.Label(frmRegistroInterno, font=("Times New Roman", 25, "bold"), bg="#E5C41E")
    lbl_fecha_hora.pack(pady=10)

    lblPlaca = tk.Label(frmRegistroInterno, fg="black", text="Placa:", font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblPlaca.pack(pady=10)

    placa_var = tk.StringVar()

    placa = tk.Entry(frmRegistroInterno, bg="black", fg="white", font=("Times New Roman", 62), width=9, justify="center",
                     textvariable=placa_var, insertbackground="white")

    placa.pack(ipady=10)
    placa.focus_set()

    def to_uppercase_placa(*args):
        v = placa_var.get()
        if v != v.upper():
            placa_var.set(v.upper())
    placa_var.trace_add("write", to_uppercase_placa)

    placa.bind('<Control-b>', lambda event: abrir_tabla_placas())

    def on_placa_key(event=None):
        if event and event.keysym == 'Return':
            casco.focus_set()
            casco.icursor('end')
    placa.bind('<KeyRelease>', on_placa_key)
    placa.bind('<Return>', on_placa_key)

    frmBotones = tk.Frame(frmRegistroInterno, bg="#E5C41E")
    frmBotones.pack(pady=20)

    def seleccionar_boton(boton):
        for b in botones:
            b.config(highlightbackground="white", bg="white", fg="black")
        boton.config(highlightbackground="red", bg="black", fg="white")

    filaModalidades1 = tk.Frame(frmBotones, bg="#E5C41E")
    filaModalidades1.pack()
    btn_hora = tk.Button(filaModalidades1, text="Hora", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_estudiante = tk.Button(filaModalidades1, text="Estudiante", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_dia = tk.Button(filaModalidades1, text="Día", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_24h = tk.Button(filaModalidades1, text="24 Horas", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_hora.pack(side="left", padx=3, pady=3)
    btn_estudiante.pack(side="left", padx=3, pady=3)
    btn_dia.pack(side="left", padx=3, pady=3)
    btn_24h.pack(side="left", padx=3, pady=3)

    filaModalidades2 = tk.Frame(frmBotones, bg="#E5C41E")
    filaModalidades2.pack()
    btn_semana = tk.Button(filaModalidades2, text="Semana", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_quincena = tk.Button(filaModalidades2, text="Quincena", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_mes = tk.Button(filaModalidades2, text="Mes", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_semana.pack(side="left", padx=3, pady=3)
    btn_quincena.pack(side="left", padx=3, pady=3)
    btn_mes.pack(side="left", padx=3, pady=3)

    botones = [btn_hora, btn_estudiante, btn_dia, btn_24h, btn_semana, btn_quincena, btn_mes]
    for b in botones:
        b.config(command=lambda btn=b: seleccionar_boton(btn))

    seleccionar_boton(btn_hora)

    for b in botones:
        b.bind('<Return>', lambda e: casco.focus_set())

    def askstring_no_cancel(parent, title, prompt):
        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.transient(parent)

        result = {"value": None, "closed": True}

        lbl = tk.Label(dlg, text=prompt, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
        lbl.pack()

        var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, font=("Times New Roman", 12), width=30)
        entry.pack(padx=10, pady=5)

        def on_ok():
            result["value"] = var.get()
            result["closed"] = False
            dlg.destroy()

        def on_close():
            result["value"] = None
            result["closed"] = True
            dlg.destroy()

        btn = tk.Button(dlg, text="OK", command=on_ok, bg="#E5C41E", fg="#111111", cursor="hand2")
        btn.pack(pady=10)

        for btn in [
            btn
        ]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

        dlg.protocol("WM_DELETE_WINDOW", on_close)
        entry.bind("<Return>", lambda e: on_ok())
        entry.focus_set()
        dlg.grab_set()
        dlg.wait_window()

        return result["value"]

    filaCasco = tk.Frame(frmRegistroInterno, bg="#E5C41E")
    filaCasco.pack(pady=10)

    lblCasco = tk.Label(filaCasco, fg="black", text="Casco:", font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblCasco.pack(side='left', padx=(0, 8))

    casco_var = tk.StringVar()
    def to_uppercase_casco(*args):
        value = casco_var.get()
        if value != value.upper():
            casco_var.set(value.upper())
    casco_var.trace_add("write", to_uppercase_casco)

    casco = tk.Entry(
        filaCasco,
        bg="white",
        fg="black",
        font=("Times New Roman", 16, "bold"),
        width=13,
        justify="center",
        textvariable=casco_var,
        insertbackground="black"
    )

    casco.pack(side='left', ipady=1)

    def on_casco_enter(event=None):
        btnRegistrar.invoke()
        return "break"
    casco.bind('<Return>', on_casco_enter)

    def bind_backspace_chain(entries):
        for i, ent in enumerate(entries):
            def _handler(event, idx=i, ent_widget=ent):
                try:
                    widget = event.widget
                    if widget is not ent_widget:
                        return
                    try:
                        pos = widget.index('insert')
                    except Exception:
                        pos = None
                    text = ''
                    try:
                        text = widget.get()
                    except Exception:
                        text = ''
                    if (pos == 0) or (text == ''):
                        prev_idx = idx - 1
                        if prev_idx >= 0:
                            try:
                                entries[prev_idx].focus_set()
                                entries[prev_idx].icursor('end')
                            except Exception:
                                entries[prev_idx].focus_set()
                            return 'break'
                except Exception:
                    return
            try:
                ent.bind('<BackSpace>', _handler)
            except Exception:
                pass

    try:
        bind_backspace_chain([placa, casco])
    except Exception:
        pass

    btnRegistrar = tk.Button(
        frmRegistroInterno,
        text="Registrar",
        font=("Times New Roman", 16, "bold"),
        cursor="hand2",
        bg="white",
        fg="black",
    )
    btnRegistrar.pack(pady=20)

    fechaEntrada = tk.StringVar()
    lblFechaEntrada = tk.Label(frmRegistroInterno, fg="black", text="Fecha y Hora de Entrada: " + fechaEntrada.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblFechaEntrada.pack(pady=5)

    duracionEn24Horas=tk.StringVar()
    duracionEnDias=tk.StringVar()
    duracionEnHoras=tk.StringVar()
    duracionEnMinutos=tk.StringVar()
    duracionEnSegundos=tk.StringVar()

    frmDuracion = tk.Frame(frmRegistroInterno, bg="#E5C41E")
    frmDuracion.pack(pady=5)

    filaDuracion = tk.Frame(frmDuracion, bg="#E5C41E")
    filaDuracion.pack()

    lblDuracionEn24Horas = tk.Label(filaDuracion, fg="black", text="24 Horas: " + duracionEn24Horas.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblDuracionEn24Horas.grid(row=0, column=0, padx=10)

    lblDuracionEnDias = tk.Label(filaDuracion, fg="black", text="Días (16 horas): " + duracionEnDias.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblDuracionEnDias.grid(row=0, column=1, padx=10)

    lblDuracionEnHoras = tk.Label(filaDuracion, fg="black", text="Horas: " + duracionEnHoras.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblDuracionEnHoras.grid(row=0, column=2, padx=10)

    lblDuracionEnMinutos = tk.Label(filaDuracion, fg="black", text="Minutos: " + duracionEnMinutos.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblDuracionEnMinutos.grid(row=0, column=3, padx=10)

    lblDuracionEnSegundos = tk.Label(filaDuracion, fg="black", text="Segundos: " + duracionEnSegundos.get(), font=("Times New Roman", 18, "bold"), bg="#E5C41E")
    lblDuracionEnSegundos.grid(row=0, column=4, padx=10)

    valor = tk.StringVar(value="Valor: ")
    lblValor = tk.Label(frmRegistro, textvariable=valor, font=("Times New Roman", 18, "bold"), bg="white")
    lblValor.pack(pady=5)

    lblFechaEntrada.pack_forget()
    frmDuracion.pack_forget()
    lblValor.pack_forget()

    def limpiar_pantalla():
        placa_var.set("")
        casco_var.set("")
        seleccionar_boton(btn_hora)
        placa.focus_set()
        frmDuracion.pack_forget()
        lblFechaEntrada.pack_forget()
        lblValor.pack_forget()
        btnRegistrar.config(text="Registrar")
    btnRegistrar.config(text="Registrar", command=lambda: confirmar_registro())


    btnLimpiarPantalla = tk.Button(
        frmRegistro,
        text="Limpiar Pantalla",
        font=("Times New Roman", 16, "bold"),
        cursor="hand2",
        command=limpiar_pantalla,
        bg="white",
        fg="black",
    )
    btnLimpiarPantalla.place(relx=1, rely=1, anchor="se", x=-20, y=-20)
  

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

    frmClientesDia = tk.Frame(parent, border=1, relief="solid", bg="#1B1B1B")
    frmClientesDia.place(x=0, y=0, relx=0.65, relheight=0.5, relwidth=0.175)
    frmClientesDia.pack_propagate(False)

    frameDiaInterno = tk.Frame(frmClientesDia, bg="#1B1B1B")
    frameDiaInterno.pack(expand=True)

    lblClientesDiarios = tk.Label(frameDiaInterno, text="Clientes Diarios", font=("Times New Roman", 18, "bold"), bg="#1B1B1B", fg="white")
    lblClientesDiarios.pack(pady=10)

    horas = 0
    estudiantes = 0
    dias = 0
    horas_24 = 0
    totalDiarios = horas + estudiantes + dias + horas_24

    lblHoras = tk.Label(frameDiaInterno, text=f"Horas: {horas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblHoras.pack(pady=5)

    lblEstudiantes = tk.Label(frameDiaInterno, text=f"Estudiantes: {estudiantes}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblEstudiantes.pack(pady=5)

    lblDias = tk.Label(frameDiaInterno, text=f"Días: {dias}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblDias.pack(pady=5)

    lbl24h = tk.Label(frameDiaInterno, text=f"24 Horas: {horas_24}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lbl24h.pack(pady=5)

    lblTotalPlacas = tk.Label(frameDiaInterno, text=f"Total: {totalDiarios}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblTotalPlacas.pack(pady=5)


    frmClientesFijos = tk.Frame(parent, border=1, relief="solid", bg="#1B1B1B")
    frmClientesFijos.place(x=0, y=0, relx=0.825, relheight=0.5, relwidth=0.175)
    frmClientesFijos.pack_propagate(False)

    frameFijosInterno = tk.Frame(frmClientesFijos, bg="#1B1B1B")
    frameFijosInterno.pack(expand=True)

    lblClientesFijos = tk.Label(frameFijosInterno, text="Clientes Fijos", font=("Times New Roman", 18, "bold"), bg="#1B1B1B", fg="white")
    lblClientesFijos.pack(pady=10)

    semanas = 0
    quincenas = 0
    mensualidades = 0
    totalFijos = semanas + quincenas + mensualidades

    lblSemanas = tk.Label(frameFijosInterno, text=f"Semanas: {semanas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblSemanas.pack(pady=5)

    lblQuincenas = tk.Label(frameFijosInterno, text=f"Quincenas: {quincenas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblQuincenas.pack(pady=5)

    lblMensualidades = tk.Label(frameFijosInterno, text=f"Mensualidades: {mensualidades}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblMensualidades.pack(pady=5)

    lblTotalFijos = tk.Label(frameFijosInterno, text=f"Total: {totalFijos}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblTotalFijos.pack(pady=5)


    def actualizarConteoModalidadesDelDia():
        conexion = None
        cursor = None
        try:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return

            cursor = conexion.cursor()
            cursor.execute("SELECT modalidad, COUNT(*) FROM placas GROUP BY modalidad")
            conteos = cursor.fetchall()

            horas = estudiantes = dias = horas_24 = 0

            for modalidad, cantidad in conteos:
                if modalidad == "Hora":
                    horas = cantidad
                elif modalidad == "Estudiante":
                    estudiantes = cantidad
                elif modalidad == "Día":
                    dias = cantidad
                elif modalidad == "24 Horas":
                    horas_24 = cantidad

            lblHoras.config(text=f"Horas: {horas}")
            lblEstudiantes.config(text=f"Estudiantes: {estudiantes}")
            lblDias.config(text=f"Días: {dias}")
            lbl24h.config(text=f"24 Horas: {horas_24}")

            totalDiarios = horas + estudiantes + dias + horas_24
            lblTotalPlacas.config(text=f"Total: {totalDiarios}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar el conteo de modalidades: {e}")

        finally:
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
    actualizarConteoModalidadesDelDia()

    def asegurar_columnas_fijas(conexion):
        tablas = ["semanasMoto", "quincenasMoto", "mensualidadesMoto"]
        try:
            cursor = conexion.cursor()
            for tabla in tablas:
                cursor.execute(f"PRAGMA table_info({tabla})")
                cols = [r[1] for r in cursor.fetchall()]
                if 'congelado' not in cols:
                    cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN congelado INTEGER DEFAULT 0")
                if 'fechaCongelado' not in cols:
                    cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN fechaCongelado TEXT")
                if 'recientementeDescongelado' not in cols:
                    cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN recientementeDescongelado INTEGER DEFAULT 0")
            conexion.commit()
        except Exception:
            pass

    def actualizarConteoFijos():
        conexion = None
        try:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                return
            asegurar_columnas_fijas(conexion)
            cursor = conexion.cursor()
            cursor.execute("SELECT COUNT(*) FROM semanasMoto")
            cnt_semanas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM quincenasMoto")
            cnt_quincenas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mensualidadesMoto")
            cnt_mensualidades = cursor.fetchone()[0]

            nonlocal semanas, quincenas, mensualidades, totalFijos
            semanas = cnt_semanas
            quincenas = cnt_quincenas
            mensualidades = cnt_mensualidades
            totalFijos = semanas + quincenas + mensualidades

            lblSemanas.config(text=f"Semanas: {semanas}")
            lblQuincenas.config(text=f"Quincenas: {quincenas}")
            lblMensualidades.config(text=f"Mensualidades: {mensualidades}")
            lblTotalFijos.config(text=f"Total: {totalFijos}")

        except Exception:
            pass
        finally:
            if conexion:
                conexion.close()

    actualizarConteoFijos()


    frmFunciones = tk.Frame(parent, border=1, relief="solid", bg="black")
    frmFunciones.place(x=0, y=0, relx=0.65, rely=0.5, relwidth=0.35, relheight=0.5)
    frmFunciones.pack_propagate(False)

    frameFuncionesInterno = tk.Frame(frmFunciones, bg="black")
    frameFuncionesInterno.pack(expand=True)

    btnConsultarPlacas = tk.Button(frameFuncionesInterno, text="Consultar Placas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnHistorialDePlacas = tk.Button(frameFuncionesInterno, text="Historial de Placas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnConsultar = tk.Button(frameFuncionesInterno, text="Consultar Clientes", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnTarifas = tk.Button(frameFuncionesInterno, text="Tarifas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnArqueo = tk.Button(frameFuncionesInterno, text="Arqueo de Caja", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")

    btnConsultarPlacas.pack(pady=10)
    btnHistorialDePlacas.pack(pady=10)
    btnConsultar.pack(pady=10)
    btnTarifas.pack(pady=10)
    btnArqueo.pack(pady=10)


    for btn in [
        btnRegistrar,
        btnLimpiarPantalla,
        btnConsultarPlacas,
        btnHistorialDePlacas,
        btnConsultar,
        btnTarifas,
        btnArqueo
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="#1B1B1B", fg="white"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="white", fg="black"))

    def mostrar_tarifas_motos():
        ventana_tarifas = tk.Toplevel()
        ventana_tarifas.title("Tarifas")
        ventana_tarifas.geometry("800x600")
        ventana_tarifas.bind('<Escape>', lambda e: ventana_tarifas.destroy())

        frame_tabla = tk.Frame(ventana_tarifas)
        frame_tabla.pack(fill="both", expand=True)

        scrollbar_vertical = tk.Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = tk.Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(frame_tabla, columns=("ID", "Tarifa", "Duración", "Valor"), 
                                show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)

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
        tree.column("Tarifa", width=200, anchor="center")
        tree.column("Duración", width=150, anchor="center")
        tree.column("Valor", width=100, anchor="center")

        def cargar_tarifas_motos():
            conexion = conectar_bd_parqueaderojmj()
            ventana_tarifas.focus_set()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idTarifasMotos, tarifa, duracion, valor FROM tarifasmotos")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for row in rows:
                    tree.insert("", "end", values=row)
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

        cargar_tarifas_motos()

    btnTarifas.config(command=mostrar_tarifas_motos)


    modalidad_seleccionada = tk.StringVar(value="Hora")

    def seleccionar_boton(boton):
            for b in botones:
                b.config(highlightbackground="white", bg="white", fg="black")
            boton.config(highlightbackground="red", bg="black", fg="white")
            modalidad_seleccionada.set(boton.cget("text"))
    

    def registrar_placa(imprimir_al_final=True):
        placa_valor = placa_var.get().strip()
        casco_valor = casco_var.get().strip() or None
        hora_actual = dt.datetime.now()
        modalidad_valor = modalidad_seleccionada.get()

        conexion = conectar_bd_parqueaderojmj()
        if conexion is None:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
            return
        
        if not placa_valor:
            messagebox.showerror("Error", "El campo Placa es obligatorio.")
            return

        try:
            cursor = conexion.cursor()

            query_verificar = "SELECT modalidad, fechaHoraEntrada FROM placas WHERE placa = ?"
            cursor.execute(query_verificar, (placa_valor,))
            resultado = cursor.fetchone()

            if resultado:
                modalidad_valor, hora_entrada = resultado
                hora_entrada = dt.datetime.strptime(hora_entrada, "%Y-%m-%d %H:%M:%S")
            else:
                tablas_fijas = {
                    "Semana": ("semanasMoto", 7),
                    "Quincena": ("quincenasMoto", 15),
                    "Mes": ("mensualidadesMoto", 30)
                }


                if modalidad_valor in tablas_fijas:
                    tabla, duracion_dias = tablas_fijas[modalidad_valor]
                    cursor.execute(f"SELECT entrada, salida, cedula, nombreCompleto FROM {tabla} WHERE placa = ?", (placa_valor,))
                    fila_modalidad = cursor.fetchone()

                    if fila_modalidad:
                        entrada_str, salida_str, cedula_hist, nombre_hist = fila_modalidad
                        try:
                            try:
                                salida_prev = dt.datetime.strptime(salida_str, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                salida_prev = dt.datetime.strptime(salida_str, "%Y-%m-%d")
                        except Exception:
                            salida_prev = None

                        try:
                            try:
                                entrada_prev = dt.datetime.strptime(entrada_str, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                entrada_prev = dt.datetime.strptime(entrada_str, "%Y-%m-%d")
                        except Exception:
                            entrada_prev = None

                        ahora = dt.datetime.now().replace(microsecond=0)
                        entrada_actual = ahora
                        if modalidad_valor == "Mes":
                            salida_actual = (entrada_actual + dt.timedelta(days=duracion_dias))
                        else:
                            salida_actual = (entrada_actual + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                        if salida_prev:
                            try:

                                if entrada_prev:
                                    hora_ref = entrada_prev.time()
                                else:
                                    hora_ref = salida_prev.time()

                                nueva_entrada_original = (salida_prev + dt.timedelta(days=1)).replace(
                                    hour=hora_ref.hour, minute=hora_ref.minute, second=hora_ref.second, microsecond=0
                                )
                                if modalidad_valor == "Mes":
                                    nueva_salida_original = add_months(nueva_entrada_original, months=1) - dt.timedelta(days=1)
                                else:
                                    nueva_salida_original = (nueva_entrada_original + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)
                            except Exception:
                                nueva_entrada_original = entrada_actual
                                nueva_salida_original = salida_actual
                        else:
                            nueva_entrada_original = None
                            nueva_salida_original = None

                        ventana_confirm = tk.Toplevel()
                        ventana_confirm.title("Registro existente - Confirmar")
                        ventana_confirm.resizable(False, False)
                        ventana_confirm.grab_set()
                        ventana_confirm.focus_set()

                        txt = "Se encontró un registro existente para esta placa.\n\n"
                        txt += f"Cédula: {cedula_hist or ''}\nNombre: {nombre_hist or ''}\nPlaca: {placa_valor}\n\n"

                        if nueva_entrada_original and nueva_salida_original:
                            nombre_modalidad = "Mensualidad" if modalidad_valor == "Mes" else modalidad_valor
                            txt += f"Última {nombre_modalidad}:\n  Entrada: {entrada_prev.strftime('%Y-%m-%d %H:%M:%S') if entrada_prev else ''}\n  Salida: {salida_prev.strftime('%Y-%m-%d %H:%M:%S') if salida_prev else ''}\n\n"
                            txt += f"Nueva {nombre_modalidad}:\n  Entrada: {nueva_entrada_original.strftime('%Y-%m-%d %H:%M:%S')}\n  Salida: {nueva_salida_original.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        else:
                            txt += f"Nueva {modalidad_valor} (por defecto):\n  Entrada: {entrada_actual.strftime('%Y-%m-%d %H:%M:%S')}\n  Salida: {salida_actual.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                        txt += "¿Desea continuar o modificar?"

                        lbl_info = tk.Label(ventana_confirm, text=txt, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
                        lbl_info.pack()

                        resultado_eleccion = {"opcion": None}

                        def elegir_original():
                            resultado_eleccion["opcion"] = "original"
                            ventana_confirm.destroy()

                        def elegir_actual():
                            resultado_eleccion["opcion"] = "actual"
                            ventana_confirm.destroy()

                        frm_bot = tk.Frame(ventana_confirm, pady=10)
                        frm_bot.pack()
                        btn_orig = tk.Button(frm_bot, text="Continuar", command=elegir_original, bg="#E5C41E", fg="#111111", cursor="hand2")
                        btn_act = tk.Button(frm_bot, text="Modificar", command=elegir_actual, bg="#E5C41E", fg="#111111", cursor="hand2")
                        btn_orig.grid(row=0, column=0, padx=10)
                        btn_act.grid(row=0, column=1, padx=10)

                        for btn in [
                            btn_orig,
                            btn_act
                        ]:
                            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                            btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

                        ventana_confirm.transient()
                        def _on_confirm_escape(event=None):
                            # mark as cancelled and close dialog
                            try:
                                resultado_eleccion["opcion"] = None
                            except Exception:
                                pass
                            try:
                                ventana_confirm.destroy()
                            except Exception:
                                pass

                        ventana_confirm.bind('<Escape>', _on_confirm_escape)
                        ventana_confirm.protocol('WM_DELETE_WINDOW', _on_confirm_escape)
                        ventana_confirm.transient()
                        ventana_confirm.wait_window()

                        # If the user cancelled via Escape or closed the dialog, abort the registration
                        if resultado_eleccion.get("opcion") is None:
                            try:
                                conexion.rollback()
                            except Exception:
                                pass
                            return

                        if clasificacion_actual != "Usuario":
                            entrada_para_guardar = None
                            salida_para_guardar = None
                            if resultado_eleccion["opcion"] == "original":
                                if nueva_entrada_original and nueva_salida_original:
                                    entrada_para_guardar = nueva_entrada_original
                                    salida_para_guardar = nueva_salida_original
                                else:
                                    entrada_para_guardar = entrada_actual
                                    salida_para_guardar = salida_actual
                            elif resultado_eleccion["opcion"] == "actual":
                                ventana_editar = tk.Toplevel()
                                ventana_editar.title("Modificar Fechas")
                                ventana_editar.resizable(False, False)
                                ventana_editar.grab_set()
                                ventana_editar.focus_set()

                                lbl_info = tk.Label(ventana_editar, text="Modifique las fechas si es necesario:", font=("Times New Roman", 12), padx=10, pady=10)
                                lbl_info.pack()

                                frm_fechas = tk.Frame(ventana_editar)
                                frm_fechas.pack(padx=10, pady=5)

                                tk.Label(frm_fechas, text="Fecha de Entrada:", font=("Times New Roman", 11)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
                                tk.Label(frm_fechas, text="Fecha de Salida:", font=("Times New Roman", 11)).grid(row=1, column=0, sticky="e", padx=5, pady=5)

                                try:
                                    if 'entrada_nueva' in locals() and entrada_nueva:
                                        entrada_propuesta = entrada_nueva
                                        salida_propuesta = salida_nueva
                                    elif 'nueva_entrada_original' in locals() and nueva_entrada_original:
                                        entrada_propuesta = nueva_entrada_original
                                        salida_propuesta = nueva_salida_original
                                    else:
                                        entrada_propuesta = entrada_actual
                                        salida_propuesta = salida_actual
                                except Exception:
                                    entrada_propuesta = entrada_actual
                                    salida_propuesta = salida_actual

                                entrada_var = tk.StringVar(value=entrada_propuesta.strftime('%Y-%m-%d %H:%M:%S'))
                                salida_var = tk.StringVar(value=salida_propuesta.strftime('%Y-%m-%d %H:%M:%S'))

                                entry_entrada = tk.Entry(frm_fechas, textvariable=entrada_var, font=("Times New Roman", 11), width=22)
                                entry_salida = tk.Entry(frm_fechas, textvariable=salida_var, font=("Times New Roman", 11), width=22)
                                entry_entrada.grid(row=0, column=1, padx=5, pady=5)
                                entry_salida.grid(row=1, column=1, padx=5, pady=5)

                                def on_ok_editar():
                                    try:
                                        entrada_dt = dt.datetime.strptime(entrada_var.get(), "%Y-%m-%d %H:%M:%S")
                                        salida_dt = dt.datetime.strptime(salida_var.get(), "%Y-%m-%d %H:%M:%S")
                                    except Exception:
                                        messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD HH:MM:SS")
                                        return
                                    nonlocal entrada_para_guardar, salida_para_guardar
                                    entrada_para_guardar = entrada_dt
                                    salida_para_guardar = salida_dt
                                    ventana_editar.destroy()

                                btn_ok = tk.Button(ventana_editar, text="OK", command=on_ok_editar, bg="#E5C41E", fg="#111111", cursor="hand2")
                                btn_ok.pack(pady=10)
                                btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                                btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

                                def _on_editar_cancel(event=None):
                                    nonlocal entrada_para_guardar, salida_para_guardar
                                    entrada_para_guardar = None
                                    salida_para_guardar = None
                                    try:
                                        ventana_editar.destroy()
                                    except Exception:
                                        pass

                                ventana_editar.bind('<Return>', lambda e: on_ok_editar())
                                ventana_editar.bind('<Escape>', _on_editar_cancel)
                                ventana_editar.protocol('WM_DELETE_WINDOW', _on_editar_cancel)
                                ventana_editar.transient()
                                ventana_editar.wait_window()
                                if entrada_para_guardar is None or salida_para_guardar is None:
                                    conexion.rollback()
                                    return
                            else:
                                conexion.rollback()
                                return
                        else:
                            messagebox.showinfo("Acceso Denegado", "No tiene permisos para modificar las fechas.")
                            return

                        try:
                            cursor.execute(
                                f"UPDATE {tabla} SET entrada = ?, salida = ?, recientementeDescongelado = 0 WHERE placa = ?",
                                (entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), salida_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), placa_valor)
                            )
                            
                            if modalidad_valor == "Mes":
                                tabla_hist = "historialMensualidadesMoto"
                            elif modalidad_valor == "Quincena":
                                tabla_hist = "historialQuincenasMoto"
                            else:
                                tabla_hist = "historialSemanasMoto"
                            cursor.execute(
                                f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, placa, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula_hist if cedula_hist else "", nombre_hist if nombre_hist else "", placa_valor, entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), salida_para_guardar.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            conexion.commit()
                        except Exception as e:
                            conexion.rollback()
                            messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")
                            return
                        limpiar_pantalla()
                    else:
                        cedula = askstring_no_cancel(frmRegistro, "Cédula", "Ingrese la cédula del cliente:")
                        if not cedula:
                            return
                        nombre_completo = None
                        try:
                            c2 = conexion.cursor()
                            c2.execute("SELECT nombreCompleto FROM clientes WHERE cedula = ?", (cedula,))
                            res_cliente = c2.fetchone()
                            c2.close()
                            if not res_cliente:
                                messagebox.showerror("Cliente no encontrado", "El cliente no existe en el sistema, por favor créalo primero.", parent=frmRegistro)
                                return
                            nombre_completo = res_cliente[0]
                        except Exception:
                            nombre_completo = None

                        existente = None
                        if cedula:
                            try:
                                id_col = 'idMensualidadesMoto' if tabla == 'mensualidadesMoto' else ('idQuincenasMoto' if tabla == 'quincenasMoto' else 'idSemanasMoto')
                                cursor.execute(f"SELECT {id_col}, placa, nombreCompleto FROM {tabla} WHERE cedula = ?", (cedula,))
                                existente = cursor.fetchone()
                            except Exception:
                                existente = None

                        if existente:
                            id_existente, placa_actual, nombre_exist = existente
                            ventana_choice = tk.Toplevel()
                            ventana_choice.title("Cédula encontrada")
                            ventana_choice.resizable(False, False)
                            ventana_choice.grab_set()
                            ventana_choice.focus_set()

                            texto = f"Cédula: {cedula}\nNombre: {nombre_exist or nombre_completo or ''}\nPlaca actual del cliente: {placa_actual}\n\n¿Desea agregar o actualizar esta placa?"
                            lbl = tk.Label(ventana_choice, text=texto, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
                            lbl.pack()

                            decision = {"accion": None}

                            def accion_registrar():
                                decision["accion"] = "registrar"
                                ventana_choice.destroy()

                            def accion_actualizar():
                                decision["accion"] = "actualizar"
                                ventana_choice.destroy()

                            frm_btns = tk.Frame(ventana_choice, pady=8)
                            frm_btns.pack()
                            btn_reg = tk.Button(frm_btns, text="Agregar", command=accion_registrar, bg="#E5C41E", fg="#111111", cursor="hand2")
                            btn_upd = tk.Button(frm_btns, text="Actualizar", command=accion_actualizar, bg="#E5C41E", fg="#111111", cursor="hand2")
                            btn_reg.grid(row=0, column=0, padx=8)
                            btn_upd.grid(row=0, column=1, padx=8)

                            for btn in [
                                btn_reg,
                                btn_upd
                            ]:
                                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                                btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

                            def _on_choice_escape(event=None):
                                try:
                                    decision["accion"] = None
                                except Exception:
                                    pass
                                try:
                                    ventana_choice.destroy()
                                except Exception:
                                    pass

                            ventana_choice.bind('<Escape>', _on_choice_escape)
                            ventana_choice.protocol('WM_DELETE_WINDOW', _on_choice_escape)
                            ventana_choice.transient()
                            ventana_choice.wait_window()

                            if decision["accion"] is None:
                                return

                            if decision["accion"] == "registrar":
                                entrada_nueva = hora_actual.replace(microsecond=0)
                                if modalidad_valor == "Mes":
                                    salida_nueva = add_months(entrada_nueva, months=1) - dt.timedelta(days=1)
                                else:
                                    salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)
                                cursor.execute(
                                    f"INSERT INTO {tabla} (cedula, nombreCompleto, placa, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                    (cedula if cedula else "", nombre_completo if nombre_completo else "", placa_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                                )
                                # Nota: no insertar en el historial al registrar cliente fijo.
                                # El registro de historial se realizará cuando se quite/elimine el registro.
                                conexion.commit()
                                try:
                                    actualizarConteoFijos()
                                except Exception:
                                    pass
                            else:
                                try:
                                    id_col = 'idMensualidadesMoto' if tabla == 'mensualidadesMoto' else ('idQuincenasMoto' if tabla == 'quincenasMoto' else 'idSemanasMoto')
                                    cursor.execute(f"UPDATE {tabla} SET placa = ? WHERE {id_col} = ?", (placa_valor, id_existente))
                                    conexion.commit()
                                except Exception as e:
                                    conexion.rollback()
                                    messagebox.showerror("Error", f"No se pudo actualizar la placa: {e}")
                                    return
                        else:
                            if not nombre_completo:
                                nombre_completo = askstring_no_cancel(frmRegistro, "Nombre Completo", "No se encontró el cliente. Ingrese el nombre completo:")
                                if not nombre_completo:
                                    return
                            entrada_nueva = hora_actual.replace(microsecond=0)
                            if modalidad_valor == "Mes":
                                salida_nueva = add_months(entrada_nueva, months=1) - dt.timedelta(days=1)
                            else:
                                salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)
                            cursor.execute(
                                f"INSERT INTO {tabla} (cedula, nombreCompleto, placa, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula if cedula else "", nombre_completo if nombre_completo else "", placa_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            # Nota: no insertar en el historial al registrar cliente fijo.
                            # El registro de historial se realizará cuando se quite/elimine el registro.
                            conexion.commit()
                            try:
                                actualizarConteoFijos()
                            except Exception:
                                pass
                query_insertar = """
                    INSERT INTO placas (placa, modalidad, casco, fechaHoraEntrada)
                    VALUES (?, ?, ?, ?)
                """
                parametros = (placa_valor, modalidad_valor, casco_valor, hora_actual.strftime("%Y-%m-%d %H:%M:%S"))
                cursor.execute(query_insertar, parametros)

                # No insertar en historialDePlacas al registrar; se insertará al quitar el registro.

                conexion.commit()

                if modalidad_valor in ["Hora", "Estudiante", "Día", "24 Horas"] and imprimir_al_final:
                    imprimir_recibo_entrada(
                        placa=placa_valor,
                        modalidad=modalidad_valor,
                        casco=casco_valor,
                        fecha_entrada=hora_actual.strftime("%Y-%m-%d %H:%M:%S"),
                        usuario=usuario_actual
                    )
                limpiar_pantalla()
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar la placa: {e}")
        finally:
            conexion.close()
        actualizarConteoModalidadesDelDia()

    workflow_state = {"exit_in_progress": False}

    def confirmar_registro():
        if workflow_state["exit_in_progress"]:
            return
        modalidad_valor = modalidad_seleccionada.get()
        placa_valor = placa_var.get().strip()
        if not placa_valor:
            messagebox.showerror("Error", "El campo Placa es obligatorio.")
            return
        if modalidad_valor in ["Mes", "Quincena", "Semana"]:
            registrar_placa(imprimir_al_final=False)
            return

        mini = tk.Toplevel()
        mini.title("Opciones de Registro")
        mini.resizable(False, False)
        mini.grab_set()

        tk.Label(mini, text="¿Desea imprimir recibo de entrada?", font=("Times New Roman", 12), padx=10, pady=10).pack()

        def do_imprimir():
            mini.destroy()
            try:
                placa_valor = placa_var.get().strip()
                casco_valor = casco_var.get().strip() or None
                modalidad_valor = modalidad_seleccionada.get()
                fecha_entrada_valor = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                placa_valor = placa_var.get().strip() if placa_var else ""
                casco_valor = casco_var.get().strip() if casco_var else None
                modalidad_valor = modalidad_seleccionada.get() if modalidad_seleccionada else ""
                fecha_entrada_valor = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if placa_valor and modalidad_valor:
                try:
                    imprimir_recibo_entrada(
                        placa=placa_valor,
                        modalidad=modalidad_valor,
                        casco=casco_valor,
                        fecha_entrada=fecha_entrada_valor,
                        usuario=usuario_actual
                    )
                except Exception as e:
                    try:
                        messagebox.showerror("Error de impresión", f"No se pudo imprimir el recibo: {e}")
                    except Exception:
                        pass

            try:
                registrar_placa(imprimir_al_final=False)
            except Exception:
                try:
                    messagebox.showerror("Error", "Ocurrió un error al registrar la entrada. Revise la consola para más detalles.")
                except Exception:
                    pass

        def do_continuar():
            mini.destroy()
            registrar_placa(imprimir_al_final=False)

        frm = tk.Frame(mini, pady=10)
        frm.pack()
        btn_imp = tk.Button(frm, text="Imprimir recibo", command=do_imprimir, bg="#E5C41E", fg="#111111", cursor="hand2")
        btn_cont = tk.Button(frm, text="Continuar", command=do_continuar, bg="#E5C41E", fg="#111111", cursor="hand2")
        btn_imp.grid(row=0, column=0, padx=8)
        btn_cont.grid(row=0, column=1, padx=8)

        for b in [btn_imp, btn_cont]:
            b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
            b.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="#111111"))

        btn_imp.focus_set()

        def on_popup_key(event):
            if event.keysym == 'Return':
                mini.unbind('<Return>')
                mini.unbind('<Escape>')
                btn_imp.invoke()
            elif event.keysym == 'Escape':
                mini.unbind('<Return>')
                mini.unbind('<Escape>')
                btn_cont.invoke()
        mini.bind('<Return>', on_popup_key)
        mini.bind('<Escape>', on_popup_key)

    btnRegistrar.config(command=confirmar_registro)


    def mostrar_ventana_pago(placa_valor, valor_cobrado, continuar_callback):
        ventana_pago = tk.Toplevel()
        ventana_pago.title("Pago")
        ventana_pago.geometry("400x300")
        ventana_pago.resizable(False, False)

        ventana_pago.update_idletasks()
        ancho_ventana = 400
        alto_ventana = 300
        x = (ventana_pago.winfo_screenwidth() // 2) - (ancho_ventana // 2)
        y = (ventana_pago.winfo_screenheight() // 2) - (alto_ventana // 2)
        ventana_pago.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        try:
            fondo_img = None
            for fname in ("fondoLogin.png",):
                try:
                    img = Image.open(fname).resize((ancho_ventana, alto_ventana))
                    fondo_img = ImageTk.PhotoImage(img)
                    break
                except Exception:
                    fondo_img = None
                    continue
            if fondo_img:
                lbl_fondo = tk.Label(ventana_pago, image=fondo_img)
                lbl_fondo.image = fondo_img
                lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            else:
                ventana_pago.configure(bg="black")
        except Exception:
            ventana_pago.configure(bg="black")

        try:
            if not ventana_pago.winfo_exists():
                return
            frmPago = tk.Frame(ventana_pago, bg="#111111", bd=0, relief="flat")
            frmPago.place(relx=0.5, rely=0.5, anchor="center", width=380, height=270)

            lbl_valor = tk.Label(frmPago, text=f"{valor_cobrado}", font=("Times New Roman", 16, "bold"), bg="#111111", fg="#E5C41E")
            lbl_valor.pack(pady=(50, 10))

            medio_pago = tk.StringVar(value="Efectivo")

            frame_medios_pago = tk.Frame(frmPago, bg="#111111")
            frame_medios_pago.pack(pady=10)

            rb_efectivo = tk.Radiobutton(frame_medios_pago, text="Efectivo", variable=medio_pago, value="Efectivo", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E", activebackground="#111111", activeforeground="#E5C41E", selectcolor="#111111")
            rb_nequi = tk.Radiobutton(frame_medios_pago, text="Nequi", variable=medio_pago, value="Nequi", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E", activebackground="#111111", activeforeground="#E5C41E", selectcolor="#111111")
            rb_bancolombia = tk.Radiobutton(frame_medios_pago, text="Bancolombia", variable=medio_pago, value="Bancolombia", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E", activebackground="#111111", activeforeground="#E5C41E", selectcolor="#111111")

            rb_efectivo.grid(row=0, column=0, padx=10)
            rb_nequi.grid(row=0, column=1, padx=10)
            rb_bancolombia.grid(row=0, column=2, padx=10)
        except Exception:
            return


        def procesar_salida(imprimir_factura=False):
            conexion = None
            cursor = None
            try:
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return

                cursor = conexion.cursor()
                fecha_salida = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("SELECT modalidad, fechaHoraEntrada FROM placas WHERE placa = ?", (placa_valor,))
                row = cursor.fetchone()
                modalidad_pago = row[0] if row else ""
                fecha_entrada = row[1] if row else ""

                if not row:
                    try:
                        cursor.execute("SELECT modalidad, fechaEntrada FROM historialDePlacas WHERE placa = ? ORDER BY datetime(fechaEntrada) DESC LIMIT 1", (placa_valor,))
                        row2 = cursor.fetchone()
                        if row2:
                            modalidad_pago = row2[0] if row2[0] is not None else modalidad_pago
                            fecha_entrada = row2[1] if row2[1] is not None else fecha_entrada
                    except Exception:
                        pass

                try:
                    cursor.execute(
                        "INSERT INTO pagos (placa, modalidad, valor, medio_pago, fecha) VALUES (?, ?, ?, ?, ?)",
                        (placa_valor, modalidad_pago, float(str(valor_cobrado).replace('Valor: $','').replace('Valor: ','').replace('$','').replace(',','')), medio_pago.get(), fecha_salida)
                    )
                except Exception as e:
                    print(f"Error al insertar en pagos: {e}")

                try:
                    dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                    dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                    duracion_td = dt_salida - dt_entrada
                    horas, rem = divmod(duracion_td.total_seconds(), 3600)
                    minutos, segundos = divmod(rem, 60)
                    duracion_str = f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
                except Exception:
                    duracion_str = "-"
                valor_raw = str(valor_cobrado)
                try:
                    for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                        if p in valor_raw:
                            valor_raw = valor_raw.replace(p, "")
                    valor_raw = valor_raw.replace(',', '')
                    valor_num = float(valor_raw)
                    total_str = f"{valor_num:.2f}"
                except Exception:
                    total_str = str(valor_cobrado)

                if imprimir_factura:
                    if not modalidad_pago or modalidad_pago in ["Hora", "Estudiante", "Día", "24 Horas"]:
                        imprimir_factura_salida(
                            placa=placa_valor,
                            modalidad=modalidad_pago,
                            fecha_entrada=fecha_entrada,
                            fecha_salida=fecha_salida,
                            duracion=duracion_str,
                            total=total_str,
                            usuario=usuario_actual
                        )
                    else:
                        try:
                            conexion_f = conectar_bd_parqueaderojmj()
                            if conexion_f is not None:
                                cur_f = conexion_f.cursor()
                                for tabla, modalidad_nombre in [("mensualidadesMoto", "Mes"), ("quincenasMoto", "Quincena"), ("semanasMoto", "Semana")]:
                                    cur_f.execute(f"SELECT cedula, nombreCompleto, placa, entrada, salida FROM {tabla} WHERE placa = ?", (placa_valor,))
                                    fila = cur_f.fetchone()
                                    if fila:
                                        cedula_f, nombre_f, placa_f, entrada_f, salida_f = fila
                                        try:
                                            total_f = total_str
                                        except NameError:
                                            try:
                                                vr = str(valor_cobrado)
                                                for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                                                    if p in vr:
                                                        vr = vr.replace(p, "")
                                                vr = vr.replace(',', '')
                                                total_f = f"{float(vr):.2f}"
                                            except Exception:
                                                total_f = ""
                                        imprimir_factura_salida_fijo(
                                            modalidad=modalidad_nombre,
                                            cedula=cedula_f,
                                            nombre=nombre_f,
                                            placa=placa_f,
                                            entrada=entrada_f,
                                            salida=salida_f,
                                            total=total_f,
                                            usuario=usuario_actual
                                        )
                                        break
                        except Exception:
                            pass

                # Ensure historial record exists for this placa/entrada. If an open historial
                # row exists (fechaSalida IS NULL) with same fechaEntrada, update it; otherwise
                # insert a new historial record with entrada+salida.
                try:
                    cursor.execute("SELECT idHistorialDePlacas FROM historialDePlacas WHERE placa = ? AND fechaEntrada = ? AND fechaSalida IS NULL", (placa_valor, fecha_entrada))
                    existing_hist = cursor.fetchone()
                except Exception:
                    existing_hist = None

                if existing_hist:
                    try:
                        cursor.execute("UPDATE historialDePlacas SET fechaSalida = ? WHERE idHistorialDePlacas = ?", (fecha_salida, existing_hist[0]))
                    except Exception as e:
                        print(f"Error actualizando historialDePlacas: {e}")
                else:
                    try:

                        entrada_val = fecha_entrada if fecha_entrada else fecha_salida
                        cursor.execute(
                            "INSERT INTO historialDePlacas (placa, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?)",
                            (placa_valor, modalidad_pago, entrada_val, fecha_salida)
                        )
                    except Exception as e:
                        print(f"Error inserting historialDePlacas: {e}")

                # For fixed-modalidades (Semana/Quincena/Mes) also insert into the
                # corresponding historial for fixed clients (mensualidades/quincenas/semanas)
                try:
                    if modalidad_pago in ["Semana", "Quincena", "Mes"]:
                        try:
                            # check each fixed table for a matching placa and insert into its historial
                            for tabla, modalidad_nombre, tabla_hist in [("mensualidadesMoto", "Mes", "historialMensualidadesMoto"), ("quincenasMoto", "Quincena", "historialQuincenasMoto"), ("semanasMoto", "Semana", "historialSemanasMoto")]:
                                try:
                                    cur2 = conexion.cursor()
                                    cur2.execute(f"SELECT cedula, nombreCompleto, placa, entrada, salida FROM {tabla} WHERE placa = ?", (placa_valor,))
                                    fila = cur2.fetchone()
                                    if fila:
                                        cedula_f, nombre_f, placa_f, entrada_f, salida_f = fila
                                        entrada_to_use = entrada_f if entrada_f else (fecha_entrada if fecha_entrada else fecha_salida)
                                        salida_to_use = fecha_salida
                                        try:
                                            cur2.execute(
                                                f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, placa, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                                (cedula_f if cedula_f else "", nombre_f if nombre_f else "", placa_f if placa_f else placa_valor, entrada_to_use, salida_to_use)
                                            )
                                            conexion.commit()
                                        except Exception:
                                            # ignore insertion errors for now
                                            pass
                                        finally:
                                            cur2.close()
                                        break
                                except Exception:
                                    try:
                                        cur2.close()
                                    except Exception:
                                        pass
                                    continue
                        except Exception:
                            pass
                except Exception:
                    pass

                query_eliminar_placa = "DELETE FROM placas WHERE placa = ?"
                cursor.execute(query_eliminar_placa, (placa_valor,))

                conexion.commit()

            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la salida: {e}")

            finally:
                if cursor:
                    cursor.close()
                if conexion:
                    conexion.close()

            ventana_pago.destroy()
            continuar_callback()

            btnRegistrar.config(text="Registrar")

            actualizarConteoModalidadesDelDia()

        frame_botones = tk.Frame(frmPago, bg="#111111")
        frame_botones.pack(pady=20)

        btn_imprimir = tk.Button(frame_botones, text="Imprimir factura", command=lambda: procesar_salida(True), font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", activebackground="black", activeforeground="#E5C41E")
        btn_imprimir.grid(row=0, column=0, padx=10)

        btn_continuar = tk.Button(frame_botones, text="Continuar", command=lambda: procesar_salida(False), font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", activebackground="black", activeforeground="#E5C41E")
        btn_continuar.grid(row=0, column=1, padx=10)

        for btn in [
            btn_imprimir,
            btn_continuar
        ]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

        btn_imprimir.focus_set()
        def on_pago_key(event):
            if event.keysym == 'Return':
                ventana_pago.unbind('<Return>')
                ventana_pago.unbind('<Escape>')
                btn_imprimir.invoke()
            elif event.keysym == 'Escape':
                ventana_pago.unbind('<Return>')
                ventana_pago.unbind('<Escape>')
                btn_continuar.invoke()
        ventana_pago.bind('<Return>', on_pago_key)
        ventana_pago.bind('<Escape>', on_pago_key)

        ventana_pago.transient()
        ventana_pago.grab_set()
        ventana_pago.wait_window()


    def registrar_salida(placa_valor, valor_cobrado):
        workflow_state["exit_in_progress"] = True
        def on_pago_close():
            workflow_state["exit_in_progress"] = False
            verificar_placa()
        mostrar_ventana_pago(placa_valor, valor_cobrado, on_pago_close)
        btnRegistrar.config(command=confirmar_registro)
        actualizarConteoModalidadesDelDia()
        limpiar_pantalla()


    def verificar_placa(event=None):
        placa_valor = placa_var.get().strip()
        if not placa_valor:
            btnRegistrar.config(text="Registrar", command=confirmar_registro)
            lblFechaEntrada.pack_forget()
            frmDuracion.pack_forget()
            lblValor.pack_forget()
            return

        conexion = conectar_bd_parqueaderojmj()
        if conexion is None:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
            return

        try:
            cursor = conexion.cursor()

            query_verificar = "SELECT modalidad, casco, fechaHoraEntrada FROM placas WHERE placa = ?"
            cursor.execute(query_verificar, (placa_valor,))
            resultado = cursor.fetchone()

            if resultado:
                modalidad_valor, casco_valor, hora_entrada = resultado
                hora_entrada = dt.datetime.strptime(hora_entrada, "%Y-%m-%d %H:%M:%S")
                hora_actual = dt.datetime.now()
                duracion = hora_actual - hora_entrada

                total_segundos = int(duracion.total_seconds())
                total_minutos = total_segundos // 60
                total_horas = total_minutos // 60
                total_24_horas = total_horas // 24
                horas_restantes = total_horas % 24
                total_dias_16h = total_horas // 16

                if modalidad_valor == "Día":
                    total_horas = total_segundos // 3600
                    dias_completos = total_horas // 16
                    horas_restantes = total_horas % 16

                    duracionEnDias.set(str(dias_completos))
                    duracionEnHoras.set(str(horas_restantes))

                    lblDuracionEnDias.config(text=f"Días: {duracionEnDias.get()}")
                    lblDuracionEnHoras.config(text=f"Horas: " + duracionEnHoras.get())

                if modalidad_valor == "24 Horas":
                    duracionEnDias.set("0")
                    lblDuracionEnDias.config(text="Días (16 horas): 0")
                    lblDuracionEnDias.grid_remove()
                    lblDuracionEn24Horas.grid()
                elif modalidad_valor == "Día":
                    duracionEn24Horas.set("0")
                    lblDuracionEn24Horas.config(text="24 Horas: 0")
                    lblDuracionEn24Horas.grid_remove()
                    lblDuracionEnDias.grid()
                else:
                    lblDuracionEnDias.grid()
                    lblDuracionEn24Horas.grid()

                duracionEnSegundos.set(str(total_segundos % 60))
                duracionEnMinutos.set(str(total_minutos % 60))
                duracionEnHoras.set(str(horas_restantes))
                duracionEn24Horas.set(str(total_24_horas))
                duracionEnDias.set(str(total_dias_16h))

                lblDuracionEnSegundos.config(text="Segundos: " + duracionEnSegundos.get())
                lblDuracionEnMinutos.config(text="Minutos: " + duracionEnMinutos.get())
                lblDuracionEnHoras.config(text="Horas: " + duracionEnHoras.get())
                lblDuracionEn24Horas.config(text="24 Horas: " + duracionEn24Horas.get())
                lblDuracionEnDias.config(text="Días (16 horas): " + duracionEnDias.get())

                horas_transcurridas = float(duracionEnHoras.get()) + float(duracionEn24Horas.get()) * 24
                if horas_transcurridas < 24:
                    ciclo_actual = 1
                else:
                    ciclo_actual = int(horas_transcurridas // 24)
                    if horas_transcurridas % 24 != 0:
                        ciclo_actual += 1

                query_tarifa = "SELECT valor FROM tarifasmotos WHERE tarifa = ?"
                cursor.execute(query_tarifa, (modalidad_valor,))
                tarifa = cursor.fetchone()
                if tarifa:
                    tarifa_valor = tarifa[0]
                    if modalidad_valor == "Hora":
                        tarifa_valor = tarifa[0]
                        total_minutos = total_segundos // 60
                        ciclo_actual = total_minutos // 60
                        minutos_en_ciclo = total_minutos % 60
                        if ciclo_actual == 0:
                            total_a_cobrar = tarifa_valor
                        else:
                            cuarto_hora = tarifa_valor / 4
                            cuarto_hora_aproximado = (round(cuarto_hora / 100) * 100)

                            if minutos_en_ciclo == 0:
                                total_a_cobrar = tarifa_valor * ciclo_actual
                            elif minutos_en_ciclo <= 15:
                                total_a_cobrar = tarifa_valor * ciclo_actual + cuarto_hora_aproximado
                            elif minutos_en_ciclo <= 30:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (2 * cuarto_hora_aproximado)
                            elif minutos_en_ciclo <= 45:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (3 * cuarto_hora_aproximado)
                            else:
                                total_a_cobrar = tarifa_valor * (ciclo_actual + 1)

                    elif modalidad_valor in ["Estudiante", "Día"]:
                        query_duracion = "SELECT duracion FROM tarifasmotos WHERE tarifa = ?"
                        cursor.execute(query_duracion, (modalidad_valor,))
                        duracion_base = cursor.fetchone()
                        if duracion_base:
                            duracion_base = int(duracion_base[0].split()[0])
                            ciclos_completos = total_horas // duracion_base
                            total_a_cobrar = tarifa_valor * max(1, ciclos_completos + 1)
                        else:
                            messagebox.showerror("Error", f"No se encontró la duración base para la modalidad {modalidad_valor}")
                            total_a_cobrar = tarifa_valor

                    elif modalidad_valor == "24 Horas":
                        tarifa_valor = tarifa[0]
                        total_horas = total_segundos // 3600
                        ciclo_actual = total_horas // 24
                        horas_en_ciclo = total_horas % 24
                        if ciclo_actual == 0:
                            total_a_cobrar = tarifa_valor
                        else:
                            cuarto_24h = tarifa_valor / 4
                            cuarto_24h_aproximado = (round(cuarto_24h / 100) * 100)

                            if horas_en_ciclo <= 6:
                                total_a_cobrar = tarifa_valor * ciclo_actual + cuarto_24h_aproximado
                            elif horas_en_ciclo <= 12:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (2 * cuarto_24h_aproximado)
                            elif horas_en_ciclo <= 18:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (3 * cuarto_24h_aproximado)
                            else:
                                total_a_cobrar = tarifa_valor * (ciclo_actual + 1)

                    elif modalidad_valor in ["Semana", "Quincena", "Mes"]:
                        total_a_cobrar = tarifa_valor

                    valor.set(f"Valor: {total_a_cobrar}")

                else:
                    print(f"Tarifa no encontrada para modalidad: {modalidad_valor}")
                    valor.set("Valor: Tarifa no encontrada")


                fechaEntrada.set(hora_entrada.strftime("%d/%m/%Y %H:%M:%S"))
                frmDuracion.pack(pady=5)
                lblFechaEntrada.config(text="Fecha y Hora de Entrada: " + fechaEntrada.get())
                lblFechaEntrada.pack(pady=5)
                lblValor.pack(pady=5)

                btn_modalidad = [btn_hora, btn_estudiante, btn_dia, btn_24h, btn_semana, btn_quincena, btn_mes]
                for btn in btn_modalidad:
                    if btn.cget("text") == modalidad_valor:
                        seleccionar_boton(btn)

                casco_var.set(casco_valor if casco_valor else "")
                fechaEntrada.set(hora_entrada.strftime("%d/%m/%Y %H:%M:%S"))

                btnRegistrar.config(
                    text="Facturar",
                    command=lambda: registrar_salida(placa_valor, valor.get())
                )
            else:
                btnRegistrar.config(text="Registrar", command=confirmar_registro)
                frmDuracion.pack_forget()
                lblValor.pack_forget()
                casco_var.set("")
                lblFechaEntrada.pack_forget()
                seleccionar_boton(btn_hora)
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar la placa: {e}")
        finally:
            conexion.close()

    placa.bind("<KeyRelease>", verificar_placa)

    limpiar_pantalla()

    def consultarPlacas():
        def reimprimir_recibo_entrada(event):
            item = tree.focus()
            if not item:
                return
            valores = tree.item(item, "values")
            if not valores:
                return
            placa = valores[1]
            modalidad = valores[2]
            casco = valores[3]
            fecha_entrada = valores[4]
            imprimir_recibo_entrada(
                placa=placa,
                modalidad=modalidad,
                casco=casco,
                fecha_entrada=fecha_entrada,
                usuario=usuario_actual
            )

        ventana_consultarPlacas = tk.Toplevel()
        ventana_consultarPlacas.title("Consultar Placas")
        ventana_consultarPlacas.geometry("800x600")
        ventana_consultarPlacas.bind('<Escape>', lambda e: ventana_consultarPlacas.destroy())

        frame_consultarPlacas = tk.Frame(ventana_consultarPlacas)
        frame_consultarPlacas.pack(fill="both", expand=True)

        scrollbar_vertical = tk.Scrollbar(frame_consultarPlacas, orient="vertical")
        scrollbar_horizontal = tk.Scrollbar(frame_consultarPlacas, orient="horizontal")

        tree = ttk.Treeview(frame_consultarPlacas, columns=("ID", "Placa", "Modalidad", "Casco", "Fecha y Hora de Entrada"), 
                            show="headings", yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        def eliminar_placa(event=None):
            from tkinter import messagebox
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para eliminar registros.")
                return
            it = tree.focus()
            if not it:
                return
            vals = tree.item(it, "values")
            if not vals or not vals[0]:
                return
            id_placa = vals[0]
            placa_text = vals[1] if len(vals) > 1 else ""
            modalidad_text = vals[2] if len(vals) > 2 else ""
            if messagebox.askyesno("Eliminar", "¿Seguro que deseas eliminar este registro?"):
                try:
                
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is not None:
                        cur = conexion.cursor()
                        cur.execute("DELETE FROM placas WHERE idPlacas = ?", (id_placa,))
                        try:
                            if modalidad_text in ("Semana", "Quincena", "Mes"):
                                try:
                                    cur.execute("DELETE FROM mensualidadesMoto WHERE placa = ?", (placa_text,))
                                except Exception:
                                    pass
                                try:
                                    cur.execute("DELETE FROM quincenasMoto WHERE placa = ?", (placa_text,))
                                except Exception:
                                    pass
                                try:
                                    cur.execute("DELETE FROM semanasMoto WHERE placa = ?", (placa_text,))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        conexion.commit()
                        tree.delete(it)
                        conexion.close()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {e}")
                actualizarConteoFijos()
                actualizarConteoModalidadesDelDia()
            ventana_consultarPlacas.focus_set()

        try:
            tree.bind("<KeyPress-r>", reimprimir_recibo_entrada)
            tree.bind("<KeyPress-s>", eliminar_placa)
        except Exception:
            pass
        

        tree.heading("ID", text="ID")
        tree.heading("Placa", text="Placa")
        tree.heading("Modalidad", text="Modalidad")
        tree.heading("Casco", text="Casco")
        tree.heading("Fecha y Hora de Entrada", text="Fecha y Hora de Entrada")

        tree.column("ID", width=50, anchor="center")
        tree.column("Placa", width=200, anchor="center")
        tree.column("Modalidad", width=150, anchor="center")
        tree.column("Casco", width=100, anchor="center")
        tree.column("Fecha y Hora de Entrada", width=200, anchor="center")

        def cargarPlacas():
            ventana_consultarPlacas.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idPlacas, placa, modalidad, casco, fechaHoraEntrada FROM placas")
                rows = cursor.fetchall()
                tree.delete(*tree.get_children())
                for row in rows:
                    tree.insert("", "end", values=row)
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar placas: {e}")
            finally:
                conexion.close()

        cargarPlacas()

        def seleccionar_placa(event):
            item = tree.focus()
            if not item:
                return

            valores = tree.item(item, "values")
            if valores:
                placa_var.set(valores[1])
                ventana_consultarPlacas.destroy()
            placa.icursor('end')

        tree.bind("<Return>", seleccionar_placa)

        def actualizarPlacas(event):
            item = tree.focus()
            if not item:
                return

            columna = tree.identify_column(event.x)
            columna_index = int(columna.replace("#", "")) - 1
            valores = tree.item(item, "values")

            if clasificacion_actual == "Usuario":
                if columna_index == 3:
                    fecha_hora_entrada = dt.datetime.strptime(valores[4], "%Y-%m-%d %H:%M:%S")
                    tiempo_transcurrido = dt.datetime.now() - fecha_hora_entrada
                    if tiempo_transcurrido.total_seconds() > 300:
                        messagebox.showerror("Error", "No puedes cambiar el casco después de 5 minutos.")
                        ventana_consultarPlacas.focus_set()
                        return
                else:
                    messagebox.showerror("Error", "No tienes permiso para modificar este campo.")
                    ventana_consultarPlacas.focus_set()
                    return
            
            if clasificacion_actual == "Usuario avanzado" and columna_index in [4]:
                messagebox.showerror("Error", "No tienes permiso para modificar este campo.")
                ventana_consultarPlacas.focus_set()
                return

            dlg = tk.Toplevel(tree)
            dlg.title("Editar Placa")
            dlg.resizable(False, False)
            entries = []
            if clasificacion_actual == "Usuario":
                fecha_hora_entrada = dt.datetime.strptime(valores[4], "%Y-%m-%d %H:%M:%S")
                tiempo_transcurrido = dt.datetime.now() - fecha_hora_entrada
                tk.Label(dlg, text="Casco:").grid(row=0, column=0, padx=6, pady=6)
                casco_var_edit = tk.StringVar(value=valores[3])
                entry_casco = tk.Entry(dlg, textvariable=casco_var_edit)
                entry_casco.grid(row=0, column=1, padx=6, pady=6)
                entries.append(entry_casco)
                if tiempo_transcurrido.total_seconds() > 300:
                    entry_casco.config(state="disabled")
                fecha_var_edit = tk.StringVar(value=valores[4])
                placa_var_edit = tk.StringVar(value=valores[1])
                modalidad_var_edit = tk.StringVar(value=valores[2])
            else:
                tk.Label(dlg, text="Placa:").grid(row=0, column=0, padx=6, pady=6)
                placa_var_edit = tk.StringVar(value=valores[1])
                entry_placa = tk.Entry(dlg, textvariable=placa_var_edit)
                entry_placa.grid(row=0, column=1, padx=6, pady=6)
                entries.append(entry_placa)
                def to_uppercase_var(*args):
                    val = placa_var_edit.get()
                    if val != val.upper():
                        placa_var_edit.set(val.upper())
                placa_var_edit.trace_add('write', lambda *args: to_uppercase_var())

                tk.Label(dlg, text="Modalidad:").grid(row=1, column=0, padx=6, pady=6)
                modalidades_fijas = {"Mes", "Quincena", "Semana"}
                modalidades_opts = [b.cget('text') for b in botones if b.cget('text') not in modalidades_fijas]
                modalidad_var_edit = tk.StringVar(value=valores[2])
                combo_modalidad = ttk.Combobox(dlg, values=modalidades_opts, textvariable=modalidad_var_edit, state='readonly')
                combo_modalidad.grid(row=1, column=1, padx=6, pady=6)
                entries.append(combo_modalidad)

                tk.Label(dlg, text="Casco:").grid(row=2, column=0, padx=6, pady=6)
                casco_var_edit = tk.StringVar(value=valores[3])
                entry_casco = tk.Entry(dlg, textvariable=casco_var_edit)
                entry_casco.grid(row=2, column=1, padx=6, pady=6)
                entries.append(entry_casco)

                def to_uppercase_casco_var(*args):
                    val = casco_var_edit.get()
                    if val != val.upper():
                        casco_var_edit.set(val.upper())
                casco_var_edit.trace_add('write', lambda *args: to_uppercase_casco_var())

                if clasificacion_actual == "Superusuario":
                    tk.Label(dlg, text="Fecha y Hora de Entrada:").grid(row=3, column=0, padx=6, pady=6)
                    fecha_var_edit = tk.StringVar(value=valores[4])
                    entry_fecha = tk.Entry(dlg, textvariable=fecha_var_edit, width=25)
                    entry_fecha.grid(row=3, column=1, padx=6, pady=6)
                    entries.append(entry_fecha)
                else:
                    fecha_var_edit = tk.StringVar(value=valores[4])

            def on_ok():
                nueva_placa = placa_var_edit.get().strip()
                nueva_modalidad = modalidad_var_edit.get().strip()
                nueva_casco = casco_var_edit.get().strip()
                nueva_fecha = fecha_var_edit.get().strip()
                if not nueva_placa or not nueva_modalidad or not nueva_fecha:
                    messagebox.showerror('Error', 'Todos los campos son obligatorios')
                    return
                try:
                    _ = dt.datetime.strptime(nueva_fecha, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    messagebox.showerror('Error', 'Formato de fecha inválido. Use YYYY-MM-DD HH:MM:SS')
                    return
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        messagebox.showerror('Error', 'No se pudo conectar a la base de datos')
                        return
                    cursor = conexion.cursor()
                    cursor.execute(
                        "UPDATE placas SET placa = ?, modalidad = ?, casco = ?, fechaHoraEntrada = ? WHERE idPlacas = ?",
                        (nueva_placa, nueva_modalidad, nueva_casco, nueva_fecha, valores[0])
                    )
                    cursor.execute(
                        "UPDATE historialDePlacas SET modalidad = ?, fechaEntrada = ? WHERE placa = ?",
                        (nueva_modalidad, nueva_fecha, nueva_placa)
                    )
                    conexion.commit()
                    cargarPlacas()
                    actualizarConteoModalidadesDelDia()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo actualizar: {e}')
                finally:
                    try:
                        if conexion:
                            conexion.close()
                    except Exception:
                        pass
                dlg.destroy()

            btn_ok = tk.Button(dlg, text='OK', command=on_ok, bg='#E5C41E', cursor='hand2')
            btn_ok.grid(row=4, column=0, columnspan=2, pady=8)

            for btn in [btn_ok]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

            def focus_entry_end(entry):
                entry.focus_set()
                entry.icursor('end')

            if entries:
                focus_entry_end(entries[0])

            def entry_nav_handler(event, idx):
                if event.keysym == 'Return':
                    if idx < len(entries) - 1:
                        focus_entry_end(entries[idx + 1])
                    else:
                        btn_ok.invoke()
                elif event.keysym == 'BackSpace':
                    # Solo cambiar si el entry está vacío
                    widget = event.widget
                    if idx > 0 and widget.get() == '':
                        focus_entry_end(entries[idx - 1])
                elif event.keysym == 'Escape':
                    dlg.destroy()

            for i, entry in enumerate(entries):
                entry.bind('<Key>', lambda e, idx=i: entry_nav_handler(e, idx))

            btn_ok.bind('<Return>', lambda e: btn_ok.invoke())
            dlg.bind('<Escape>', lambda e: dlg.destroy())

            btn_ok = tk.Button(dlg, text='OK', command=on_ok, bg='#E5C41E', cursor='hand2')
            btn_ok.grid(row=4, column=0, columnspan=2, pady=8)
            
            for btn in [
            btn_ok
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

        tree.bind("<Double-1>", actualizarPlacas)

    btnConsultarPlacas.config(command=consultarPlacas)


    def historialDePlacas():
        def reimprimir_factura_salida(event):
            item = tree.focus()
            if not item:
                return
            valores = tree.item(item, "values")
            if not valores:
                return
            placa = valores[1]
            modalidad = valores[2]
            fecha_entrada = valores[3]
            fecha_salida = valores[4]
            try:
                dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                duracion_td = dt_salida - dt_entrada
                horas, rem = divmod(duracion_td.total_seconds(), 3600)
                minutos, segundos = divmod(rem, 60)
                duracion_str = f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
            except Exception:
                duracion_str = "-"
            total = ""
            cedula_fijo = ""
            nombre_fijo = ""
            try:
                conexion = conectar_bd_parqueaderojmj()
                cursor = conexion.cursor()
                row = None
                try:
                    cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha DESC LIMIT 1", (placa, modalidad, fecha_salida))
                    row = cursor.fetchone()
                except Exception:
                    row = None

                if not row:
                    try:
                        cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (placa, modalidad))
                        row = cursor.fetchone()
                    except Exception:
                        row = None

                if not row:
                    try:
                        cursor.execute("SELECT valor FROM pagos WHERE placa = ? ORDER BY fecha DESC LIMIT 1", (placa,))
                        row = cursor.fetchone()
                    except Exception:
                        row = None

                if not row and modalidad not in ["Hora", "Estudiante", "Día", "24 Horas"]:
                    cedula_lookup = None
                    nombre_lookup = None
                    try:
                        for tabla in ["mensualidadesMoto", "quincenasMoto", "semanasMoto"]:
                            cursor.execute(f"SELECT cedula, nombreCompleto FROM {tabla} WHERE placa = ?", (placa,))
                            fila = cursor.fetchone()
                            if fila:
                                cedula_lookup, nombre_lookup = fila
                                break
                    except Exception:
                        cedula_lookup = None

                    if cedula_lookup:
                        try:
                            cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha DESC LIMIT 1", (cedula_lookup, modalidad, fecha_salida))
                            row = cursor.fetchone()
                        except Exception:
                            row = None

                        if not row:
                            try:
                                cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (cedula_lookup, modalidad))
                                row = cursor.fetchone()
                            except Exception:
                                row = None

                        if not row:
                            try:
                                cursor.execute("SELECT valor FROM pagos WHERE placa = ? ORDER BY fecha DESC LIMIT 1", (cedula_lookup,))
                                row = cursor.fetchone()
                            except Exception:
                                row = None

                if row and row[0] is not None:
                    try:
                        v = row[0]
                        if isinstance(v, (int, float)):
                            total = f"{float(v):.2f}"
                        else:
                            s = str(v)
                            for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                                if p in s:
                                    s = s.replace(p, "")
                            s = s.replace(',', '')
                            try:
                                total = f"{float(s):.2f}"
                            except Exception:
                                total = s
                    except Exception:
                        total = str(row[0])
                else:
                    total = ""
                if modalidad not in ["Hora", "Estudiante", "Día", "24 Horas"]:
                    for tabla in ["mensualidadesMoto", "quincenasMoto", "semanasMoto"]:
                        cursor.execute(f"SELECT cedula, nombreCompleto FROM {tabla} WHERE placa = ?", (placa,))
                        fila = cursor.fetchone()
                        if fila:
                            cedula_fijo, nombre_fijo = fila
                            break
            except Exception:
                total = ""
            finally:
                try:
                    cursor.close()
                except:
                    pass
                try:
                    conexion.close()
                except:
                    pass
            if modalidad in ["Hora", "Estudiante", "Día", "24 Horas"]:
                imprimir_factura_salida(
                    placa=placa,
                    modalidad=modalidad,
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    duracion=duracion_str,
                    total=total,
                    usuario=usuario_actual
                )
            else:
                imprimir_factura_salida_fijo(
                    modalidad=modalidad,
                    cedula=cedula_fijo,
                    nombre=nombre_fijo,
                    placa=placa,
                    entrada=fecha_entrada,
                    salida=fecha_salida,
                    total=total,
                    usuario=usuario_actual
                )

        ventana_historialDePlacas = tk.Toplevel()
        ventana_historialDePlacas.title("Historial de Placas")
        ventana_historialDePlacas.geometry("900x500")
        ventana_historialDePlacas.configure(bg="white")
        ventana_historialDePlacas.bind('<Escape>', lambda e: ventana_historialDePlacas.destroy())

        ventana_historialDePlacas.grid_rowconfigure(0, weight=0)
        ventana_historialDePlacas.grid_rowconfigure(1, weight=1)
        ventana_historialDePlacas.grid_columnconfigure(0, weight=1)

        frame_filtros = tk.Frame(ventana_historialDePlacas, bg="#111111")
        frame_filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame_filtros.grid_columnconfigure(0, weight=1)
        frame_filtros.grid_columnconfigure(1, weight=1)
        frame_filtros.grid_columnconfigure(2, weight=1)
        frame_filtros.grid_columnconfigure(3, weight=1)

        lbl_placa = tk.Label(frame_filtros, text="Placa:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
        lbl_placa.grid(row=0, column=0, padx=5, pady=5)
        placa_var = tk.StringVar()
        entry_placa = tk.Entry(frame_filtros, textvariable=placa_var, font=("Times New Roman", 14), width=20, bg="#F1E7B1", fg="black", justify="center")
        entry_placa.grid(row=0, column=1, padx=5, pady=5)

        def to_uppercase_hist(*args):
            v = placa_var.get()
            if v != v.upper():
                placa_var.set(v.upper())
        placa_var.trace_add("write", to_uppercase_hist)

        entry_placa.bind("<KeyRelease>", lambda e: cargarHistorialDePlacas())

        lbl_fecha_inicio = tk.Label(frame_filtros, text="Desde:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
        lbl_fecha_inicio.grid(row=0, column=2, padx=5, pady=5)
        fecha_inicio = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
        fecha_inicio.grid(row=0, column=3, padx=5, pady=5)

        lbl_fecha_fin = tk.Label(frame_filtros, text="Hasta:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
        lbl_fecha_fin.grid(row=0, column=4, padx=5, pady=5)
        fecha_fin = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
        fecha_fin.grid(row=0, column=5, padx=5, pady=5)

        btn_consultar = tk.Button(frame_filtros, text="Consultar", font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2")
        btn_consultar.grid(row=0, column=6, padx=10, pady=5, sticky="e")

        frame_historialDePlacas = tk.Frame(ventana_historialDePlacas)
        frame_historialDePlacas.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar_vertical = tk.Scrollbar(frame_historialDePlacas, orient="vertical")
        scrollbar_horizontal = tk.Scrollbar(frame_historialDePlacas, orient="horizontal")

        tree = ttk.Treeview(
            frame_historialDePlacas,
            columns=("ID", "Placa", "Modalidad", "Fecha de Entrada", "Fecha de Salida", "Valor"),
            show="headings",
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set
        )

        scrollbar_vertical.config(command=tree.yview)
        scrollbar_horizontal.config(command=tree.xview)

        scrollbar_vertical.pack(side="right", fill="y")
        scrollbar_horizontal.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # Visual tag for persisted-deleted rows
        try:
            tree.tag_configure('marked_deleted', background="#AEAEAE")
        except Exception:
            pass

        # Ensure marcadoEliminado column exists in historialDePlacas
        try:
            _conn_tmp = conectar_bd_parqueaderojmj()
            if _conn_tmp is not None:
                try:
                    _cur_tmp = _conn_tmp.cursor()
                    _cur_tmp.execute("PRAGMA table_info('historialDePlacas')")
                    _cols_tmp = [r[1] for r in _cur_tmp.fetchall()]
                    if 'marcadoEliminado' not in _cols_tmp:
                        try:
                            _cur_tmp.execute("ALTER TABLE historialDePlacas ADD COLUMN marcadoEliminado INTEGER DEFAULT 0")
                            _conn_tmp.commit()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    _cur_tmp.close()
                except Exception:
                    pass
                try:
                    _conn_tmp.close()
                except Exception:
                    pass
        except Exception:
            pass

        def eliminar_registro(event=None):
            from tkinter import messagebox
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Error", "No tienes permiso para eliminar registros.")
                return
            it = tree.focus()
            if not it:
                return
            vals = tree.item(it, "values")
            if not vals or not vals[0]:
                return
            id_placa = vals[0]
            if messagebox.askyesno("Eliminar", "¿Seguro que deseas marcar este registro como eliminado y borrar los pagos asociados?"):
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is not None:
                        cur = conexion.cursor()
                        try:
                            cur.execute("UPDATE historialDePlacas SET marcadoEliminado = 1 WHERE idHistorialDePlacas = ?", (id_placa,))
                        except Exception:
                            pass
                        try:
                            cur.execute("DELETE FROM pagos WHERE placa = ? AND modalidad = ? AND date(fecha) = date(?)", (vals[1], vals[2], vals[4]))
                        except Exception:
                            pass
                        try:
                            conexion.commit()
                        except Exception:
                            pass
                        try:
                            conexion.close()
                        except Exception:
                            pass
                        try:
                            tree.item(it, tags=('marked_deleted',))
                        except Exception:
                            pass
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {e}")
                actualizarConteoFijos()
                actualizarConteoModalidadesDelDia()
            entry_placa.focus_set()

        try:
            tree.bind("<KeyPress-r>", reimprimir_factura_salida)
            tree.bind("<KeyPress-a>", eliminar_registro)
        except Exception:
            pass

        tree.heading("ID", text="ID")
        tree.heading("Placa", text="Placa")
        tree.heading("Modalidad", text="Modalidad")
        tree.heading("Fecha de Entrada", text="Fecha de Entrada")
        tree.heading("Fecha de Salida", text="Fecha de Salida")
        tree.heading("Valor", text="Valor")

        tree.column("ID", width=50, anchor="center")
        tree.column("Placa", width=200, anchor="center")
        tree.column("Modalidad", width=150, anchor="center")
        tree.column("Fecha de Entrada", width=200, anchor="center")
        tree.column("Fecha de Salida", width=200, anchor="center")
        tree.column("Valor", width=100, anchor="center")

        for btn in [btn_consultar]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

        def on_tree_backspace(event):
            entry_placa.focus_set()
        tree.bind("<BackSpace>", on_tree_backspace)

        def cargarHistorialDePlacas():
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return

            entry_placa.focus_set()

            cursor = conexion.cursor()
            query = """
                SELECT idHistorialDePlacas, placa, modalidad, fechaEntrada, fechaSalida, COALESCE(marcadoEliminado,0) FROM historialDePlacas WHERE fechaSalida IS NOT NULL
            """
            params = []

            placa_filtro = placa_var.get().strip().upper()
            if placa_filtro:
                query += " AND UPPER(placa) LIKE ?"
                params.append(f"%{placa_filtro}%")

            fecha_i = fecha_inicio.get().strip()
            fecha_f = fecha_fin.get().strip()
            if fecha_i and fecha_f:
                try:
                    di = dt.datetime.strptime(fecha_i, "%Y-%m-%d")
                    df = dt.datetime.strptime(fecha_f, "%Y-%m-%d")
                    if di > df:
                        di, df = df, di
                    query += " AND date(fechaSalida) BETWEEN ? AND ?"
                    params.extend([di.strftime("%Y-%m-%d"), df.strftime("%Y-%m-%d")])
                except Exception:
                    pass

            query += " ORDER BY datetime(fechaSalida) ASC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            tree.delete(*tree.get_children())
            for row in rows:
                try:
                    cur2 = conexion.cursor()
                    cur2.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha DESC LIMIT 1", (row[1], row[2], row[4]))
                    pago = cur2.fetchone()
                    valor = pago[0] if pago and pago[0] is not None else ''
                except Exception:
                    valor = ''
                marcado = 0
                try:
                    marcado = int(row[5]) if len(row) > 5 and row[5] is not None else 0
                except Exception:
                    marcado = 0
                display_values = (*row[:5], valor)
                item = tree.insert("", "end", values=display_values)
                if marcado:
                    try:
                        tree.item(item, tags=('marked_deleted',))
                    except Exception:
                        pass
            
        btn_consultar.config(command=cargarHistorialDePlacas)
        entry_placa.bind("<KeyRelease>", lambda e: cargarHistorialDePlacas())
        def on_entry_placa_enter(event):
            if tree.get_children():
                first_item = tree.get_children()[0]
                tree.focus(first_item)
                tree.selection_set(first_item)
                tree.see(first_item)
                tree.focus_set()
        entry_placa.bind("<Return>", on_entry_placa_enter)
        cargarHistorialDePlacas()

    btnHistorialDePlacas.config(command=historialDePlacas)


    def consultarClientes():
        ventana_consultarClientes = tk.Toplevel()
        ventana_consultarClientes.title("Consultar Clientes")
        ventana_consultarClientes.geometry("400x150")
        ventana_consultarClientes.resizable(False, False)
        ventana_consultarClientes.bind('<Escape>', lambda e: ventana_consultarClientes.destroy())

        ancho, alto = 400, 150
        x = (ventana_consultarClientes.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana_consultarClientes.winfo_screenheight() // 2) - (alto // 2)
        ventana_consultarClientes.geometry(f"{ancho}x{alto}+{x}+{y}")
        ventana_consultarClientes.resizable(False, False)

        try:
            img = Image.open("fondoLogin.png").resize((ancho, alto))
            fondo_img = ImageTk.PhotoImage(img)
            lbl_fondo = tk.Label(ventana_consultarClientes, image=fondo_img)
            lbl_fondo.image = fondo_img
            lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            ventana_consultarClientes.configure(bg="black")

        ventana_consultarClientes.focus_set()

        frame_botones = tk.Frame(ventana_consultarClientes, bg="#111111")
        frame_botones.pack(expand=True)

        def mostrar_tabla(tipo_cliente):
            def reimprimir_factura_fijo(event):
                item = tree.focus()
                if not item:
                    return
                valores = tree.item(item, "values")
                if not valores:
                    return
                if combo_ver.get() == "Activos":
                    messagebox.showinfo("Info", "Solo se pueden reimprimir facturas desde el historial.")
                    ventana_tabla.focus_set()
                    return
                cedula = valores[1]
                nombre = valores[2]
                placa = valores[3]
                entrada = valores[4]
                salida = valores[5]
                modalidad = tipo_cliente[:-1] if tipo_cliente.endswith('s') else tipo_cliente
                total = ""
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    cursor = conexion.cursor()
                    row = None
                    try:
                        cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha ASC LIMIT 1", (placa, modalidad, salida))
                        row = cursor.fetchone()
                    except Exception:
                        row = None
                    if not row:
                        try:
                            cursor.execute("SELECT valor FROM pagos WHERE placa = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (placa, modalidad))
                            row = cursor.fetchone()
                        except Exception:
                            row = None
                    if not row:
                        try:
                            cursor.execute("SELECT valor FROM pagos WHERE placa = ? ORDER BY fecha DESC LIMIT 1", (placa,))
                            row = cursor.fetchone()
                        except Exception:
                            row = None
                    if row and row[0] is not None:
                        total = str(row[0])
                    cursor.close()
                    conexion.close()
                except Exception:
                    total = ""
                imprimir_factura_salida_fijo(
                    modalidad=modalidad,
                    cedula=cedula,
                    nombre=nombre,
                    placa=placa,
                    entrada=entrada,
                    salida=salida,
                    total=total,
                    usuario=usuario_actual
                )      

            ventana_consultarClientes.destroy()
            ventana_tabla = tk.Toplevel()
            ventana_tabla.title(f"{tipo_cliente}")
            ventana_tabla.geometry("900x600")
            ventana_tabla.bind('<Escape>', lambda e: ventana_tabla.destroy())

            def _on_close_tabla():
                try:
                    actualizarConteoFijos()
                except Exception:
                    pass
                ventana_tabla.destroy()

            ventana_tabla.protocol("WM_DELETE_WINDOW", _on_close_tabla)
            ventana_tabla.bind("<Destroy>", lambda e: actualizarConteoFijos())

            ventana_tabla.grid_rowconfigure(0, weight=0)
            ventana_tabla.grid_rowconfigure(1, weight=1)
            ventana_tabla.grid_rowconfigure(2, weight=0)
            ventana_tabla.grid_columnconfigure(0, weight=1)

            frame_filtros = tk.Frame(ventana_tabla, bg="#111111")
            frame_filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            frame_filtros.grid_columnconfigure(0, weight=1)
            frame_filtros.grid_columnconfigure(1, weight=1)
            frame_filtros.grid_columnconfigure(2, weight=1)
            frame_filtros.grid_columnconfigure(3, weight=1)

            lbl_cedula = tk.Label(frame_filtros, text="Cédula:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
            lbl_cedula.grid(row=0, column=0, padx=5, pady=5)
            cedula_var = tk.StringVar()
            entry_cedula = tk.Entry(frame_filtros, textvariable=cedula_var, font=("Times New Roman", 14), width=20, bg="#F1E7B1", fg="black", justify="center")
            entry_cedula.grid(row=0, column=1, padx=5, pady=5)

            lbl_placa = tk.Label(frame_filtros, text="Placa:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
            lbl_placa.grid(row=0, column=2, padx=5, pady=5)
            var_placa = tk.StringVar()
            entry_placa = tk.Entry(frame_filtros, textvariable=var_placa, font=("Times New Roman", 14), width=20, bg="#F1E7B1", fg="black", justify="center")
            entry_placa.grid(row=0, column=3, padx=5, pady=5)

            def validate_numeric_input(new_value):
                return new_value.isdigit() or new_value == ""

            validate_command = ventana_tabla.register(validate_numeric_input)
            entry_cedula.config(validate="key", validatecommand=(validate_command, "%P"))

            def to_uppercase_placa(*args):
                v = var_placa.get()
                if v != v.upper():
                    var_placa.set(v.upper())

            var_placa.trace_add("write", to_uppercase_placa)

            entry_cedula.bind("<KeyRelease>", lambda e: cargar_datos())
            entry_placa.bind("<KeyRelease>", lambda e: cargar_datos())

            entry_cedula.focus_set()

            def on_cedula_enter(event):
                entry_placa.focus_set()
            entry_cedula.bind("<Return>", on_cedula_enter)

            def on_placa_enter(event):
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
                def on_tree_backspace(event):
                    entry_placa.focus_set()
                tree.bind("<BackSpace>", on_tree_backspace)
            entry_placa.bind("<Return>", on_placa_enter)

            def on_placa_backspace(event):
                if entry_placa.get() == "":
                    entry_cedula.focus_set()
            entry_placa.bind("<BackSpace>", on_placa_backspace)

            lbl_ver = tk.Label(frame_filtros, text="Ver:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#E5C41E")
            lbl_ver.grid(row=0, column=4, padx=5, pady=5)
            ver_var = tk.StringVar(value="Activos")
            combo_ver = ttk.Combobox(frame_filtros, textvariable=ver_var, values=("Activos", "Historial"), font=("Times New Roman", 14), width=18, state="readonly", justify="center")
            combo_ver.grid(row=0, column=5, padx=5, pady=5)
            try:
                combo_ver.bind("<<ComboboxSelected>>", lambda e: cargar_datos())
            except Exception:
                pass

            frame_tabla = tk.Frame(ventana_tabla)
            frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

            scrollbar_vertical = tk.Scrollbar(frame_tabla, orient="vertical")
            scrollbar_horizontal = tk.Scrollbar(frame_tabla, orient="horizontal")

            tree = ttk.Treeview(
                frame_tabla,
                columns=("ID", "Cedula", "Nombre Completo", "Placa", "Desde", "Hasta"),
                show="headings",
                yscrollcommand=scrollbar_vertical.set,
                xscrollcommand=scrollbar_horizontal.set
            )

            scrollbar_vertical.config(command=tree.yview)
            scrollbar_horizontal.config(command=tree.xview)

            scrollbar_vertical.pack(side="right", fill="y")
            scrollbar_horizontal.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)

            try:
                tree.bind("<KeyPress-r>", reimprimir_factura_fijo)
            except Exception:
                pass

            tree.heading("ID", text="ID")
            tree.heading("Cedula", text="Cédula")
            tree.heading("Nombre Completo", text="Nombre Completo")
            tree.heading("Placa", text="Placa")
            tree.heading("Desde", text="Desde")
            tree.heading("Hasta", text="Hasta")

            tree.column("ID", width=60, anchor="center")
            tree.column("Cedula", width=120, anchor="center")
            tree.column("Nombre Completo", width=220, anchor="center")
            tree.column("Placa", width=120, anchor="center")
            tree.column("Desde", width=220, anchor="center")
            tree.column("Hasta", width=220, anchor="center")

            tree.tag_configure('congelado', background='#ADD8E6')
            tree.tag_configure('descongelado', background='#C7F0C7')

            btn_frame_ops = tk.Frame(ventana_tabla, bg="#111111")
            btn_frame_ops.grid(row=2, column=0, sticky="ew", pady=4, padx=10)
            btn_frame_ops.grid_columnconfigure(0, weight=1)
            btn_congelar = tk.Button(btn_frame_ops, text="Congelar", bg="#E5C41E", fg="#111111", cursor="hand2")
            btn_descongelar = tk.Button(btn_frame_ops, text="Descongelar", bg="#E5C41E", fg="#111111", cursor="hand2")
            btn_congelar.grid(row=0, column=0, sticky="e", padx=6)
            btn_descongelar.grid(row=0, column=1, sticky="e", padx=6)
            btn_quitar = tk.Button(btn_frame_ops, text="Quitar", bg="#E5C41E", fg="#111111", cursor="hand2")
            btn_quitar.grid(row=0, column=2, sticky="e", padx=6)

            def cargar_datos():
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                                
                try:
                    cursor = conexion.cursor()
                    mostrar = ver_var.get()
                    params = []
                    ced = cedula_var.get().strip()
                    plc = var_placa.get().strip()
                    where_clauses = []
                    if mostrar == "Activos":
                        if tipo_cliente == "Mensualidades":
                            sql = "SELECT idMensualidadesMoto, cedula, nombreCompleto, placa, entrada, salida FROM mensualidadesMoto"
                            id_col = 'idMensualidadesMoto'
                            tabla_activa = 'mensualidadesMoto'
                        elif tipo_cliente == "Quincenas":
                            sql = "SELECT idQuincenasMoto, cedula, nombreCompleto, placa, entrada, salida FROM quincenasMoto"
                            id_col = 'idQuincenasMoto'
                            tabla_activa = 'quincenasMoto'
                        else:
                            sql = "SELECT idSemanasMoto, cedula, nombreCompleto, placa, entrada, salida FROM semanasMoto"
                            id_col = 'idSemanasMoto'
                            tabla_activa = 'semanasMoto'
                        if ced:
                            where_clauses.append("LOWER(cedula) LIKE ?")
                            params.append(f"%{ced.lower()}%")
                        if plc:
                            where_clauses.append("LOWER(placa) LIKE ?")
                            params.append(f"%{plc.lower()}%")
                        if where_clauses:
                            sql += " WHERE " + " AND ".join(where_clauses)
                        sql += " ORDER BY datetime(salida) ASC"
                        cursor.execute(sql, tuple(params))
                        rows = cursor.fetchall()
                        tree.delete(*tree.get_children())
                        for row in rows:
                            item_id = tree.insert("", "end", values=row)
                            try:
                                cursor.execute(f"SELECT congelado, fechaCongelado, recientementeDescongelado FROM {tabla_activa} WHERE {id_col} = ?", (row[0],))
                                meta = cursor.fetchone()
                                if meta:
                                    congelado_flag = meta[0]
                                    recientemente_descongelado = meta[2] if len(meta) > 2 else 0
                                    if congelado_flag:
                                        tree.item(item_id, tags=("congelado",))
                                    elif recientemente_descongelado == 1:
                                        tree.item(item_id, tags=("descongelado",))
                                    else:
                                        tree.item(item_id, tags=())
                            except Exception:
                                pass
                        for w in (btn_congelar, btn_descongelar, btn_quitar):
                            w.config(state="normal")
                    else:
                        if tipo_cliente == "Mensualidades":
                            sql = "SELECT idHistorialMensualidadesMoto, cedula, nombreCompleto, placa, entrada, salida FROM historialMensualidadesMoto"
                        elif tipo_cliente == "Quincenas":
                            sql = "SELECT idHistorialQuincenasMoto, cedula, nombreCompleto, placa, entrada, salida FROM historialQuincenasMoto"
                        else:
                            sql = "SELECT idHistorialSemanasMoto, cedula, nombreCompleto, placa, entrada, salida FROM historialSemanasMoto"
                        if ced:
                            where_clauses.append("LOWER(cedula) LIKE ?")
                            params.append(f"%{ced.lower()}%")
                        if plc:
                            where_clauses.append("LOWER(placa) LIKE ?")
                            params.append(f"%{plc.lower()}%")
                        if where_clauses:
                            sql += " WHERE " + " AND ".join(where_clauses)
                        sql += " ORDER BY datetime(salida) ASC"
                        cursor.execute(sql, tuple(params))
                        rows = cursor.fetchall()
                        tree.delete(*tree.get_children())
                        for row in rows:
                            tree.insert("", "end", values=row)
                        for w in (btn_congelar, btn_descongelar, btn_quitar):
                            w.config(state="disabled")

                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar los datos: {e}")
                finally:
                    conexion.close()                
            cargar_datos()

            def congelar_registro():
                selected = tree.focus()
                if not selected:
                    return
                vals = tree.item(selected, 'values')
                id_reg = vals[0]
                tabla = 'mensualidadesMoto' if tipo_cliente=='Mensualidades' else ('quincenasMoto' if tipo_cliente=='Quincenas' else 'semanasMoto')
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    id_col = 'idMensualidadesMoto' if tipo_cliente=='Mensualidades' else ('idQuincenasMoto' if tipo_cliente=='Quincenas' else 'idSemanasMoto')
                    cursor.execute(f"UPDATE {tabla} SET congelado = 1, fechaCongelado = ?, recientementeDescongelado = 0 WHERE {id_col} = ?", (ahora, id_reg))
                    conexion.commit()
                    tree.item(selected, tags=('congelado',))
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo congelar el registro: {e}')
                finally:
                    if conexion:
                        conexion.close()
            btn_congelar.config(command=congelar_registro)

            def descongelar_registro():
                selected = tree.focus()
                if not selected:
                    return
                vals = tree.item(selected, 'values')
                id_reg = vals[0]
                tabla = 'mensualidadesMoto' if tipo_cliente=='Mensualidades' else ('quincenasMoto' if tipo_cliente=='Quincenas' else 'semanasMoto')
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    id_col = 'idMensualidadesMoto' if tipo_cliente=='Mensualidades' else ('idQuincenasMoto' if tipo_cliente=='Quincenas' else 'idSemanasMoto')
                    cursor.execute(f"SELECT fechaCongelado, salida FROM {tabla} WHERE {id_col} = ?", (id_reg,))
                    fila = cursor.fetchone()
                    if not fila:
                        return
                    fecha_congelado, salida_actual = fila
                    if not fecha_congelado:
                        messagebox.showinfo('Info', 'El registro no estaba congelado.')
                        return

                    try:
                        fecha_cong_dt = dt.datetime.strptime(fecha_congelado, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        try:
                            fecha_cong_dt = dt.datetime.strptime(fecha_congelado, "%Y-%m-%d")
                        except Exception:
                            fecha_cong_dt = None

                    ahora = dt.datetime.now()
                    if fecha_cong_dt:
                        dias_congelado = (ahora.date() - fecha_cong_dt.date()).days
                        if dias_congelado < 0:
                            dias_congelado = 0
                    else:
                        dias_congelado = 0

                    try:
                        salida_dt = None
                        if salida_actual:
                            try:
                                salida_dt = dt.datetime.strptime(salida_actual, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                try:
                                    salida_dt = dt.datetime.strptime(salida_actual, "%Y-%m-%d")
                                except Exception:
                                    salida_dt = None
                        if salida_dt:
                            nueva_salida = salida_dt + dt.timedelta(days=dias_congelado)
                            nueva_salida_str = nueva_salida.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            nueva_salida_str = salida_actual
                    except Exception:
                        nueva_salida_str = salida_actual

                    cursor.execute(f"UPDATE {tabla} SET congelado = 0, fechaCongelado = NULL, salida = ?, recientementeDescongelado = 1 WHERE {id_col} = ?", (nueva_salida_str, id_reg))
                    conexion.commit()
                    tree.item(selected, tags=('descongelado',))

                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo descongelar el registro: {e}')
                finally:
                    if conexion:
                        conexion.close()
                cargar_datos()
            btn_descongelar.config(command=descongelar_registro)

            def quitar_registro():
                try:
                    ventana_tabla.focus_set()
                except Exception:
                    pass
                selected = tree.focus()
                if not selected:
                    return
                if clasificacion_actual == 'Usuario':
                    messagebox.showerror("Error", "No tienes permiso para quitar registros.")
                    return
                try:
                    if not messagebox.askyesno("Quitar", "¿Seguro que deseas quitar este registro?"):
                        entry_cedula.focus_set()
                        return
                    entry_cedula.focus_set()
                except Exception:
                    pass
                vals = tree.item(selected, 'values')
                if not vals:
                    return
                id_reg = vals[0]
                tabla = 'mensualidadesMoto' if tipo_cliente == 'Mensualidades' else ('quincenasMoto' if tipo_cliente == 'Quincenas' else 'semanasMoto')
                conexion = None
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    id_col = 'idMensualidadesMoto' if tipo_cliente == 'Mensualidades' else ('idQuincenasMoto' if tipo_cliente == 'Quincenas' else 'idSemanasMoto')
                    try:
                        cursor.execute(f"DELETE FROM {tabla} WHERE {id_col} = ?", (id_reg,))
                    except Exception:
                        pass
                    try:
                        conexion.commit()
                    except Exception:
                        pass
                    try:
                        tree.delete(selected)
                    except Exception:
                        pass
                    try:
                        actualizarConteoFijos()
                    except Exception:
                        pass
                    try:
                        actualizarConteoModalidadesDelDia()
                    except Exception:
                        pass
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo quitar el registro: {e}")
                finally:
                    try:
                        if conexion:
                            conexion.close()
                    except Exception:
                        pass
            btn_quitar.config(command=quitar_registro)

            for btn in [btn_congelar, btn_descongelar, btn_quitar]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

            cargar_datos()

        btn_mensualidades = tk.Button(frame_botones, text="Mensualidades", font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Mensualidades"))
        btn_quincenas = tk.Button(frame_botones, text="Quincenas", font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Quincenas"))
        btn_semanas = tk.Button(frame_botones, text="Semanas", font=("Times New Roman", 14, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Semanas"))
        btn_mensualidades.grid(row=0, column=0, padx=10, pady=10)
        btn_quincenas.grid(row=0, column=1, padx=10, pady=10)
        btn_semanas.grid(row=0, column=2, padx=10, pady=10)
        for btn in [btn_mensualidades, btn_quincenas, btn_semanas]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="#111111"))

    btnConsultar.config(command=consultarClientes)

    def arqueo_de_caja():
        if clasificacion_actual == "Usuario":
            messagebox.showerror("Error", "No tienes permiso para realizar un arqueo de caja.")
            return
        
        else:
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

            root = frmFunciones.winfo_toplevel()
            dlg = FechaDialog(root, title="Arqueo de Caja")
            if dlg.result is None:
                return
            fecha_ini, fecha_fin = dlg.result
            conexion = conectar_bd_parqueaderojmj()
            efectivo = 0
            nequi = 0
            bancolombia = 0
            try:
                cursor = conexion.cursor()
                query = '''SELECT medio_pago, SUM(valor) FROM pagos WHERE date(fecha) >= ? AND date(fecha) <= ? GROUP BY medio_pago'''
                cursor.execute(query, (fecha_ini, fecha_fin))
                for medio, total in cursor.fetchall():
                    if medio == 'Efectivo':
                        efectivo = total or 0
                    elif medio == 'Nequi':
                        nequi = total or 0
                    elif medio == 'Bancolombia':
                        bancolombia = total or 0
            except Exception as e:
                messagebox.showerror("Error", f"Error al consultar pagos: {e}")
                return
            finally:
                if conexion:
                    conexion.close()
            total = (efectivo or 0) + (nequi or 0) + (bancolombia or 0)
            resumen = tk.Toplevel(root)
            resumen.title("Arqueo de Caja")
            resumen.geometry("300x600")
            hoy_str = dt.datetime.now().strftime('%d/%m/%Y')

            info = f"{hoy_str}\nParqueadero JMJ\nNIT: 87715766-9\nDireccion: Carrera 43 #52-36\n\n"
            info += f"Fecha inicial: {fecha_ini}\nFecha final: {fecha_fin}\n\n"
            line_width = 32
            title = "ARQUEO DE MOTOS"
            info += title.center(line_width)
            info += "\n\n"
            info += "VENTAS / FACTURACION\n"
            info += f"Efectivo: ${efectivo:,.0f}\n"
            if nequi > 0:
                info += f"Nequi: ${nequi:,.0f}\n"
            if bancolombia > 0:
                info += f"Bancolombia: ${bancolombia:,.0f}\n"
            info += f"TOTAL: ${total:,.0f}\n"
            info += "\n" * 4

            lbl = tk.Label(resumen, text=info, font=("Times New Roman", 13), justify="left")
            lbl.pack(padx=20, pady=20)

            resumen.focus_set()

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

                        hJob = win32print.StartDocPrinter(hPrinter, 1, ("ArqueoCaja.txt", None, "RAW"))
                        win32print.StartPagePrinter(hPrinter)
                        texto = info.replace('\n', '\r\n')
                        win32print.WritePrinter(hPrinter, texto.encode('utf-8'))
                        win32print.EndPagePrinter(hPrinter)
                        win32print.EndDocPrinter(hPrinter)
                    finally:
                        if hPrinter:
                            win32print.ClosePrinter(hPrinter)

                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo imprimir en la impresora: {e}")

            btn_imprimir = tk.Button(resumen, text="Imprimir", font=("Times New Roman", 13, "bold"), bg="#E5C41E", fg="#111111", cursor="hand2", command=imprimir_ventana)
            btn_imprimir.pack(pady=50)

            for btn in [
                btn_imprimir
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#E5C41E"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#E5C41E", fg="black"))

            try:
                resumen.bind('<Escape>', lambda e: resumen.destroy())
                resumen.bind('<Return>', lambda e: btn_imprimir.invoke())
                btn_imprimir.focus_set()
            except Exception:
                pass

            resumen.transient(root)
            resumen.grab_set()
            resumen.wait_window()

    btnArqueo.config(command=arqueo_de_caja)

    placa.focus_set()

    placa.bind('<Control-b>', lambda event: abrir_tabla_placas())