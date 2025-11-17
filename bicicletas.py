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
import unicodedata

def crearFramesBicicletas(parent, usuario_actual, clasificacion_actual):
    workflow_state = {"exit_in_progress": False}
    
    def abrir_tabla_cedulas(event=None):
        consultarCedulas()
    parent.bind('<Control-b>', lambda event: abrir_tabla_cedulas())
    
    def add_months(dtobj, months=1):
        year = dtobj.year + (dtobj.month - 1 + months) // 12
        month = (dtobj.month - 1 + months) % 12 + 1
        day = min(dtobj.day, [31,
                              29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                              31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return dt.datetime(year, month, day, dtobj.hour, dtobj.minute, dtobj.second, dtobj.microsecond)
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
                SET tarifa = REPLACE(tarifa, ' Bicicleta', '')
            """
            cursor.execute(query_actualizar)
            conexion.commit()

        except Exception as e:
            messagebox.showerror("Error", f"Error al sincronizar tarifas: {e}")
        finally:
            conexion.close()
    sincronizar_tarifas("tarifasbicicletas", "%Bicicleta%")
    frmRegistro = tk.Frame(parent, bg="#F6EAAE")
    frmRegistro.place(x=0, y=0, relheight=1, relwidth=0.65)
    frmRegistro.pack_propagate(False)

    img_motos = Image.open("iconoBicicletas.ico").resize((100, 100))
    icono_motos = ImageTk.PhotoImage(img_motos)
    lbl_icono_motos = tk.Label(frmRegistro, image=icono_motos, bg="#F6EAAE")
    lbl_icono_motos.image = icono_motos
    lbl_icono_motos.place(relx=0, rely=1, anchor="sw", x=10, y=-10)


    # Detectar inicial del usuario logueado
    inicial = usuario_actual.strip()[0].upper() if usuario_actual else "N"
    if inicial not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        inicial = "N"
    icono_path = f"{inicial}.png"
    try:
        imgUsuario = Image.open(icono_path).resize((90, 90))
    except Exception:
        imgUsuario = Image.open("N.png").resize((90, 90))
    iconoUsuario = ImageTk.PhotoImage(imgUsuario)
    lblIconoUsuario = tk.Label(frmRegistro, image=iconoUsuario, bg="#F6EAAE")
    lblIconoUsuario.image = iconoUsuario
    lblIconoUsuario.place(relx=0, rely=0, anchor="nw", x=10, y=10)

    frmRegistroInterno = tk.Frame(frmRegistro, bg="#F6EAAE")
    frmRegistroInterno.pack(expand=True)

    lbl_fecha_hora = tk.Label(frmRegistroInterno, font=("Times New Roman", 25, "bold"), bg="#F6EAAE")
    lbl_fecha_hora.pack(pady=10)

    frmInputs = tk.Frame(frmRegistroInterno, bg="#F6EAAE")
    frmInputs.pack(pady=10)

    frmFila1 = tk.Frame(frmInputs, bg="#F6EAAE")
    frmFila1.pack(pady=5)
    lbl_cedula = tk.Label(frmFila1, text="Cédula:", font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lbl_cedula.pack(side="left", padx=(0, 8))
    cedula_var = tk.StringVar()
    def solo_numeros_y_autocompletar(*args):
        valor = cedula_var.get()
        if not valor.isdigit():
            cedula_var.set(''.join(filter(str.isdigit, valor)))
            valor = cedula_var.get()
        if valor:
            conexion = conectar_bd_parqueaderojmj()
            if conexion:
                try:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT nombreCompleto FROM clientes WHERE cedula = ?", (valor,))
                    row = cursor.fetchone()
                    if row:
                        nombre_var.set(row[0])
                    else:
                        nombre_var.set("")
                        combo_tipo.set("")
                        color_var.set("")
                        casco_var.set("")

                except Exception:
                    nombre_var.set("")
                finally:
                    conexion.close()
        else:
            nombre_var.set("")
    cedula_var.trace_add("write", solo_numeros_y_autocompletar)
    entry_cedula = tk.Entry(frmFila1, textvariable=cedula_var, font=("Times New Roman", 24), width=12, justify="center", bg="black", fg="white", insertbackground="white")
    entry_cedula.pack(side="left", padx=(0, 20))
    lbl_nombre = tk.Label(frmFila1, text="Nombre Completo:", font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lbl_nombre.pack(side="left", padx=(0, 8))
    nombre_var = tk.StringVar()
    def _valid_no_digits(new_value):
        if new_value is None:
            return True
        # Allow empty string
        if new_value == "":
            return True
        for ch in new_value:
            if ch.isdigit():
                return False
        return True

    _vcmd_nombre = frmFila1.register(_valid_no_digits)
    entry_nombre = tk.Entry(frmFila1, textvariable=nombre_var, font=("Times New Roman", 24), width=20, justify="center", bg="black", fg="white", insertbackground="white", validate='key', validatecommand=(_vcmd_nombre, '%P'))
    entry_nombre.pack(side="left")

    frmFila2 = tk.Frame(frmInputs, bg="#F6EAAE")
    frmFila2.pack(pady=5)
    lbl_tipo = tk.Label(frmFila2, text="Tipo de Bicicleta:", font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lbl_tipo.pack(side="left", padx=(0, 8))
    tipos_bici = ["Todoterreno", "Ciclismo", "Monopatin", "Electrica", "Otro..."]
    tipo_var = tk.StringVar()
    combo_tipo = ttk.Combobox(frmFila2, values=tipos_bici, font=("Times New Roman", 24), width=14, state="readonly", textvariable=tipo_var, justify="center", style="Black.TCombobox")
    combo_tipo.pack(side="left", padx=(0, 20))
    combo_tipo.set("")
    lbl_color = tk.Label(frmFila2, text="Color:", font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lbl_color.pack(side="left", padx=(0, 8))
    color_var = tk.StringVar()
    _vcmd_color = frmFila2.register(_valid_no_digits)
    entry_color = tk.Entry(frmFila2, textvariable=color_var, font=("Times New Roman", 24), width=14, justify="center", bg="black", fg="white", insertbackground="white", validate='key', validatecommand=(_vcmd_color, '%P'))
    entry_color.pack(side="left")

    def to_uppercase_nombre_no_digits(*args):
        try:
            v = nombre_var.get()
            filtered = ''.join(ch for ch in v if not ch.isdigit())
            up = filtered.upper()
            if up != v:
                nombre_var.set(up)
        except Exception:
            pass

    def to_uppercase_color_no_digits(*args):
        try:
            v = color_var.get()
            filtered = ''.join(ch for ch in v if not ch.isdigit())
            up = filtered.upper()
            if up != v:
                color_var.set(up)
        except Exception:
            pass

    try:
        nombre_var.trace_add("write", to_uppercase_nombre_no_digits)
    except Exception:
        try:
            nombre_var.trace("w", to_uppercase_nombre_no_digits)
        except Exception:
            pass

    try:
        color_var.trace_add("write", to_uppercase_color_no_digits)
    except Exception:
        try:
            color_var.trace("w", to_uppercase_color_no_digits)
        except Exception:
            pass

    entry_cedula.bind('<Control-b>', lambda event: abrir_tabla_cedulas())
    entry_nombre.bind('<Control-b>', lambda event: abrir_tabla_cedulas())
    entry_color.bind('<Control-b>', lambda event: abrir_tabla_cedulas())

    frmBotones = tk.Frame(frmRegistroInterno, bg="#F6EAAE")
    frmBotones.pack(pady=20)

    modalidad_seleccionada = tk.StringVar(value="Hora")

    def seleccionar_boton(boton):
        for b in botones:
            b.config(highlightbackground="white", bg="white", fg="black")
        boton.config(highlightbackground="red", bg="black", fg="white")
        modalidad_seleccionada.set(boton.cget("text"))

    fila1 = tk.Frame(frmBotones, bg="#F6EAAE")
    fila1.pack()
    btn_hora = tk.Button(fila1, text="Hora", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_estudiante = tk.Button(fila1, text="Estudiante", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_dia = tk.Button(fila1, text="Día", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_24h = tk.Button(fila1, text="24 Horas", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_hora.pack(side="left", padx=3, pady=3)
    btn_estudiante.pack(side="left", padx=3, pady=3)
    btn_dia.pack(side="left", padx=3, pady=3)
    btn_24h.pack(side="left", padx=3, pady=3)

    fila2 = tk.Frame(frmBotones, bg="#F6EAAE")
    fila2.pack()
    btn_semana = tk.Button(fila2, text="Semana", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_quincena = tk.Button(fila2, text="Quincena", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_mes = tk.Button(fila2, text="Mes", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_semana.pack(side="left", padx=3, pady=3)
    btn_quincena.pack(side="left", padx=3, pady=3)
    btn_mes.pack(side="left", padx=3, pady=3)

    botones = [btn_hora, btn_estudiante, btn_dia, btn_24h, btn_semana, btn_quincena, btn_mes]
    for b in botones:
        b.config(command=lambda btn=b: seleccionar_boton(btn))
    seleccionar_boton(btn_hora)

    filaCasco = tk.Frame(frmRegistroInterno, bg="#F6EAAE")
    filaCasco.pack(pady=10)

    lblCasco = tk.Label(filaCasco, fg="black", text="Casco:", font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
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
        width=14,
        justify="center",
        textvariable=casco_var,
        insertbackground="black"
    )
    casco.pack(side='left', ipady=1)

    btnRegistrar = tk.Button(
        frmRegistroInterno,
        text="Registrar",
        font=("Times New Roman", 16, "bold"),
        cursor="hand2",
        bg="white",
        fg="black",
    )
    btnRegistrar.pack(pady=20)

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
        bind_backspace_chain([entry_cedula, entry_nombre, entry_color, casco])
    except Exception:
        pass

    def on_nombre_enter(event=None):
        entry_cedula.focus_set()
        entry_nombre.focus_set()
        entry_nombre.icursor('end')
        return 'break'
    entry_cedula.unbind('<Return>')
    entry_cedula.bind('<Return>', on_nombre_enter)

    def on_nombre_enter(event=None):
        entry_nombre.focus_set()
        combo_tipo.focus_set()
        return 'break'
    entry_nombre.unbind('<Return>')
    entry_nombre.bind('<Return>', on_nombre_enter)

    def on_nombre_enter(event=None):
        combo_tipo.focus_set()
        entry_color.focus_set()
        entry_color.icursor('end')
        return 'break'
    combo_tipo.unbind('<Return>')
    combo_tipo.bind('<Return>', on_nombre_enter)

    def on_nombre_enter(event=None):
        entry_color.focus_set()
        casco.focus_set()
        casco.icursor('end')
        return 'break'
    entry_color.unbind('<Return>')
    entry_color.bind('<Return>', on_nombre_enter)

    def on_cantidad_enter(event=None):
        btnRegistrar.focus_set()
        btnRegistrar.invoke()
        return 'break'
    casco.unbind('<Return>')
    casco.bind('<Return>', on_cantidad_enter)

    def bind_escape_chain(entries):
        for i, ent in enumerate(entries):
            def _handler(event, idx=i, ent_widget=ent):
                try:
                    widget = event.widget
                    if widget is not ent_widget:
                        return
                    try:
                        text = widget.get()
                    except Exception:
                        text = ''
                    if (text is None) or (str(text).strip() == ''):
                        prev_idx = idx - 1
                        if prev_idx >= 0:
                            try:
                                entries[prev_idx].focus_set()
                                try:
                                    entries[prev_idx].icursor('end')
                                except Exception:
                                    pass
                            except Exception:
                                try:
                                    entries[prev_idx].focus_set()
                                except Exception:
                                    pass
                            return 'break'
                except Exception:
                    return
            try:
                ent.bind('<Escape>', _handler)
            except Exception:
                pass

    try:
        bind_escape_chain([entry_cedula, entry_nombre, combo_tipo, entry_color, casco])
    except Exception:
        try:
            bind_escape_chain([entry_cedula, entry_nombre, entry_color, casco])
        except Exception:
            pass

    fechaEntrada = tk.StringVar()
    lblFechaEntrada = tk.Label(frmRegistroInterno, fg="black", text="Fecha y Hora de Entrada: " + fechaEntrada.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblFechaEntrada.pack(pady=5)

    duracionEn24Horas = tk.StringVar()
    duracionEnDias = tk.StringVar()
    duracionEnHoras = tk.StringVar()
    duracionEnMinutos = tk.StringVar()
    duracionEnSegundos = tk.StringVar()

    frmDuracion = tk.Frame(frmRegistroInterno, bg="#F6EAAE")
    frmDuracion.pack(pady=5)

    filaDuracion = tk.Frame(frmDuracion, bg="#F6EAAE")
    filaDuracion.pack()

    lblDuracionEn24Horas = tk.Label(filaDuracion, fg="black", text="24 Horas: " + duracionEn24Horas.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblDuracionEn24Horas.grid(row=0, column=0, padx=10)

    lblDuracionEnDias = tk.Label(filaDuracion, fg="black", text="Días (16 horas): " + duracionEnDias.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblDuracionEnDias.grid(row=0, column=1, padx=10)

    lblDuracionEnHoras = tk.Label(filaDuracion, fg="black", text="Horas: " + duracionEnHoras.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblDuracionEnHoras.grid(row=0, column=2, padx=10)

    lblDuracionEnMinutos = tk.Label(filaDuracion, fg="black", text="Minutos: " + duracionEnMinutos.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblDuracionEnMinutos.grid(row=0, column=3, padx=10)

    lblDuracionEnSegundos = tk.Label(filaDuracion, fg="black", text="Segundos: " + duracionEnSegundos.get(), font=("Times New Roman", 18, "bold"), bg="#F6EAAE")
    lblDuracionEnSegundos.grid(row=0, column=4, padx=10)

    valor = tk.StringVar(value="Valor: ")
    lblValor = tk.Label(frmRegistro, textvariable=valor, font=("Times New Roman", 18, "bold"), bg="white")
    lblValor.pack(pady=5)

    lblFechaEntrada.pack_forget()
    frmDuracion.pack_forget()
    lblValor.pack_forget()

    def askstring_no_cancel(parent, title, prompt):
        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.transient(parent)

        result = {"value": None, "closed": True}

        lbl = tk.Label(dlg, text=prompt, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
        lbl.pack()

        var = tk.StringVar()

        def _valid_no_digits(new_value):
            if new_value is None:
                return True
            if new_value == "":
                return True
            for ch in new_value:
                if ch.isdigit():
                    return False
            return True

        def _force_upper(*args):
            try:
                v = var.get()
                filtered = ''.join(ch for ch in v if not ch.isdigit())
                up = filtered.upper()
                if up != v:
                    var.set(up)
            except Exception:
                pass

        vcmd = dlg.register(_valid_no_digits)
        entry = tk.Entry(dlg, textvariable=var, font=("Times New Roman", 12), width=30, validate='key', validatecommand=(vcmd, '%P'))
        var.trace_add('write', _force_upper)
        entry.pack(padx=10, pady=5)

        def on_ok():
            result["value"] = var.get()
            result["closed"] = False
            dlg.destroy()

        def on_close():
            result["value"] = None
            result["closed"] = True
            dlg.destroy()

        btn = tk.Button(dlg, text="OK", command=on_ok, bg="#F6EAAE", fg="#111111", cursor="hand2")
        btn.pack(pady=10)

        for btnw in [btn]:
            btnw.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
            btnw.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

        dlg.protocol("WM_DELETE_WINDOW", on_close)
        
        try:
            dlg.bind('<Escape>', lambda e: on_close())
        except Exception:
            pass

        entry.bind("<Return>", lambda e: on_ok())
        entry.focus_set()
        dlg.grab_set()
        dlg.wait_window()

        return result["value"]

    def registrar(imprimir_tiquete=False):
        nombre_valor = nombre_var.get().strip()
        cedula_val = cedula_var.get().strip()
        modalidad_valor = modalidad_seleccionada.get()

        if not nombre_valor and not (modalidad_valor in tablas_fijas and skip_name_if_cedula_exists):
            messagebox.showerror("Error", "El campo Nombre es obligatorio.")
            return
        
        if not cedula_val and not (modalidad_valor in tablas_fijas and skip_name_if_cedula_exists):
            messagebox.showerror("Error", "El campo Cédula es obligatorio.")
            return

        tablas_fijas = {
            "Semana": ("semanasBicicleta", 7, "idSemanasBicicleta", "historialSemanasBicicleta"),
            "Quincena": ("quincenasBicicleta", 15, "idQuincenasBicicleta", "historialQuincenasBicicleta"),
            "Mes": ("mensualidadesBicicleta", 30, "idMensualidadesBicicleta", "historialMensualidadesBicicleta")
        }

        skip_name_if_cedula_exists = False
        if modalidad_valor in tablas_fijas and cedula_val:
            try:
                _con = conectar_bd_parqueaderojmj()
                if _con:
                    _cur = _con.cursor()
                    found_row = None
                    try:
                        _cur.execute("SELECT nombreCompleto FROM semanasBicicleta WHERE cedula = ? LIMIT 1", (cedula_val,))
                        found_row = _cur.fetchone()
                        if not found_row:
                            _cur.execute("SELECT nombreCompleto FROM quincenasBicicleta WHERE cedula = ? LIMIT 1", (cedula_val,))
                            found_row = _cur.fetchone()
                        if not found_row:
                            _cur.execute("SELECT nombreCompleto FROM mensualidadesBicicleta WHERE cedula = ? LIMIT 1", (cedula_val,))
                            found_row = _cur.fetchone()
                        if found_row:
                            skip_name_if_cedula_exists = True
                            if not nombre_valor and found_row[0]:
                                nombre_valor = found_row[0]
                                nombre_var.set(nombre_valor)
                    except Exception:
                        pass
                    try:
                        _cur.execute("SELECT nombreCompleto FROM clientes WHERE cedula = ?", (cedula_val,))
                        cliente_row = _cur.fetchone()
                        if not cliente_row:
                            messagebox.showerror("Cliente no encontrado", "El cliente no existe en el sistema, por favor créalo primero.", parent=frmRegistro)
                            return
                    except Exception:
                        pass
                    finally:
                        try:
                            _cur.close()
                        except Exception:
                            pass
            except Exception:
                pass
        
        hora_actual = dt.datetime.now()


        if modalidad_valor in ["Hora", "Estudiante", "Día", "24 Horas"]:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                fecha_entrada = hora_actual.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
                tipo = tipo_var.get().strip() if tipo_var else ""
                color = color_var.get().strip() if color_var else ""
                casco_val = casco_var.get().strip() if casco_var else ""
                cursor.execute(
                    "INSERT INTO cedulas (cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, casco, fechaHoraEntrada) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        cedula_val if cedula_val else "",
                        nombre_valor,
                        tipo if tipo else "",
                        color if color else "",
                        modalidad_valor,
                        casco_val if casco_val else "",
                        fecha_entrada
                    )
                )
                conexion.commit()

                try:
                    actualizarConteoModalidadesDelDia()
                except Exception:
                    pass
                if imprimir_tiquete:
                    try:
                        imprimir_recibo_entrada_bici(cedula_val, modalidad_valor, nombre_valor, fecha_entrada, usuario_actual, casco_val, tipo, color)
                    except Exception:
                        pass
            except Exception as e:
                conexion.rollback()
                messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                return
            finally:
                try:
                    conexion.close()
                except Exception:
                    pass
            try:
                actualizarConteoModalidadesDelDia()
            except Exception:
                pass
            limpiar_pantalla()
            return
    

        if modalidad_valor in tablas_fijas:
            tabla, duracion_dias, id_col, tabla_hist = tablas_fijas[modalidad_valor]
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                try:
                    cursor.execute(f"SELECT {id_col}, cedula, caracteristica, entrada, salida FROM {tabla} WHERE cedula = ?", (cedula_val,))
                    existentes = cursor.fetchall()
                except Exception:
                    existentes = []

                if existentes:
                    opciones = []
                    for r in existentes:
                        rid, rcedula, rcar, renta, rsal = r
                        opciones.append((rid, rcar or ""))

                    ventana_choice = tk.Toplevel()
                    ventana_choice.title("Registro(s) encontrado(s)")
                    ventana_choice.resizable(False, False)
                    ventana_choice.grab_set()
                    ventana_choice.focus_set()

                    texto = f"Se encontraron {len(opciones)} registro(s) para este cliente:\nCédula: {cedula_val}\n\nCaracterísticas disponibles:\n"
                    texto += "\n".join([f"- {opt[1]}" for opt in opciones])
                    lbl = tk.Label(ventana_choice, text=texto, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
                    lbl.pack()

                    decision = {"accion": None, "seleccion": None}

                    def accion_agregar():
                        decision["accion"] = "agregar"
                        ventana_choice.destroy()

                    def accion_omitir():
                        decision["accion"] = "omitir"
                        ventana_choice.destroy()

                    frm_btns = tk.Frame(ventana_choice, pady=8)
                    frm_btns.pack()
                    btn_add = tk.Button(frm_btns, text="Agregar", command=accion_agregar, bg="#F6EAAE", fg="#111111", cursor="hand2")
                    btn_skip = tk.Button(frm_btns, text="Continuar", command=accion_omitir, bg="#F6EAAE", fg="#111111", cursor="hand2")
                    btn_add.grid(row=0, column=0, padx=8)
                    btn_skip.grid(row=0, column=1, padx=8)

                    for b in [btn_add, btn_skip]:
                        b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                        b.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

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

                    if decision["accion"] == "omitir":
                        ventana_select = tk.Toplevel()
                        ventana_select.title("Seleccionar registro")
                        ventana_select.resizable(False, False)
                        ventana_select.grab_set()
                        ventana_select.focus_set()

                        def _on_select_escape(event=None):
                            try:
                                decision["accion"] = None
                                decision["seleccion"] = None
                            except Exception:
                                pass
                            try:
                                ventana_select.destroy()
                            except Exception:
                                pass

                        ventana_select.bind('<Escape>', _on_select_escape)
                        ventana_select.protocol('WM_DELETE_WINDOW', _on_select_escape)

                        lbl_sel = tk.Label(ventana_select, text="Seleccione la característica del registro a modificar:", font=("Times New Roman", 11), padx=10, pady=8)
                        lbl_sel.pack()

                        try:
                            from tkinter import ttk as _ttk
                        except Exception:
                            _ttk = ttk
                        lista_car = [r[2] or "" for r in existentes]
                        sel_char_var = tk.StringVar()
                        combo_sel = _ttk.Combobox(ventana_select, values=lista_car, textvariable=sel_char_var, state='readonly', width=40)
                        if lista_car:
                            try:
                                combo_sel.current(0)
                            except Exception:
                                pass
                        combo_sel.pack(padx=10, pady=(0, 8))

                        def usar_seleccion():
                            decision["accion"] = "usar"
                            decision["seleccion"] = combo_sel.get()
                            ventana_select.destroy()

                        try:
                            ventana_select.bind('<Return>', lambda e: usar_seleccion())
                            combo_sel.bind('<Return>', lambda e: usar_seleccion())
                        except Exception:
                            pass

                        frm_sel_btns = tk.Frame(ventana_select, pady=8)
                        frm_sel_btns.pack()
                        btn_use_sel = tk.Button(frm_sel_btns, text="Usar seleccionado", command=usar_seleccion, bg="#F6EAAE", fg="#111111", cursor="hand2")
                        btn_use_sel.grid(row=0, column=0, padx=8)
                        for b in [btn_use_sel]:
                            b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                            b.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

                        ventana_select.transient()
                        ventana_select.wait_window()
                    if decision["accion"] is None:
                        return

                    if decision["accion"] == "agregar":
                        caracteristica_nueva = askstring_no_cancel(frmRegistro, "Característica", "Ingrese la característica de la bicicleta:")
                        if not caracteristica_nueva:
                            return

                        entrada_nueva = hora_actual.replace(microsecond=0)
                        if modalidad_valor == "Mes":
                            salida_nueva = add_months(entrada_nueva, months=1) - dt.timedelta(days=1)
                        else:
                            salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                        try:
                            cedula_base = existentes[0][1] if existentes and existentes[0][1] else (cedula_val if cedula_val else "")
                            cursor.execute(
                                f"INSERT INTO {tabla} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula_base, nombre_valor, caracteristica_nueva, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            cursor.execute(
                                f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula_base, nombre_valor, caracteristica_nueva, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            try:
                                cursor.execute(
                                    "INSERT INTO cedulas (cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, casco, fechaHoraEntrada) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (
                                        cedula_base if cedula_base else "",
                                        nombre_valor,
                                        tipo_var.get().strip() if tipo_var else "",
                                        color_var.get().strip() if color_var else "",
                                        modalidad_valor,
                                        casco_var.get().strip() if casco_var else "",
                                        entrada_nueva.strftime("%Y-%m-%d %H:%M:%S")
                                    )
                                )
                            except Exception:
                                pass
                            conexion.commit()
                        except Exception as e:
                            conexion.rollback()
                            messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                            return
                        try:
                            actualizarConteoModalidadesDelDia()
                        except Exception:
                            pass
                        try:
                            actualizarConteoFijosBicicletas()
                        except Exception:
                            pass
                        limpiar_pantalla()
                        return

                    if decision["accion"] == "usar":
                        sel_text = decision.get("seleccion")
                        sel_id = None
                        for rid, txt in opciones:
                            if txt == sel_text:
                                sel_id = rid
                                break
                        sel_row = None
                        for r in existentes:
                            if r[0] == sel_id:
                                sel_row = r
                                break
                        if sel_row:
                            id_exist, cedula_exist, caracteristica_exist, entrada_prev, salida_prev = sel_row

                    entrada_prev_dt = None
                    salida_prev_dt = None
                    try:
                        if entrada_prev:
                            try:
                                entrada_prev_dt = dt.datetime.strptime(entrada_prev, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                entrada_prev_dt = dt.datetime.strptime(entrada_prev, "%Y-%m-%d")
                        if salida_prev:
                            try:
                                salida_prev_dt = dt.datetime.strptime(salida_prev, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                salida_prev_dt = dt.datetime.strptime(salida_prev, "%Y-%m-%d")
                    except Exception:
                        pass

                    ventana_confirm = tk.Toplevel()
                    ventana_confirm.title("Confirmar registro")
                    ventana_confirm.resizable(False, False)
                    ventana_confirm.grab_set()
                    ventana_confirm.focus_set()

                    def _on_confirm_escape(event=None):
                        try:
                            opcion["valor"] = None
                        except Exception:
                            pass
                        try:
                            ventana_confirm.destroy()
                        except Exception:
                            pass

                    ventana_confirm.bind('<Escape>', _on_confirm_escape)
                    ventana_confirm.protocol('WM_DELETE_WINDOW', _on_confirm_escape)

                    ahora = dt.datetime.now().replace(microsecond=0)
                    if 'salida_prev_dt' in locals() and salida_prev_dt:
                        entrada_actual = salida_prev_dt + dt.timedelta(days=1)
                        if modalidad_valor == "Mes":
                            salida_actual = add_months(entrada_actual, months=1) - dt.timedelta(days=1)
                        else:
                            salida_actual = (entrada_actual + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)
                    else:
                        entrada_actual = ahora
                        if modalidad_valor == "Mes":
                            salida_actual = (entrada_actual + dt.timedelta(days=duracion_dias))
                        else:
                            salida_actual = (entrada_actual + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                    txt = "Se procederá con el registro existente.\n\n"
                    txt += f"Último registro:\n  Entrada: {entrada_prev or ''}\n  Salida: {salida_prev or ''}\n\n"
                    txt += f"Propuesta de nueva entrada:\n  Entrada: {entrada_actual.strftime('%Y-%m-%d %H:%M:%S')}\n  Salida: {salida_actual.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    txt += "¿Desea continuar o modificar?"

                    lbl_info = tk.Label(ventana_confirm, text=txt, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
                    lbl_info.pack()

                    opcion = {"valor": None}
                    opcion["confirmado"] = False

                    def optar_continuar():
                        opcion["valor"] = "continuar"
                        ventana_confirm.destroy()

                    def optar_modificar():
                        opcion["valor"] = "modificar"
                        ventana_confirm.destroy()

                    frm_bot = tk.Frame(ventana_confirm, pady=10)
                    frm_bot.pack()
                    btn_cont = tk.Button(frm_bot, text="Continuar", command=optar_continuar, bg="#F6EAAE", fg="#111111", cursor="hand2")
                    btn_mod = tk.Button(frm_bot, text="Modificar", command=optar_modificar, bg="#F6EAAE", fg="#111111", cursor="hand2")
                    btn_cont.grid(row=0, column=0, padx=10)
                    btn_mod.grid(row=0, column=1, padx=10)

                    for b in [btn_cont, btn_mod]:
                        b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                        b.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

                    ventana_confirm.transient()
                    ventana_confirm.wait_window()

                    if opcion["valor"] is None:
                        return

                    if opcion["valor"] == "modificar":
                        ventana_editar = tk.Toplevel()
                        ventana_editar.title("Modificar Fechas")
                        ventana_editar.resizable(False, False)
                        ventana_editar.grab_set()
                        ventana_editar.focus_set()

                        def _on_editar_escape(event=None):
                            try:
                                ventana_editar.destroy()
                            except Exception:
                                pass

                        ventana_editar.bind('<Escape>', _on_editar_escape)
                        ventana_editar.protocol('WM_DELETE_WINDOW', _on_editar_escape)

                        lbl_info2 = tk.Label(ventana_editar, text="Modifique las fechas si es necesario:", font=("Times New Roman", 12), padx=10, pady=10)
                        lbl_info2.pack()

                        frm_fechas = tk.Frame(ventana_editar)
                        frm_fechas.pack(padx=10, pady=5)

                        tk.Label(frm_fechas, text="Fecha de Entrada:", font=("Times New Roman", 11)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
                        tk.Label(frm_fechas, text="Fecha de Salida:", font=("Times New Roman", 11)).grid(row=1, column=0, sticky="e", padx=5, pady=5)

                        entrada_var = tk.StringVar(value=entrada_actual.strftime('%Y-%m-%d %H:%M:%S'))
                        salida_var = tk.StringVar(value=salida_actual.strftime('%Y-%m-%d %H:%M:%S'))

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
                            opcion["entrada"] = entrada_dt
                            opcion["salida"] = salida_dt
                            ventana_editar.destroy()

                        btn_ok = tk.Button(ventana_editar, text="OK", command=on_ok_editar, bg="#F6EAAE", fg="#111111", cursor="hand2")
                        btn_ok.pack(pady=10)
                        btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                        btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

                        try:
                            ventana_editar.bind('<Return>', lambda e: on_ok_editar())
                        except Exception:
                            pass

                        ventana_editar.transient()
                        ventana_editar.wait_window()

                        if "entrada" not in opcion or "salida" not in opcion:
                            return
                        entrada_para_guardar = opcion["entrada"]
                        salida_para_guardar = opcion["salida"]
                    else:
                        entrada_para_guardar = entrada_actual
                        salida_para_guardar = salida_actual

                    try:
                        cursor.execute(
                            f"UPDATE {tabla} SET entrada = ?, salida = ? WHERE {id_col} = ?",
                            (entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), salida_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), id_exist)
                        )

                        # Record history for this fixed client
                        try:
                            cursor.execute(
                                f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (
                                    cedula_exist if cedula_exist else (cedula_val if cedula_val else ""),
                                    nombre_valor,
                                    caracteristica_exist if caracteristica_exist else "",
                                    entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"),
                                    salida_para_guardar.strftime("%Y-%m-%d %H:%M:%S")
                                )
                            )
                        except Exception:
                            pass

                        # Also insert into active cedulas table so client is registered as present
                        try:
                            cursor.execute(
                                "INSERT INTO cedulas (cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, casco, fechaHoraEntrada) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (
                                    cedula_exist if cedula_exist else (cedula_val if cedula_val else ""),
                                    nombre_valor,
                                    tipo_var.get().strip() if tipo_var else "",
                                    color_var.get().strip() if color_var else "",
                                    modalidad_valor,
                                    casco_var.get().strip() if casco_var else "",
                                    entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S")
                                )
                            )
                        except Exception:
                            pass

                        conexion.commit()
                        try:
                            actualizarConteoFijosBicicletas()
                            actualizarConteoModalidadesDelDia()
                        except Exception as e:
                            messagebox.showerror("Error", f"Error actualizando conteos: {e}")

                        if imprimir_tiquete:
                            try:
                                ced_for_print = cedula_exist if cedula_exist else (cedula_val if cedula_val else "")
                                imprimir_recibo_entrada_bici(ced_for_print, modalidad_valor, nombre_valor, entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), usuario_actual, casco_var.get().strip() if casco_var else "", tipo_var.get().strip() if tipo_var else "", color_var.get().strip() if color_var else "")
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                print("Error al imprimir recibo (registrar):", e)
                                print(tb)
                                try:
                                    messagebox.showerror("Error de impresión", f"No se pudo imprimir el recibo: {e}\nRevise la consola para más detalles.")
                                except Exception:
                                    pass
                    except Exception as e:
                        conexion.rollback()
                        messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")
                        return
                    except Exception as e:
                        conexion.rollback()
                        messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")
                        return
                    limpiar_pantalla()
                    return

                caracteristica = askstring_no_cancel(frmRegistro, "Característica", "Ingrese la característica de la bicicleta:")
                if not caracteristica:
                    return

                entrada_nueva = hora_actual.replace(microsecond=0)
                if modalidad_valor == "Mes":
                    salida_nueva = add_months(entrada_nueva, months=1) - dt.timedelta(days=1)
                else:
                    salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                try:
                    cursor.execute(
                        f"INSERT INTO {tabla} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                        (cedula_val if cedula_val else "", nombre_valor, caracteristica, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    cursor.execute(
                        f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                        (cedula_val if cedula_val else "", nombre_valor, caracteristica, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    try:
                        cursor.execute(
                            "INSERT INTO cedulas (cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, casco, fechaHoraEntrada) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                cedula_val if cedula_val else "",
                                nombre_valor,
                                tipo_var.get().strip() if tipo_var else "",
                                color_var.get().strip() if color_var else "",
                                modalidad_valor,
                                casco_var.get().strip() if casco_var else "",
                                entrada_nueva.strftime("%Y-%m-%d %H:%M:%S")
                            )
                        )
                    except Exception:
                        pass
                    conexion.commit()
                    try:
                        if imprimir_tiquete:
                            try:
                                imprimir_recibo_entrada_bici(cedula_val if cedula_val else "", modalidad_valor, nombre_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), usuario_actual)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        actualizarConteoFijosBicicletas()
                    except Exception:
                        pass
                except Exception as e:
                    conexion.rollback()
                    messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                    return
                finally:
                    try:
                        conexion.close()
                    except Exception:
                        pass
                try:
                    actualizarConteoModalidadesDelDia()
                except Exception:
                    pass
                limpiar_pantalla()
                return
            except Exception as e:
                try:
                    conexion.rollback()
                except Exception:
                    pass
                messagebox.showerror("Error", f"Error en el registro: {e}")
                return
            finally:
                try:
                    conexion.close()
                except Exception:
                    pass

    def confirmar_registro():
        if workflow_state["exit_in_progress"]:
            return
        modalidad_valor = modalidad_seleccionada.get()
        nombre_valor = nombre_var.get().strip()
        cedula_val = cedula_var.get().strip()
        if not nombre_valor:
            messagebox.showerror("Error", "El campo Nombre es obligatorio.")
            return
        
        if not cedula_val:
            messagebox.showerror("Error", "El campo Cédula es obligatorio.")
            return
        
        if modalidad_valor in ["Mes", "Quincena", "Semana"]:
            registrar(imprimir_tiquete=False)
            return

        if modalidad_valor in ["Hora", "Estudiante", "Día", "24 Horas"]:
            mini = tk.Toplevel()
            mini.title("Opciones de Registro")
            mini.resizable(False, False)
            mini.grab_set()

            tk.Label(mini, text="¿Desea imprimir recibo de entrada?", font=("Times New Roman", 12), padx=10, pady=10).pack()

            def do_imprimir():
                mini.destroy()
                registrar(imprimir_tiquete=True)

            def do_continuar():
                mini.destroy()
                registrar(imprimir_tiquete=False)

            frm = tk.Frame(mini, pady=10)
            frm.pack()
            btn_imp = tk.Button(frm, text="Imprimir recibo", command=do_imprimir, bg="#F6EAAE", fg="#111111", cursor="hand2")
            btn_cont = tk.Button(frm, text="Continuar", command=do_continuar, bg="#F6EAAE", fg="#111111", cursor="hand2")
            btn_imp.grid(row=0, column=0, padx=8)
            btn_cont.grid(row=0, column=1, padx=8)

            for b in [btn_imp, btn_cont]:
                b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                b.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

            def on_modal_key(event):
                if event.keysym == 'Return':
                    mini.unbind('<Return>')
                    mini.unbind('<Escape>')
                    btn_imp.invoke()
                elif event.keysym == 'Escape':
                    mini.unbind('<Return>')
                    mini.unbind('<Escape>')
                    btn_cont.invoke()
            mini.bind('<Return>', on_modal_key)
            mini.bind('<Escape>', on_modal_key)
            btn_imp.focus_set()

    btnRegistrar.config(command=confirmar_registro)

    displayed_cedula = ""

    def limpiar_pantalla():
        nonlocal displayed_cedula
        cedula_var.set("")
        nombre_var.set("")
        tipo_var.set("")
        color_var.set("")
        casco_var.set("")
        seleccionar_boton(btn_hora)
        entry_cedula.focus_set()
        frmDuracion.pack_forget()
        lblFechaEntrada.pack_forget()
        lblValor.pack_forget()
        displayed_cedula = ""
        try:
            btnRegistrar.config(text="Registrar", command=confirmar_registro)
        except Exception:
            pass

    def clear_display_fields():
        nonlocal displayed_cedula
        current_ced = cedula_var.get().strip()
        nombre_var.set("")
        tipo_var.set("")
        color_var.set("")
        casco_var.set("")
        frmDuracion.pack_forget()
        lblFechaEntrada.pack_forget()
        lblValor.pack_forget()
        seleccionar_boton(btn_hora)
        displayed_cedula = str(current_ced)
        try:
            btnRegistrar.config(text="Registrar", command=confirmar_registro)
        except Exception:
            pass

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
    lblClientesDiarios.pack(pady=5)

    horas = 0
    estudiantes = 0
    dias = 0
    horas_24 = 0
    totalDiarios = horas + estudiantes + dias + horas_24

    lblHoras = tk.Label(frameDiaInterno, text=f"Horas: {horas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblHoras.pack(pady=2)
    lblEstudiantes = tk.Label(frameDiaInterno, text=f"Estudiantes: {estudiantes}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblEstudiantes.pack(pady=2)
    lblDias = tk.Label(frameDiaInterno, text=f"Días: {dias}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblDias.pack(pady=2)
    lbl24h = tk.Label(frameDiaInterno, text=f"24 Horas: {horas_24}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lbl24h.pack(pady=2)
    lblTotalDiarios = tk.Label(frameDiaInterno, text=f"Total: {totalDiarios}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white")
    lblTotalDiarios.pack(pady=2)

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
            cursor.execute("SELECT modalidad, COUNT(*) FROM cedulas GROUP BY modalidad")
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
            lblTotalDiarios.config(text=f"Total: {totalDiarios}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar el conteo de modalidades: {e}")

        finally:
            if cursor:
                cursor.close()
            if conexion:
                conexion.close()
    actualizarConteoModalidadesDelDia()

    def actualizarConteoFijosBicicletas():
        conexion = None
        try:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("SELECT COUNT(*) FROM semanasBicicleta")
            cnt_semanas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM quincenasBicicleta")
            cnt_quincenas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mensualidadesBicicleta")
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
            try:
                if conexion:
                    conexion.close()
            except Exception:
                pass

    try:
        actualizarConteoModalidadesDelDia()
    except Exception:
        pass

    frmFunciones = tk.Frame(parent, border=1, relief="solid", bg="black")
    frmFunciones.place(x=0, y=0, relx=0.65, rely=0.5, relwidth=0.35, relheight=0.5)
    frmFunciones.pack_propagate(False)

    frameFuncionesInterno = tk.Frame(frmFunciones, bg="black")
    frameFuncionesInterno.pack(expand=True)

    btnConsultarCedulas = tk.Button(frameFuncionesInterno, text="Consultar Cédulas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnHistorialDeCedulas = tk.Button(frameFuncionesInterno, text="Historial de Cédulas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnConsultarFijos = tk.Button(frameFuncionesInterno, text="Consultar Clientes", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnTarifas = tk.Button(frameFuncionesInterno, text="Tarifas", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btnArqueo = tk.Button(frameFuncionesInterno, text="Arqueo de Caja", width=25, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")

    btnConsultarCedulas.pack(pady=10)
    btnHistorialDeCedulas.pack(pady=10)
    btnConsultarFijos.pack(pady=10)
    btnTarifas.pack(pady=10)
    btnArqueo.pack(pady=10)

    for btn in [
        btnRegistrar,
        btnLimpiarPantalla,
        btnConsultarCedulas,
        btnHistorialDeCedulas,
        btnConsultarFijos,
        btnTarifas,
        btnArqueo,
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="#1B1B1B", fg="white"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="white", fg="black"))

    def registrar_salida(nombre_valor, valor_cobrado):
        workflow_state["exit_in_progress"] = True
        def on_pago_close(salida_exitosa=False):
            workflow_state["exit_in_progress"] = False
            if salida_exitosa:
                limpiar_pantalla()
            else:
                verificar_cedula()
        mostrar_ventana_pago(nombre_valor, valor_cobrado, on_pago_close)
        btnRegistrar.config(command=confirmar_registro)
        actualizarConteoModalidadesDelDia()
        limpiar_pantalla()

    def mostrar_ventana_pago(cedula_valor, valor_cobrado, continuar_callback):
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
            img = Image.open("fondoBicicletas.png").resize((ancho_ventana, alto_ventana))
            fondo_img = ImageTk.PhotoImage(img)
            lbl_fondo = tk.Label(ventana_pago, image=fondo_img)
            lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            ventana_pago.configure(bg="black")

        frmPago = tk.Frame(ventana_pago, bg="#111111", bd=0, relief="flat")
        frmPago.place(relx=0.5, rely=0.5, anchor="center", width=380, height=270)

        lbl_valor = tk.Label(frmPago, text=f"{valor_cobrado}", font=("Times New Roman", 16, "bold"), bg="#111111", fg="#F6EAAE")
        lbl_valor.pack(pady=(50, 10))

        medio_pago = tk.StringVar(value="Efectivo")

        frame_medios_pago = tk.Frame(frmPago, bg="#111111")
        frame_medios_pago.pack(pady=10)

        rb_efectivo = tk.Radiobutton(frame_medios_pago, text="Efectivo", variable=medio_pago, value="Efectivo", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE", activebackground="#111111", activeforeground="#F6EAAE", selectcolor="#111111")
        rb_nequi = tk.Radiobutton(frame_medios_pago, text="Nequi", variable=medio_pago, value="Nequi", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE", activebackground="#111111", activeforeground="#F6EAAE", selectcolor="#111111")
        rb_bancolombia = tk.Radiobutton(frame_medios_pago, text="Bancolombia", variable=medio_pago, value="Bancolombia", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE", activebackground="#111111", activeforeground="#F6EAAE", selectcolor="#111111")

        rb_efectivo.grid(row=0, column=0, padx=10)
        rb_nequi.grid(row=0, column=1, padx=10)
        rb_bancolombia.grid(row=0, column=2, padx=10)

        def procesar_salida(imprimir_factura=False):
            conexion = None
            cursor = None
            salida_exitosa = False
            try:
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return

                cursor = conexion.cursor()
                fecha_salida = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    cursor.execute("SELECT nombreCompleto, modalidad, fechaHoraEntrada FROM cedulas WHERE cedula = ?", (cedula_valor,))
                    row = cursor.fetchone()
                except Exception:
                    row = None

                nombre = row[0] if row and len(row) > 0 and row[0] is not None else ""
                modalidad_pago = row[1] if row and len(row) > 1 and row[1] is not None else ""
                fecha_entrada = row[2] if row and len(row) > 2 and row[2] is not None else ""

                if not row:
                    try:
                        cursor.execute("SELECT nombreCompleto, modalidad, fechaEntrada FROM historialDeCedulas WHERE cedula = ? ORDER BY datetime(fechaEntrada) DESC LIMIT 1", (cedula_valor,))
                        row2 = cursor.fetchone()
                        if row2:
                            if row2[0] is not None:
                                nombre = row2[0]
                            if len(row2) > 1 and row2[1] is not None:
                                modalidad_pago = row2[1]
                            if len(row2) > 2 and row2[2] is not None:
                                fecha_entrada = row2[2]
                    except Exception:
                        pass

                valor_raw = str(valor_cobrado)
                try:
                    for p in ("Valor: $", "Valor: ", "$", "Valor:"):
                        if p in valor_raw:
                            valor_raw = valor_raw.replace(p, "")
                    valor_raw = valor_raw.replace(',', '')
                    valor_num = float(valor_raw)
                except Exception as e:
                    messagebox.showerror("Error", f"Valor inválido para pago: {valor_cobrado}\n\nDetalle: {e}", parent=ventana_pago)
                    return

                try:
                    cursor.execute(
                        "INSERT INTO pagosBicicletas (cedula, nombreCompleto, modalidad, valor, medio_pago, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                        (cedula_valor, nombre, modalidad_pago, valor_num, medio_pago.get(), fecha_salida)
                    )
                except Exception as e:
                    messagebox.showerror("Error", f"Error al insertar en pagos: {e}", parent=ventana_pago)
                    if conexion:
                        try:
                            conexion.rollback()
                        except Exception:
                            pass
                    return

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
                        try:
                            imprimir_factura_salida_bici(
                                cedula=cedula_valor,
                                modalidad=modalidad_pago,
                                nombre=nombre,
                                fecha_entrada=fecha_entrada,
                                fecha_salida=fecha_salida,
                                duracion=duracion_str,
                                total=total_str,
                                usuario=usuario_actual
                            )
                        except Exception as e:
                            print(f"Error al imprimir factura diaria bici: {e}")
                    else:
                        try:
                            conexion_f = conectar_bd_parqueaderojmj()
                            if conexion_f is not None:
                                cur_f = conexion_f.cursor()
                                for tabla, modalidad_nombre in [("mensualidadesBicicleta", "Mes"), ("quincenasBicicleta", "Quincena"), ("semanasBicicleta", "Semana")]:
                                    try:
                                        cur_f.execute(f"SELECT cedula, nombreCompleto, caracteristica, entrada, salida FROM {tabla} WHERE cedula = ?", (cedula_valor,))
                                        fila = cur_f.fetchone()
                                    except Exception:
                                        fila = None
                                    if fila:
                                        cedula_f = fila[0]
                                        nombre_f = fila[1] if len(fila) > 1 and fila[1] is not None else nombre
                                        caracteristica_f = fila[2] if len(fila) > 2 and fila[2] is not None else ''
                                        entrada_f = fila[3] if len(fila) > 3 and fila[3] is not None else fecha_entrada
                                        salida_f = fila[4] if len(fila) > 4 and fila[4] is not None else fecha_salida
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
                                        try:
                                            imprimir_factura_salida_fijo_bici(
                                                modalidad=modalidad_nombre,
                                                cedula=cedula_f,
                                                nombre=nombre_f,
                                                entrada=entrada_f,
                                                salida=salida_f,
                                                total=total_f,
                                                usuario=usuario_actual,
                                                caracteristica=caracteristica_f
                                            )
                                        except Exception as e:
                                            print(f"Error al imprimir factura fijo bici: {e}")
                                        break
                        except Exception:
                            pass

                try:
                    try:
                        cursor.execute("SELECT 1 FROM historialDeCedulas WHERE cedula = ? AND fechaSalida IS NULL LIMIT 1", (cedula_valor,))
                        exists_open = cursor.fetchone()
                    except Exception:
                        exists_open = None

                    if exists_open:
                        try:
                            cursor.execute(
                                "UPDATE historialDeCedulas SET fechaSalida = ? WHERE cedula = ? AND valor = ? AND fechaSalida IS NULL",
                                (fecha_salida, cedula_valor)
                            )
                        except Exception:
                            pass
                    else:
                        try:
                            query_insert_hist = (
                                "INSERT INTO historialDeCedulas (cedula, nombreCompleto, modalidad, fechaEntrada, fechaSalida)"
                                " VALUES (?, ?, ?, ?, ?)"
                            )
                            cursor.execute(query_insert_hist, (
                                cedula_valor if cedula_valor else "",
                                nombre if nombre else "",
                                modalidad_pago if modalidad_pago else "",
                                fecha_entrada if fecha_entrada else "",
                                fecha_salida
                            ))
                        except Exception:
                            pass
                except Exception:
                    pass

                try:
                    if modalidad_pago in ["Semana", "Quincena", "Mes"]:
                        try:
                            for tabla, modalidad_nombre, tabla_hist in [("mensualidadesBicicleta", "Mes", "historialMensualidadesBicicleta"), ("quincenasBicicleta", "Quincena", "historialQuincenasBicicleta"), ("semanasBicicleta", "Semana", "historialSemanasBicicleta")]:
                                try:
                                    cur2 = conexion.cursor()
                                    cur2.execute(f"SELECT cedula, nombreCompleto, caracteristica, entrada, salida FROM {tabla} WHERE cedula = ?", (cedula_valor,))
                                    fila = cur2.fetchone()
                                    if fila:
                                        cedula_f = fila[0]
                                        nombre_f = fila[1] if len(fila) > 1 and fila[1] is not None else nombre
                                        caracteristica_f = fila[2] if len(fila) > 2 and fila[2] is not None else ''
                                        entrada_f = fila[3] if len(fila) > 3 and fila[3] is not None else fecha_entrada
                                        salida_f = fecha_salida
                                        try:
                                            cur2.execute(
                                                f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                                (cedula_f if cedula_f else "", nombre_f if nombre_f else "", caracteristica_f, entrada_f, salida_f)
                                            )
                                            conexion.commit()
                                        except Exception:
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

                try:
                    query_eliminar_placa = "DELETE FROM cedulas WHERE cedula = ?"
                    cursor.execute(query_eliminar_placa, (cedula_valor,))
                except Exception:
                    pass
                salida_exitosa = True
                conexion.commit()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la salida: {e}")

            finally:
                if cursor:
                    cursor.close()
                if conexion:
                    conexion.close()

            ventana_pago.destroy()
            continuar_callback(salida_exitosa)

            actualizarConteoModalidadesDelDia()


        frame_botones = tk.Frame(frmPago, bg="#111111")
        frame_botones.pack(pady=20)

        btn_imprimir = tk.Button(frame_botones, text="Imprimir factura", command=lambda: procesar_salida(True), font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2")
        btn_imprimir.grid(row=0, column=0, padx=10)

        btn_continuar = tk.Button(frame_botones, text="Continuar", command=lambda: procesar_salida(False), font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2")
        btn_continuar.grid(row=0, column=1, padx=10)

        for b in [btn_imprimir, btn_continuar]:
            b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
            b.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

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

    def verificar_cedula(event=None):
        ced = cedula_var.get().strip()
        nonlocal displayed_cedula
        prev = str(displayed_cedula) if displayed_cedula is not None else ""
        if prev and ced and len(ced) < len(prev):
            clear_display_fields()
            return
        if prev and not ced:
            limpiar_pantalla()
            return
        if not ced:
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
            resultado = None
            if ced:
                 cursor.execute("SELECT modalidad, casco, fechaHoraEntrada, nombreCompleto, tipoBicicleta, colorBicicleta, cedula FROM cedulas WHERE cedula = ?", (ced,))
                 resultado = cursor.fetchone()

            if resultado:
                modalidad_valor = resultado[0]
                casco_valor = resultado[1] if len(resultado) > 1 else ""
                hora_entrada = resultado[2] if len(resultado) > 2 else None
                nombre_encontrado = resultado[3] if len(resultado) > 3 else ""
                tipo_encontrado = resultado[4] if len(resultado) > 4 else ""
                color_encontrado = resultado[5] if len(resultado) > 5 else ""
                cedula_encontrada = resultado[6] if len(resultado) > 6 else ced
                if hora_entrada:
                    try:
                        hora_entrada_dt = dt.datetime.strptime(hora_entrada, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        try:
                            hora_entrada_dt = dt.datetime.strptime(hora_entrada, "%Y-%m-%d")
                        except Exception:
                            hora_entrada_dt = None
                else:
                    hora_entrada_dt = None

                if hora_entrada_dt:
                    hora_actual = dt.datetime.now()
                    duracion = hora_actual - hora_entrada_dt
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
                        lblDuracionEn24Horas.grid()
                        lblDuracionEnDias.grid_remove()
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

                    cursor.execute("SELECT valor FROM tarifasbicicletas WHERE tarifa = ?", (modalidad_valor,))
                    tarifa = cursor.fetchone()
                    total_a_cobrar = ""
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
                            cursor.execute("SELECT duracion FROM tarifasbicicletas WHERE tarifa = ?", (modalidad_valor,))
                            duracion_base = cursor.fetchone()
                            if duracion_base:
                                duracion_base = int(str(duracion_base[0]).split()[0])
                                ciclos_completos = total_horas // duracion_base
                                total_a_cobrar = tarifa_valor * max(1, ciclos_completos + 1)
                            else:
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
                            try:
                                duracion_map = {"Semana": 7, "Quincena": 15, "Mes": 30}
                                dias_transcurridos = max(1, math.ceil((hora_actual - hora_entrada_dt).total_seconds() / 86400))
                                duracion_dias = duracion_map.get(modalidad_valor, 30)
                                ciclos = math.ceil(dias_transcurridos / duracion_dias)
                                total_a_cobrar = tarifa_valor * ciclos
                            except Exception:
                                total_a_cobrar = tarifa_valor
                        else:
                            total_a_cobrar = tarifa_valor

                        valor.set(f"Valor: {total_a_cobrar}")
                    else:
                        valor.set("Valor: Tarifa no encontrada")

                    fechaEntrada.set(hora_entrada_dt.strftime("%d/%m/%Y %H:%M:%S"))
                    frmDuracion.pack(pady=5)
                    lblFechaEntrada.config(text="Fecha y Hora de Entrada: " + fechaEntrada.get())
                    lblFechaEntrada.pack(pady=5)
                    lblValor.pack(pady=5)

                    for btn in [btn_hora, btn_estudiante, btn_dia, btn_24h, btn_semana, btn_quincena, btn_mes]:
                        if btn.cget("text") == modalidad_valor:
                            seleccionar_boton(btn)

                    try:
                        nombre_var.set(nombre_encontrado if nombre_encontrado else "")
                    except Exception:
                        pass
                    try:
                        casco_var.set(casco_valor if casco_valor else "")
                    except Exception:
                        pass
                    try:
                        tipo_var.set(tipo_encontrado if tipo_encontrado else "")
                    except Exception:
                        pass
                    try:
                        color_var.set(color_encontrado if color_encontrado else "")
                    except Exception:
                        pass

                    displayed_cedula = str(cedula_encontrada if cedula_encontrada else ced)
                    btnRegistrar.config(text="Facturar", command=lambda: registrar_salida(displayed_cedula, valor.get()))
                else:
                    btnRegistrar.config(text="Registrar", command=confirmar_registro)
                    frmDuracion.pack_forget()
                    lblValor.pack_forget()
                    casco_var.set("")
                    lblFechaEntrada.pack_forget()
                    seleccionar_boton(btn_hora)
            else:
                btnRegistrar.config(text="Registrar", command=confirmar_registro)
                frmDuracion.pack_forget()
                lblValor.pack_forget()
                casco_var.set("")
                lblFechaEntrada.pack_forget()
                seleccionar_boton(btn_hora)
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar la cédula: {e}")
        finally:
            conexion.close()

    try:
        entry_cedula.bind("<KeyRelease>", verificar_cedula)
        entry_nombre.bind("<KeyRelease>", verificar_cedula)
    except Exception:
        pass


    def mostrar_tarifas_bicicletas():
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

            def cargar_tarifas_bicicletas():
                ventana_tarifas.focus_set()
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                try:
                    cursor = conexion.cursor()
                    cursor.execute("SELECT rowid, tarifa, duracion, valor FROM tarifasbicicletas")
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

            cargar_tarifas_bicicletas()

    btnTarifas.config(command=mostrar_tarifas_bicicletas)

    def imprimir_recibo_entrada_bici(cedula, modalidad, nombre, fecha_entrada, usuario, casco_val, tipo, color):
            recibo = []
            recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n\n")
            recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSÁBADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
            line_width = 32
            title = "BICICLETAS"
            centered = title.center(line_width)
            recibo.append("\x1b\x61\x01")
            recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
            recibo.append("\nRECIBO DE ENTRADA\n")
            recibo.append(f"Modalidad: {modalidad.replace('Día', 'Dia')}\n********************************\n")
            recibo.append("Cedula: {}\n********************************\n".format(cedula))
            recibo.append("Cliente: {}\n".format(nombre or ""))
            if casco_val and str(casco_val).strip() != "":
                recibo.append("Casco: {}\n".format(casco_val))
            if tipo and str(tipo).strip() != "":
                recibo.append("Tipo: {}\n".format(tipo))
            if color and str(color).strip() != "":
                recibo.append("Color: {}\n".format(color))
            recibo.append("Entrada: {}\n".format(fecha_entrada))
            recibo.append("Atendido por: {}\n".format(usuario))
            recibo.append("\n" * 3)
            texto = "".join(recibo)
            try:
                printer_name = win32print.GetDefaultPrinter()
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("ReciboEntradaBici.txt", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, texto.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
            except Exception:
                dlg = tk.Toplevel()
                dlg.title("Recibo de Entrada")
                txt = tk.Text(dlg, wrap="word", width=60, height=20)
                txt.insert("1.0", texto)
                txt.config(state="disabled")
                txt.pack(fill="both", expand=True)

    def _remove_accents(text):
            try:
                nkfd_form = unicodedata.normalize('NFKD', text)
                return ''.join([c for c in nkfd_form if not unicodedata.combining(c)])
            except Exception:
                return text

    def imprimir_factura_salida_bici(cedula, modalidad, nombre, fecha_entrada, fecha_salida, duracion, total, usuario):
            recibo = []
            recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n\n")
            recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
            line_width = 32
            title = "BICICLETAS"
            centered = title.center(line_width)
            recibo.append("\x1b\x61\x01")
            recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
            recibo.append("\nFACTURA\n")
            recibo.append(f"Modalidad: {modalidad}\n")
            recibo.append(f"Cedula: {cedula}\n")
            recibo.append(f"Cliente: {nombre}\n")
            recibo.append(f"Entrada: {fecha_entrada}\n")
            recibo.append(f"Salida: {fecha_salida}\n")
            recibo.append(f"Duracion: {duracion}\n")
            recibo.append(f"Total: ${total}\n")
            recibo.append(f"Atendido por: {usuario}\n")
            recibo.append("\n" * 3)
            texto = "".join(recibo)
            texto = _remove_accents(texto)
            try:
                printer_name = win32print.GetDefaultPrinter()
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalidaBici.txt", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, texto.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
            except Exception:
                dlg = tk.Toplevel()
                dlg.title("Factura de Salida")
                txt = tk.Text(dlg, wrap="word", width=60, height=20)
                txt.insert("1.0", texto)
                txt.config(state="disabled")
                txt.pack(fill="both", expand=True)

    def imprimir_factura_salida_fijo_bici(modalidad, cedula, nombre, entrada, salida, total, usuario, caracteristica=''):
            recibo = []
            recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n\n")
            recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
            line_width = 32
            title = "BICICLETAS"
            centered = title.center(line_width)
            recibo.append("\x1b\x61\x01")
            recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
            recibo.append("\nFACTURA\n")
            recibo.append(f"Modalidad: {modalidad}\n")
            recibo.append(f"Cedula: {cedula}\n")
            recibo.append(f"Cliente: {nombre}\n")
            recibo.append("Caracteristica: {}\n".format(caracteristica))
            recibo.append(f"Desde: {entrada}\n")
            recibo.append(f"Hasta: {salida}\n")
            recibo.append(f"Total: ${total}\n")
            recibo.append(f"Atendido por: {usuario}\n")
            recibo.append("\n" * 3)
            texto = "".join(recibo)
            texto = _remove_accents(texto)
            try:
                printer_name = win32print.GetDefaultPrinter()
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalidaFijoBici.txt", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, texto.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
            except Exception:
                dlg = tk.Toplevel()
                dlg.title("Factura de Salida (Fijo)")
                txt = tk.Text(dlg, wrap="word", width=60, height=20)
                txt.insert("1.0", texto)
                txt.config(state="disabled")
                txt.pack(fill="both", expand=True)

    def consultarCedulas():
            ventana = tk.Toplevel()
            ventana.title("Consultar Cédulas")
            ventana.geometry("850x500")
            ventana.bind('<Escape>', lambda e: ventana.destroy())
            ventana.bind('<Escape>', lambda e: ventana.destroy())

            frame = tk.Frame(ventana)
            frame.pack(fill="both", expand=True)

            sv_v = tk.Scrollbar(frame, orient="vertical")
            sv_h = tk.Scrollbar(frame, orient="horizontal")

            cols = ("ID", "Cédula", "Nombre Completo", "Tipo", "Color", "Modalidad", "Casco", "FechaHoraEntrada")
            tree = ttk.Treeview(frame, columns=cols, show="headings", yscrollcommand=sv_v.set, xscrollcommand=sv_h.set)
            sv_v.config(command=tree.yview)
            sv_h.config(command=tree.xview)
            sv_v.pack(side="right", fill="y")
            sv_h.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)


            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, anchor="center")

            def eliminar_cedula(event=None):
                from tkinter import messagebox
                if clasificacion_actual == "Usuario":
                    ventana.destroy()
                    messagebox.showerror("Error", "No tienes permiso para eliminar registros.")
                    return
                else:
                    it = tree.focus()
                    if not it:
                        return
                    vals = tree.item(it, "values")
                    if not vals or not vals[0]:
                        return
                    id_cedula = vals[0]
                    cedula_text = vals[1] if len(vals) > 1 else ""
                    modalidad_text = vals[5] if len(vals) > 5 else ""
                    if messagebox.askyesno("Eliminar", "¿Seguro que deseas eliminar este registro?"):
                        try:
                            conexion = conectar_bd_parqueaderojmj()
                            if conexion is not None:
                                cur = conexion.cursor()
                                cur.execute("DELETE FROM cedulas WHERE idCedulas = ?", (id_cedula,))
                                try:
                                    if modalidad_text in ("Semana", "Quincena", "Mes"):
                                        try:
                                            cur.execute("DELETE FROM mensualidadesBicicleta WHERE cedula = ?", (cedula_text,))
                                        except Exception:
                                            pass
                                        try:
                                            cur.execute("DELETE FROM quincenasBicicleta WHERE cedula = ?", (cedula_text,))
                                        except Exception:
                                            pass
                                        try:
                                            cur.execute("DELETE FROM semanasBicicleta WHERE cedula = ?", (cedula_text,))
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                conexion.commit()
                                tree.delete(it)
                                conexion.close()
                        except Exception as e:
                            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
                        actualizarConteoFijosBicicletas()
                        actualizarConteoModalidadesDelDia()
                    ventana.focus_set()
            
            try:
                tree.bind("<KeyPress-s>", eliminar_cedula)
            except Exception:
                pass

            def cargar():
                ventana.focus_set()
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                try:
                    cur = conexion.cursor()
                    cur.execute("SELECT idCedulas, cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, casco, fechaHoraEntrada FROM cedulas")
                    rows = cur.fetchall()
                    tree.delete(*tree.get_children())
                    for r in rows:
                        tree.insert("", "end", values=r)
                    if tree.get_children():
                        first_item = tree.get_children()[0]
                        tree.focus(first_item)
                        tree.selection_set(first_item)
                        tree.see(first_item)
                        tree.focus_set()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar cédulas: {e}")
                finally:
                    conexion.close()

            def reimprimir(event=None):
                it = tree.focus()
                if not it:
                    return
                vals = tree.item(it, "values")
                if not vals:
                    return
                imprimir_recibo_entrada_bici(cedula=vals[1], modalidad=vals[5], nombre=vals[2], fecha_entrada=vals[7], usuario=usuario_actual, casco_val=vals[6], tipo=vals[3], color=vals[4])

            try:
                tree.bind("<KeyPress-r>", reimprimir)
            except Exception:
                pass

            def seleccionar_desde_tree(event=None):
                it = tree.focus()
                if not it:
                    return
                vals = tree.item(it, "values")
                if not vals:
                    return
                try:
                    cedula_var.set(str(vals[1]))
                    nombre_var.set(str(vals[2]))
                    ventana.destroy()
                    verificar_cedula()
                except Exception:
                    pass
                entry_cedula.icursor('end')

            def actualizarCedulas(event):
                item = tree.focus()
                if not item:
                    return
                columna = tree.identify_column(event.x)
                columna_index = int(columna.replace("#", "")) - 1
                valores = tree.item(item, "values")
                if not valores:
                    return

                editable_cols = {3: 'tipoBicicleta', 4: 'colorBicicleta', 5: 'modalidad', 6: 'casco', 7: 'fechaHoraEntrada'}
                if columna_index not in editable_cols:
                    messagebox.showinfo("No editable", "No puede modificar esta columna desde aquí.")
                    return

                if clasificacion_actual == 'Usuario':
                    if columna_index != 6:
                        messagebox.showerror("Error", "No tienes permiso para modificar este campo.")
                        return
                    try:
                        fecha_entrada_str = valores[7]
                        fecha_entrada_dt = dt.datetime.strptime(fecha_entrada_str, "%Y-%m-%d %H:%M:%S")
                        if (dt.datetime.now() - fecha_entrada_dt).total_seconds() > 300:
                            messagebox.showerror("Error", "No puedes cambiar el casco después de 5 minutos.")
                            return
                    except Exception:
                        messagebox.showerror("Error", "No se pudo validar el tiempo de registro.")
                        return

                if clasificacion_actual == 'Usuario avanzado' and columna_index == 7:
                    messagebox.showerror("Error", "No tienes permiso para modificar la fecha de entrada.")
                    return

                columna_text = tree.heading(columna, 'text')
                valores_list = list(valores)
                valor_actual = valores_list[columna_index]
                nuevo_valor = simpledialog.askstring("Editar", f"Ingrese el nuevo valor para {columna_text}:", initialvalue=valor_actual)
                if nuevo_valor is None:
                    return

                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                try:
                    cur = conexion.cursor()
                    id_ced = valores_list[0]
                    col_name = editable_cols[columna_index]
                    if col_name == 'fechaHoraEntrada':
                        try:
                            dt.datetime.strptime(nuevo_valor, "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD HH:MM:SS")
                            return
                    try:
                        cur.execute(f"UPDATE cedulas SET {col_name} = ? WHERE idCedulas = ?", (nuevo_valor, id_ced))
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo actualizar cedulas: {e}")
                        conexion.rollback()
                        return

                    try:
                        cedula_key = valores_list[1]
                        hist_col = 'fechaEntrada' if col_name == 'fechaHoraEntrada' else col_name
                        cur.execute(f"UPDATE historialDeCedulas SET {hist_col} = ? WHERE cedula = ? AND fechaSalida IS NULL", (nuevo_valor, cedula_key))
                    except Exception:
                        pass

                    conexion.commit()
                    valores_list[columna_index] = nuevo_valor
                    tree.item(item, values=valores_list)

                    try:
                        actualizarConteoModalidadesDelDia()
                    except Exception:
                        pass
                    try:
                        actualizarConteoFijosBicicletas()
                    except Exception:
                        pass

                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
                    try:
                        conexion.close()
                    except Exception:
                        pass

            try:
                tree.bind('<Double-1>', actualizarCedulas)
            except Exception:
                pass
            try:
                tree.bind("<Return>", seleccionar_desde_tree)
            except Exception:
                pass

            cargar()
    btnConsultarCedulas.config(command=consultarCedulas)

    def historialDeCedulas():
            def reimprimir_factura_historial(event=None):
                it = tree.focus()
                if not it:
                    return
                vals = tree.item(it, "values")
                if not vals:
                    return
                try:
                    cedula = vals[1]
                    nombre = vals[2]
                    modalidad = vals[5] if len(vals) > 5 else ''
                    fecha_entrada = vals[6] if len(vals) > 6 else ''
                    fecha_salida = vals[7] if len(vals) > 7 else ''

                    diarios = ["Hora", "Estudiante", "Día", "24 Horas"]
                    total = ""
                    caracteristica = ''
                    salida_from_fixed = None

                    if modalidad not in diarios:
                        try:
                            conexion = conectar_bd_parqueaderojmj()
                            cursor = conexion.cursor()
                            for tabla, modalidad_nombre in [("mensualidadesBicicleta", "Mes"), ("quincenasBicicleta", "Quincena"), ("semanasBicicleta", "Semana")]:
                                try:
                                    if fecha_entrada:
                                        cursor.execute(f"SELECT caracteristica, entrada, salida FROM {tabla} WHERE cedula = ? AND entrada = ? LIMIT 1", (cedula, fecha_entrada))
                                        fila_f = cursor.fetchone()
                                        if fila_f:
                                            caracteristica = fila_f[0] if len(fila_f) > 0 and fila_f[0] is not None else ''
                                            salida_from_fixed = fila_f[2] if len(fila_f) > 2 and fila_f[2] is not None else None
                                            modalidad_lookup = modalidad_nombre
                                            break
                                    cursor.execute(f"SELECT caracteristica, entrada, salida FROM {tabla} WHERE cedula = ? ORDER BY datetime(entrada) DESC LIMIT 1", (cedula,))
                                    fila_f = cursor.fetchone()
                                    if fila_f:
                                        caracteristica = fila_f[0] if len(fila_f) > 0 and fila_f[0] is not None else caracteristica
                                        if not salida_from_fixed:
                                            salida_from_fixed = fila_f[2] if len(fila_f) > 2 and fila_f[2] is not None else salida_from_fixed
                                        modalidad_lookup = modalidad_nombre
                                        break
                                except Exception:
                                    continue
                        except Exception:
                            modalidad_lookup = modalidad
                        finally:
                            try:
                                cursor.close()
                            except Exception:
                                pass
                            try:
                                conexion.close()
                            except Exception:
                                pass

                        try:
                            conexion = conectar_bd_parqueaderojmj()
                            cursor = conexion.cursor()
                            modo = modalidad_lookup if 'modalidad_lookup' in locals() else modalidad
                            cursor.execute("SELECT valor FROM pagosBicicletas WHERE cedula = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (cedula, modo))
                            row = cursor.fetchone()
                            if row:
                                total = str(row[0])
                        except Exception:
                            total = ""
                        finally:
                            try:
                                cursor.close()
                            except Exception:
                                pass
                            try:
                                conexion.close()
                            except Exception:
                                pass

                        salida_para_imprimir = salida_from_fixed if salida_from_fixed else fecha_salida

                        imprimir_factura_salida_fijo_bici(modalidad=modalidad, cedula=cedula, nombre=nombre, entrada=fecha_entrada, salida=salida_para_imprimir, total=total, usuario=usuario_actual, caracteristica=caracteristica)
                    else:
                        duracion = "-"
                        try:
                            dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                            dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                            dur_td = dt_salida - dt_entrada
                            h, rem = divmod(dur_td.total_seconds(), 3600)
                            m, s = divmod(rem, 60)
                            duracion = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                        except Exception:
                            duracion = "-"
                        try:
                            conexion = conectar_bd_parqueaderojmj()
                            cursor = conexion.cursor()
                            cursor.execute("SELECT valor FROM pagosBicicletas WHERE cedula = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (cedula, modalidad))
                            row = cursor.fetchone()
                            if row:
                                total = str(row[0])
                        except Exception:
                            total = ""
                        finally:
                            try:
                                cursor.close()
                            except Exception:
                                pass
                            try:
                                conexion.close()
                            except Exception:
                                pass

                        imprimir_factura_salida_bici(cedula=cedula, modalidad=modalidad, nombre=nombre, fecha_entrada=fecha_entrada, fecha_salida=fecha_salida, duracion=duracion, total=total, usuario=usuario_actual)
                except Exception as e:
                    print(f"Error reimprimiendo factura historial: {e}")

            ventana = tk.Toplevel()
            ventana.title("Historial de Cédulas")
            ventana.geometry("900x500")
            ventana.bind('<Escape>', lambda e: ventana.destroy())

            ventana.grid_rowconfigure(0, weight=0)
            ventana.grid_rowconfigure(1, weight=1)
            ventana.grid_columnconfigure(0, weight=1)

            frame_filtros = tk.Frame(ventana, bg="#111111")
            frame_filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            frame_filtros.grid_columnconfigure(0, weight=1)
            frame_filtros.grid_columnconfigure(1, weight=1)
            frame_filtros.grid_columnconfigure(2, weight=1)
            frame_filtros.grid_columnconfigure(3, weight=1)

            lblCed = tk.Label(frame_filtros, text="Cédula:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE")
            lblCed.grid(row=0, column=0, padx=5, pady=5)
            ced_var = tk.StringVar()
            entry_ced = tk.Entry(frame_filtros, textvariable=ced_var, font=("Times New Roman", 14), width=20, bg="#FBF7E5", fg="black", justify="center")
            entry_ced.grid(row=0, column=1, padx=5, pady=5)

            lblDesde = tk.Label(frame_filtros, text="Desde:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE")
            lblDesde.grid(row=0, column=2, padx=5, pady=5)
            desde = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
            desde.grid(row=0, column=3, padx=5, pady=5)

            lblHasta = tk.Label(frame_filtros, text="Hasta:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE")
            lblHasta.grid(row=0, column=4, padx=5, pady=5)
            hasta = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
            hasta.grid(row=0, column=5, padx=5, pady=5)

            btn_cons = tk.Button(frame_filtros, text="Consultar", font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2")
            btn_cons.grid(row=0, column=6, padx=10, pady=5, sticky="e")

            for btn in [
                btn_cons
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

            frame_tabla = tk.Frame(ventana)
            frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

            sv_v = tk.Scrollbar(frame_tabla, orient="vertical")
            sv_h = tk.Scrollbar(frame_tabla, orient="horizontal")
            cols = ("ID", "Cédula", "Nombre Completo", "Tipo", "Color", "Modalidad", "Fecha de Entrada", "Fecha de Salida")
            cols = ("ID", "Cédula", "Nombre Completo", "Tipo", "Color", "Modalidad", "Fecha de Entrada", "Fecha de Salida", "Valor")
            tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", yscrollcommand=sv_v.set, xscrollcommand=sv_h.set)
            sv_v.config(command=tree.yview)
            sv_h.config(command=tree.xview)
            sv_v.pack(side="right", fill="y")
            sv_h.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)

            try:
                tree.bind("<KeyPress-r>", reimprimir_factura_historial)
            except Exception:
                pass

            try:
                tree.tag_configure('marked_deleted', background="#AEAEAE")
            except Exception:
                pass

            try:
                conexion_tmp = conectar_bd_parqueaderojmj()
                if conexion_tmp is not None:
                    try:
                        cur_tmp = conexion_tmp.cursor()
                        cur_tmp.execute("PRAGMA table_info('historialDeCedulas')")
                        cols_tmp = [r[1] for r in cur_tmp.fetchall()]
                        if 'marcadoEliminado' not in cols_tmp:
                            try:
                                cur_tmp.execute("ALTER TABLE historialDeCedulas ADD COLUMN marcadoEliminado INTEGER DEFAULT 0")
                                conexion_tmp.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        cur_tmp.close()
                    except Exception:
                        pass
                    try:
                        conexion_tmp.close()
                    except Exception:
                        pass
            except Exception:
                pass

            def _marcar_y_eliminar_pago_bici(event=None):
                from tkinter import messagebox
                try:
                    if clasificacion_actual == "Usuario":
                        messagebox.showerror("Error", "No tienes permiso para eliminar registros.")
                        entry_ced.focus_set()
                        return
                except Exception:
                    pass
                item = tree.focus()
                if not item:
                    return
                vals = tree.item(item, 'values')
                if not vals:
                    return
                try:
                    if not messagebox.askyesno("Eliminar", "¿Seguro que deseas marcar este registro como eliminado y borrar los pagos asociados?"):
                        entry_ced.focus_set()
                        return
                    entry_ced.focus_set()
                except Exception:
                    pass
                id_hist = vals[0]
                cedula = vals[1]
                modalidad = vals[5]
                fecha_salida = vals[7] if len(vals) > 7 else None

                try:
                    tree.item(item, tags=('marked_deleted',))
                except Exception:
                    pass

                try:
                    conexion_u = conectar_bd_parqueaderojmj()
                    if conexion_u is not None:
                        cur_u = conexion_u.cursor()
                        try:
                            cur_u.execute("UPDATE historialDeCedulas SET marcadoEliminado = 1 WHERE idHistorialDeCedulas = ?", (id_hist,))
                            conexion_u.commit()
                        except Exception:
                            pass
                        try:
                            cur_u.close()
                        except Exception:
                            pass
                        try:
                            conexion_u.close()
                        except Exception:
                            pass
                except Exception:
                    pass

                try:
                    conexion_p = conectar_bd_parqueaderojmj()
                    if conexion_p is None:
                        return
                    curp = conexion_p.cursor()
                    try:
                        curp.execute("DELETE FROM pagosBicicletas WHERE cedula = ? AND modalidad = ? AND date(fecha) = date(?)", (cedula, modalidad, fecha_salida))
                        conexion_p.commit()
                    except Exception as e:
                        try:
                            messagebox.showerror('Error', f'No se pudo eliminar el pago asociado: {e}')
                        except Exception:
                            pass
                    finally:
                        try:
                            curp.close()
                        except Exception:
                            pass
                        try:
                            conexion_p.close()
                        except Exception:
                            pass
                except Exception:
                    pass

            try:
                tree.bind('<KeyPress-a>', _marcar_y_eliminar_pago_bici)
            except Exception:
                pass

            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, anchor="center")

            def on_tree_backspace(event):
                entry_ced.focus_set()
            tree.bind("<BackSpace>", on_tree_backspace)

            def cargar():
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                entry_ced.focus_set()
                try:
                    cur = conexion.cursor()
                    q = "SELECT idHistorialDeCedulas, cedula, nombreCompleto, tipoBicicleta, colorBicicleta, modalidad, fechaEntrada, fechaSalida, COALESCE(marcadoEliminado,0) FROM historialDeCedulas WHERE 1=1"
                    params = []
                    if ced_var.get().strip():
                        q += " AND cedula LIKE ?"
                        params.append(f"%{ced_var.get().strip()}%")
                    if desde.get_date() and hasta.get_date():
                        q += " AND date(fechaEntrada) BETWEEN ? AND ?"
                        params.append(desde.get_date().strftime('%Y-%m-%d'))
                        params.append(hasta.get_date().strftime('%Y-%m-%d'))
                    cur.execute(q, params)
                    rows = cur.fetchall()
                    tree.delete(*tree.get_children())
                    for r in rows:
                        try:
                            cur2 = conexion.cursor()
                            cur2.execute("SELECT valor FROM pagosBicicletas WHERE cedula = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha DESC LIMIT 1", (r[1], r[5], r[7]))
                            pago = cur2.fetchone()
                            valor = pago[0] if pago and pago[0] is not None else ''
                        except Exception:
                            valor = ''
                        marcado = 0
                        try:
                            marcado = int(r[8]) if len(r) > 8 and r[8] is not None else 0
                        except Exception:
                            marcado = 0
                        display_values = (*r[:8], valor)
                        item_id = tree.insert("", "end", values=display_values)
                        if marcado:
                            try:
                                tree.item(item_id, tags=('marked_deleted',))
                            except Exception:
                                pass
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar historial: {e}")
                finally:
                    conexion.close()

                btn_cons.config(command=cargar)
                entry_ced.bind("<KeyRelease>", lambda e: cargar())

                def on_entry_ced_enter(event):
                    if tree.get_children():
                        first_item = tree.get_children()[0]
                        tree.focus(first_item)
                        tree.selection_set(first_item)
                        tree.see(first_item)
                        tree.focus_set()
                entry_ced.bind("<Return>", on_entry_ced_enter)
            cargar()
    btnHistorialDeCedulas.config(command=historialDeCedulas)

    def consultarClientesFijos():
            ventana = tk.Toplevel()
            ventana.title("Consultar Clientes")
            ventana.geometry("400x150")
            ventana.resizable(False, False)
            ventana.bind('<Escape>', lambda e: ventana.destroy())

            try:
                img = Image.open("fondoBicicletas.png").resize((400, 150))
                fondo_img = ImageTk.PhotoImage(img)
                lbl_fondo = tk.Label(ventana, image=fondo_img)
                lbl_fondo.image = fondo_img
                lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                ventana.configure(bg="black")

            ventana.focus_set()

            frame = tk.Frame(ventana, bg="#111111")
            frame.pack(expand=True)

            def mostrar_tabla(tipo):
                ventana.destroy()
                if tipo == "Mensualidades":
                    tabla_activa = "mensualidadesBicicleta"
                    tabla_hist = "historialMensualidadesBicicleta"
                    idcol = "idMensualidadesBicicleta"
                elif tipo == "Quincenas":
                    tabla_activa = "quincenasBicicleta"
                    tabla_hist = "historialQuincenasBicicleta"
                    idcol = "idQuincenasBicicleta"
                else:
                    tabla_activa = "semanasBicicleta"
                    tabla_hist = "historialSemanasBicicleta"
                    idcol = "idSemanasBicicleta"

                ventana_tabla = tk.Toplevel()
                ventana_tabla.title(tipo)
                ventana_tabla.geometry("900x600")
                ventana_tabla.bind('<Escape>', lambda e: ventana_tabla.destroy())

                ventana_tabla.grid_rowconfigure(0, weight=0)
                ventana_tabla.grid_rowconfigure(1, weight=1)
                ventana_tabla.grid_columnconfigure(0, weight=1)

                frame_filtros = tk.Frame(ventana_tabla, bg="#111111")
                frame_filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
                frame_filtros.grid_columnconfigure(0, weight=1)
                frame_filtros.grid_columnconfigure(1, weight=1)
                frame_filtros.grid_columnconfigure(2, weight=1)
                frame_filtros.grid_columnconfigure(3, weight=1)

                tk.Label(frame_filtros, text="Cédula:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE").grid(row=0, column=0, padx=5, pady=5)
                ced_var = tk.StringVar()
                entry_ced = tk.Entry(frame_filtros, textvariable=ced_var, font=("Times New Roman", 14), width=20, bg="#FBF7E5", fg="black", justify="center")
                entry_ced.grid(row=0, column=1, padx=5, pady=5)

                tk.Label(frame_filtros, text="Nombre:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE").grid(row=0, column=2, padx=5, pady=5)
                var_nombre = tk.StringVar()
                entry_nombre = tk.Entry(frame_filtros, textvariable=var_nombre, font=("Times New Roman", 14), width=20, bg="#FBF7E5", fg="black", justify="center")
                entry_nombre.grid(row=0, column=3, padx=5, pady=5)

                tk.Label(frame_filtros, text="Ver:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#F6EAAE").grid(row=0, column=4, padx=5, pady=5)
                ver_var = tk.StringVar(value="Activos")
                combo_ver = ttk.Combobox(frame_filtros, textvariable=ver_var, values=("Activos", "Historial"), font=("Times New Roman", 14), width=18, state="readonly", justify="center")
                combo_ver.grid(row=0, column=5, padx=5, pady=5)

                frame_tabla = tk.Frame(ventana_tabla)
                frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

                sv_v = tk.Scrollbar(frame_tabla, orient="vertical")
                sv_h = tk.Scrollbar(frame_tabla, orient="horizontal")
                cols = ("ID", "Cédula", "Nombre Completo", "Característica", "Desde", "Hasta")
                tree = ttk.Treeview(frame_tabla, columns=cols, show="headings", yscrollcommand=sv_v.set, xscrollcommand=sv_h.set)
                sv_v.config(command=tree.yview)
                sv_h.config(command=tree.xview)
                sv_v.pack(side="right", fill="y")
                sv_h.pack(side="bottom", fill="x")
                tree.pack(fill="both", expand=True)

                for c in cols:
                    tree.heading(c, text=c)
                    tree.column(c, anchor="center")

                tree.tag_configure('congelado', background='#ADD8E6')
                tree.tag_configure('descongelado', background='#C7F0C7')

                def on_cedula_enter(event):
                    entry_nombre.focus_set()
                entry_ced.bind("<Return>", on_cedula_enter)

                def on_nombre_enter(event):
                    if tree.get_children():
                        first_item = tree.get_children()[0]
                        tree.focus(first_item)
                        tree.selection_set(first_item)
                        tree.see(first_item)
                        tree.focus_set()
                    def on_tree_backspace(event):
                        entry_nombre.focus_set()
                    tree.bind("<BackSpace>", on_tree_backspace)
                entry_nombre.bind("<Return>", on_nombre_enter)

                def on_nombre_backspace(event):
                    if entry_nombre.get() == "":
                        entry_ced.focus_set()
                entry_nombre.bind("<BackSpace>", on_nombre_backspace)

                def reimprimir_factura_fijo(event=None):
                    it = tree.focus()
                    if not it:
                        return
                    vals = tree.item(it, "values")
                    if not vals:
                        return
                    try:
                        if ver_var.get() != "Historial":
                            return
                    except Exception:
                        pass
                    try:
                        cedula = vals[1]
                        nombre = vals[2]
                        caracteristica = vals[3] if len(vals) > 3 else ''
                        entrada = vals[4] if len(vals) > 4 else ''
                        salida = vals[5] if len(vals) > 5 else ''
                        if tipo.lower().startswith('mens'):
                            modalidad = 'Mes'
                        elif tipo.lower().startswith('quinc'):
                            modalidad = 'Quincena'
                        else:
                            modalidad = 'Semana'

                        total = ""
                        try:
                            conexion = conectar_bd_parqueaderojmj()
                            cursor = conexion.cursor()
                            cursor.execute("SELECT valor FROM pagosBicicletas WHERE cedula = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (cedula, modalidad))
                            row = cursor.fetchone()
                            if row:
                                total = str(row[0])
                        except Exception:
                            total = ""
                        finally:
                            try:
                                cursor.close()
                            except Exception:
                                pass
                            try:
                                conexion.close()
                            except Exception:
                                pass

                        imprimir_factura_salida_fijo_bici(modalidad=modalidad, cedula=cedula, nombre=nombre, entrada=entrada, salida=salida, total=total, usuario=usuario_actual, caracteristica=caracteristica)
                    except Exception as e:
                        print(f"Error reimprimiendo factura fijo: {e}")

                try:
                    tree.bind('<KeyPress-r>', reimprimir_factura_fijo)
                except Exception:
                    pass

                btn_frame = tk.Frame(ventana_tabla, bg="#111111")
                btn_frame.grid(row=2, column=0, sticky="ew", pady=4, padx=10)
                btn_frame.grid_columnconfigure(0, weight=1)
                btn_congelar = tk.Button(btn_frame, text="Congelar", bg="#F6EAAE", fg="#111111", cursor="hand2")
                btn_descongelar = tk.Button(btn_frame, text="Descongelar", bg="#F6EAAE", fg="#111111", cursor="hand2")
                btn_quitar = tk.Button(btn_frame, text="Quitar", bg="#F6EAAE", fg="#111111", cursor="hand2")
                btn_congelar.grid(row=0, column=0, sticky="e", padx=6)
                btn_descongelar.grid(row=0, column=1, sticky="e", padx=6)
                btn_quitar.grid(row=0, column=2, sticky="e", padx=6)

                for btn in [
                    btn_congelar, btn_descongelar, btn_quitar
                ]:
                    btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                    btn.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

                def cargar_datos():
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                        return
                    try:
                        cur = conexion.cursor()
                        if ver_var.get() == "Activos":
                            q = f"SELECT {idcol}, cedula, nombreCompleto, caracteristica, entrada, salida, congelado, fechaCongelado, recientementeDescongelado FROM {tabla_activa} WHERE 1=1"
                        else:
                            q = f"SELECT rowid, cedula, nombreCompleto, caracteristica, entrada, salida FROM {tabla_hist} WHERE 1=1"
                        params = []
                        if ced_var.get().strip():
                            q += " AND LOWER(cedula) LIKE ?"
                            params.append(f"%{ced_var.get().strip().lower()}%")
                        if var_nombre.get().strip():
                            q += " AND LOWER(nombreCompleto) LIKE ?"
                            params.append(f"%{var_nombre.get().strip().lower()}%")
                        if 'FROM ' in q and ('hist' in q.lower() or 'historial' in q.lower()):
                            q += ' ORDER BY datetime(salida) ASC'
                        cur.execute(q, params)
                        rows = cur.fetchall()
                        tree.delete(*tree.get_children())
                        for r in rows:
                            if ver_var.get() == "Activos":
                                tag = ''
                                try:
                                    if int(r[6]) == 1:
                                        tag = 'congelado'
                                    elif int(r[8]) == 1:
                                        tag = 'descongelado'
                                except Exception:
                                    tag = ''
                                tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5]), tags=(tag,))
                            else:
                                tree.insert("", "end", values=r)

                        try:
                            if ver_var.get() == "Activos":
                                for w in (btn_congelar, btn_descongelar, btn_quitar):
                                    w.config(state="normal")
                            else:
                                for w in (btn_congelar, btn_descongelar, btn_quitar):
                                    w.config(state="disabled")
                        except Exception:
                            pass
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al cargar datos: {e}")
                    finally:
                        conexion.close()
                cargar_datos()
                entry_nombre.bind('<KeyRelease>', lambda e: cargar_datos())

                def congelar():
                    try:
                        if ver_var.get() == "Historial":
                            return
                    except Exception:
                        pass
                    it = tree.focus()
                    if not it:
                        return
                    vals = tree.item(it, "values")
                    if not vals:
                        return
                    idval = vals[0]
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    try:
                        cur = conexion.cursor()
                        cur.execute(f"UPDATE {tabla_activa} SET congelado=1, fechaCongelado=?, recientementeDescongelado=0 WHERE {idcol}=?", (dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idval))
                        conexion.commit()
                        cargar_datos()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al congelar: {e}")
                    finally:
                        conexion.close()
                btn_congelar.config(command=congelar)

                def descongelar():
                    try:
                        if ver_var.get() == "Historial":
                            return
                    except Exception:
                        pass
                    it = tree.focus()
                    if not it:
                        return
                    vals = tree.item(it, "values")
                    if not vals:
                        return
                    idval = vals[0]
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    try:
                        cur = conexion.cursor()
                        cur.execute(f"SELECT fechaCongelado, salida FROM {tabla_activa} WHERE {idcol} = ?", (idval,))
                        fila = cur.fetchone()
                        fecha_congelado = None
                        salida_actual = None
                        if fila:
                            fecha_congelado, salida_actual = fila[0], fila[1]

                        if not fecha_congelado:
                            cur.execute(f"UPDATE {tabla_activa} SET congelado=0, fechaCongelado=NULL, recientementeDescongelado=1 WHERE {idcol}=?", (idval,))
                            conexion.commit()
                            cargar_datos()
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

                        nueva_salida_str = salida_actual
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
                        except Exception:
                            nueva_salida_str = salida_actual

                        cur.execute(f"UPDATE {tabla_activa} SET congelado=0, fechaCongelado=NULL, salida = ?, recientementeDescongelado=1 WHERE {idcol} = ?", (nueva_salida_str, idval))
                        conexion.commit()
                        tree.item(it, tags=('descongelado',))

                    except Exception as e:
                        messagebox.showerror("Error", f"Error al descongelar: {e}")
                    finally:
                        try:
                            conexion.close()
                        except Exception:
                            pass
                    cargar_datos()
                btn_descongelar.config(command=descongelar)

                def quitar():
                    try:
                        if ver_var.get() == "Historial":
                            return
                    except Exception:
                        pass
                    if clasificacion_actual == "Usuario":
                        messagebox.showerror("Error", "No tienes permiso para quitar registros.")
                        entry_ced.focus_set()
                        return
                    try:
                        if not messagebox.askyesno("Quitar", "¿Seguro que deseas quitar este registro?"):
                            entry_ced.focus_set()
                            return
                        entry_ced.focus_set()
                    except Exception:
                        pass
                    else:
                        it = tree.focus()
                        if not it:
                            return
                        vals = tree.item(it, "values")
                        if not vals:
                            return
                        idval = vals[0]
                        conexion = conectar_bd_parqueaderojmj()
                        if conexion is None:
                            return
                        try:
                            cur = conexion.cursor()
                            cur.execute(f"DELETE FROM {tabla_activa} WHERE {idcol}=?", (idval,))
                            conexion.commit()
                            cargar_datos()
                            try:
                                actualizarConteoFijosBicicletas()
                            except Exception:
                                pass
                        except Exception as e:
                            messagebox.showerror("Error", f"Error al quitar: {e}")
                        finally:
                            conexion.close()
                btn_quitar.config(command=quitar)

                combo_ver.bind("<<ComboboxSelected>>", lambda e: cargar_datos())
                entry_ced.bind("<KeyRelease>", lambda e: cargar_datos())
                actualizarConteoModalidadesDelDia()

                def focus_entry_cedula():
                    entry_ced.focus_set()
                    entry_ced.icursor('end')
                entry_ced.bind("<KeyRelease>", lambda e: (cargar_datos(), ventana_tabla.after_idle(focus_entry_cedula)))
                combo_ver.bind("<<ComboboxSelected>>", lambda e: (cargar_datos(), ventana_tabla.after_idle(focus_entry_cedula)))
                cargar_datos()

                ventana_tabla.after_idle(focus_entry_cedula)

            btn_mensual = tk.Button(frame, text="Mensualidades", font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Mensualidades"))
            btn_quinc = tk.Button(frame, text="Quincenas", font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Quincenas"))
            btn_seman = tk.Button(frame, text="Semanas", font=("Times New Roman", 14, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Semanas"))
            btn_mensual.grid(row=0, column=0, padx=10, pady=10)
            btn_quinc.grid(row=0, column=1, padx=10, pady=10)
            btn_seman.grid(row=0, column=2, padx=10, pady=10)

            for btn in [
                btn_mensual, btn_quinc, btn_seman
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

            
    btnConsultarFijos.config(command=consultarClientesFijos)

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
                query = '''SELECT medio_pago, SUM(valor) FROM pagosBicicletas WHERE date(fecha) >= ? AND date(fecha) <= ? GROUP BY medio_pago'''
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
            title = "ARQUEO DE BICICLETAS"
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

            btn_imprimir = tk.Button(resumen, text="Imprimir", font=("Times New Roman", 13, "bold"), bg="#F6EAAE", fg="#111111", cursor="hand2", command=imprimir_ventana)
            btn_imprimir.pack(pady=50)

            for btn in [
                btn_imprimir
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#F6EAAE"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#F6EAAE", fg="black"))

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
    try:
        actualizarConteoFijosBicicletas()
        actualizarConteoModalidadesDelDia()
    except Exception:
        pass

    entry_cedula.bind('<Control-b>', lambda event: abrir_tabla_cedulas())
    entry_nombre.bind('<Control-b>', lambda event: abrir_tabla_cedulas())
    entry_color.bind('<Control-b>', lambda event: abrir_tabla_cedulas())