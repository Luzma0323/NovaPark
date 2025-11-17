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

def crearFramesChazas(parent, usuario_actual, clasificacion_actual):
    workflow_state = {"exit_in_progress": False}
    def abrir_tabla_facturas(event=None):
        mostrar_facturas_de_venta()
    parent.bind('<Control-b>', lambda event: abrir_tabla_facturas())
    
    def add_months(dtobj, months=1):
        year = dtobj.year + (dtobj.month - 1 + months) // 12
        month = (dtobj.month - 1 + months) % 12 + 1
        day = dtobj.day
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        return dt.datetime(year, month, day, dtobj.hour, dtobj.minute, dtobj.second, dtobj.microsecond)
    
    def obtener_numero_factura():
        try:
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
        except Exception:
            return None

    def _normalize_total(total):
        if total is None:
            return "0"
        try:
            if isinstance(total, (int, float)):
                v = float(total)
                if v.is_integer():
                    return str(int(v))
                return f"{v:.2f}"
        except Exception:
            pass
        s = str(total)
        for p in ("Valor: $", "Valor: ", "$", "Valor:"):
            s = s.replace(p, "")
        s = s.replace(',', '').strip()
        if s == "":
            return "0"
        try:
            v = float(s)
            if v.is_integer():
                return str(int(v))
            return f"{v:.2f}"
        except Exception:
            return s

    def _fix_mojibake(s):

        try:
            if not isinstance(s, str):
                return s
            if any(x in s for x in ("Ã", "Â", "â", "├", "░")):
                try:
                    fixed = s.encode('latin-1').decode('utf-8')
                    if fixed != s:
                        return fixed
                except Exception:
                    pass
            return s
        except Exception:
            return s

    def _buscar_valor_pago_chaza(nombre, modalidad, fecha=None):
        total = ""
        try:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                return ""
            cursor = conexion.cursor()
            try:
                if fecha:
                    cursor.execute("SELECT valor FROM pagosChazas WHERE nombreCompleto = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha ASC LIMIT 1", (nombre, modalidad, fecha))
                    row = cursor.fetchone()
                    if row and row[0] is not None:
                        val = row[0]
                        return _normalize_total(val)
            except Exception:
                pass
            try:
                cursor.execute("SELECT valor FROM pagosChazas WHERE nombreCompleto = ? AND modalidad = ? ORDER BY fecha DESC LIMIT 1", (nombre, modalidad))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return _normalize_total(row[0])
            except Exception:
                pass
            try:
                cursor.execute("SELECT valor FROM pagosChazas WHERE nombreCompleto = ? ORDER BY fecha DESC LIMIT 1", (nombre,))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return _normalize_total(row[0])
            except Exception:
                pass
        except Exception:
            return ""
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conexion.close()
            except Exception:
                pass
        return ""

    def imprimir_factura_salida_fijo_chaza(modalidad, cedula, nombre, caracteristica, entrada, salida, total, usuario):
        num_factura = obtener_numero_factura() if 'obtener_numero_factura' in globals() else None
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n")
        if num_factura:
            recibo.append(f"Factura de venta: #{num_factura}\n\n")
        recibo.append("\nHORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "CHAZAS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("FACTURA\n")
        recibo.append(f"Modalidad: {modalidad}\n")
        recibo.append(f"Cedula: {cedula}\n")
        recibo.append(f"Cliente: {nombre}\n")
        recibo.append(f"Caracteristica: {caracteristica}\n")
        recibo.append(f"Desde: {entrada}\n")
        recibo.append(f"Hasta: {salida}\n")
        clean_total = _normalize_total(total)
        recibo.append(f"TOTAL: ${clean_total}\n")
        recibo.append(f"Atendido por: {usuario_actual}\n")
        recibo.append("\n" * 3)
        texto_recibo = "".join(recibo)
        texto_recibo = _fix_mojibake(texto_recibo)
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

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalidaFijoChaza.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                try:
                    payload = texto_recibo.encode('cp1252')
                except Exception:
                    try:
                        payload = texto_recibo.encode('cp850')
                    except Exception:
                        try:
                            payload = texto_recibo.encode('cp437')
                        except Exception:
                            try:
                                payload = texto_recibo.encode('latin-1')
                            except Exception:
                                payload = texto_recibo.encode('utf-8', errors='replace')

                win32print.WritePrinter(hPrinter, payload)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    win32print.ClosePrinter(hPrinter)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir la factura: {e}")

    def imprimir_factura_salida_chaza(nombre, modalidad, fecha_entrada, fecha_salida, duracion, total, usuario, cantidad):
        num_factura = obtener_numero_factura() if 'obtener_numero_factura' in globals() else None
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n")
        if num_factura:
            recibo.append(f"Factura de venta: #{num_factura}\n\n")
        recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "CHAZAS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("FACTURA\n")
        recibo.append(f"Cliente: {nombre}\n")
        recibo.append(f"Modalidad: {modalidad.replace('Pequeña', 'Pequena')}\n")
        recibo.append(f"Cantidad: {str(cantidad)}\n")
        recibo.append(f"Ingreso: {fecha_entrada}\n")
        recibo.append(f"Salida: {fecha_salida}\n")
        recibo.append(f"Duracion: {duracion}\n")
        clean_total = _normalize_total(total)
        recibo.append(f"TOTAL: ${clean_total}\n")
        recibo.append(f"Atendido por: {usuario}\n")
        recibo.append("\n" * 3)
        texto_recibo = "".join(recibo)
        texto_recibo = _fix_mojibake(texto_recibo)
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

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("FacturaSalidaChaza.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                try:
                    payload = texto_recibo.encode('cp1252')
                except Exception:
                    try:
                        payload = texto_recibo.encode('cp850')
                    except Exception:
                        try:
                            payload = texto_recibo.encode('cp437')
                        except Exception:
                            try:
                                payload = texto_recibo.encode('latin-1')
                            except Exception:
                                payload = texto_recibo.encode('utf-8', errors='replace')

                win32print.WritePrinter(hPrinter, payload)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    win32print.ClosePrinter(hPrinter)
        except Exception as e:
            messagebox.showerror("Error de impresión", f"No se pudo imprimir la factura: {e}")

    def imprimir_recibo_entrada_chaza(nombre, cantidad, modalidad, fecha_entrada, usuario):
        recibo = []
        recibo.append("PARQUEADERO JMJ\nNIT: 87715766-9\nNO RESPONSABLE DE IVA\nDireccion: Carrera 43 #52-36\nCelular: 3136190473\n\n")
        recibo.append("HORARIO\nLUNES A VIERNES: 5:30 AM - 9:30 PM\nSABADO: 5:30 AM - 7:00 PM\nNO ABRIMOS DOMINGOS NI FESTIVOS\n\n")
        line_width = 32
        title = "CHAZAS"
        centered = title.center(line_width)
        recibo.append("\x1b\x61\x01")
        recibo.append("\x1b\x45\x01" + centered + "\x1b\x45\x00" + "\x1b\x61\x00" + "\n")
        recibo.append("\nRECIBO DE ENTRADA\nModalidad: {}\n********************************\n".format(modalidad.replace('Pequeña', 'Pequena')))
        recibo.append("Cliente: {}\n********************************\n".format(nombre))
        recibo.append(f"Cantidad: {str(cantidad)}\n")
        recibo.append("Entrada: {}\n".format(fecha_entrada))
        recibo.append("Atendido por: {}\n".format(usuario))
        recibo.append("\n" * 3)
        texto_recibo = "".join(recibo)
        texto_recibo = _fix_mojibake(texto_recibo)
        try:
            try:
                import win32print
            except Exception as imp_err:
                raise RuntimeError(f"win32print no disponible: {imp_err}")

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

                hJob = win32print.StartDocPrinter(hPrinter, 1, ("ReciboEntradaChaza.txt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                try:
                    payload = texto_recibo.encode('cp1252')
                except Exception:
                    try:
                        payload = texto_recibo.encode('cp850')
                    except Exception:
                        try:
                            payload = texto_recibo.encode('cp437')
                        except Exception:
                            try:
                                payload = texto_recibo.encode('latin-1')
                            except Exception:
                                payload = texto_recibo.encode('utf-8', errors='replace')

                win32print.WritePrinter(hPrinter, payload)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                if hPrinter:
                    try:
                        win32print.ClosePrinter(hPrinter)
                    except Exception:
                        pass
        except Exception as e:
            try:
                import traceback
                tb = traceback.format_exc()
                print("Error al imprimir el recibo (chazas):", e)
                print(tb)
            except Exception:
                pass

            try:
                preview = tk.Toplevel()
                preview.title("Vista previa - Recibo de entrada")
                preview.geometry("500x600")
                txt = tk.Text(preview, wrap='none', font=('Courier', 10))
                txt.insert('1.0', texto_recibo)
                txt.config(state='disabled')
                txt.pack(expand=True, fill='both')

                def _copiar_portapapeles():
                    try:
                        preview.clipboard_clear()
                        preview.clipboard_append(texto_recibo)
                        messagebox.showinfo("Copiado", "Texto copiado al portapapeles.")
                    except Exception:
                        messagebox.showwarning("Copiar", "No se pudo copiar al portapapeles.")

                btn_frame = tk.Frame(preview)
                btn_frame.pack(pady=6)
                btn_copy = tk.Button(btn_frame, text="Copiar al portapapeles", command=_copiar_portapapeles, bg="#AEAEAE", cursor="hand2")
                btn_copy.pack(side='left', padx=6)
                try:
                    messagebox.showwarning("Impresión no disponible", f"No se pudo imprimir el recibo: {e}\nSe ha abierto una vista previa para imprimir manualmente.")
                except Exception:
                    pass
            except Exception:
                try:
                    messagebox.showerror("Error de impresión", f"No se pudo imprimir el recibo: {e}")
                except Exception:
                    pass

    def mostrar_facturas_de_venta():
        ventana = tk.Toplevel()
        ventana.title("Facturas de Venta")
        ventana.geometry("900x500")
        ventana.bind('<Escape>', lambda e: ventana.destroy())
        frame = tk.Frame(ventana)
        frame.pack(fill="both", expand=True)
        scrollbar_v = tk.Scrollbar(frame, orient="vertical")
        scrollbar_h = tk.Scrollbar(frame, orient="horizontal")
        tree = ttk.Treeview(frame, columns=("ID", "Nombre Completo", "Cantidad", "Modalidad", "Fecha y Hora de Entrada"),
                            show="headings", yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        try:
            tree.tag_configure('congelado', background='#ADD8E6')
            tree.tag_configure('descongelado', background='#C7F0C7')
        except Exception:
            pass
        scrollbar_v.config(command=tree.yview)
        scrollbar_h.config(command=tree.xview)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        tree.heading("ID", text="ID")
        tree.heading("Nombre Completo", text="Nombre Completo")
        tree.heading("Cantidad", text="Cantidad")
        tree.heading("Modalidad", text="Modalidad")
        tree.heading("Fecha y Hora de Entrada", text="Fecha y Hora de Entrada")
        tree.column("ID", width=60, anchor="center")
        tree.column("Nombre Completo", width=220, anchor="center")
        tree.column("Cantidad", width=100, anchor="center")
        tree.column("Modalidad", width=120, anchor="center")
        tree.column("Fecha y Hora de Entrada", width=200, anchor="center")

        def eliminar_factura(event=None):
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
                nombre_text = vals[1] if len(vals) > 1 else ""
                modalidad_text = vals[3] if len(vals) > 3 else ""
                if messagebox.askyesno("Eliminar", "¿Seguro que deseas eliminar este registro?"):
                    try:
                        conexion = conectar_bd_parqueaderojmj()
                        if conexion is not None:
                            cur = conexion.cursor()
                            cur.execute("DELETE FROM facturasDeVenta WHERE idFacturasDeVenta = ?", (id_cedula,))
                            # If this was a fixed-modalidad, also remove from fixed tables for chazas
                            try:
                                if modalidad_text in ("Semana", "Quincena", "Mes"):
                                    try:
                                        cur.execute("DELETE FROM mensualidadesChaza WHERE nombreCompleto = ?", (nombre_text,))
                                    except Exception:
                                        pass
                                    try:
                                        cur.execute("DELETE FROM quincenasChaza WHERE nombreCompleto = ?", (nombre_text,))
                                    except Exception:
                                        pass
                                    try:
                                        cur.execute("DELETE FROM semanasChaza WHERE nombreCompleto = ?", (nombre_text,))
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

        try:
            tree.bind("<KeyPress-s>", eliminar_factura)
        except Exception:
            pass

        def cargar():
            ventana.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT idFacturasDeVenta, nombreCompleto, cantidad, modalidad, fechaHoraEntrada FROM facturasDeVenta")
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
                messagebox.showerror("Error", f"Error al cargar facturas: {e}")
            finally:
                conexion.close()
        cargar()

        def reimprimir_recibo_entrada(event=None):
            item = tree.focus()
            if not item:
                return
            vals = tree.item(item, 'values')
            if not vals:
                return
            nombre = vals[1]
            cantidad = vals[2] if len(vals) > 2 else ""
            modalidad = vals[3]
            fecha_entrada = vals[4]
            try:
                try:
                    cantidad_int = int(cantidad)
                except Exception:
                    cantidad_int = cantidad

                imprimir_recibo_entrada_chaza(nombre, cantidad_int, modalidad, fecha_entrada, usuario_actual)
            except Exception:
                pass

        def editar_factura(event=None):
            if clasificacion_actual == "Usuario":
                messagebox.showerror("Acceso Denegado", "No tienes permiso para editar facturas.")
                ventana.focus_set()
                return
            else:
                selected = tree.focus()
                if not selected:
                    return
                vals = tree.item(selected, 'values')
                id_fact = vals[0]
                nombre_sel = vals[1]
                cantidad_sel = vals[2]
                modalidad_sel = vals[3]
                fecha_sel = vals[4]

                dlg = tk.Toplevel(ventana)

                dlg.title("Editar Factura")
                dlg.resizable(False, False)
                row_idx = 0
                entry_widgets = []


                if clasificacion_actual in ["Superusuario", "Usuario avanzado"]:
                    tk.Label(dlg, text="Nombre:").grid(row=row_idx, column=0, padx=6, pady=6)
                    nombre_var_edit = tk.StringVar(value=nombre_sel)
                    entry_nombre = tk.Entry(dlg, textvariable=nombre_var_edit)
                    entry_nombre.grid(row=row_idx, column=1, padx=6, pady=6)
                    entry_widgets.append(entry_nombre)
                    # Forzar mayúsculas y no permitir números en el entry de nombre
                    def to_uppercase_nombre(*args):
                        val = nombre_var_edit.get()
                        new_val = ''.join([c for c in val if not c.isdigit()]).upper()
                        if val != new_val:
                            nombre_var_edit.set(new_val)
                    nombre_var_edit.trace_add('write', lambda *args: to_uppercase_nombre())
                    row_idx += 1


                tk.Label(dlg, text="Cantidad:").grid(row=row_idx, column=0, padx=6, pady=6)
                cant_var = tk.StringVar(value=str(cantidad_sel))
                entry_cant = tk.Entry(dlg, textvariable=cant_var)
                entry_cant.grid(row=row_idx, column=1, padx=6, pady=6)
                entry_widgets.append(entry_cant)
                # Solo permitir números en el entry de cantidad
                def validate_numeric(new_value):
                    return new_value.isdigit() or new_value == ""
                vcmd = dlg.register(validate_numeric)
                entry_cant.config(validate="key", validatecommand=(vcmd, "%P"))
                row_idx += 1

                tk.Label(dlg, text="Modalidad:").grid(row=row_idx, column=0, padx=6, pady=6)
                modalidades_fijas = {"Mes", "Quincena", "Semana"}
                modalidades_opts = [b.cget('text') for b in botones if b.cget('text') not in modalidades_fijas]
                modalidad_var = tk.StringVar(value=modalidad_sel)
                combo_modalidad = ttk.Combobox(dlg, values=modalidades_opts, textvariable=modalidad_var, state='readonly')
                combo_modalidad.grid(row=row_idx, column=1, padx=6, pady=6)
                entry_widgets.append(combo_modalidad)
                row_idx += 1

                if clasificacion_actual == "Superusuario":
                    tk.Label(dlg, text="Fecha y Hora (YYYY-MM-DD HH:MM:SS):").grid(row=row_idx, column=0, padx=6, pady=6)
                    fecha_var = tk.StringVar(value=str(fecha_sel))
                    entry_fecha = tk.Entry(dlg, textvariable=fecha_var, width=25)
                    entry_fecha.grid(row=row_idx, column=1, padx=6, pady=6)
                    entry_widgets.append(entry_fecha)

                def focus_next(event=None):
                    widget = event.widget
                    try:
                        idx = entry_widgets.index(widget)
                        if idx < len(entry_widgets) - 1:
                            entry_widgets[idx + 1].focus_set()
                        else:
                            on_ok()
                    except Exception:
                        pass
                    return "break"


                def focus_prev(event=None):
                    widget = event.widget
                    try:
                        idx = entry_widgets.index(widget)
                        if idx > 0 and isinstance(widget, tk.Entry):
                            if widget.get() == "" and widget.index(tk.INSERT) == 0:
                                entry_widgets[idx - 1].focus_set()
                                prev = entry_widgets[idx - 1]
                                if isinstance(prev, tk.Entry):
                                    prev.icursor(tk.END)
                                return "break"
                    except Exception:
                        pass
                    return None

                def close_dlg(event=None):
                    dlg.destroy()
                    return "break"

                def set_cursor_end(event=None):
                    widget = event.widget
                    if isinstance(widget, tk.Entry):
                        widget.icursor(tk.END)

                for w in entry_widgets:
                    w.bind("<Return>", focus_next)
                    w.bind("<KP_Enter>", focus_next)
                    w.bind("<Escape>", close_dlg)
                    if isinstance(w, tk.Entry):
                        w.bind("<BackSpace>", focus_prev)
                        w.bind("<FocusIn>", set_cursor_end)

                dlg.bind("<Escape>", close_dlg)
                def focus_first_entry():
                    entry_widgets[0].focus_set()
                    if isinstance(entry_widgets[0], tk.Entry):
                        entry_widgets[0].icursor(tk.END)
                dlg.after(100, focus_first_entry)

                def on_ok():
                    try:
                        nueva_cant = int(cant_var.get())
                    except Exception:
                        messagebox.showerror('Error', 'Cantidad inválida')
                        return
                    nueva_modalidad = modalidad_var.get()
                    if clasificacion_actual == "Superusuario":
                        nueva_fecha = fecha_var.get().strip()
                    else:
                        nueva_fecha = str(fecha_sel)
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
                        nueva_nombre = nombre_var_edit.get().strip() if 'nombre_var_edit' in locals() else nombre_sel
                        cursor.execute("UPDATE facturasDeVenta SET nombreCompleto = ?, cantidad = ?, modalidad = ?, fechaHoraEntrada = ? WHERE idFacturasDeVenta = ?",
                                    (nueva_nombre, nueva_cant, nueva_modalidad, nueva_fecha, id_fact))
                        try:
                            cursor.execute(
                                "UPDATE historialDeFacturas SET nombreCompleto = ?, cantidad = ?, modalidad = ?, fechaEntrada = ? WHERE nombreCompleto = ? AND fechaEntrada = ? AND fechaSalida IS NULL",
                                (nueva_nombre, nueva_cant, nueva_modalidad, nueva_fecha, nombre_sel, fecha_sel)
                            )
                            if cursor.rowcount == 0:
                                cursor.execute(
                                    "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                                    (nueva_nombre, nueva_cant, nueva_modalidad, nueva_fecha)
                                )
                        except Exception:
                            pass
                        conexion.commit()
                        try:
                            actualizarConteoModalidadesDelDia()
                        except Exception:
                            pass
                        try:
                            actualizarConteoFijos()
                        except Exception:
                            pass
                    except Exception as e:
                        messagebox.showerror('Error', f'No se pudo actualizar: {e}')
                    finally:
                        try:
                            if conexion:
                                conexion.close()
                        except Exception:
                            pass
                    cargar()
                    dlg.destroy()

                btn_ok = tk.Button(dlg, text='OK', command=on_ok, bg='#AEAEAE', cursor='hand2')
                btn_ok.grid(row=4, column=0, columnspan=2, pady=8)

                for btn in [
                btn_ok
                ]:
                    btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                    btn.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

        def llenar_en_principal(event=None):
            selected = tree.focus()
            if not selected:
                return
            vals = tree.item(selected, 'values')
            ventana.destroy()
            try:
                nombre_sel = vals[1]
                cantidad_sel = vals[2]
                modalidad_sel = vals[3]
                fecha_sel = vals[4]
            except Exception:
                return
            try:
                nombre_var.set(nombre_sel)
            except Exception:
                pass
            try:
                cantidad_var.set(str(cantidad_sel))
            except Exception:
                pass
            try:
                ms = modalidad_sel.strip().lower() if isinstance(modalidad_sel, str) else str(modalidad_sel).strip().lower()
                for b in botones:
                    if b.cget('text').strip().lower() == ms:
                        seleccionar_boton(b)
                        break
            except Exception:
                pass
            try:
                dt_obj = dt.datetime.strptime(fecha_sel, "%Y-%m-%d %H:%M:%S")
                fechaEntrada.set(dt_obj.strftime('%d/%m/%Y %H:%M:%S'))
                lblFechaEntrada.config(text="Fecha y Hora de Entrada: " + fechaEntrada.get())
                lblFechaEntrada.pack(pady=5)
            except Exception:
                try:
                    fechaEntrada.set(str(fecha_sel))
                    lblFechaEntrada.config(text="Fecha y Hora de Entrada: " + fechaEntrada.get())
                    lblFechaEntrada.pack(pady=5)
                except Exception:
                    pass
            nombre.focus_set()
            nombre.icursor('end')

        try:
            tree.bind('<Double-1>', editar_factura)
            tree.bind('<Return>', llenar_en_principal)
            try:
                tree.bind("<KeyPress-r>", reimprimir_recibo_entrada)
            except Exception:
                pass
        except Exception:
            pass

    def mostrar_historial_de_facturas():
        ventana = tk.Toplevel()
        ventana.title("Historial de Facturas")
        ventana.geometry("900x500")
        ventana.configure(bg="white")
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
        frame_filtros.grid_columnconfigure(4, weight=1)
        frame_filtros.grid_columnconfigure(5, weight=1)

        lbl_nombre = tk.Label(frame_filtros, text="Nombre:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
        lbl_nombre.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        nombre_hist_var = tk.StringVar()
        entry_nombre = tk.Entry(frame_filtros, textvariable=nombre_hist_var, font=("Times New Roman", 14), width=20, bg="#E6E6E6", fg="black", justify="center")
        entry_nombre.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        def to_uppercase_nombre(*args):
            v = nombre_hist_var.get()
            if v != v.upper():
                nombre_hist_var.set(v.upper())
        nombre_hist_var.trace_add("write", to_uppercase_nombre)

        entry_nombre.bind("<KeyRelease>", lambda e: (cargarHistorialDeFacturas()))

        lbl_fecha_inicio = tk.Label(frame_filtros, text="Desde:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
        lbl_fecha_inicio.grid(row=0, column=2, padx=5, pady=5)
        fecha_inicio = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
        fecha_inicio.grid(row=0, column=3, padx=5, pady=5)

        lbl_fecha_fin = tk.Label(frame_filtros, text="Hasta:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
        lbl_fecha_fin.grid(row=0, column=4, padx=5, pady=5)
        fecha_fin = DateEntry(frame_filtros, font=("Times New Roman", 14), width=12, date_pattern="yyyy-mm-dd")
        fecha_fin.grid(row=0, column=5, padx=5, pady=5)

        btn_consultar = tk.Button(frame_filtros, text="Consultar", font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2")
        btn_consultar.grid(row=0, column=6, padx=10, pady=5, sticky="e")

        frame_tabla = tk.Frame(ventana)
        frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar_vertical = tk.Scrollbar(frame_tabla, orient="vertical")
        scrollbar_horizontal = tk.Scrollbar(frame_tabla, orient="horizontal")

        tree = ttk.Treeview(
            frame_tabla,
            columns=("ID", "Nombre", "Cantidad", "Modalidad", "Fecha Entrada", "Fecha Salida", "Valor"),
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
            tree.tag_configure('marked_deleted', background="#AEAEAE")
        except Exception:
            pass

        try:
            conexion_tmp = conectar_bd_parqueaderojmj()
            if conexion_tmp is not None:
                try:
                    cur_tmp = conexion_tmp.cursor()
                    cur_tmp.execute("PRAGMA table_info('historialDeFacturas')")
                    cols = [r[1] for r in cur_tmp.fetchall()]
                    if 'marcadoEliminado' not in cols:
                        try:
                            cur_tmp.execute("ALTER TABLE historialDeFacturas ADD COLUMN marcadoEliminado INTEGER DEFAULT 0")
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

        def _marcar_y_eliminar_pago(event=None):
            from tkinter import messagebox

            try:
                if clasificacion_actual == "Usuario":
                    messagebox.showerror("Error", "No tienes permiso para eliminar registros.")
                    return
            except Exception:
                pass

            try:
                if not messagebox.askyesno("Eliminar", "¿Seguro que deseas marcar este registro como eliminado y borrar los pagos asociados?"):
                    entry_nombre.focus_set()
                    return
                entry_nombre.focus_set()
            except Exception:
                pass

            item = tree.focus()
            if not item:
                return
            vals = tree.item(item, 'values')
            if not vals or len(vals) < 6:
                return
            id_hist = vals[0]
            nombre = vals[1]
            modalidad = vals[3]
            fecha_salida = vals[5]

            try:
                tree.item(item, tags=('marked_deleted',))
            except Exception:
                pass

            try:
                conexion_u = conectar_bd_parqueaderojmj()
                if conexion_u is not None:
                    cur_u = conexion_u.cursor()
                    try:
                        cur_u.execute("UPDATE historialDeFacturas SET marcadoEliminado = 1 WHERE idHistorialDeFacturas = ?", (id_hist,))
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
                    curp.execute("DELETE FROM pagosChazas WHERE nombreCompleto = ? AND modalidad = ? AND date(fecha) = date(?)", (nombre, modalidad, fecha_salida))
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
            tree.bind('<KeyPress-a>', _marcar_y_eliminar_pago)
        except Exception:
            pass

        tree.heading("ID", text="ID")
        tree.heading("Nombre", text="Nombre")
        tree.heading("Cantidad", text="Cantidad")
        tree.heading("Modalidad", text="Modalidad")
        tree.heading("Fecha Entrada", text="Fecha Entrada")
        tree.heading("Fecha Salida", text="Fecha Salida")
        tree.heading("Valor", text="Valor")

        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre", width=220, anchor="center")
        tree.column("Cantidad", width=100, anchor="center")
        tree.column("Modalidad", width=120, anchor="center")
        tree.column("Fecha Entrada", width=180, anchor="center")
        tree.column("Fecha Salida", width=180, anchor="center")
        tree.column("Valor", width=100, anchor="center")

        for btn in [btn_consultar]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

        def on_tree_backspace(event):
            entry_nombre.focus_set()
        tree.bind("<BackSpace>", on_tree_backspace)

        def cargarHistorialDeFacturas():
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            
            entry_nombre.focus_set()

            cursor = conexion.cursor() 
            query = "SELECT idHistorialDeFacturas, nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida, COALESCE(marcadoEliminado,0) FROM historialDeFacturas WHERE fechaSalida IS NOT NULL"
            params = []

            nombre_filtro = nombre_hist_var.get().strip()
            if nombre_filtro:
                query += " AND UPPER(nombreCompleto) LIKE ?"
                params.append(f"%{nombre_filtro.upper()}%")

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
                    cur2.execute("SELECT valor FROM pagosChazas WHERE nombreCompleto = ? AND modalidad = ? AND date(fecha) = date(?) ORDER BY fecha DESC LIMIT 1", (row[1], row[3], row[5]))
                    pago = cur2.fetchone()
                    valor = pago[0] if pago and pago[0] is not None else ''
                except Exception:
                    valor = ''
                marcado = 0
                try:
                    marcado = int(row[6]) if len(row) > 6 and row[6] is not None else 0
                except Exception:
                    marcado = 0
                display_values = (*row[:6], valor)
                item_id = tree.insert("", "end", values=display_values)
                if marcado:
                    try:
                        tree.item(item_id, tags=('marked_deleted',))
                    except Exception:
                        pass

            btn_consultar.config(command=cargarHistorialDeFacturas)
            entry_nombre.bind("<KeyRelease>", lambda e: cargarHistorialDeFacturas())
            def on_entry_nombre_enter(event):
                if tree.get_children():
                    first_item = tree.get_children()[0]
                    tree.focus(first_item)
                    tree.selection_set(first_item)
                    tree.see(first_item)
                    tree.focus_set()
            entry_nombre.bind("<Return>", on_entry_nombre_enter)

        cargarHistorialDeFacturas()

        def reimprimir_factura_salida(event=None):
            item = tree.focus()
            if not item:
                return
            vals = tree.item(item, 'values')
            if not vals:
                return
            nombre = vals[1]
            cantidad = vals[2]
            modalidad = vals[3]
            fecha_entrada = vals[4]
            fecha_salida = vals[5]
            try:
                dt_entrada = None
                dt_salida = None
                try:
                    dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d")
                    except Exception:
                        dt_entrada = None
                try:
                    dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d")
                    except Exception:
                        dt_salida = None

                if dt_entrada and dt_salida:
                    duracion_td = dt_salida - dt_entrada
                    horas, rem = divmod(duracion_td.total_seconds(), 3600)
                    minutos, segundos = divmod(rem, 60)
                    duracion_str = f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
                else:
                    duracion_str = "-"

                salida_print = fecha_salida
                try:
                    if modalidad in ["Mes", "Quincena", "Semana"]:
                        tabla_act = 'mensualidadesChaza' if modalidad == 'Mes' else ('quincenasChaza' if modalidad == 'Quincena' else 'semanasChaza')
                        conexion2 = conectar_bd_parqueaderojmj()
                        if conexion2 is not None:
                            cur2 = conexion2.cursor()
                            try:
                                cur2.execute(f"SELECT salida FROM {tabla_act} WHERE nombreCompleto = ? ORDER BY datetime(salida) DESC LIMIT 1", (nombre,))
                                ract = cur2.fetchone()
                            except Exception:
                                ract = None
                            if ract and ract[0]:
                                salida_print = ract[0]
                            try:
                                cur2.close()
                            except Exception:
                                pass
                            try:
                                conexion2.close()
                            except Exception:
                                pass

                        try:
                            if (not salida_print) or (dt_entrada and dt_salida and dt_salida <= dt_entrada):
                                dur_map = {"Semana": 7, "Quincena": 15, "Mes": 30}
                                days = dur_map.get(modalidad, 30)
                                if dt_entrada:
                                    dt_due = dt_entrada + dt.timedelta(days=days)
                                    salida_print = dt_due.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass

                        total = ""
                        try:
                            total = _buscar_valor_pago_chaza(nombre, modalidad, salida_print)
                        except Exception:
                            total = ""

                        cedula = ""
                        caracteristica = ""
                        try:
                            conexion2 = conectar_bd_parqueaderojmj()
                            if conexion2 is not None:
                                cur2 = conexion2.cursor()
                                try:
                                    cur2.execute(f"SELECT cedula, caracteristica FROM historialMensualidadesChaza WHERE nombreCompleto = ? AND entrada = ? AND salida = ?", (nombre, fecha_entrada, fecha_salida))
                                    row2 = cur2.fetchone()
                                except Exception:
                                    row2 = None
                                if not row2:
                                    tabla_act = 'mensualidadesChaza' if modalidad == 'Mes' else ('quincenasChaza' if modalidad == 'Quincena' else 'semanasChaza')
                                    try:
                                        cur2.execute(f"SELECT cedula, caracteristica FROM {tabla_act} WHERE nombreCompleto = ? ORDER BY datetime(salida) DESC LIMIT 1", (nombre,))
                                        row2 = cur2.fetchone()
                                    except Exception:
                                        row2 = None
                                if row2:
                                    cedula = row2[0] or ""
                                    caracteristica = row2[1] or ""
                                try:
                                    cur2.close()
                                except Exception:
                                    pass
                                try:
                                    conexion2.close()
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        try:
                            imprimir_factura_salida_fijo_chaza(modalidad, cedula, nombre, caracteristica, fecha_entrada, salida_print, total, usuario_actual)
                        except Exception:
                            pass
                    else:
                        total = ""
                        try:
                            total = _buscar_valor_pago_chaza(nombre, modalidad, fecha_salida)
                        except Exception:
                            total = ""
                        try:
                            imprimir_factura_salida_chaza(nombre, modalidad, fecha_entrada, fecha_salida, duracion_str, total, usuario_actual, cantidad)
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass

        try:
            tree.bind("<KeyPress-r>", reimprimir_factura_salida)
        except Exception:
            pass

    def consultar_clientes_fijos():
        ventana = tk.Toplevel()
        ventana.title("Consultar Clientes")
        ventana.geometry("400x150")
        ventana.bind('<Escape>', lambda e: ventana.destroy())
        ventana.resizable(False, False)
        ancho, alto = 400, 150
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        try:
            img = Image.open("fondoChazas.png").resize((ancho, alto))
            fondo_img = ImageTk.PhotoImage(img)
            lbl_fondo = tk.Label(ventana, image=fondo_img)
            lbl_fondo.image = fondo_img
            lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            ventana.configure(bg="black")

        ventana.focus_set()

        frame_botones = tk.Frame(ventana, bg="#111111")
        frame_botones.pack(expand=True)

        def mostrar_tabla(tipo):
            ventana.destroy()
            ventana_tabla = tk.Toplevel()
            ventana_tabla.title(tipo)
            ventana_tabla.geometry("900x600")
            ventana_tabla.bind('<Escape>', lambda e: ventana_tabla.destroy())

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

            lbl_cedula = tk.Label(frame_filtros, text="Cédula:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
            lbl_cedula.grid(row=0, column=0, padx=5, pady=5)
            cedula_var = tk.StringVar()
            entry_cedula = tk.Entry(frame_filtros, textvariable=cedula_var, font=("Times New Roman", 14), width=20, bg="#E6E6E6", fg="black", justify="center")
            entry_cedula.grid(row=0, column=1, padx=5, pady=5)

            lbl_nombre = tk.Label(frame_filtros, text="Nombre:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
            lbl_nombre.grid(row=0, column=2, padx=5, pady=5)
            var_nombre = tk.StringVar()
            entry_nombre = tk.Entry(frame_filtros, textvariable=var_nombre, font=("Times New Roman", 14), width=20, bg="#E6E6E6", fg="black", justify="center")
            entry_nombre.grid(row=0, column=3, padx=5, pady=5)

            def validate_numeric_input(new_value):
                return new_value.isdigit() or new_value == ""

            validate_command = ventana_tabla.register(validate_numeric_input)
            entry_cedula.config(validate="key", validatecommand=(validate_command, "%P"))

            def to_uppercase_nombre(*args):
                v = var_nombre.get()
                if v != v.upper():
                    var_nombre.set(v.upper())
            var_nombre.trace_add("write", to_uppercase_nombre)

            lbl_ver = tk.Label(frame_filtros, text="Ver:", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE")
            lbl_ver.grid(row=0, column=4, padx=5, pady=5)
            ver_var = tk.StringVar(value="Activos")
            combo_ver = ttk.Combobox(frame_filtros, textvariable=ver_var, values=("Activos", "Historial"), font=("Times New Roman", 14), width=18, state="readonly", justify="center")
            combo_ver.grid(row=0, column=5, padx=5, pady=5)

            frame_tabla = tk.Frame(ventana_tabla)
            frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

            scrollbar_vertical = tk.Scrollbar(frame_tabla, orient="vertical")
            scrollbar_horizontal = tk.Scrollbar(frame_tabla, orient="horizontal")

            tree = ttk.Treeview(
                frame_tabla,
                columns=("ID", "Cédula", "Nombre Completo", "Característica", "Desde", "Hasta"),
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
                tree.tag_configure('congelado', background='#ADD8E6')
                tree.tag_configure('descongelado', background='#C7F0C7')
            except Exception:
                pass

            tree.heading("ID", text="ID")
            tree.heading("Cédula", text="Cédula")
            tree.heading("Nombre Completo", text="Nombre Completo")
            tree.heading("Característica", text="Característica")
            tree.heading("Desde", text="Desde")
            tree.heading("Hasta", text="Hasta")

            tree.column("ID", width=60, anchor="center")
            tree.column("Cédula", width=120, anchor="center")
            tree.column("Nombre Completo", width=220, anchor="center")
            tree.column("Característica", width=120, anchor="center")
            tree.column("Desde", width=180, anchor="center")
            tree.column("Hasta", width=180, anchor="center")

            def on_cedula_enter(event):
                entry_nombre.focus_set()
            entry_cedula.bind("<Return>", on_cedula_enter)

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
                    entry_cedula.focus_set()
            entry_nombre.bind("<BackSpace>", on_nombre_backspace)

            def reimprimir_factura_fijo(event=None):
                item = tree.focus()
                if not item:
                    return
                vals = tree.item(item, 'values')
                if not vals or len(vals) < 6:
                    return
                if combo_ver.get() == "Activos":
                    messagebox.showinfo("Info", "Solo se pueden reimprimir facturas desde el historial.")
                    ventana_tabla.focus_set()
                    return
                modalidad = tipo
                cedula = vals[1]
                nombre = vals[2]
                caracteristica = vals[3]
                entrada = vals[4]
                salida = vals[5]

                salida_print = salida
                try:
                    tabla_act = 'mensualidadesChaza' if modalidad == 'Mes' else ('quincenasChaza' if modalidad == 'Quincena' else 'semanasChaza')
                    conexion2 = conectar_bd_parqueaderojmj()
                    if conexion2 is not None:
                        cur2 = conexion2.cursor()
                        try:
                            cur2.execute(f"SELECT cedula, caracteristica, salida FROM {tabla_act} WHERE nombreCompleto = ? ORDER BY datetime(salida) DESC LIMIT 1", (nombre,))
                            ract = cur2.fetchone()
                        except Exception:
                            ract = None
                        if ract and len(ract) >= 3 and ract[2]:
                            salida_print = ract[2]
                        try:
                            cur2.close()
                        except Exception:
                            pass
                        try:
                            conexion2.close()
                        except Exception:
                            pass
                except Exception:
                    pass

                try:
                    dt_entrada = None
                    try:
                        dt_entrada = dt.datetime.strptime(entrada, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        try:
                            dt_entrada = dt.datetime.strptime(entrada, "%Y-%m-%d")
                        except Exception:
                            dt_entrada = None

                    if not salida_print or salida_print == "" or dt_entrada is not None and dt.datetime.strptime(salida_print, "%Y-%m-%d %H:%M:%S") <= dt_entrada:
                        dur_map = {"Semana": 7, "Quincena": 15, "Mes": 30}
                        days = dur_map.get(modalidad, 30)
                        if dt_entrada is not None:
                            dt_due = dt_entrada + dt.timedelta(days=days)
                            salida_print = dt_due.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

                try:
                    total = ""
                    try:
                        total = _buscar_valor_pago_chaza(nombre, modalidad, salida_print)
                    except Exception:
                        total = ""

                    try:
                        imprimir_factura_salida_fijo_chaza(modalidad, cedula, nombre, caracteristica, entrada, salida_print, total, usuario_actual)
                    except Exception:
                        pass
                except Exception:
                    pass
            tree.bind("<KeyPress-r>", reimprimir_factura_fijo)
            
            def cargar():
                conexion = conectar_bd_parqueaderojmj()
                if conexion is None:
                    messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                    return
                try:
                    cursor = conexion.cursor()
                    mostrar = ver_var.get()
                    params = []
                    ced = cedula_var.get().strip()
                    nom = var_nombre.get().strip()
                    if mostrar == "Activos":
                        if tipo == "Mensualidades":
                            sql = "SELECT idMensualidadesChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM mensualidadesChaza"
                            id_col = 'idMensualidadesChaza'
                            tabla_activa = 'mensualidadesChaza'
                        elif tipo == "Quincenas":
                            sql = "SELECT idQuincenasChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM quincenasChaza"
                            id_col = 'idQuincenasChaza'
                            tabla_activa = 'quincenasChaza'
                        else:
                            sql = "SELECT idSemanasChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM semanasChaza"
                            id_col = 'idSemanasChaza'
                            tabla_activa = 'semanasChaza'
                        where_clauses = []
                        if ced:
                            where_clauses.append("LOWER(cedula) LIKE ?")
                            params.append(f"%{ced.lower()}%")
                        if nom:
                            where_clauses.append("LOWER(nombreCompleto) LIKE ?")
                            params.append(f"%{nom.lower()}%")
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
                    else:
                        if tipo == "Mensualidades":
                            sql = "SELECT idHistorialMensualidadesChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM historialMensualidadesChaza"
                        elif tipo == "Quincenas":
                            sql = "SELECT idHistorialQuincenasChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM historialQuincenasChaza"
                        else:
                            sql = "SELECT idHistorialSemanasChaza, cedula, nombreCompleto, caracteristica, entrada, salida FROM historialSemanasChaza"
                        where_clauses = []
                        if ced:
                            where_clauses.append("LOWER(cedula) LIKE ?")
                            params.append(f"%{ced.lower()}%")
                        if nom:
                            where_clauses.append("LOWER(nombreCompleto) LIKE ?")
                            params.append(f"%{nom.lower()}%")
                        if where_clauses:
                            sql += " WHERE " + " AND ".join(where_clauses)
                        sql += " ORDER BY datetime(salida) ASC"
                        cursor.execute(sql, tuple(params))
                        rows = cursor.fetchall()
                        tree.delete(*tree.get_children())
                        for row in rows:
                            tree.insert("", "end", values=row)
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar los datos: {e}")
                finally:
                    conexion.close()
            cargar()

            entry_nombre.bind('<KeyRelease>', lambda e: cargar())

            btn_frame_ops = tk.Frame(ventana_tabla, bg="#111111")
            btn_frame_ops.grid(row=2, column=0, sticky="ew", pady=4, padx=10)
            btn_frame_ops.grid_columnconfigure(0, weight=1)
            btn_congelar = tk.Button(btn_frame_ops, text="Congelar", bg="#E6E6E6", fg="#111111", cursor="hand2")
            btn_descongelar = tk.Button(btn_frame_ops, text="Descongelar", bg="#E6E6E6", fg="#111111", cursor="hand2")
            btn_quitar = tk.Button(btn_frame_ops, text="Quitar", bg="#E6E6E6", fg="#111111", cursor="hand2")
            btn_congelar.grid(row=0, column=0, sticky="e", padx=6)
            btn_descongelar.grid(row=0, column=1, sticky="e", padx=6)
            btn_quitar.grid(row=0, column=2, sticky="e", padx=6)

            def actualizar_estado_botones(*args):
                try:
                    if ver_var.get() == "Activos":
                        for w in (btn_congelar, btn_descongelar, btn_quitar):
                            w.config(state="normal")
                    else:
                        for w in (btn_congelar, btn_descongelar, btn_quitar):
                            w.config(state="disabled")
                except Exception:
                    pass

            def congelar_registro():
                try:
                    if ver_var.get() == "Historial":
                        return
                except Exception:
                    pass
                selected = tree.focus()
                if not selected:
                    return
                vals = tree.item(selected, 'values')
                id_reg = vals[0]
                tabla = 'mensualidadesChaza' if tipo=='Mensualidades' else ('quincenasChaza' if tipo=='Quincenas' else 'semanasChaza')
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    id_col = 'idMensualidadesChaza' if tipo=='Mensualidades' else ('idQuincenasChaza' if tipo=='Quincenas' else 'idSemanasChaza')
                    cursor.execute(f"UPDATE {tabla} SET congelado = 1, fechaCongelado = ?, recientementeDescongelado = 0 WHERE {id_col} = ?", (ahora, id_reg))
                    conexion.commit()
                    tree.item(selected, tags=('congelado',))
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo congelar el registro: {e}')
                finally:
                    try:
                        if conexion:
                            conexion.close()
                    except Exception:
                        pass

            def descongelar_registro():
                try:
                    if ver_var.get() == "Historial":
                        return
                except Exception:
                    pass
                selected = tree.focus()
                if not selected:
                    return
                vals = tree.item(selected, 'values')
                id_reg = vals[0]
                tabla = 'mensualidadesChaza' if tipo=='Mensualidades' else ('quincenasChaza' if tipo=='Quincenas' else 'semanasChaza')
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    id_col = 'idMensualidadesChaza' if tipo=='Mensualidades' else ('idQuincenasChaza' if tipo=='Quincenas' else 'idSemanasChaza')
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
                    try:
                        if conexion:
                            conexion.close()
                    except Exception:
                        pass
                cargar()

            def quitar_registro():
                try:
                    if ver_var.get() == "Historial":
                        return
                except Exception:
                    pass
                selected = tree.focus()
                if not selected:
                    return
                if clasificacion_actual == 'Usuario':
                    messagebox.showerror('Error', 'No tienes permiso para quitar registros.')
                    return
                try:
                    if not messagebox.askyesno('Quitar', '¿Seguro que deseas quitar este registro?'):
                        entry_cedula.focus_set()
                        return
                    entry_cedula.focus_set()
                except Exception:
                    pass
                vals = tree.item(selected, 'values')
                id_reg = vals[0]
                cedula = vals[1]
                nombre_sel = vals[2]
                caracteristica = vals[3]
                entrada = vals[4]
                salida = vals[5]
                tabla = 'mensualidadesChaza' if tipo=='Mensualidades' else ('quincenasChaza' if tipo=='Quincenas' else 'semanasChaza')
                tabla_hist = 'historialMensualidadesChaza' if tipo=='Mensualidades' else ('historialQuincenasChaza' if tipo=='Quincenas' else 'historialSemanasChaza')
                try:
                    conexion = conectar_bd_parqueaderojmj()
                    if conexion is None:
                        return
                    cursor = conexion.cursor()
                    cursor.execute(f"INSERT INTO {tabla_hist} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)", (cedula, nombre_sel, caracteristica, entrada, salida))
                    id_col = 'idMensualidadesChaza' if tipo=='Mensualidades' else ('idQuincenasChaza' if tipo=='Quincenas' else 'idSemanasChaza')
                    cursor.execute(f"DELETE FROM {tabla} WHERE {id_col} = ?", (id_reg,))
                    cursor.execute(f"DELETE FROM {tabla_hist} WHERE cedula = ? OR nombreCompleto = ?", (cedula, nombre_sel))
                    conexion.commit()
                    tree.delete(selected)
                    try:
                        actualizarConteoFijos()
                    except Exception:
                        pass
                    try:
                        actualizarConteoModalidadesDelDia()
                    except Exception:
                        pass
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo quitar el registro: {e}')
                finally:
                    try:
                        if conexion:
                            conexion.close()
                    except Exception:
                        pass

            entry_cedula.bind("<KeyRelease>", lambda e: cargar())
            combo_ver.bind("<<ComboboxSelected>>", lambda e: cargar())
            btn_congelar.config(command=congelar_registro)
            btn_descongelar.config(command=descongelar_registro)
            btn_quitar.config(command=quitar_registro)

            for btnw in [btn_congelar, btn_descongelar, btn_quitar]:
                btnw.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                btnw.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="#111111"))

            def focus_entry_cedula():
                entry_cedula.focus_set()
                entry_cedula.icursor('end')
            entry_cedula.bind("<KeyRelease>", lambda e: (cargar(), ventana_tabla.after_idle(focus_entry_cedula)))
            combo_ver.bind("<<ComboboxSelected>>", lambda e: (cargar(), ventana_tabla.after_idle(focus_entry_cedula)))
            cargar()
            ventana_tabla.after_idle(focus_entry_cedula)

            ver_var.trace_add("write", actualizar_estado_botones)
            actualizar_estado_botones()

        btn_mensualidades = tk.Button(frame_botones, text="Mensualidades", font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Mensualidades"))
        btn_quincenas = tk.Button(frame_botones, text="Quincenas", font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Quincenas"))
        btn_semanas = tk.Button(frame_botones, text="Semanas", font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", command=lambda: mostrar_tabla("Semanas"))
        btn_mensualidades.grid(row=0, column=0, padx=10, pady=10)
        btn_quincenas.grid(row=0, column=1, padx=10, pady=10)
        btn_semanas.grid(row=0, column=2, padx=10, pady=10)
        for btn in [btn_mensualidades, btn_quincenas, btn_semanas]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="#111111"))

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
                SET tarifa = REPLACE(tarifa, 'Chaza ', '')
            """
            cursor.execute(query_actualizar)
            conexion.commit()

        except Exception as e:
            messagebox.showerror("Error", f"Error al sincronizar tarifas: {e}")
        finally:
            conexion.close()
    sincronizar_tarifas("tarifaschazas", "%Chaza%")
    try:
        actualizarConteoModalidadesDelDia()
    except Exception:
        pass

    frmRegistro = tk.Frame(parent, bg="#AEAEAE")
    frmRegistro.place(x=0, y=0, relheight=1, relwidth=0.65)
    frmRegistro.pack_propagate(False)

    img_motos = Image.open("iconoChazas.ico").resize((100, 100))
    icono_motos = ImageTk.PhotoImage(img_motos)
    lbl_icono_motos = tk.Label(frmRegistro, image=icono_motos, bg="#AEAEAE")
    lbl_icono_motos.image = icono_motos
    lbl_icono_motos.place(relx=0, rely=1, anchor="sw", x=10, y=-10)


    inicial = usuario_actual.strip()[0].upper() if usuario_actual else "N"
    if inicial not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        inicial = "N"
    icono_path = f"{inicial}.png"
    try:
        imgUsuario = Image.open(icono_path).resize((90, 90))
    except Exception:
        imgUsuario = Image.open("N.png").resize((90, 90))
    iconoUsuario = ImageTk.PhotoImage(imgUsuario)
    lblIconoUsuario = tk.Label(frmRegistro, image=iconoUsuario, bg="#AEAEAE")
    lblIconoUsuario.image = iconoUsuario
    lblIconoUsuario.place(relx=0, rely=0, anchor="nw", x=10, y=10)

    frmRegistroInterno = tk.Frame(frmRegistro, bg="#AEAEAE")
    frmRegistroInterno.pack(expand=True)

    lbl_fecha_hora = tk.Label(frmRegistroInterno, font=("Times New Roman", 25, "bold"), bg="#AEAEAE")
    lbl_fecha_hora.pack(pady=10)

    lbl_nombre = tk.Label(frmRegistroInterno, text="Nombre:", font=("Times New Roman", 18, "bold"), bg="#AEAEAE")
    lbl_nombre.pack(pady=(10, 2))

    nombre_var = tk.StringVar()

    nombre = tk.Entry(frmRegistroInterno, bg="black", fg="white", font=("Times New Roman", 50), width=25, justify="center",
                     textvariable=nombre_var, insertbackground="white")
    nombre.pack(ipady=10)
    nombre.focus_set()

    def to_uppercase_nombre(*args):
        v = nombre_var.get()
        if v != v.upper():
            nombre_var.set(v.upper())
    nombre_var.trace_add("write", to_uppercase_nombre)

    nombre.bind('<Control-b>', lambda event: abrir_tabla_facturas())

    frmCantidad = tk.Frame(frmRegistroInterno, bg="#AEAEAE")
    frmCantidad.pack(pady=5)
    lbl_cantidad = tk.Label(frmCantidad, text="Cantidad:", font=("Times New Roman", 18, "bold"), bg="#AEAEAE")
    lbl_cantidad.pack(side="left", padx=(0, 10))
    cantidad_var = tk.StringVar(value="1")

    def validar_cantidad(*args):
        v = cantidad_var.get()
        if not v.isdigit() or len(v) > 2:
            cantidad_var.set(v[:2] if v[:2].isdigit() else "")
    cantidad_var.trace_add("write", validar_cantidad)

    entry_cantidad = tk.Entry(frmCantidad, textvariable=cantidad_var, font=("Times New Roman", 16), width=2, justify="center")
    entry_cantidad.pack(side="left")

    def on_nombre_enter(event=None):
        entry_cantidad.focus_set()
        entry_cantidad.icursor('end')
        return 'break'
    nombre.unbind('<Return>')
    nombre.bind('<Return>', on_nombre_enter)

    def on_cantidad_enter(event=None):
        btn_registrar.focus_set()
        btn_registrar.invoke()
        return 'break'
    entry_cantidad.unbind('<Return>')
    entry_cantidad.bind('<Return>', on_cantidad_enter)
    
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
        bind_backspace_chain([nombre, entry_cantidad])
    except Exception:
        pass

    frmModalidades1 = tk.Frame(frmRegistroInterno, bg="#AEAEAE")
    frmModalidades1.pack()
    btn_grande = tk.Button(frmModalidades1, text="Grande", font=("Times New Roman", 14, "bold"), width=10, height=1, cursor="hand2")
    btn_mediana = tk.Button(frmModalidades1, text="Mediana", font=("Times New Roman", 14, "bold"), width=10, height=1, cursor="hand2")
    btn_pequena = tk.Button(frmModalidades1, text="Pequeña", font=("Times New Roman", 14, "bold"), width=10, height=1, cursor="hand2")
    btn_grande.pack(side="left", padx=3, pady=3)
    btn_mediana.pack(side="left", padx=3, pady=3)
    btn_pequena.pack(side="left", padx=3, pady=3)

    filaModalidades2 = tk.Frame(frmRegistroInterno, bg="#AEAEAE")
    filaModalidades2.pack()
    btn_mes = tk.Button(filaModalidades2, text="Mes", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_quincena = tk.Button(filaModalidades2, text="Quincena", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_semana = tk.Button(filaModalidades2, text="Semana", width=10, height=1, font=("Times New Roman", 14, "bold"), cursor="hand2")
    btn_mes.pack(side="left", padx=3, pady=3)
    btn_quincena.pack(side="left", padx=3, pady=3)
    btn_semana.pack(side="left", padx=3, pady=3)
    

    botones = [btn_grande, btn_mediana, btn_pequena, btn_semana, btn_quincena, btn_mes]
    modalidad_seleccionada = tk.StringVar(value="Grande")
    modalidad_lock = False
    modalidad_locked_explicit = False
    def seleccionar_boton(boton):
        nonlocal modalidad_lock, modalidad_locked_explicit
        for b in botones:
            b.config(relief="raised", bg="white", fg="black")
        boton.config(relief="sunken", bg="black", fg="white")
        modalidad_seleccionada.set(boton.cget("text"))
        modalidad_lock = True
        modalidad_locked_explicit = True
        try:
            sel = boton.cget("text")
            if sel in ["Semana", "Quincena", "Mes"]:
                try:
                    cantidad_var.set("1")
                except Exception:
                    pass
                try:
                    entry_cantidad.config(state='disabled')
                except Exception:
                    pass
            else:
                try:
                    entry_cantidad.config(state='normal')
                except Exception:
                    pass
        except Exception:
            pass
    for b in botones:
        b.config(command=lambda btn=b: seleccionar_boton(btn))
    seleccionar_boton(btn_grande)


    def askstring_no_cancel(parent, title, prompt, validate=None):
        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.transient(parent)

        result = {"value": None, "closed": True}

        lbl = tk.Label(dlg, text=prompt, justify="left", font=("Times New Roman", 11), padx=10, pady=10)
        lbl.pack()

        var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, font=("Times New Roman", 12), width=30)
        if validate == 'numeric':
            def _only_digits(*args):
                v = var.get()
                filtered = ''.join(filter(str.isdigit, v))
                if v != filtered:
                    var.set(filtered)
            try:
                var.trace_add('write', _only_digits)
            except Exception:
                pass
        elif validate == 'text_upper':
            def _text_upper_no_digits(*args):
                v = var.get()
                filtered = ''.join(ch for ch in v if not ch.isdigit())
                up = filtered.upper()
                if v != up:
                    var.set(up)
            try:
                var.trace_add('write', _text_upper_no_digits)
            except Exception:
                pass
        entry.pack(padx=10, pady=5)

        def on_ok():
            result["value"] = var.get()
            result["closed"] = False
            dlg.destroy()

        def on_close():
            result["value"] = None
            result["closed"] = True
            dlg.destroy()

        btn = tk.Button(dlg, text="OK", command=on_ok, bg="#AEAEAE", fg="#111111", cursor="hand2")
        btn.pack(pady=10)

        for btnw in [btn]:
            btnw.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
            btnw.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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


    btn_registrar = tk.Button(frmRegistroInterno, text="Registrar", font=("Times New Roman", 16, "bold"), bg="white", fg="black", cursor="hand2")
    btn_registrar.pack(pady=20)
    btn_registrar.bind('<Return>', lambda e: (btn_registrar.invoke(), 'break'))

    def confirmar_registro():
        if workflow_state["exit_in_progress"]:
            return
        modalidad_valor = modalidad_seleccionada.get()
        nombre_valor = nombre_var.get().strip()
        if not nombre_valor:
            messagebox.showerror("Error", "El campo Nombre es obligatorio.")
            return
        try:
            cantidad_valor = cantidad_var.get().strip()
        except Exception:
            cantidad_valor = ''
        if not cantidad_valor and modalidad_valor not in ["Mes", "Quincena", "Semana"]:
            messagebox.showerror("Error", "El campo Cantidad es obligatorio.")
            try:
                entry_cantidad.focus_set()
            except Exception:
                pass
            return
        if modalidad_valor in ["Mes", "Quincena", "Semana"]:
            registrar(imprimir_tiquete=False)
            return

        mini = tk.Toplevel()
        mini.title("Opciones de Registro")
        mini.resizable(False, False)
        mini.grab_set()

        tk.Label(mini, text="¿Desea imprimir recibo de entrada?", font=("Times New Roman", 12), padx=10, pady=10).pack()

        def do_imprimir():
            mini.destroy()
            try:
                nombre_valor = nombre_var.get().strip()
                cantidad_valor = cantidad_var.get().strip()
                modalidad_valor = modalidad_seleccionada.get()
                fecha_entrada_valor = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                nombre_valor = nombre_var.get().strip() if nombre_var else ""
                cantidad_valor = cantidad_var.get().strip() if cantidad_var else "1"
                modalidad_valor = modalidad_seleccionada.get() if modalidad_seleccionada else ""
                fecha_entrada_valor = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if nombre_valor and cantidad_valor and modalidad_valor:
                try:
                    imprimir_recibo_entrada_chaza(
                        nombre=nombre_valor,
                        cantidad=cantidad_valor,
                        modalidad=modalidad_valor,
                        fecha_entrada=fecha_entrada_valor,
                        usuario=usuario_actual
                    )
                except Exception as e:
                    try:
                        import traceback
                        tb = traceback.format_exc()
                        print("Error al imprimir recibo (do_imprimir):", e)
                        print(tb)
                    except Exception:
                        pass
                    try:
                        messagebox.showerror("Error de impresión", f"No se pudo imprimir el recibo: {e}\nRevise la consola para más detalles.")
                    except Exception:
                        pass

            try:
                registrar(imprimir_tiquete=False)
            except Exception:
                try:
                    messagebox.showerror("Error", "Ocurrió un error al registrar la entrada. Revise la consola para más detalles.")
                except Exception:
                    pass
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print("Error inesperado en do_imprimir:", e)
                print(tb)
                try:
                    messagebox.showerror("Error", f"Ocurrió un error al preparar el recibo: {e}\nRevise la consola para más detalles.")
                except Exception:
                    pass

        def do_continuar():
            mini.destroy()
            registrar(imprimir_tiquete=False)

        frm = tk.Frame(mini, pady=10)
        frm.pack()
        btn_imp = tk.Button(frm, text="Imprimir recibo", command=do_imprimir, bg="#AEAEAE", fg="#111111", cursor="hand2")
        btn_cont = tk.Button(frm, text="Continuar", command=do_continuar, bg="#AEAEAE", fg="#111111", cursor="hand2")
        btn_imp.grid(row=0, column=0, padx=8)
        btn_cont.grid(row=0, column=1, padx=8)

        for b in [btn_imp, btn_cont]:
            b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
            b.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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

    fechaEntrada = tk.StringVar()
    lblFechaEntrada = tk.Label(frmRegistroInterno, fg="black", text="Fecha y Hora de Entrada: " + fechaEntrada.get(), font=("Times New Roman", 18, "bold"), bg="#AEAEAE")
    lblFechaEntrada.pack(pady=5)

    duracionEn24Horas=tk.StringVar()
    duracionEnHoras=tk.StringVar()

    frmDuracion = tk.Frame(frmRegistroInterno, bg="#AEAEAE")
    frmDuracion.pack(pady=5)

    filaDuracion = tk.Frame(frmDuracion, bg="#AEAEAE")
    filaDuracion.pack()

    lblDuracionEn24Horas = tk.Label(filaDuracion, fg="black", text="24 Horas: " + duracionEn24Horas.get(), font=("Times New Roman", 18, "bold"), bg="#AEAEAE")
    lblDuracionEn24Horas.grid(row=0, column=0, padx=10)

    lblDuracionEnHoras = tk.Label(filaDuracion, fg="black", text="Horas: " + duracionEnHoras.get(), font=("Times New Roman", 18, "bold"), bg="#AEAEAE")
    lblDuracionEnHoras.grid(row=0, column=1, padx=10)

    valor = tk.StringVar(value="Valor: ")
    lblValor = tk.Label(frmRegistro, textvariable=valor, font=("Times New Roman", 18, "bold"), bg="white")
    lblValor.pack(pady=5)

    lblFechaEntrada.pack_forget()
    frmDuracion.pack_forget()
    lblValor.pack_forget()


    def limpiar_pantalla():
        nombre_var.set("")
        nombre.focus_set()
        cantidad_var.set(1)
        nonlocal modalidad_lock, modalidad_locked_explicit
        modalidad_lock = False
        modalidad_locked_explicit = False
        seleccionar_boton(btn_grande)
        frmDuracion.pack_forget()
        lblFechaEntrada.pack_forget()
        lblValor.pack_forget()
        btn_registrar.config(text="Registrar")
    btn_registrar.config(text="Registrar", command=confirmar_registro)

    btn_limpiar = tk.Button(frmRegistro, text="Limpiar Pantalla", font=("Times New Roman", 16, "bold"), bg="white", fg="black", cursor="hand2", command=limpiar_pantalla)
    btn_limpiar.place(relx=1, rely=1, anchor="se", x=-20, y=-20)

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

    def registrar_salida(nombre_valor, valor_cobrado):
        workflow_state["exit_in_progress"] = True
        def on_pago_close(salida_exitosa=False):
            workflow_state["exit_in_progress"] = False
            if salida_exitosa:
                limpiar_pantalla()
            else:
                verificar_nombre()
        mostrar_ventana_pago_chaza(nombre_valor, valor_cobrado, on_pago_close)
        btn_registrar.config(command=confirmar_registro)
        actualizarConteoModalidadesDelDia()
        limpiar_pantalla()

    def mostrar_ventana_pago_chaza(nombre_valor, valor_cobrado, continuar_callback):
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
            for fname in ("fondoChazas.png", "fondoChaza.png", "fondoLogin.png", "fondo.png"):
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

        frmPago = tk.Frame(ventana_pago, bg="#111111", bd=0, relief="flat")
        frmPago.place(relx=0.5, rely=0.5, anchor="center", width=380, height=270)

        lbl_valor = tk.Label(frmPago, text=f"{valor_cobrado}", font=("Times New Roman", 16, "bold"), bg="#111111", fg="#AEAEAE")
        lbl_valor.pack(pady=(50, 10))

        medio_pago = tk.StringVar(value="Efectivo")

        frame_medios_pago = tk.Frame(frmPago, bg="#111111")
        frame_medios_pago.pack(pady=10)

        rb_efectivo = tk.Radiobutton(frame_medios_pago, text="Efectivo", variable=medio_pago, value="Efectivo", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE", activebackground="#111111", activeforeground="#AEAEAE", selectcolor="#111111")
        rb_nequi = tk.Radiobutton(frame_medios_pago, text="Nequi", variable=medio_pago, value="Nequi", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE", activebackground="#111111", activeforeground="#AEAEAE", selectcolor="#111111")
        rb_bancolombia = tk.Radiobutton(frame_medios_pago, text="Bancolombia", variable=medio_pago, value="Bancolombia", font=("Times New Roman", 14, "bold"), bg="#111111", fg="#AEAEAE", activebackground="#111111", activeforeground="#AEAEAE", selectcolor="#111111")

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

                cursor.execute("SELECT idFacturasDeVenta, modalidad, fechaHoraEntrada, cantidad FROM facturasDeVenta WHERE nombreCompleto = ? ORDER BY datetime(fechaHoraEntrada) ASC LIMIT 1", (nombre_valor,))
                row = cursor.fetchone()
                if not row:
                    messagebox.showerror("Error", "No se encontró una factura activa para este cliente.")
                    return

                id_fact, modalidad_pago, fecha_entrada, cantidad_fact = row

                calc_modalidad = modalidad_pago
                if modalidad_pago in ["Grande", "Mediana", "Pequeña"]:
                    calc_modalidad = "24 Horas"

                total_a_cobrar = None
                try:
                    dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                    dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                    duracion_td = dt_salida - dt_entrada
                    total_segundos = int(duracion_td.total_seconds())
                    total_minutos = total_segundos // 60
                    total_horas = total_minutos // 60
                except Exception:
                    total_segundos = 0
                    total_minutos = 0
                    total_horas = 0

                tarifa_valor = None
                try:
                    candidates = [str(calc_modalidad), str(modalidad_pago), str(modalidad_pago).strip().title(), str(modalidad_pago).strip().upper()]
                    if "24" not in str(calc_modalidad):
                        candidates.append("24 Horas")
                    for cand in candidates:
                        try:
                            cursor.execute("SELECT valor FROM tarifaschazas WHERE tarifa = ?", (cand,))
                            r = cursor.fetchone()
                            if r:
                                tarifa_valor = r[0]
                                break
                        except Exception:
                            continue
                except Exception:
                    tarifa_valor = None
                if tarifa_valor is None:
                    try:
                        cursor.execute("SELECT valor FROM tarifaschazas WHERE UPPER(tarifa) LIKE ?", (f"%{str(modalidad_pago).upper()}%",))
                        r = cursor.fetchone()
                        if r:
                            tarifa_valor = r[0]
                    except Exception:
                        tarifa_valor = None

                if tarifa_valor is None:
                    total_a_cobrar = 0
                else:
                    if calc_modalidad == "Hora":
                        tarifa_valor = tarifa_valor
                        ciclo_actual = total_minutos // 60
                        minutos_en_ciclo = total_minutos % 60
                        if ciclo_actual == 0:
                            total_a_cobrar = tarifa_valor
                        else:
                            cuarto_hora = tarifa_valor / 4
                            cuarto_hora_aproximado = (round(cuarto_hora / 100) * 100)

                            if minutos_en_ciclo <= 1:
                                total_a_cobrar = tarifa_valor
                            elif minutos_en_ciclo <= 15:
                                total_a_cobrar = tarifa_valor * ciclo_actual + cuarto_hora_aproximado
                            elif minutos_en_ciclo <= 30:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (2 * cuarto_hora_aproximado)
                            elif minutos_en_ciclo <= 45:
                                total_a_cobrar = tarifa_valor * ciclo_actual + (3 * cuarto_hora_aproximado)
                            else:
                                total_a_cobrar = tarifa_valor * (ciclo_actual + 1)

                    elif calc_modalidad == "24 Horas":
                        tarifa_valor = tarifa_valor
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

                    elif modalidad_pago in ["Semana", "Quincena", "Mes"]:
                        try:
                            duracion_map = {"Semana": 7, "Quincena": 15, "Mes": 30}
                            dias_transcurridos = max(1, math.ceil((dt_salida - dt_entrada).total_seconds() / 86400))
                            duracion_dias = duracion_map.get(modalidad_pago, 30)
                            ciclos = math.ceil(dias_transcurridos / duracion_dias)
                            total_a_cobrar = tarifa_valor * ciclos
                        except Exception:
                            total_a_cobrar = tarifa_valor
                    else:
                        total_a_cobrar = tarifa_valor

                try:
                    cantidad_n = int(cantidad_fact) if cantidad_fact else 1
                except Exception:
                    cantidad_n = 1
                if total_a_cobrar is None:
                    total_a_cobrar = 0
                total_a_cobrar = int(total_a_cobrar) * cantidad_n

                medio_pago_val = medio_pago.get().strip().lower()
                if medio_pago_val in ["efectivo", "cash"]:
                    medio_pago_val = "Efectivo"
                elif medio_pago_val in ["nequi"]:
                    medio_pago_val = "Nequi"
                elif medio_pago_val in ["bancolombia", "banco"]:
                    medio_pago_val = "Bancolombia"
                else:
                    medio_pago_val = medio_pago.get().strip().title()

                try:
                    valor_guardar = float(str(valor_cobrado).replace("$","").replace(",","").replace("Valor:","").strip())
                except Exception:
                    valor_guardar = 0

                try:
                    cursor.execute(
                        "INSERT INTO pagosChazas (nombre, modalidad, valor, medio_pago, fecha) VALUES (?, ?, ?, ?, ?)",
                        (nombre_valor, modalidad_pago, valor_guardar, medio_pago_val, fecha_salida)
                    )
                except Exception:
                    try:
                        cursor.execute(
                            "INSERT INTO pagosChazas (nombreCompleto, modalidad, valor, medio_pago, fecha) VALUES (?, ?, ?, ?, ?)",
                            (nombre_valor, modalidad_pago, valor_guardar, medio_pago_val, fecha_salida)
                        )
                    except Exception:
                        pass

                try:
                    cursor.execute(
                        "UPDATE historialDeFacturas SET fechaSalida = ?, valor = ? WHERE nombreCompleto = ? AND fechaSalida IS NULL",
                        (fecha_salida, valor_cobrado, nombre_valor)
                    )
                except Exception:
                    pass

                # For fixed-modalidades, insert into the corresponding historial tables
                try:
                    if modalidad_pago in ["Semana", "Quincena", "Mes"]:
                        try:
                            for tabla, modalidad_nombre, tabla_hist in [("mensualidadesChaza", "Mes", "historialMensualidadesChaza"), ("quincenasChaza", "Quincena", "historialQuincenasChaza"), ("semanasChaza", "Semana", "historialSemanasChaza")]:
                                try:
                                    cur2 = conexion.cursor()
                                    cur2.execute(f"SELECT cedula, nombreCompleto, caracteristica, entrada, salida FROM {tabla} WHERE nombreCompleto = ?", (nombre_valor,))
                                    fila = cur2.fetchone()
                                    if fila:
                                        cedula_f = fila[0]
                                        nombre_f = fila[1] if len(fila) > 1 and fila[1] is not None else nombre_valor
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
                    cursor.execute("DELETE FROM facturasDeVenta WHERE idFacturasDeVenta = ?", (id_fact,))
                except Exception:
                    try:
                        cursor.execute("DELETE FROM facturasDeVenta WHERE nombreCompleto = ? AND fechaHoraEntrada = ?", (nombre_valor, fecha_entrada))
                    except Exception:
                        pass

                conexion.commit()
                try:
                    actualizarConteoModalidadesDelDia()
                except Exception:
                    pass

                if imprimir_factura:
                    if modalidad_pago in ["Grande", "Mediana", "Pequeña"]:
                        total_valor = str(total_a_cobrar)
                        try:
                            dt_entrada = dt.datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S")
                            dt_salida = dt.datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S")
                            duracion_td = dt_salida - dt_entrada
                            horas, rem = divmod(duracion_td.total_seconds(), 3600)
                            minutos, segundos = divmod(rem, 60)
                            duracion_str = f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
                        except Exception:
                            duracion_str = "-"
                        imprimir_factura_salida_chaza(
                            nombre=nombre_valor,
                            modalidad=modalidad_pago,
                            fecha_entrada=fecha_entrada,
                            fecha_salida=fecha_salida,
                            duracion=duracion_str,
                            total=valor_cobrado,
                            usuario=usuario_actual,
                            cantidad=cantidad_n
                        )
                    else:
                        try:
                            conexion_f = conectar_bd_parqueaderojmj()
                            if conexion_f is not None:
                                cur_f = conexion_f.cursor()
                                for tabla, modalidad_nombre in [("mensualidadesChaza", "Mes"), ("quincenasChaza", "Quincena"), ("semanasChaza", "Semana")]:
                                    cur_f.execute(f"SELECT cedula, nombreCompleto, caracteristica, entrada, salida FROM {tabla} WHERE nombreCompleto = ?", (nombre_valor,))
                                    fila = cur_f.fetchone()
                                    if fila:
                                        cedula_f, nombre_f, caracteristica_f, entrada_f, salida_f = fila
                                        try:
                                            total_val = _buscar_valor_pago_chaza(nombre_f, modalidad_nombre, salida_f)
                                        except Exception:
                                            total_val = "0"

                                        imprimir_factura_salida_fijo_chaza(
                                            modalidad=modalidad_nombre,
                                            cedula=cedula_f,
                                            nombre=nombre_f,
                                            caracteristica=caracteristica_f,
                                            entrada=entrada_f,
                                            salida=salida_f,
                                            total=total_val,
                                            usuario=usuario_actual
                                        )
                        except Exception:
                            pass

                salida_exitosa = True
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la salida: {e}")
            finally:
                if cursor:
                    cursor.close()
                if conexion:
                    conexion.close()

            try:
                btn_registrar.config(text="Registrar", command=confirmar_registro)
            except Exception:
                pass

            ventana_pago.destroy()
            continuar_callback(salida_exitosa)
            try:
                actualizarConteoModalidadesDelDia()
            except Exception:
                pass

        frame_botones = tk.Frame(frmPago, bg="#111111")
        frame_botones.pack(pady=20)

        btn_imprimir = tk.Button(frame_botones, text="Imprimir factura", command=lambda: procesar_salida(True), font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", activebackground="black", activeforeground="#AEAEAE")
        btn_imprimir.grid(row=0, column=0, padx=10)

        btn_continuar = tk.Button(frame_botones, text="Continuar", command=lambda: procesar_salida(False), font=("Times New Roman", 14, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", activebackground="black", activeforeground="#AEAEAE")
        btn_continuar.grid(row=0, column=1, padx=10)

        for btn in [
            btn_imprimir,
            btn_continuar
        ]:
            btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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

    def verificar_nombre(event=None):
        btn_registrar.config(text="Registrar", command=confirmar_registro)
        nombre_valor = nombre_var.get().strip()
        if not nombre_valor:
            btn_registrar.config(text="Registrar", command=confirmar_registro)
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
            query_verificar = "SELECT modalidad, fechaHoraEntrada, cantidad FROM facturasDeVenta WHERE nombreCompleto = ? ORDER BY datetime(fechaHoraEntrada) ASC LIMIT 1"
            cursor.execute(query_verificar, (nombre_valor,))
            resultado = cursor.fetchone()

            if resultado:
                modalidad_valor, hora_entrada, cantidad_reg = resultado
                if modalidad_valor in ["Grande", "Mediana", "Pequeña"]:
                    modalidad_duracion = "24 Horas"
                else:
                    modalidad_duracion = modalidad_valor

                hora_entrada = dt.datetime.strptime(hora_entrada, "%Y-%m-%d %H:%M:%S")
                hora_actual = dt.datetime.now()
                duracion = hora_actual - hora_entrada

                total_segundos = int(duracion.total_seconds())
                total_minutos = total_segundos // 60
                total_horas = total_minutos // 60
                total_24_horas = total_horas // 24
                horas_restantes = total_horas % 24

                if modalidad_duracion == "24 Horas":
                    duracionEn24Horas.set(str(total_24_horas))
                    duracionEnHoras.set(str(horas_restantes))
                    lblDuracionEn24Horas.config(text="24 Horas: " + duracionEn24Horas.get())
                    lblDuracionEn24Horas.grid()
                    lblDuracionEnHoras.config(text="Horas: " + duracionEnHoras.get())
                    lblDuracionEnHoras.grid()
                elif modalidad_duracion == "Hora":
                    total_minutos = total_segundos // 60
                    horas_para_hora = total_minutos // 60
                    duracionEn24Horas.set("0")
                    duracionEnHoras.set(str(horas_para_hora))
                    lblDuracionEn24Horas.grid_remove()
                    lblDuracionEnHoras.config(text="Horas: " + duracionEnHoras.get())
                    lblDuracionEnHoras.grid()
                else:
                    lblDuracionEn24Horas.grid_remove()
                    lblDuracionEnHoras.grid_remove()

                try:
                    for b in [btn_grande, btn_mediana, btn_pequena, btn_semana, btn_quincena, btn_mes]:
                        if b.cget('text').strip().lower() == str(modalidad_valor).strip().lower():
                            seleccionar_boton(b)
                            break
                except Exception:
                    pass

                calc_modalidad = "24 Horas" if modalidad_valor in ["Grande", "Mediana", "Pequeña"] else modalidad_valor
                query_tarifa = "SELECT valor FROM tarifaschazas WHERE tarifa = ?"
                fila = None
                candidates = [str(calc_modalidad), str(modalidad_valor), str(modalidad_valor).strip().title(), str(modalidad_valor).strip().upper()]
                if "24" not in str(calc_modalidad):
                    candidates.append("24 Horas")
                for cand in candidates:
                    try:
                        cursor.execute(query_tarifa, (cand,))
                        fila = cursor.fetchone()
                        if fila:
                            break
                    except Exception:
                        fila = None
                        continue
                if not fila:
                    try:
                        cursor.execute("SELECT valor FROM tarifaschazas WHERE UPPER(tarifa) LIKE ?", (f"%{str(modalidad_valor).upper()}%",))
                        fila = cursor.fetchone()
                    except Exception:
                        fila = None
                if not fila:
                    try:
                        cursor.execute("SELECT valor FROM tarifaschazas WHERE UPPER(tarifa) LIKE ?", (f"%{str(modalidad_valor).upper()}%",))
                        fila = cursor.fetchone()
                    except Exception:
                        fila = None
                if fila:
                    tarifa_valor = fila[0]
                    total_a_cobrar = None
                    try:
                        if calc_modalidad == "Hora":
                            ciclo_actual = total_minutos // 60
                            minutos_en_ciclo = total_minutos % 60
                            if ciclo_actual == 0:
                                total_a_cobrar = tarifa_valor
                            else:
                                cuarto_hora = tarifa_valor / 4
                                cuarto_hora_aproximado = (round(cuarto_hora / 100) * 100)
                                if minutos_en_ciclo <= 1:
                                    total_a_cobrar = tarifa_valor
                                elif minutos_en_ciclo <= 15:
                                    total_a_cobrar = tarifa_valor * ciclo_actual + cuarto_hora_aproximado
                                elif minutos_en_ciclo <= 30:
                                    total_a_cobrar = tarifa_valor * ciclo_actual + (2 * cuarto_hora_aproximado)
                                elif minutos_en_ciclo <= 45:
                                    total_a_cobrar = tarifa_valor * ciclo_actual + (3 * cuarto_hora_aproximado)
                                else:
                                    total_a_cobrar = tarifa_valor * (ciclo_actual + 1)

                        elif calc_modalidad == "24 Horas":
                            total_horas_local = total_segundos // 3600
                            ciclo_actual = total_horas_local // 24
                            horas_en_ciclo = total_horas_local % 24
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
                                dias_transcurridos = max(1, math.ceil((hora_actual - hora_entrada).total_seconds() / 86400))
                                duracion_dias = duracion_map.get(modalidad_valor, 30)
                                ciclos = math.ceil(dias_transcurridos / duracion_dias)
                                total_a_cobrar = tarifa_valor * ciclos
                            except Exception:
                                total_a_cobrar = tarifa_valor
                        else:
                            total_a_cobrar = tarifa_valor
                    except Exception:
                        total_a_cobrar = tarifa_valor

                    try:
                        cantidad_n = int(cantidad_reg) if cantidad_reg else 1
                    except Exception:
                        cantidad_n = 1
                    try:
                        total_a_cobrar = int(total_a_cobrar or 0) * cantidad_n
                    except Exception:
                        total_a_cobrar = total_a_cobrar

                    valor.set(f"Valor: {total_a_cobrar}")
                else:
                    valor.set("Valor: Tarifa no encontrada")

                fechaEntrada.set(hora_entrada.strftime("%d/%m/%Y %H:%M:%S"))
                frmDuracion.pack(pady=5)
                lblFechaEntrada.config(text="Fecha y Hora de Entrada: " + fechaEntrada.get())
                lblFechaEntrada.pack(pady=5)
                lblValor.pack(pady=5)
                try:
                    cantidad_var.set(str(cantidad_reg))
                except Exception:
                    pass

                for btn in [btn_grande, btn_mediana, btn_pequena, btn_semana, btn_quincena, btn_mes]:
                    if btn.cget("text") == modalidad_valor:
                        try:
                            if not modalidad_lock:
                                seleccionar_boton(btn)
                        except Exception:
                            seleccionar_boton(btn)

                fechaEntrada.set(hora_entrada.strftime("%d/%m/%Y %H:%M:%S"))

                btn_registrar.config(
                    text="Facturar",
                    command=lambda: registrar_salida(nombre_var.get(), valor.get())
                )
            else:
                btn_registrar.config(text="Registrar", command=confirmar_registro)
                frmDuracion.pack_forget()
                lblValor.pack_forget()
                lblFechaEntrada.pack_forget()
                try:
                    seleccionar_boton(btn_grande)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar el registro: {e}")
        finally:
            conexion.close()

    nombre.bind("<KeyRelease>", verificar_nombre)

    nombre.bind('<Return>', on_nombre_enter)

    def registrar(imprimir_tiquete=False):
        nombre_valor = nombre_var.get().strip()
        modalidad_valor = modalidad_seleccionada.get()
        if not nombre_valor:
            messagebox.showerror("Error", "El campo Nombre es obligatorio.")
            nombre.focus_set()
            return

        cantidad = cantidad_var.get().strip()
        tablas_fijas = {
            "Semana": ("semanasChaza", 7, "idSemanasChaza", "historialSemanasChaza"),
            "Quincena": ("quincenasChaza", 15, "idQuincenasChaza", "historialQuincenasChaza"),
            "Mes": ("mensualidadesChaza", 30, "idMensualidadesChaza", "historialMensualidadesChaza")
        }

        if modalidad_valor in tablas_fijas:
            try:
                cantidad_int = int(cantidad) if cantidad else 1
            except Exception:
                cantidad_int = 1
        else:
            if not cantidad:
                messagebox.showerror("Error", "El campo Cantidad es obligatorio.")
                try:
                    entry_cantidad.focus_set()
                except Exception:
                    pass
                return
            try:
                cantidad_int = int(cantidad)
                if cantidad_int <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror("Error", "Cantidad inválida. Ingrese un número mayor que 0.")
                try:
                    entry_cantidad.focus_set()
                except Exception:
                    pass
                return

        modalidad_valor = modalidad_seleccionada.get()
        hora_actual = dt.datetime.now()

        tablas_fijas = {
            "Semana": ("semanasChaza", 7, "idSemanasChaza", "historialSemanasChaza"),
            "Quincena": ("quincenasChaza", 15, "idQuincenasChaza", "historialQuincenasChaza"),
            "Mes": ("mensualidadesChaza", 30, "idMensualidadesChaza", "historialMensualidadesChaza")
        }

        if modalidad_valor in tablas_fijas:
            tabla, duracion_dias, id_col, _ = tablas_fijas[modalidad_valor]

            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return

            try:
                cursor = conexion.cursor()

                try:
                    cursor.execute(f"SELECT {id_col}, cedula, caracteristica, entrada, salida FROM {tabla} WHERE nombreCompleto = ?", (nombre_valor,))
                    existentes = cursor.fetchall()
                except Exception:
                    existentes = []

                if existentes:
                    # Ask for cédula first to disambiguate clients with the same name
                    try:
                        cedula_input = askstring_no_cancel(frmRegistro, "Cédula", "Ingrese la cédula del cliente:", validate='numeric')
                    except Exception:
                        cedula_input = None

                    if not cedula_input:
                        # User cancelled or didn't provide cedula: abort registration to avoid ambiguity
                        try:
                            conexion.rollback()
                        except Exception:
                            pass
                        return

                    # Verify cedula exists in administrative `clientes` table
                    try:
                        c_check = conexion.cursor()
                        c_check.execute("SELECT nombreCompleto FROM clientes WHERE cedula = ?", (cedula_input,))
                        cliente_row = c_check.fetchone()
                        c_check.close()
                        if not cliente_row:
                            messagebox.showerror("Cliente no encontrado", "El cliente no existe en el sistema, por favor créalo primero.", parent=frmRegistro)
                            try:
                                conexion.rollback()
                            except Exception:
                                pass
                            return
                        # normalize name from admin table (use official name)
                        nombre_oficial = cliente_row[0]
                    except Exception:
                        nombre_oficial = nombre_valor

                    # Filter existing records by cedula if possible
                    existentes_por_cedula = [r for r in existentes if len(r) > 1 and r[1] and str(r[1]) == str(cedula_input)]

                    if existentes_por_cedula:
                        existentes = existentes_por_cedula
                    else:
                        caracteristica_nueva = askstring_no_cancel(frmRegistro, "Característica", "Ingrese la característica de la chaza:", validate='text_upper')
                        if not caracteristica_nueva:
                            try:
                                conexion.rollback()
                            except Exception:
                                pass
                            return

                        entrada_nueva = hora_actual.replace(microsecond=0)
                        if modalidad_valor == "Mes":
                            salida_nueva = add_months(entrada_nueva, months=1) - dt.timedelta(days=1)
                        else:
                            salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                        try:
                            cursor.execute(
                                f"INSERT INTO {tabla} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula_input, nombre_oficial if nombre_oficial else nombre_valor, caracteristica_nueva, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )

                            cursor.execute(
                                "INSERT INTO facturasDeVenta (nombreCompleto, cantidad, modalidad, fechaHoraEntrada) VALUES (?, ?, ?, ?)",
                                (nombre_oficial if nombre_oficial else nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            try:
                                cursor.execute(
                                    "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                                    (nombre_oficial if nombre_oficial else nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                                )
                            except Exception:
                                pass
                            conexion.commit()
                            try:
                                actualizarConteoFijos()
                                actualizarConteoModalidadesDelDia()
                            except Exception as e:
                                messagebox.showerror("Error", f"Error actualizando conteo fijos: {e}")
                            try:
                                actualizarConteoModalidadesDelDia()
                            except Exception as e:
                                messagebox.showerror("Error", f"Error actualizando conteos del día: {e}")
                        except Exception as e:
                            conexion.rollback()
                            messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                            return
                        limpiar_pantalla()
                        actualizarConteoModalidadesDelDia()
                        return

                    opciones = []
                    for r in existentes:
                        try:
                            rid = r[0]
                            rcar = r[2] if len(r) > 2 else ""
                        except Exception:
                            try:
                                rid = r[0]
                            except Exception:
                                rid = None
                            rcar = str(r[1]) if len(r) > 1 else ""
                        opciones.append((rid, rcar or ""))

                    ventana_choice = tk.Toplevel()
                    ventana_choice.title("Registro(s) encontrado(s)")
                    ventana_choice.resizable(False, False)
                    ventana_choice.grab_set()
                    ventana_choice.focus_set()

                    texto = f"Se encontraron {len(opciones)} registro(s) para este cliente:\nNombre: {nombre_valor}\n\nCaracterísticas disponibles:\n"
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
                    btn_add = tk.Button(frm_btns, text="Agregar", command=accion_agregar, bg="#AEAEAE", fg="#111111", cursor="hand2")
                    btn_skip = tk.Button(frm_btns, text="Continuar", command=accion_omitir, bg="#AEAEAE", fg="#111111", cursor="hand2")
                    btn_add.grid(row=0, column=0, padx=8)
                    btn_skip.grid(row=0, column=1, padx=8)

                    for b in [btn_add, btn_skip]:
                        b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                        b.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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
                            combo_sel.current(0)
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
                        btn_use_sel = tk.Button(frm_sel_btns, text="Usar seleccionado", command=usar_seleccion, bg="#AEAEAE", fg="#111111", cursor="hand2")
                        btn_use_sel.grid(row=0, column=0, padx=8)
                        for b in [btn_use_sel]:
                            b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                            b.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

                        ventana_select.transient()
                        ventana_select.wait_window()

                    if decision["accion"] is None:
                        return

                    if decision["accion"] == "agregar":
                        caracteristica_nueva = askstring_no_cancel(frmRegistro, "Característica", "Ingrese la característica de la chaza:", validate='text_upper')
                        if not caracteristica_nueva:
                            return

                        entrada_nueva = hora_actual.replace(microsecond=0)
                        if modalidad_valor == "Mes":
                            salida_nueva = add_months(entrada_nueva, months=1)
                            salida_nueva = salida_nueva - dt.timedelta(days=1)
                        else:
                            salida_nueva = (entrada_nueva + dt.timedelta(days=duracion_dias)) - dt.timedelta(days=1)

                        try:
                            cedula_base = existentes[0][1] if existentes and existentes[0][1] else ""
                            cursor.execute(
                                f"INSERT INTO {tabla} (cedula, nombreCompleto, caracteristica, entrada, salida) VALUES (?, ?, ?, ?, ?)",
                                (cedula_base, nombre_valor, caracteristica_nueva, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )

                            cursor.execute(
                                "INSERT INTO facturasDeVenta (nombreCompleto, cantidad, modalidad, fechaHoraEntrada) VALUES (?, ?, ?, ?)",
                                (nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            try:
                                cursor.execute(
                                    "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                                    (nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                                )
                            except Exception:
                                pass
                            conexion.commit()
                            try:
                                actualizarConteoFijos()
                                actualizarConteoModalidadesDelDia()
                            except Exception as e:
                                messagebox.showerror("Error", f"Error actualizando conteo fijos: {e}")
                            try:
                                actualizarConteoModalidadesDelDia()
                            except Exception as e:
                                messagebox.showerror("Error", f"Error actualizando conteos del día: {e}")
                        except Exception as e:
                            conexion.rollback()
                            messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                            return
                        limpiar_pantalla()
                        actualizarConteoModalidadesDelDia()
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
                            try:
                                id_exist = sel_row[0] if len(sel_row) > 0 else None
                                entrada_prev = sel_row[3] if len(sel_row) > 3 else (sel_row[1] if len(sel_row) > 1 else None)
                                salida_prev = sel_row[4] if len(sel_row) > 4 else (sel_row[2] if len(sel_row) > 2 else None)
                            except Exception:
                                try:
                                    id_exist = sel_row[0]
                                except Exception:
                                    id_exist = None
                                entrada_prev = sel_row[1] if len(sel_row) > 1 else None
                                salida_prev = sel_row[2] if len(sel_row) > 2 else None
                            try:
                                actualizarConteoModalidadesDelDia()
                            except Exception:
                                pass

                    salida_prev_dt = None
                    try:
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

                    def optar_continuar():
                        opcion["valor"] = "continuar"
                        ventana_confirm.destroy()

                    def optar_modificar():
                        opcion["valor"] = "modificar"
                        ventana_confirm.destroy()

                    frm_bot = tk.Frame(ventana_confirm, pady=10)
                    frm_bot.pack()
                    btn_cont = tk.Button(frm_bot, text="Continuar", command=optar_continuar, bg="#AEAEAE", fg="#111111", cursor="hand2")
                    btn_mod = tk.Button(frm_bot, text="Modificar", command=optar_modificar, bg="#AEAEAE", fg="#111111", cursor="hand2")
                    btn_cont.grid(row=0, column=0, padx=10)
                    btn_mod.grid(row=0, column=1, padx=10)

                    for b in [btn_cont, btn_mod]:
                        b.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                        b.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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

                        btn_ok = tk.Button(ventana_editar, text="OK", command=on_ok_editar, bg="#AEAEAE", fg="#111111", cursor="hand2")
                        btn_ok.pack(pady=10)
                        btn_ok.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                        btn_ok.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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

                        cursor.execute(
                            "INSERT INTO facturasDeVenta (nombreCompleto, cantidad, modalidad, fechaHoraEntrada) VALUES (?, ?, ?, ?)",
                            (nombre_valor, cantidad_int, modalidad_valor, entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        try:
                            cursor.execute(
                                "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                                (nombre_valor, cantidad_int, modalidad_valor, entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                        except Exception:
                            pass
                        conexion.commit()
                        try:
                            actualizarConteoFijos()
                            actualizarConteoModalidadesDelDia()
                        except Exception as e:
                            messagebox.showerror("Error", f"Error actualizando conteo fijos: {e}")
                        try:
                            actualizarConteoModalidadesDelDia()
                        except Exception as e:
                            messagebox.showerror("Error", f"Error actualizando conteos del día: {e}")
                        try:
                            if imprimir_tiquete:
                                try:
                                    imprimir_recibo_entrada_chaza(nombre_valor, cantidad_int, modalidad_valor, entrada_para_guardar.strftime("%Y-%m-%d %H:%M:%S"), usuario_actual)
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
                            import traceback
                            tb = traceback.format_exc()
                            print("Error inesperado al intentar imprimir en registrar:", e)
                            print(tb)
                            try:
                                messagebox.showerror("Error", f"Ocurrió un error al intentar imprimir: {e}\nRevise la consola para más detalles.")
                            except Exception:
                                pass
                    except Exception as e:
                        conexion.rollback()
                        messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")
                        return
                    limpiar_pantalla()
                    return

                cedula = askstring_no_cancel(frmRegistro, "Cédula", "Ingrese la cédula del cliente:", validate='numeric')
                if not cedula:
                    return
                nombre_completo = nombre_valor
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
                    pass

                caracteristica = askstring_no_cancel(frmRegistro, "Característica", "Ingrese la característica de la chaza:", validate='text_upper')
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
                        (cedula if cedula else "", nombre_completo if nombre_completo else "", caracteristica, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), salida_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                    )

                    cursor.execute(
                        "INSERT INTO facturasDeVenta (nombreCompleto, cantidad, modalidad, fechaHoraEntrada) VALUES (?, ?, ?, ?)",
                        (nombre_completo, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    try:
                        cursor.execute(
                            "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                            (nombre_completo, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                        )
                    except Exception:
                        pass
                    conexion.commit()
                    try:
                        actualizarConteoFijos()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error actualizando conteo fijos: {e}")
                    try:
                        actualizarConteoModalidadesDelDia()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error actualizando conteos del día: {e}")
                    try:
                        if imprimir_tiquete:
                            try:
                                imprimir_recibo_entrada_chaza(nombre_completo, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"), usuario_actual)
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception as e:
                    conexion.rollback()
                    messagebox.showerror("Error", f"No se pudo insertar el registro: {e}")
                    return
                finally:
                    conexion.close()
                limpiar_pantalla()
                actualizarConteoModalidadesDelDia()
                return
            except Exception as e:
                try:
                    conexion.rollback()
                except Exception:
                    pass
                messagebox.showerror("Error", f"Error en el proceso de registro: {e}")
                return
            finally:
                try:
                    if conexion:
                        conexion.close()
                except Exception:
                    pass

        else:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                entrada_nueva = hora_actual.replace(microsecond=0)
                cursor.execute(
                    "INSERT INTO facturasDeVenta (nombreCompleto, cantidad, modalidad, fechaHoraEntrada) VALUES (?, ?, ?, ?)",
                    (nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                )
                try:
                    cursor.execute(
                        "INSERT INTO historialDeFacturas (nombreCompleto, cantidad, modalidad, fechaEntrada, fechaSalida) VALUES (?, ?, ?, ?, NULL)",
                        (nombre_valor, cantidad_int, modalidad_valor, entrada_nueva.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                except Exception:
                    pass
                conexion.commit()
                try:
                    actualizarConteoModalidadesDelDia()
                except Exception:
                    pass
            except Exception as e:
                conexion.rollback()
                messagebox.showerror("Error", f"No se pudo insertar la factura de venta: {e}")
            finally:
                conexion.close()
            limpiar_pantalla()
            actualizarConteoModalidadesDelDia()
            return


    frmRegistrosDia = tk.Frame(parent, border=1, relief="solid", bg="#1B1B1B")
    frmRegistrosDia.place(x=0, y=0, relx=0.65, relheight=0.5, relwidth=0.175)
    frmRegistrosDia.pack_propagate(False)

    frameDiaInterno = tk.Frame(frmRegistrosDia, bg="#1B1B1B")
    frameDiaInterno.pack(expand=True)

    lblClientesDiarios = tk.Label(frameDiaInterno, text="Registros del Día", font=("Times New Roman", 18, "bold"), bg="#1B1B1B", fg="white")
    lblClientesDiarios.pack(pady=(10))

    grandes = 0
    medianas = 0
    pequenas = 0
    totalClientesDiarios = grandes + medianas + pequenas

    lblGrandes = tk.Label(frameDiaInterno, text=f"Grandes: {grandes}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white", width=15)
    lblGrandes.pack(pady=5)
    lblMedianas = tk.Label(frameDiaInterno, text=f"Medianas: {medianas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white", width=15)
    lblMedianas.pack(pady=5)
    lblPequenas = tk.Label(frameDiaInterno, text=f"Pequeñas: {pequenas}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white", width=15)
    lblPequenas.pack(pady=5)
    lblTotalClientesDiarios = tk.Label(frameDiaInterno, text=f"Total: {totalClientesDiarios}", font=("Times New Roman", 16, "bold"), bg="#1B1B1B", fg="white", width=15)
    lblTotalClientesDiarios.pack(pady=5)

    def actualizarConteoModalidadesDelDia():
        conexion = None
        try:
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                return
            cursor = conexion.cursor()
            cursor.execute("SELECT COUNT(*) FROM facturasDeVenta WHERE modalidad = 'Grande' AND date(fechaHoraEntrada) = date('now', 'localtime')")
            cnt_grandes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM facturasDeVenta WHERE modalidad = 'Mediana' AND date(fechaHoraEntrada) = date('now', 'localtime')")
            cnt_medianas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM facturasDeVenta WHERE modalidad = 'Pequeña' AND date(fechaHoraEntrada) = date('now', 'localtime')")
            cnt_pequenas = cursor.fetchone()[0]

            nonlocal pequenas, medianas, grandes, totalClientesDiarios
            pequenas = cnt_pequenas
            medianas = cnt_medianas
            grandes = cnt_grandes
            totalClientesDiarios = pequenas + medianas + grandes
            lblGrandes.config(text=f"Grandes: {grandes}")
            lblMedianas.config(text=f"Medianas: {medianas}")
            lblPequenas.config(text=f"Pequeñas: {pequenas}")
            lblTotalClientesDiarios.config(text=f"Total: {totalClientesDiarios}")

        except Exception:
            pass
        finally:
            if conexion:
                conexion.close()

    actualizarConteoModalidadesDelDia()

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

    def asegurar_columnas_fijas(conexion):
        tablas = ["semanasChaza", "quincenasChaza", "mensualidadesChaza"]
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
            cursor.execute("SELECT COUNT(*) FROM semanasChaza")
            cnt_semanas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM quincenasChaza")
            cnt_quincenas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mensualidadesChaza")
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

    btn_kwargs = {"width": 25, "height": 1, "font": ("Times New Roman", 14, "bold"), "cursor": "hand2"}
    btnFacturas = tk.Button(frameFuncionesInterno, text="Consultar Facturas de Venta", **btn_kwargs)
    btnHistorialDeFacturas = tk.Button(frameFuncionesInterno, text="Historial de Facturas", **btn_kwargs)
    btnClientesFijos = tk.Button(frameFuncionesInterno, text="Consultar Clientes", **btn_kwargs)
    btnTarifas = tk.Button(frameFuncionesInterno, text="Tarifas", **btn_kwargs)
    btnArqueoCaja = tk.Button(frameFuncionesInterno, text="Arqueo de Caja", **btn_kwargs)

    btnFacturas.pack(pady=8)
    btnHistorialDeFacturas.pack(pady=8)
    btnClientesFijos.pack(pady=8)
    btnTarifas.pack(pady=8)
    btnArqueoCaja.pack(pady=8)

    for btn in [
        btn_registrar,
        btn_limpiar,
        btnFacturas,
        btnHistorialDeFacturas,
        btnClientesFijos,
        btnTarifas,
        btnArqueoCaja
    ]:
        btn.bind("<Enter>", lambda e: e.widget.config(bg="#1B1B1B", fg="white"))
        btn.bind("<Leave>", lambda e: e.widget.config(bg="white", fg="black"))


    def mostrar_tarifas_chazas():
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

        def cargar_tarifas_chazas():
            ventana_tarifas.focus_set()
            conexion = conectar_bd_parqueaderojmj()
            if conexion is None:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
                return
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT rowid, tarifa, duracion, valor FROM tarifaschazas")
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

        cargar_tarifas_chazas()

    btnTarifas.config(command=mostrar_tarifas_chazas)
    btnFacturas.config(command=mostrar_facturas_de_venta)
    btnHistorialDeFacturas.config(command=mostrar_historial_de_facturas)
    btnClientesFijos.config(command=consultar_clientes_fijos)

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
                query = '''SELECT medio_pago, SUM(valor) FROM pagosChazas WHERE date(fecha) >= ? AND date(fecha) <= ? GROUP BY medio_pago'''
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
            title = "ARQUEO DE CHAZAS"
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
                        texto = _fix_mojibake(texto)
                        try:
                            payload = texto.encode('cp1252')
                        except Exception:
                            try:
                                payload = texto.encode('cp850')
                            except Exception:
                                try:
                                    payload = texto.encode('cp437')
                                except Exception:
                                    try:
                                        payload = texto.encode('latin-1')
                                    except Exception:
                                        payload = texto.encode('utf-8', errors='replace')

                        win32print.WritePrinter(hPrinter, payload)
                        win32print.EndPagePrinter(hPrinter)
                        win32print.EndDocPrinter(hPrinter)
                    finally:
                        if hPrinter:
                            win32print.ClosePrinter(hPrinter)

                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo imprimir en la impresora: {e}")

            btn_imprimir = tk.Button(resumen, text="Imprimir", font=("Times New Roman", 13, "bold"), bg="#AEAEAE", fg="#111111", cursor="hand2", command=imprimir_ventana)
            btn_imprimir.pack(pady=50)

            for btn in [
                btn_imprimir
            ]:
                btn.bind("<Enter>", lambda e: e.widget.config(bg="black", fg="#AEAEAE"))
                btn.bind("<Leave>", lambda e: e.widget.config(bg="#AEAEAE", fg="black"))

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

    btnArqueoCaja.config(command=arqueo_de_caja)

    nombre.bind('<Control-b>', lambda event: abrir_tabla_facturas())